"""Engine integration expectations, with independently edited reference exports."""
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET
from engine.calculator import calculate
from engine.scenarios import apply_scenario, compare_scenario

FIXTURE = Path(__file__).parent / 'fixtures/abyssal-lich-0.5.5.xml'


def reference_belt(xml, left_life=59, right_life=80, left_spirit=18, right_spirit=16):
    # Independent of the Ingenuity constructor and of bonus-effect modifiers.
    # Start with a neutral belt, then manually apply truncated ring Life/Spirit.
    root = ET.fromstring(xml)
    belt = root.find('./Items/Item[@id="8"]')
    belt.text = '\nRarity: RARE\nReference Belt\nUtility Belt\nImplicits: 2\nHas 3 Charm Slots\n20% of Flask Recovery applied Instantly\n'
    for child in list(belt):
        belt.remove(child)
    for item_id, old_life, new_life, spirit in [('19',46,left_life,left_spirit),('7',67,right_life,right_spirit)]:
        item = root.find(f'./Items/Item[@id="{item_id}"]')
        item.text = item.text.replace(f'+{old_life} to maximum Life', f'+{new_life} to maximum Life').replace('+14 to Spirit', f'+{spirit} to Spirit')
    return ET.tostring(root,encoding='unicode')


class InteractionEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.xml = FIXTURE.read_text()

    def test_iron_tiers_and_replacement(self):
        for rune, increase, es in [('Iron Rune',31,6386),('Greater Iron Rune',34,6415),('Perfect Iron Rune',38,6453)]:
            with self.subTest(rune=rune):
                result = compare_scenario(self.xml, {'darknessRune':{'socket':1,'rune':rune,'effectPercent':94}})
                independent = calculate(self.xml.replace('Rune: Fox Idol', 'Rune: '+rune))
                self.assertEqual(result['upgraded']['totals'], independent['totals'])
                self.assertEqual(result['upgraded']['totals'], dict(Life=1892,EnergyShield=es))
                mods = result['upgraded']['ledger']
                belt_es = sum(row['value'] for row in mods if row['scope']=='Global' and row['source'].startswith('Item:8:') and row['stat']=='EnergyShield')
                self.assertEqual(belt_es, increase)
                self.assertEqual(result['changes'][0]['before'], 'Fox Idol')
                belt = next(i for i in result['upgraded']['equipment'] if i['slot']=='Belt')
                self.assertEqual(belt['runes'], [rune,'Rune of the Blossom'])

    def test_empty_socket_and_second_occupied_socket(self):
        for source, socket, old, expected in [
            (self.xml.replace('Rune: Fox Idol','Rune: None'),1,'None',6386),
            (self.xml,2,'Rune of the Blossom',6386)]:
            with self.subTest(socket=socket,old=old):
                result = compare_scenario(source, {'darknessRune':{'socket':socket,'rune':'Iron Rune'}})
                self.assertEqual(result['upgraded']['totals']['EnergyShield'], expected)
                self.assertEqual(result['changes'][0]['before'], old)
                self.assertTrue(result['baseline']['reconciled'])
        # Combined same-stat runes aggregate before their additional effect is truncated.
        source = self.xml.replace('Rune: Fox Idol','Rune: Greater Iron Rune')
        result = compare_scenario(source, {'darknessRune':{'socket':2,'rune':'Greater Iron Rune'}})
        mods = result['upgraded']['ledger']
        self.assertEqual(sum(r['value'] for r in mods if r['scope']=='Global' and r['source'].startswith('Item:8:') and r['stat']=='EnergyShield'), 69)

    def test_rune_noop_and_effect_roll(self):
        source = self.xml.replace('Rune: Fox Idol','Rune: Iron Rune')
        result = compare_scenario(source, {'darknessRune':{'socket':1,'rune':'Iron Rune'}})
        self.assertEqual(result['baseline']['totals'], result['upgraded']['totals'])
        result = compare_scenario(self.xml, {'darknessRune':{'socket':1,'rune':'Iron Rune','effectPercent':100}})
        mods=result['upgraded']['ledger']
        self.assertEqual(sum(r['value'] for r in mods if r['scope']=='Global' and r['source'].startswith('Item:8:') and r['stat']=='EnergyShield'),32)

    def test_ingenuity_sides_rounding_and_reservations(self):
        for left,right,life,es,l1,l2,s1,s2 in [(30,20,1919,6122,59,80,18,16),(20,30,1922,6122,55,87,16,18),(30,30,1927,6129,59,87,18,18)]:
            with self.subTest(left=left,right=right):
                result=compare_scenario(self.xml, {'ingenuity':{'leftPercent':left,'rightPercent':right,'charmSlots':3}})
                independent=calculate(reference_belt(self.xml,l1,l2,s1,s2))
                self.assertEqual(result['upgraded']['totals'], independent['totals'])
                self.assertEqual(result['upgraded']['totals'],dict(Life=life,EnergyShield=es))
                self.assertEqual(result['upgraded']['resources'], independent['resources'])
                self.assertLess(result['upgraded']['resources']['SpiritUnreserved'],0)
                self.assertTrue(any('insufficient Spirit' in w for w in result['warnings']))
                self.assertTrue(any('diagnostic and not reconciled' in w for w in result['warnings']))
                belt=next(i for i in result['upgraded']['equipment'] if i['slot']=='Belt')
                self.assertEqual(belt['name'],'Ingenuity, Utility Belt')
                self.assertEqual(belt['runes'],[])
                self.assertFalse(any('Darkness Enthroned' in r['source'] for r in result['upgraded']['ledger']))

    def test_combined_interaction_jewel_and_chest(self):
        result=compare_scenario(self.xml, {'darknessRune':{'socket':1,'rune':'Iron Rune'},
            'jewels':{'mode':'one','itemId':'2','targetPercent':20}, 'chestEnergyShield':400})
        independent=self.xml.replace('Rune: Fox Idol','Rune: Iron Rune').replace(
            '16% increased maximum Energy Shield','20% increased maximum Energy Shield').replace(
            '136% increased Evasion and Energy Shield','339% increased Evasion and Energy Shield')
        self.assertEqual(result['upgraded']['totals'],calculate(independent)['totals'])
        self.assertEqual(result['upgraded']['totals'],dict(Life=1892,EnergyShield=7660))


