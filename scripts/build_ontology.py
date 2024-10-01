#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build Ontology in RDF/Turtle Format from Hierarchical Sheet

Created on Sat Sep 07 15:03:53 2024

@author: Hrishikesh Terdalkar

* Importing in Neo4j using Neosemantics
- https://neo4j.com/labs/neosemantics/

* Steps to Clean-up
- MATCH (n:Resource) REMOVE n:Resource;
- CALL apoc.refactor.rename.label("Class", "NodeLabel")
- CALL apoc.refactor.rename.label("ObjectProperty", "RelationLabel")
- MATCH (n) SET n.lemma = replace(n.uri, "http://sanskrit.iitk.ac.in/ayurveda/ontology_v2.0.rdf#", "")
"""

###############################################################################

import json
import pickle
from pathlib import Path
from collections import defaultdict, Counter

import pandas as pd

from rdflib import Graph, Namespace, Literal, RDF, RDFS, OWL, URIRef, BNode
from rdflib.namespace import XSD
from rdflib.collection import Collection

import anytree

import owlready2

###############################################################################

ONTOLOGY_SERVER = "http://sanskrit.iitk.ac.in/ayurveda"
ONTOLOGY_VERSION = "2.0"

###############################################################################

PROJECT_DIR = Path(__file__).parent.parent
DATA_DIR = PROJECT_DIR / "data"

NODE_ONTOLOGY_CSV = DATA_DIR / "node_ontology.csv"
RELATION_ONTOLOGY_CSV = DATA_DIR / "relation_ontology.csv"

EXAMPLES_PICKLE = DATA_DIR / "examples.pkl"
NODE_STATS_JSON = DATA_DIR / "node_label_stats.json"
RELATION_STATS_JSON = DATA_DIR / "relation_label_stats.json"

OUTPUT_FORMATS = [
    {
        "name": "RDF",
        "format": "xml",
        "extension": "rdf"
    },
    {
        "name": "Turtle",
        "format": "turtle",
        "extension": "ttl"
    },
]

###############################################################################
# Load node ontology and relation ontology CSVs

NODE_DATA = pd.read_csv(NODE_ONTOLOGY_CSV)
RELATION_DATA = pd.read_csv(RELATION_ONTOLOGY_CSV)

NODE_STATS = json.loads(NODE_STATS_JSON.read_text()) if NODE_STATS_JSON.exists() else defaultdict(Counter)
RELATION_STATS = json.loads(RELATION_STATS_JSON.read_text()) if RELATION_STATS_JSON.exists() else defaultdict(Counter)

with open(EXAMPLES_PICKLE, "rb") as f:
    EXAMPLES = pickle.load(f)

###############################################################################
# Ontology URI (unique but not necessarily valid)

ONTOLOGY_URI = f"{ONTOLOGY_SERVER}/ontology_v{ONTOLOGY_VERSION}.rdf#"

ONTOLOGY = Graph()
EX = Namespace(ONTOLOGY_URI)

ONTOLOGY.bind("", EX)

IS_SUBCLASS_OF = EX.IS_SUBCLASS_OF
IS_SUBRELATION_OF = EX.IS_SUBRELATION_OF

# Define properties (sanskrit, english)
LABEL_PROPERTY = EX.label
SANSKRIT_NAME_PROPERTY = EX.sanskrit
ENGLISH_NAME_PROPERTY = EX.english
CHILD_COUNT_PROPERTY = EX.child_count
NODE_COUNT_PROPERTY = EX.node_count
RELATION_COUNT_PROPERTY = EX.relation_count

DESCENDANT_COUNT_PROPERTY = EX.descendant_count
TOTAL_NODE_COUNT_PROPERTY = EX.total_node_count
TOTAL_RELATION_COUNT_PROPERTY = EX.total_relation_count

# Add properties as OWL datatype properties to the ontology
ONTOLOGY.add((LABEL_PROPERTY, RDF.type, OWL.AnnotationProperty))
ONTOLOGY.add((SANSKRIT_NAME_PROPERTY, RDF.type, OWL.AnnotationProperty))
ONTOLOGY.add((ENGLISH_NAME_PROPERTY, RDF.type, OWL.AnnotationProperty))
ONTOLOGY.add((CHILD_COUNT_PROPERTY, RDF.type, OWL.AnnotationProperty))
ONTOLOGY.add((NODE_COUNT_PROPERTY, RDF.type, OWL.AnnotationProperty))
ONTOLOGY.add((RELATION_COUNT_PROPERTY, RDF.type, OWL.AnnotationProperty))
ONTOLOGY.add((DESCENDANT_COUNT_PROPERTY, RDF.type, OWL.AnnotationProperty))
ONTOLOGY.add((TOTAL_NODE_COUNT_PROPERTY, RDF.type, OWL.AnnotationProperty))
ONTOLOGY.add((TOTAL_RELATION_COUNT_PROPERTY, RDF.type, OWL.AnnotationProperty))


###############################################################################

# # Create a BNode (Blank Node) to hold the union of classes
# domain_union = BNode()
# range_union = BNode()

# def add_union_of_classes(ontology, property, union_classes, domain_or_range="domain"):
#     """Utility to add union of Classes as domain or range for a relation"""
#     if union_classes:
#         union_node = BNode()  # Create a blank node for the union
#         list_node = BNode()   # Create a blank node for the list

#         ontology.add((union_node, RDF.type, OWL.Class))
#         Collection(ontology, list_node, union_classes)  # Create the union list
#         ontology.add((union_node, OWL.unionOf, list_node))  # Explicitly add owl:unionOf

#         if domain_or_range == "domain":
#             ontology.add((property, RDFS.domain, union_node))
#         if domain_or_range == "range":
#             ontology.add((property, RDFS.range, union_node))

###############################################################################
# Tree to store the Hierarchy


class VertexData:
    """Class to store data for the tree."""
    def __init__(self, name, sanskrit="", english=""):
        self.name = name
        self.sanskrit = sanskrit
        self.english = english
        self.child_count = 0
        self.node_count = 0
        self.relation_count = 0
        self.descendant_count = 0
        self.total_node_count = 0
        self.total_relation_count = 0

    def __repr__(self):
        return (
            f"(children: {self.child_count}, "
            f"descendants: {self.descendant_count}, "
            f"nodes: {self.total_node_count}, "
            f"relations: {self.total_relation_count})"
        )

NODE_DICT = {}
RELATION_DICT = {}

TOP_LEVEL_NODE_LABEL = "ENTITY"
TOP_LEVEL_RELATION_LABEL = "RELATION"

###############################################################################
# Create ontology hierarchy from CSV


def create_hierarchy(
    ontology: Graph,
    df: pd.DataFrame,
    tree_dict: dict,
    top_label: str,
    node_type: URIRef,
    child_predicate: URIRef
):
    parent_labels = {"lvl0": top_label}
    parent_ontology_nodes = {"lvl0": EX[parent_labels["lvl0"]]}
    tree_dict[parent_labels["lvl0"]] = anytree.Node(
        parent_labels["lvl0"],
        level=0,
        display=1,
        data=VertexData(parent_labels["lvl0"])
    )
    parent_tree_nodes = {"lvl0": tree_dict[parent_labels["lvl0"]]}
    for idx, row in df.iterrows():
        # Define ontology node URIs for each level in the hierarchy
        for level_idx in range(1, 7):
            level = f"lvl{level_idx}"
            parent_level = f"lvl{level_idx - 1}"
            if pd.notna(row[level]):
                current_label = row[level]
                current_ontology_node = EX[current_label]
                ontology.add((current_ontology_node, RDF.type, node_type))

                if level != "lvl1":
                    ontology.add((current_ontology_node, child_predicate, parent_ontology_nodes.get(parent_level)))

                ontology.add((
                    current_ontology_node,
                    LABEL_PROPERTY,
                    Literal(current_label, datatype=XSD.string)
                ))
                sanskrit_label = ""
                english_label = ""
                if pd.notna(row["sanskrit"]):
                    ontology.add((
                        current_ontology_node,
                        SANSKRIT_NAME_PROPERTY,
                        Literal(row["sanskrit"], datatype=XSD.string)
                    ))
                    sanskrit_label = row["sanskrit"]
                if pd.notna(row["english"]):
                    ontology.add((
                        current_ontology_node,
                        ENGLISH_NAME_PROPERTY,
                        Literal(row["english"], datatype=XSD.string)
                    ))
                    english_label = row["english"]

                # Set domain and range constraints if present in the CSV
                if "domain" in df.columns and pd.notna(row["domain"]):
                    domains = [EX[_domain.strip()] for _domain in row["domain"].split(",")]
                    for _domain in domains:
                        ontology.add((current_ontology_node, RDFS.domain, _domain))
                    # add_union_of_classes(ontology, current_ontology_node, domains, "domain")

                if "range" in df.columns and pd.notna(row["range"]):
                    ranges = [EX[_range.strip()] for _range in row["range"].split(",")]
                    for _range in ranges:
                        ontology.add((current_ontology_node, RDFS.range, _range))
                    # add_union_of_classes(ontology, current_ontology_node, domains, "domain")

                # Build hierarchy tree
                if current_label not in tree_dict:
                    tree_dict[current_label] = anytree.Node(
                        current_label,
                        parent=parent_tree_nodes.get(parent_level),
                        level=level_idx,
                        display=int(row["display"]),
                        data=VertexData(current_label, sanskrit_label, english_label)
                    )
                current_tree_node = tree_dict[current_label]
                current_tree_node.data.name = current_label

                # Update parents
                parent_tree_nodes[level] = current_tree_node
                parent_ontology_nodes[level] = current_ontology_node
                parent_labels[level] = current_label


###############################################################################


def add_empirical_counts_to_tree(root_node, node_stats, aggregate=True):
    root_node.data.child_count = len(root_node.children)
    root_node.data.node_count = node_stats.get(root_node.name, {}).get("node_count", 0)
    root_node.data.relation_count = node_stats.get(root_node.name, {}).get("relation_count", 0)

    root_node.data.descendant_count = len(root_node.children)
    root_node.data.total_node_count = node_stats.get(root_node.name, {}).get("node_count", 0)
    root_node.data.total_relation_count = node_stats.get(root_node.name, {}).get("relation_count", 0)

    # Aggregate counts from child nodes
    for child in root_node.children:
        add_empirical_counts_to_tree(child, node_stats)
        if aggregate:
            root_node.data.descendant_count += child.data.descendant_count
            root_node.data.total_node_count += child.data.total_node_count
            root_node.data.total_relation_count += child.data.total_relation_count


def add_empirical_counts_to_ontology(root_node, ontology):
    node = EX[root_node.name]

    # Add children, node and relation counts
    ontology.add((node, CHILD_COUNT_PROPERTY, Literal(root_node.data.child_count, datatype=XSD.integer)))
    ontology.add((node, NODE_COUNT_PROPERTY, Literal(root_node.data.node_count, datatype=XSD.integer)))
    ontology.add((node, RELATION_COUNT_PROPERTY, Literal(root_node.data.relation_count, datatype=XSD.integer)))

    ontology.add((node, DESCENDANT_COUNT_PROPERTY, Literal(root_node.data.descendant_count, datatype=XSD.integer)))
    ontology.add((node, TOTAL_NODE_COUNT_PROPERTY, Literal(root_node.data.total_node_count, datatype=XSD.integer)))
    ontology.add((node, TOTAL_RELATION_COUNT_PROPERTY, Literal(root_node.data.total_relation_count, datatype=XSD.integer)))

    # Process child nodes
    for child in root_node.children:
        add_empirical_counts_to_ontology(child, ontology)


def add_empirical_domain_range(root_node, ontology, relation_stats):
    for relation, stats in relation_stats.items():
        relation_node = anytree.find(root_node, lambda node: node.name == relation)
        relation_node.data.domain = list(map(tuple, stats["source_nodes"]))
        relation_node.data.range = list(map(tuple, stats["destination_nodes"]))

        domains = [EX[t[0]] for t in stats["source_nodes"]]
        for _domain in domains:
            ontology.add((EX[relation], RDFS.domain, _domain))

        ranges = [EX[t[0]] for t in stats["destination_nodes"]]
        for _range in ranges:
            ontology.add((EX[relation], RDFS.range, _range))

        # add_union_of_classes(ontology, EX[relation], domains, "domain")
        # add_union_of_classes(ontology, EX[relation], ranges, "range")

###############################################################################
# Build the ontology from the CSV files

create_hierarchy(ONTOLOGY, NODE_DATA, NODE_DICT, TOP_LEVEL_NODE_LABEL, OWL.Class, RDFS.subClassOf)
create_hierarchy(ONTOLOGY, RELATION_DATA, RELATION_DICT, TOP_LEVEL_RELATION_LABEL, OWL.ObjectProperty, RDFS.subPropertyOf)

NODE_TREE = NODE_DICT[TOP_LEVEL_NODE_LABEL]
RELATION_TREE = RELATION_DICT[TOP_LEVEL_RELATION_LABEL]

ROOT_LEVEL_NODE_LABELS = [node for node in NODE_DICT.values() if node.is_root]
ROOT_LEVEL_RELATION_LABELS = [node for node in RELATION_DICT.values() if node.is_root]

for root_node in ROOT_LEVEL_NODE_LABELS:
    add_empirical_counts_to_tree(root_node, NODE_STATS, aggregate=True)
    add_empirical_counts_to_ontology(root_node, ONTOLOGY)
for root_node in ROOT_LEVEL_RELATION_LABELS:
    add_empirical_counts_to_tree(root_node, RELATION_STATS, aggregate=True)
    add_empirical_counts_to_ontology(root_node, ONTOLOGY)
    add_empirical_domain_range(root_node, ONTOLOGY, RELATION_STATS)

###############################################################################

ONTOLOGY_NEO4J = Graph()
for s, p, o in ONTOLOGY:
    if p == RDF.type:
        if o not in [RDFS.Resource]:
            ONTOLOGY_NEO4J.add((s, RDF.type, o))
    elif p == RDFS.subClassOf:
        ONTOLOGY_NEO4J.add((s, IS_SUBCLASS_OF, o))
    elif p == RDFS.subPropertyOf:
        ONTOLOGY_NEO4J.add((s, IS_SUBRELATION_OF, o))
    else:
        ONTOLOGY_NEO4J.add((s, p, o))

# Serialize the ontology in various output formats
for output_format in OUTPUT_FORMATS:
    _name = output_format["name"]
    _format = output_format["format"]
    _extension = output_format["extension"]
    destination = DATA_DIR / f"ontology_v{ONTOLOGY_VERSION}.{_extension}"
    destination_neo4j = DATA_DIR / f"ontology_v{ONTOLOGY_VERSION}_neo4j.{_extension}"
    ONTOLOGY.serialize(destination=str(destination), format=_format)
    ONTOLOGY_NEO4J.serialize(destination=str(destination_neo4j), format=_format)

###############################################################################

owlready2.onto_path.append(DATA_DIR)

###############################################################################

O = owlready2.get_ontology(ONTOLOGY_URI).load()
O.save(str(DATA_DIR/  f"ontology_v{ONTOLOGY_VERSION}.owl"))

###############################################################################

LATEX_NODE_TREE_FILE = DATA_DIR / "node_tree.tex"
LATEX_NODE_EXAMPLE_FILE = DATA_DIR / "node_examples.tex"

LATEX_RELATION_TREE_FILE = DATA_DIR / "relation_tree.tex"
LATEX_RELATION_EXAMPLE_FILE = DATA_DIR / "relation_examples.tex"

# --------------------------------------------------------------------------- #

NODE_EXAMPLES = EXAMPLES["node"]
RELATION_EXAMPLES = EXAMPLES["relation"]

LATEX_GENERATION_INPUT = [
    (NODE_TREE, NODE_EXAMPLES, LATEX_NODE_TREE_FILE, LATEX_NODE_EXAMPLE_FILE),
    (RELATION_TREE, RELATION_EXAMPLES, LATEX_RELATION_TREE_FILE, LATEX_RELATION_EXAMPLE_FILE)
]

# --------------------------------------------------------------------------- #

for tree, examples, latex_tree_file, latex_example_file in LATEX_GENERATION_INPUT:
    latex_lines = ["\\dirtree{%"]
    example_lines = []

    for _, _, node in anytree.RenderTree(tree):
        if node.display < 1:
            pass
            continue
        node_name = node.name.replace("_", "\\_")
        latex_lines.append(
            f"  .{node.level} {node_name} "
            f"(C:{node.data.child_count}, "
            f"D:{node.data.descendant_count}, "
            f"N:{node.data.total_node_count}, "
            f"R:{node.data.total_relation_count})."
        )

        if examples[node.name]:
            example_lines.append(f"\\subsubsection*{{{node_name}}}")
            example_lines.append(f"\\skt{{{node.data.sanskrit}}}\\\\\n")

            for (_nt1, _nl1, _rl, _nt2, _nl2), count in examples[node.name].most_common(5):
                _nl1 = _nl1.replace("_", "\\_")
                _nl2 = _nl2.replace("_", "\\_")
                _rl = _rl.replace("_", "\\_")
                example_lines.append(f"\\noindent\\relation{{{_nt1}}}{{{_nl1}}}{{{_rl}}}{{{_nt2}}}{{{_nl2}}}\\\\\n")

    latex_lines.append("}")

    with open(latex_tree_file, "w") as f:
        f.write("\n".join(latex_lines))

    with open(latex_example_file, "w") as f:
        f.write("\n".join(example_lines))

# --------------------------------------------------------------------------- #

NODE_TREE_TEXT = []
RELATION_TREE_TEXT = []

for pre, fill, node in anytree.RenderTree(NODE_TREE):
    NODE_TREE_TEXT.append(f"{pre}{node.name} ({node.data.sanskrit}) {node.data}")

for pre, fill, node in anytree.RenderTree(RELATION_TREE):
    RELATION_TREE_TEXT.append(f"{pre}{node.name} ({node.data.sanskrit}) {node.data}")

with open(DATA_DIR / "node_ontology.txt", "w") as f:
    f.write("\n".join(NODE_TREE_TEXT))

with open(DATA_DIR / "relation_ontology.txt", "w") as f:
    f.write("\n".join(RELATION_TREE_TEXT))

###############################################################################
