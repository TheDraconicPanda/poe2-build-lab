import unittest
from pathlib import Path
import xml.etree.ElementTree as ET
from engine.calculator import calculate, prepare_input

FIXTURE = Path(__file__).parent / 'fixtures/abyssal-lich-0.5.5.xml'


class EngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.xml = FIXTURE.read_text()
        cls.result = calculate(cls.xml)

    def test_exact_baseline_and_sources(self):
        result = self.result
        self.assertEqual(result['totals'], dict(Life=1892, EnergyShield=6091))
        self.assertTrue(result['reconciled'])
        self.assertTrue(result['provenance']['savedOutputsRemoved'])
        self.assertEqual(result['missingAllocatedNodes'], [])
        self.assertTrue(any(r['source'].startswith('Quest:') for r in result['ledger']))
        self.assertTrue(any(r['source'].startswith('Tree:') for r in result['ledger']))
        self.assertTrue(any(r['source'].startswith('Item:') for r in result['ledger']))
        self.assertTrue(any(r['source'] == 'Strength' and r['value'] == 274 for r in result['ledger']))
        self.assertTrue(any(r['scope'] == 'Helmet' and r['value'] == 70 for r in result['ledger']))
        self.assertEqual([row['base'] for row in result['breakdown']['EnergyShield']['slots']], [74,65,173,215,86,341])
        self.assertTrue(any("Nature's Archon" in r['line'] for r in result['unsupported']))

    def test_saved_totals_cannot_drive_calculation(self):
        xml = self.xml.replace('stat="Life" value="1892"', 'stat="Life" value="999999"').replace('stat="EnergyShield" value="6091"', 'stat="EnergyShield" value="1"')
        result = calculate(xml)
        self.assertEqual(result['totals'], self.result['totals'])
        self.assertFalse(result['reconciled'])
        self.assertEqual(result['comparison']['EnergyShield']['difference'], 6090)

    def test_no_saved_outputs_still_calculates(self):
        stripped, _, _ = prepare_input(self.xml)
        self.assertNotIn('<PlayerStat', stripped)
        result = calculate(stripped)
        self.assertEqual(result['totals'], self.result['totals'])
        self.assertEqual(result['reference'], {})
        self.assertFalse(result['reconciled'])

    def test_real_item_change_propagates_to_life_and_es(self):
        xml = self.xml.replace('+67 to maximum Life', '+77 to maximum Life')
        result = calculate(xml)
        self.assertEqual(result['totals'], dict(Life=1902, EnergyShield=6103))
        self.assertFalse(result['reconciled'])


class EngineInputTests(unittest.TestCase):
    def test_other_tree_version_rejected(self):
        with self.assertRaisesRegex(ValueError, 'tree 0_5'):
            prepare_input(FIXTURE.read_text().replace('treeVersion="0_5"', 'treeVersion="0_4"'))

    def test_all_saved_stats_removed_and_selections_preserved(self):
        xml, references, metadata = prepare_input(FIXTURE.read_text())
        root = ET.fromstring(xml)
        self.assertEqual(root.findall('./Build/PlayerStat'), [])
        self.assertEqual(references, dict(Life=1892, EnergyShield=6091))
        self.assertEqual(metadata['activeItemSet'], '1')
        self.assertEqual(metadata['activeSpec'], '1')
        self.assertIn('7960', metadata['nodes'])

if __name__ == '__main__':
    unittest.main()