class InteractionInputTests(unittest.TestCase):
    def test_conflicting_belts_and_invalid_inputs_rejected(self):
        xml=FIXTURE.read_text()
        for config in [
            {'darknessRune':{'socket':0,'rune':'Iron Rune'}},
            {'darknessRune':{'socket':1,'rune':'Unknown'}},
            {'darknessRune':{'socket':1,'rune':'Iron Rune','effectPercent':101}},
            {'darknessRune':{'socket':1,'rune':'Iron Rune','effectPercent':49}},
            {'ingenuity':{'leftPercent':80,'rightPercent':80,'charmSlots':3}},
            {'ingenuity':{'leftPercent':30,'rightPercent':20,'charmSlots':0}},
            {'ingenuity':{'leftPercent':True,'rightPercent':20,'charmSlots':3}},
            {'darknessRune':{},'ingenuity':{}}]:
            with self.subTest(config=config),self.assertRaises(ValueError):
                apply_scenario(xml,config)

    def test_unsupported_socket_context_rejected(self):
        xml=FIXTURE.read_text().replace('as though it was a Body Armour','as though it was a Helmet')
        with self.assertRaisesRegex(ValueError,'Body Armour'):
            apply_scenario(xml,{'darknessRune':{'socket':1,'rune':'Iron Rune'}})

    def test_replacement_removes_exported_rune_effects(self):
        edited,_,_=apply_scenario(FIXTURE.read_text(),{'ingenuity':{'leftPercent':30,'rightPercent':20,'charmSlots':3}})
        root=ET.fromstring(edited)
        self.assertNotIn('Rune:',root.find('./Items/Item[@id="8"]').text)
        self.assertEqual(root.find('./Items/ItemSet/Slot[@name="Belt"]').get('itemId'),'8')
        self.assertEqual(len(root.findall('./Items/Item')),19)

if __name__=='__main__':
    unittest.main()
