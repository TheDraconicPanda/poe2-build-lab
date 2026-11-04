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
    if not isinstance(scenario, dict) or set(scenario) - {'jewels', 'chestEnergyShield', 'darknessRune', 'ingenuity'}:
        raise ValueError('Unsupported scenario field.')
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
    if 'darknessRune' in scenario and 'ingenuity' in scenario:
        raise ValueError('Choose a Darkness Enthroned rune swap or an Ingenuity replacement, not both.')
    if 'darknessRune' in scenario:
        config = scenario['darknessRune']
        if not isinstance(config, dict) or set(config) - {'socket', 'rune', 'effectPercent'}:
            raise ValueError('Invalid Darkness Enthroned scenario.')
        socket = integer(config.get('socket'), 'Socket number', 2)
        if socket < 1:
            raise ValueError('Socket number must be 1 or 2.')
        rune = config.get('rune')
        if rune not in ('None', 'Iron Rune', 'Greater Iron Rune', 'Perfect Iron Rune'):
            raise ValueError('Select a supported Iron Rune or an empty socket.')
        belt = next((i for i in build['equipment'] if i['slot'] == 'Belt'), None)
        if belt is None or belt['name'] != 'Darkness Enthroned':
            raise ValueError('Darkness Enthroned must be equipped for a rune swap.')
        if 'This item gains bonuses from Socketed Items as though it was a Body Armour' not in belt['text']:
            raise ValueError('Only the Body Armour variant of Darkness Enthroned is validated.')
        item = next(i for i in root.findall('./Items/Item') if i.get('id') == belt['id'])
        lines = item.text.splitlines(keepends=True)
        rune_indices = [index for index,line in enumerate(lines) if line.strip().startswith('Rune: ')]
        sockets = [line for line in lines if line.strip().startswith('Sockets: ')]
        if len(sockets) != 1 or len(sockets[0].strip().split()[1:]) != 2 or len(rune_indices) != 2:
            raise ValueError('Expected two explicit socket bindings, including Rune: None for an empty socket.')
        index = rune_indices[socket - 1]
        previous = lines[index].strip().removeprefix('Rune: ')
        if previous not in ('None', 'Fox Idol', 'Rune of the Blossom', 'Iron Rune', 'Greater Iron Rune', 'Perfect Iron Rune'):
            raise ValueError('The existing augment is outside the validated set.')
        lines[index] = re.sub(r'Rune: [^\r\n]+', 'Rune: ' + rune, lines[index])
        effects = [(i,re.fullmatch(r'(\s*)(\d+)% increased effect of Socketed Augment Items(\s*)', line)) for i,line in enumerate(lines)]
        effects = [(i,m) for i,m in effects if m]
        if len(effects) != 1:
            raise ValueError('Expected one explicit augment-effect roll.')
        effect_index, match = effects[0]
        old_effect = int(match[2])
        effect = config.get('effectPercent', old_effect)
        integer(effect, 'Augment effect', 100)
        if effect < 50:
            raise ValueError('Darkness Enthroned augment effect must be 50–100%.')
        lines[effect_index] = f'{match[1]}{effect}% increased effect of Socketed Augment Items{match[3]}'
        item.text = ''.join(lines)
        changes.append(dict(kind='darknessRune', name=belt['name'], socket=socket, before=previous, after=rune,
                            effectBefore=old_effect, effectAfter=effect))
    if 'ingenuity' in scenario:
        config = scenario['ingenuity']
        if not isinstance(config, dict) or set(config) - {'leftPercent', 'rightPercent', 'charmSlots'}:
            raise ValueError('Invalid Ingenuity scenario.')
        left = integer(config.get('leftPercent'), 'Left-ring effect', 30)
        right = integer(config.get('rightPercent'), 'Right-ring effect', 30)
        slots = integer(config.get('charmSlots'), 'Charm slots', 3)
        if min(left,right) < 20 or slots < 1:
            raise ValueError('Current Ingenuity requires 20–30% per ring and 1–3 charm slots.')
        belt = next((i for i in build['equipment'] if i['slot'] == 'Belt'), None)
        if belt is None:
            raise ValueError('Equip a belt before comparing its replacement.')
        item = next(i for i in root.findall('./Items/Item') if i.get('id') == belt['id'])
        item.text = f'''\nRarity: UNIQUE
Ingenuity
Utility Belt
Implicits: 2
Has {slots} Charm Slots
20% of Flask Recovery applied Instantly
0% reduced Charm Charges gained
0% reduced Charm Charges used
{left}% increased bonuses gained from left Equipped Ring
{right}% increased bonuses gained from right Equipped Ring
'''
        for child in list(item):
            item.remove(child)
        changes.append(dict(kind='ingenuity', name='Belt replacement', before=belt['name'], after='Ingenuity',
                            leftPercent=left, rightPercent=right, charmSlots=slots))
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
    if 'darknessRune' in scenario:
        warnings.append('The selected augment is replaced, including its regular and Bonded effects. PoB rebuilds all rune effects in the Body Armour context; a rune Bonded line is not automatically active.')
    if 'ingenuity' in scenario:
        warnings.append('Ingenuity replaces the entire belt and removes its socketed effects. Left = Ring 1, right = Ring 2. This current-version template uses neutral charm-charge rolls; it is not a legacy 40–80% belt.')
    for label, side in [('Original', baseline), ('Changed', after)]:
        if side.get('resources', {}).get('SpiritUnreserved', 0) < 0:
            warnings.insert(0, f'{label} build has insufficient Spirit for the selected skills. Defence totals are conditional on that skill setup and cannot be treated as a usable upgrade without fixing reservations.')
    saved_resources = baseline['provenance']['selection'].get('resourceReference', {})
    for stat, saved in saved_resources.items():
        calculated = baseline.get('resources', {}).get(stat)
        if calculated is not None and calculated != saved:
            warnings.append(f'{stat} is diagnostic and not reconciled: original engine value {calculated}, exported value {saved:g}.')
    if not baseline['reconciled']:

        warnings.insert(0, 'The calculated baseline does not match both exported totals. Resolve the baseline before trusting an upgrade.')
    return dict(baseline=baseline, upgraded=after, changes=changes, deltas=deltas, warnings=warnings)
