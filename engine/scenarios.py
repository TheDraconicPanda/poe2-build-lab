"""Controlled what-if edits. Recalculate both sides through the pinned engine."""
import re
import xml.etree.ElementTree as ET
from engine.calculator import calculate

ES_MOD = re.compile(r'^(\s*)(\d+)% increased maximum Energy Shield(\s*)$')


def integer(value, label, maximum):
    if type(value) is not int or not 0 <= value <= maximum:
        raise ValueError(f'{label} must be an integer from 0 to {maximum}.')
    return value


def apply_scenario(text, scenario):
    from app import decode_build, parse_build
    if not isinstance(scenario, dict) or set(scenario) - {'jewels', 'chestEnergyShield'}:
        raise ValueError('Scenario accepts only jewels and chestEnergyShield.')
    build = parse_build(text)
    root = decode_build(text)
    changes = []
    if 'jewels' in scenario:
        config = scenario['jewels']
        if not isinstance(config, dict) or set(config) - {'mode', 'itemId', 'targetPercent'}:
            raise ValueError('Invalid jewel scenario.')
        mode = config.get('mode')
        if mode not in ('one', 'all', 'remove'):
            raise ValueError('Jewel mode must be one, all or remove.')
        candidates = build['jewels']
        if mode != 'all':
            candidates = [j for j in candidates if j['id'] == config.get('itemId')]
        else:
            candidates = [j for j in candidates if j['esIncrease'] is not None]
        if not candidates:
            raise ValueError('Select an allocated jewel in the active weapon set.')
        if mode != 'remove':
            target = integer(config.get('targetPercent'), 'Jewel increased ES', 1000)
        items = {i.get('id'): i for i in root.findall('./Items/Item')}
        for jewel in candidates:
            if mode == 'remove':
                node_id = jewel['slot'].removeprefix('Jewel ')
                # Socket bindings are per tree spec. Select exactly the active one.
                tree = root.find('Tree')
                spec = next((s for s in tree.findall('Spec') if s.get('id') == tree.get('activeSpec')), None)
                if spec is None:
                    spec = tree.findall('Spec')[int(tree.get('activeSpec', '1')) - 1]
                socket = next(s for s in spec.findall('./Sockets/Socket') if s.get('nodeId') == node_id)
                socket.set('itemId', '0')
                changes.append(dict(kind='removeJewel', itemId=jewel['id'], name=jewel['name'], nodeId=node_id))
                continue
            item = items[jewel['id']]
            lines = (item.text or '').splitlines(keepends=True)
            matches = [index for index, line in enumerate(lines) if ES_MOD.fullmatch(line)]
            # Reject decorated, ranged or duplicate lines rather than rewriting an
            # implicit/variant/corruption with ambiguous effect semantics.
            if len(matches) != 1:
                raise ValueError(f"{jewel['name']} needs exactly one plain increased maximum ES modifier.")
            index = matches[0]
            match = ES_MOD.fullmatch(lines[index])
            old = int(match[2])
            lines[index] = f'{match[1]}{target}% increased maximum Energy Shield{match[3]}'
            item.text = ''.join(lines)
            changes.append(dict(kind='jewel', itemId=jewel['id'], name=jewel['name'], before=old, after=target))
    chest_es = None
    if 'chestEnergyShield' in scenario:
        chest_es = integer(scenario['chestEnergyShield'], 'Final local chest ES', 100000)
        chest = next((i for i in build['equipment'] if i['slot'] == 'Body Armour'), None)
        if chest is None:
            raise ValueError('No body armour is equipped in the active item set.')
        changes.append(dict(kind='chest', itemId=chest['id'], name=chest['name'], after=chest_es))
    return ET.tostring(root, encoding='unicode'), chest_es, changes


def compare_scenario(text, scenario):
    edited, chest_es, changes = apply_scenario(text, scenario)
    baseline = calculate(text)
    after = calculate(edited, body_armour_es=chest_es)
    for change in changes:
        if change['kind'] == 'chest':
            chest = next((item for item in baseline['items'] if item['slot'] == 'Body Armour'), None)
            if chest is None:
                raise ValueError('The engine did not resolve local body armour defences.')
            change['before'] = chest['energyShield']
    deltas = {stat: dict(before=value, after=after['totals'][stat], absolute=after['totals'][stat] - value,
                        percent=(after['totals'][stat] - value) / value * 100 if value else None)
              for stat, value in baseline['totals'].items()}
    warnings = [
        'Results use the pinned PoB2 snapshot; only the original baseline is confirmed in game.',
        'Jewel stat edits retain every other modifier. All-jewel mode includes allocated jewels with the supported plain ES modifier.',
        'Chest ES is final local ES after quality and local modifiers. Other chest stats, sockets and effects stay fixed; this is not a full item replacement or a claim that the item can be crafted.',
    ]
    if not baseline['reconciled']:
        warnings.insert(0, 'The calculated baseline does not match both exported totals. Resolve the baseline before trusting an upgrade.')
    return dict(baseline=baseline, upgraded=after, changes=changes, deltas=deltas, warnings=warnings)
