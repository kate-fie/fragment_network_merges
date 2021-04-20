"""
Used to generate merges between two fragments using the fragment network.
Uses code from https://github.com/tdudgeon/fragment-network-merges.
"""

import itertools
import getpass
import json
import pandas as pd
import numpy as np
from neo4j import GraphDatabase
from rdkit import Chem

try:
    password
except NameError:
    password = getpass.getpass()

driver = GraphDatabase.driver("bolt://localhost:7687", auth=("swills", password))

# functions for checking the nodes and filtering for fragments that exist as nodes
def find_molecule_node(tx, smiles):
    """
    Finds node in the fragment network.

    :param tx: transaction in which query is run
    :type tx: neo4j transaction
    :param smiles: smiles of the fragment
    :type smiles: string

    :return: molecule node
    :rtype: node
    """
    for record in tx.run('MATCH (m:F2 {smiles: $smiles}) RETURN m', smiles=smiles):
        node = record['m']
        return node

def check_for_nodes(fragments):
    """
    Checks if nodes are present.
    Prints statement with how many of the fragments are present in the network.

    :param fragments: list of smiles of the fragments
    :type fragments: list of strings
    """
    number_nodes = 0
    number_fragments = len(fragments)
    with driver.session() as session:
        for fragment in fragments:
            mol = session.read_transaction(find_molecule_node, fragment)  # run neo4j query
            if mol:
                number_nodes += 1
        print(f'{number_nodes} of {number_fragments} fragments present in network')

def filter_for_nodes(fragments, names):
    """
    Checks if nodes are present and filters fragments for those that are in network.

    :param fragments: list of fragment smiles
    :type fragments: list of strings
    :param names: list of fragment names
    :type names: list of strings

    :return: list of available fragments
    :rtype: list of smiles strings
    :return: list of available fragments (names)
    :rtype: list of strings
    """
    removed = 0
    with driver.session() as session:
        for i, fragment in enumerate(fragments):
            mol = session.read_transaction(find_molecule_node, fragment)  # run neo4j query
            if not mol:
                fragments.pop(i)
                names.pop(i)
                removed += 1
    print(f'{removed} fragments removed from list. {len(fragments)} fragments remaining.')
    return fragments, names

def get_combinations(fragments, names):
    """
    Enumerate all possible combinations of fragments for merging.

    :param fragments: list of fragment smiles
    :type fragments: list of strings
    :param names: list of fragment names
    :type names: list of strings

    :return: list of possible combinations of fragments
    :rtype: list of tuples
    :return: list of possible combinations of fragments (names)
    :rtype: list of tuples
    """
    fragment_pairs = list(itertools.permutations(fragments, 2))
    name_pairs = list(itertools.permutations(names, 2))
    return fragment_pairs, name_pairs

# code for generating the list of fragment merges
def add_required_synthons(labels, synthon):
    """
    Checks that the synthons have a single attachment point and single component.

    :param labels: set containing the synthons
    :type labels: set
    :param synthon: smiles string containing synthon with Xe atom
    :type synthon: string
    """
    if synthon.count('[Xe]') > 0:
        labels.add(synthon)

def find_synthons(tx, smiles):
    """
    Query for all child fragments (recursive).
    Extract the label property of each edge and collect a set of SMILES that match our needs.
    """
    labels = set()
    for record in tx.run('MATCH (fa:F2 {smiles: $smiles})-[e:FRAG*]->(f:F2) RETURN e',
                            smiles=smiles):
        edges = record['e']
        for edge in edges:
            s = edge['label']
            tokens = s.split('|')
            add_required_synthons(labels, tokens[1])
            add_required_synthons(labels, tokens[4])
    return list(labels)

def get_synthons(smiles):
    """
    Extract the synthons from the database.

    :param smiles: smiles of the fragment
    :type smiles: string

    :return: synthons
    :rtype: string
    """
    with driver.session() as session:
        synthons = session.read_transaction(find_synthons, smiles)
        print(f'Found {len(synthons)} synthons')
        return synthons

def find_expansions(tx, smiles, synthon):
    """
    Expand fragment 'A' using the synthons generated from fragment 'B' using a neo4j
    query. Query limited to compounds available from vendors, with HAC > 15
    and a maximum of 2 hops away.

    :param smiles: smiles of the fragment to expand
    :type smiles: string
    :param synthon: synthon of the generated synthon
    :type synthon: string

    :return: expansions
    :rtype: set
    """
    query = ("MATCH (fa:F2 {smiles: $smiles})"
                "-[:FRAG*0..2]-(:F2)"
                "<-[e:FRAG]-(c:Mol) WHERE"
                " c.hac > 15 AND"
                " (split(e.label, '|')[1] = $synthon OR split(e.label, '|')[4] = $synthon)"
                " RETURN DISTINCT c")
    expansions = set()
    for record in tx.run(query, smiles=smiles, synthon=synthon):
        node = record['c']
        expansions.add(node['smiles'])
    return expansions

def get_expansions(fragments, names):
    """
    Function executes the whole process, generating synthons for fragment B and using them to
    generate expansions of fragment A. Returns a dictionary containing all the synthons as keys,
    and the smiles of the merges they were used to generate.
    The dictionary is then saved as a json file.

    :return: dictionary of merges
    :rtype: dictionary
    """
    # get fragment A and B from the tuple
    fragmentA, fragmentB = fragments[0], fragments[1]
    nameA, nameB = names[0], names[1]
    print(f'Expanding fragment A: {nameA} with synthons of fragment B: {nameB}')

    # generate the synthons from fragment B
    synthons = get_synthons(fragmentB)
    # create empty dictionary to store results
    all_expansions = {}
    with driver.session() as session:
        number = 0
        total_expansions = 0
        expanded_synthons = 0
        for synthon in synthons:  # expand fragment A using each synthon
            print(f'Running synthon {number}')
            expansions = session.read_transaction(find_expansions, fragmentA, synthon)
            all_expansions[synthon] = list(expansions)  # store in dictionary with the synthon as key
            print(f'Synthon {number}: found {len(expansions)} expansions')
            number += 1
            total_expansions += len(expansions)
            if expansions:  # record if the synthon led to expansions
                expanded_synthons += 1
    print(f'{total_expansions} expansions from {expanded_synthons} out of {len(synthons)} synthons')

    # save as json file
    filename = 'data/' + nameA + '_' + nameB + '.json'
    with open(filename, 'w') as f:
        json.dump(all_expansions, f)

    # return results
    return all_expansions
