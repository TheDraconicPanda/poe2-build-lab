"""Version-pinned PoB2 subprocess adapter. Never uses saved build outputs."""
import json
import math
import os
from pathlib import Path
import subprocess
import tempfile
import threading
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
PINS = json.loads((ROOT / 'engine/pins.json').read_text())
LOCK = threading.Lock()


class EngineUnavailable(RuntimeError):
    pass


def prepare_input(text):
    from app import decode_build
    root = decode_build(text)
    build = root.find('Build')
    tree = root.find('Tree')
    if build is None or tree is None:
        raise ValueError('A Build section and selected passive tree are required.')
    specs = tree.findall('Spec')
    spec = next((s for s in specs if s.get('id') == tree.get('activeSpec')), None)
    if spec is None:
        try:
            index = int(tree.get('activeSpec', '1')) - 1
            if index < 0:
                raise ValueError()
            spec = specs[index]
        except (IndexError, ValueError) as exc:
            raise ValueError('Active passive tree is missing.') from exc
    if spec.get('treeVersion') != '0_5':
        raise ValueError('The pinned defence engine currently supports tree 0_5 only.')
    reference = {}
    for stat in build.findall('PlayerStat'):
        if stat.get('stat') in ('Life', 'EnergyShield'):
            try:
                value = float(stat.get('value', ''))
                if math.isfinite(value):
                    reference[stat.get('stat')] = value
            except ValueError:
                pass
        build.remove(stat)
    for stat in build.findall('MinionStat'):
        build.remove(stat)
    metadata = dict(nodes=[n for n in spec.get('nodes', '').split(',') if n],
                    treeVersion=spec.get('treeVersion'), activeSpec=tree.get('activeSpec'),
                    activeItemSet=root.find('Items').get('activeItemSet') if root.find('Items') is not None else None,
                    useSecondWeaponSet=(root.find('Items').get('useSecondWeaponSet') if root.find('Items') is not None else None),
                    activeConfigSet=root.find('Config').get('activeConfigSet') if root.find('Config') is not None else None,
                    activeSkillSet=root.find('Skills').get('activeSkillSet') if root.find('Skills') is not None else None)
    items = root.find('Items')
    if items is not None:
        selected_set = next((item_set for item_set in items.findall('ItemSet') if item_set.get('id') == items.get('activeItemSet')), None)
        if selected_set is not None:
            metadata['useSecondWeaponSet'] = selected_set.get('useSecondWeaponSet', items.get('useSecondWeaponSet'))
    return ET.tostring(root, encoding='unicode'), reference, metadata


def calculate(text):
    xml, reference, metadata = prepare_input(text)
    local = ROOT / '.local'
    runtime = local / 'luajit/bin/luajit'
    source = local / 'pob2'
    if not runtime.is_file() or not (source / 'src/HeadlessWrapper.lua').is_file() or not (local / 'lua/lua-utf8.so').is_file():
        raise EngineUnavailable('Calculation engine is not installed. Run python scripts/setup_engine.py first.')
    if not LOCK.acquire(blocking=False):
        raise EngineUnavailable('A calculation is already running. Try again shortly.')
    try:
        actual = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
        dirty = subprocess.check_output(['git', '-C', str(source), 'diff', 'HEAD', '--'], text=True)
        if actual != PINS['pob2']['commit'] or dirty:
            raise EngineUnavailable('Engine revision or tracked files differ from the pin. Restore the pinned engine before calculating.')
        env = os.environ.copy()
        env['LUA_PATH'] = '../runtime/lua/?.lua;../runtime/lua/?/init.lua;;'
        env['LUA_CPATH'] = str(local / 'lua/?.so') + ';;'
        with tempfile.TemporaryDirectory(prefix='poe2-calc-') as directory:
            input_path = Path(directory) / 'build.xml'
            input_path.write_text(xml)
            meta_path = Path(directory) / 'metadata.json'
            meta_path.write_text(json.dumps(metadata))
            completed = subprocess.run([str(runtime), str(ROOT / 'engine/runner.lua'), str(input_path), str(meta_path)],
                                       cwd=source / 'src', env=env, capture_output=True, text=True, timeout=60)
        if completed.returncode:
            raise EngineUnavailable('PoB2 calculation failed: ' + completed.stderr[-1500:])
        try:
            result = json.loads(completed.stdout)
        except ValueError as exc:
            raise EngineUnavailable('Engine returned invalid output.') from exc
        if result['missingAllocatedNodes']:
            raise ValueError('Allocated nodes are absent from the pinned tree: ' + ', '.join(result['missingAllocatedNodes']))
        result['reference'] = reference
        result['comparison'] = {stat: dict(reference=reference.get(stat), calculated=value,
                                          difference=value - reference[stat] if stat in reference else None)
                                for stat, value in result['totals'].items()}
        result['reconciled'] = all(stat in reference and reference[stat] == result['totals'][stat] for stat in ('Life', 'EnergyShield'))
        result['provenance'] = dict(engine='PathOfBuildingCommunity/PathOfBuilding-PoE2', commit=actual,
                                    treeVersion=metadata['treeVersion'], savedOutputsRemoved=True,
                                    patch='0.5.5 user-confirmed fixture; engine snapshot compatibility is build-specific',
                                    selection=metadata)
        return result
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, OSError) as exc:
        raise EngineUnavailable('Engine execution failed or timed out. Check the local installation.') from exc
    finally:
        LOCK.release()
