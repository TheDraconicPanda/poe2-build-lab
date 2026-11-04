import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET
from engine.calculator import calculate
from engine.scenarios import apply_scenario, compare_scenario

FIXTURE = Path(__file__).parent / 'fixtures/abyssal-lich-0.5.5.xml'
CASES = json.loads((FIXTURE.parent / 'defence-scenarios.json').read_text())['cases']


class ScenarioEngineTests(unittest.TestCase):
    def test_scenarios_against_independent_export_edits(self):
        original = FIXTURE.read_text()
        for case in CASES:
            with self.subTest(case=case['name']):
                # These edits do not call the scenario transformer or local-ES override.
                independent = original
                for old, new in case['edits']:
                    self.assertIn(old, independent)
                    independent = independent.replace(old, new)
                reference = calculate(independent)
                self.assertEqual(reference['totals'], case['expected'])
                if 'expectedLocalChestES' in case:
                    chest = next(i for i in reference['items'] if i['slot'] == 'Body Armour')
                    self.assertEqual(chest['energyShield'], case['expectedLocalChestES'])
                result = compare_scenario(original, case['scenario'])
                self.assertEqual(result['baseline']['totals'], dict(Life=1892, EnergyShield=6091))
                self.assertTrue(result['baseline']['reconciled'])
                self.assertEqual(result['upgraded']['totals'], reference['totals'])
                self.assertEqual(result['deltas']['EnergyShield']['absolute'], case['expected']['EnergyShield'] - 6091)
                self.assertEqual(result['deltas']['Life']['absolute'], 0)
        # A literal 200 -> 400 example, rather than only comparing each with 215.
        at_200 = original.replace('136% increased Evasion and Energy Shield', '119% increased Evasion and Energy Shield')
        result = compare_scenario(at_200, {'chestEnergyShield':400})
        self.assertEqual(result['deltas']['EnergyShield']['absolute'], 1266)
        # A no-op local override and no-op jewel edit must both preserve totals.
        result = compare_scenario(original, {'chestEnergyShield':215, 'jewels':{'mode':'one','itemId':'2','targetPercent':16}})
        self.assertEqual(result['baseline']['totals'], result['upgraded']['totals'])


class ScenarioInputTests(unittest.TestCase):
    def setUp(self):
        self.xml = FIXTURE.read_text()

    def test_jewel_edit_is_isolated(self):
        edited, es, changes = apply_scenario(self.xml, {'jewels':{'mode':'one','itemId':'2','targetPercent':20}})
        old = ET.fromstring(self.xml)
        new = ET.fromstring(edited)
        old_item = old.find('./Items/Item[@id="2"]')
        new_item = new.find('./Items/Item[@id="2"]')
        self.assertEqual(new_item.text, old_item.text.replace('16% increased maximum Energy Shield','20% increased maximum Energy Shield'))
        new_item.text = old_item.text
        self.assertEqual(ET.tostring(old), ET.tostring(new))
        self.assertIsNone(es)
        self.assertEqual(len(changes), 1)

    def test_chest_override_preserves_all_export_fields(self):
        edited, es, changes = apply_scenario(self.xml, {'chestEnergyShield':400})
        self.assertEqual(ET.tostring(ET.fromstring(edited)), ET.tostring(ET.fromstring(self.xml)))
        self.assertEqual(es, 400)
        self.assertEqual(changes[0]['itemId'], '15')

    def test_inactive_jewel_rejected(self):
        xml = self.xml.replace(',61834,', ',', 1)
        with self.assertRaisesRegex(ValueError, 'allocated jewel'):
            apply_scenario(xml, {'jewels':{'mode':'one','itemId':'2','targetPercent':20}})

    def test_invalid_scenarios_rejected(self):
        invalid = [None, [], {'unknown':1}, {'jewels':{}}, {'jewels':{'mode':'all','targetPercent':True}},
                   {'jewels':{'mode':'all','targetPercent':20.5}}, {'chestEnergyShield':-1},
                   {'chestEnergyShield':float('nan')}, {'chestEnergyShield':100001},
                   {'jewels':{'mode':'one','itemId':'999','targetPercent':20}}]
        for scenario in invalid:
            with self.subTest(scenario=scenario), self.assertRaises(ValueError):
                apply_scenario(self.xml, scenario)

    def test_ambiguous_modifier_rejected(self):
        xml = self.xml.replace('16% increased maximum Energy Shield','16% increased maximum Energy Shield\n17% increased maximum Energy Shield')
        with self.assertRaisesRegex(ValueError, 'exactly one'):
            apply_scenario(xml, {'jewels':{'mode':'one','itemId':'2','targetPercent':20}})

    def test_remove_does_not_delete_inventory_item(self):
        edited, _, _ = apply_scenario(self.xml, {'jewels':{'mode':'remove','itemId':'2'}})
        root = ET.fromstring(edited)
        self.assertIsNotNone(root.find('./Items/Item[@id="2"]'))
        self.assertEqual(root.find('./Tree/Spec/Sockets/Socket[@nodeId="61834"]').get('itemId'), '0')

if __name__ == '__main__':
    unittest.main()
