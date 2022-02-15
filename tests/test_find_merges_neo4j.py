"""Tests the find merges neo4j script"""
import unittest
from rdkit import Chem
from merge.find_merges_neo4j import MergerFinder_neo4j

merger = MergerFinder_neo4j()

class TestFindMerges(unittest.TestCase):

    def test_check_for_nodes(self):
        true_smi = Chem.MolToSmiles(Chem.MolFromSmiles("CC=1C=CC(CS(=O)(=O)N)=CC1F"))
        false_smi = "CC(NC(=O)CCl)c1cccc(Cl)c1s"
        true_results = (1, 2)
        results = merger.check_for_nodes([true_smi, false_smi])
        self.assertEqual(true_results, results)

    def test_get_synthons(self):
        smi = Chem.MolToSmiles(Chem.MolFromSmiles("CC=1C=CC(CS(=O)(=O)N)=CC1F"))
        synthons = merger.get_synthons(smi)
        num_synthons = 13
        self.assertEqual(num_synthons, len(synthons))

    def test_get_expansions(self):
        smi = Chem.MolToSmiles(Chem.MolFromSmiles("CC=1C=CC(CS(=O)(=O)N)=CC1F"))
        smi2 = Chem.MolToSmiles(Chem.MolFromSmiles("CS(=O)(=O)NCCC=1C=CC=CC1"))
        results = merger.get_expansions([smi, smi2], ["x0034_0B", "x0176_0B"], "nsp13", None)
        print(results)
        dict_len = 2
        self.assertEqual(dict_len, len(results))

## new code tests ###

    def test_get_unique_synthons(self):
        nameA = 'x0176_0B'
        nameBs = ['x0034_0B', 'x0183_0B', 'x0438_0B']
        target = 'nsp13'
        unique_synthons, synthon_dict = merger.get_unique_synthons(nameA, nameBs, target)
        self.assertEqual(19, len(unique_synthons))
        self.assertEqual(3, len(synthon_dict))
        self.assertEqual(10, len(synthon_dict['x0034_0B']))

    def test_expand_fragmentA(self):
        name_pairs = [["x0034_0B", "x0176_0B"]]
        target = 'nsp13'
        output_dir = 'tests/test_output'
        merger.expand_fragmentA(name_pairs, target, output_dir)


if __name__ == '__main__':
    unittest.main()

