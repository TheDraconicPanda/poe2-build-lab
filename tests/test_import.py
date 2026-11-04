import base64
from pathlib import Path
import unittest
import zlib
from app import parse_build, decode_build

FIXTURE = Path(__file__).parent / 'fixtures' / 'abyssal-lich-0.5.5.xml'

class ImportTests(unittest.TestCase):
    def setUp(self):
        self.xml = FIXTURE.read_text()

    def test_confirmed_character(self):
        result = parse_build(self.xml)
        self.assertEqual(result['stats']['Life'], 1892)
        self.assertEqual(result['stats']['EnergyShield'], 6091)
        self.assertEqual(result['character']['treeVersion'], '0_5')
        self.assertEqual(result['character']['ascendancy'], 'Abyssal Lich')
        self.assertEqual(len(result['equipment']), 14)
        self.assertEqual(len(result['jewels']), 5)
        self.assertEqual(sorted(j['esIncrease'] for j in result['jewels']), [14,15,16,20,20])
        self.assertTrue(any('94% increased effect' in i['text'] for i in result['equipment']))
        self.assertTrue(any('30% increased Global Armour' in q['value'] for q in result['quests']))

    def test_export_roundtrip(self):
        code = base64.urlsafe_b64encode(zlib.compress(self.xml.encode())).decode().rstrip('=')
        self.assertEqual(parse_build(code), parse_build(self.xml))

    def test_inactive_set_does_not_leak(self):
        xml = self.xml.replace('<ItemSet id="1"', '<ItemSet id="2"><Slot itemId="1" name="Helmet"/></ItemSet><ItemSet id="1"', 1)
        self.assertEqual(parse_build(xml)['equipment'], parse_build(self.xml)['equipment'])

    def test_unallocated_jewel_excluded(self):
        xml = self.xml.replace(',7960,', ',', 1)
        self.assertEqual(len(parse_build(xml)['jewels']), 4)

    def test_inactive_weapon_tree_jewel_excluded(self):
        xml = self.xml.replace('<WeaponSet2 nodes="', '<WeaponSet2 nodes="7960,', 1)
        self.assertEqual(len(parse_build(xml)['jewels']), 4)

    def test_active_weapon_items_selected(self):
        xml = self.xml.replace('<Slot itemId="0" itemPbURL="" name="Weapon 1 Swap"/>', '<Slot itemId="1" name="Weapon 1 Swap"/>', 1)
        normal = parse_build(xml)
        swapped = parse_build(xml.replace('useSecondWeaponSet="false"', 'useSecondWeaponSet="true"'))
        self.assertTrue(any(i['id'] == '6' for i in normal['equipment']))
        self.assertFalse(any(i['id'] == '6' for i in swapped['equipment']))
        self.assertTrue(any(i['id'] == '1' for i in swapped['equipment']))

    def test_missing_active_set_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Active item set'):
            parse_build(self.xml.replace('activeItemSet="1"', 'activeItemSet="99"'))

    def test_nonfinite_stats_ignored(self):
        result = parse_build(self.xml.replace('stat="Life" value="1892"', 'stat="Life" value="nan"'))
        self.assertNotIn('Life', result['stats'])

    def test_entity_declaration_rejected(self):
        with self.assertRaises(ValueError):
            decode_build('<!DOCTYPE x [<!ENTITY x "a">]><PathOfBuilding2/>')

    def test_poe1_export_rejected(self):
        with self.assertRaises(ValueError):
            parse_build('<PathOfBuilding/>')

    def test_malformed_inputs_rejected(self):
        for text in ['not an export', '<broken', 'https://pobb.in/example', '']:
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_build(text)

    def test_decompression_limit(self):
        code = base64.urlsafe_b64encode(zlib.compress(b'x' * 2_000_001)).decode()
        with self.assertRaises(ValueError):
            decode_build(code)

if __name__ == '__main__':
    unittest.main()
