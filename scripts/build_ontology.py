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
from pathlib import Path
from collections import defaultdict, Counter

import pandas as pd

from rdflib import Graph, Namespace, Literal, RDF, RDFS, OWL, BNode
from rdflib.namespace import XSD
from rdflib.collection import Collection

from anytree import Node, RenderTree, Walker
from anytree.exporter import JsonExporter

import owlready2

###############################################################################

ONTOLOGY_SERVER = "http://sanskrit.iitk.ac.in/ayurveda"
ONTOLOGY_VERSION = "2.0"

###############################################################################

PROJECT_DIR = Path(__file__).parent.parent
DATA_DIR = PROJECT_DIR / "data"

NODE_ONTOLOGY_CSV = DATA_DIR / "node_ontology.csv"
RELATION_ONTOLOGY_CSV = DATA_DIR / "relation_ontology.csv"

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
CHILDREN_COUNT_PROPERTY = EX.children_count
NODE_COUNT_PROPERTY = EX.node_count
RELATION_COUNT_PROPERTY = EX.relation_count

TOTAL_CHILDREN_COUNT_PROPERTY = EX.toal_children_count
TOTAL_NODE_COUNT_PROPERTY = EX.total_node_count
TOTAL_RELATION_COUNT_PROPERTY = EX.total_relation_count

# Add properties as OWL datatype properties to the ontology
ONTOLOGY.add((LABEL_PROPERTY, RDF.type, OWL.AnnotationProperty))
ONTOLOGY.add((SANSKRIT_NAME_PROPERTY, RDF.type, OWL.AnnotationProperty))
ONTOLOGY.add((ENGLISH_NAME_PROPERTY, RDF.type, OWL.AnnotationProperty))
ONTOLOGY.add((CHILDREN_COUNT_PROPERTY, RDF.type, OWL.AnnotationProperty))
ONTOLOGY.add((NODE_COUNT_PROPERTY, RDF.type, OWL.AnnotationProperty))
ONTOLOGY.add((RELATION_COUNT_PROPERTY, RDF.type, OWL.AnnotationProperty))
ONTOLOGY.add((TOTAL_CHILDREN_COUNT_PROPERTY, RDF.type, OWL.AnnotationProperty))
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
        self.children_count = 0
        self.node_count = 0
        self.relation_count = 0
        self.total_children_count = 0
        self.total_node_count = 0
        self.total_relation_count = 0

    def __repr__(self):
        return (
            f"(children: {self.total_children_count}, "
            f"nodes: {self.total_node_count}, "
            f"relations: {self.total_relation_count})"
        )


CLASS_DICT = {}
RELATION_DICT = {}

TOP_LEVEL_CLASS_LABEL = "THING"
TOP_LEVEL_RELATION_LABEL = "RELATION"

###############################################################################
# Create node ontology class hierarchy from CSV


def create_node_hierarchy(ontology, df):
    parent_label = {"lvl0": TOP_LEVEL_CLASS_LABEL}
    parent_class = {"lvl0": EX[parent_label["lvl0"]]}
    CLASS_DICT[parent_label["lvl0"]] = Node(
        parent_label["lvl0"],
        data=VertexData(parent_label["lvl0"])
    )
    parent_node = {"lvl0": CLASS_DICT[parent_label["lvl0"]]}
    for idx, row in df.iterrows():
        # Define class URIs for each level in the hierarchy
        for level_idx in range(1, 7):
            level = f"lvl{level_idx}"
            parent_level = f"lvl{level_idx - 1}"
            if pd.notna(row[level]):
                current_label = row[level]
                current_class = EX[current_label]
                ontology.add((current_class, RDF.type, OWL.Class))

                if level != "lvl1":
                    ontology.add((current_class, RDFS.subClassOf, parent_class.get(parent_level)))

                ontology.add((
                    current_class,
                    LABEL_PROPERTY,
                    Literal(current_label, datatype=XSD.string)
                ))
                sanskrit_label = ""
                english_label = ""
                if pd.notna(row["sanskrit"]):
                    ontology.add((
                        current_class,
                        SANSKRIT_NAME_PROPERTY,
                        Literal(row["sanskrit"], datatype=XSD.string)
                    ))
                    sanskrit_label = row["sanskrit"]
                if pd.notna(row["english"]):
                    ontology.add((
                        current_class,
                        ENGLISH_NAME_PROPERTY,
                        Literal(row["english"], datatype=XSD.string)
                    ))
                    english_label = row["english"]

                # Build class tree
                if current_label not in CLASS_DICT:
                    CLASS_DICT[current_label] = Node(
                        current_label,
                        parent=parent_node.get(parent_level),
                        data=VertexData(current_label, sanskrit_label, english_label)
                    )
                current_node = CLASS_DICT[current_label]
                current_node.data.name = current_label

                # Update parents
                parent_node[level] = current_node
                parent_class[level] = current_class
                parent_label[level] = current_label


###############################################################################
# Create relationship ontology hierarchy from CSV


def create_relation_hierarchy(ontology, df):
    parent_label = {"lvl0": TOP_LEVEL_RELATION_LABEL}
    parent_relation = {"lvl0": EX[parent_label["lvl0"]]}
    RELATION_DICT[parent_label["lvl0"]] = Node(
        parent_label["lvl0"],
        data=VertexData(parent_label["lvl0"])
    )
    parent_node = {"lvl0": RELATION_DICT[parent_label["lvl0"]]}
    for idx, row in df.iterrows():
        # Define class URIs for each level in the hierarchy
        for level_idx in range(1, 7):
            level = f"lvl{level_idx}"
            parent_level = f"lvl{level_idx - 1}"
            if pd.notna(row[level]):
                current_label = row[level]
                current_relation = EX[current_label]
                ontology.add((current_relation, RDF.type, OWL.ObjectProperty))

                if level != "lvl1":
                    ontology.add((current_relation, RDFS.subPropertyOf, parent_relation.get(parent_level)))

                ontology.add((
                    current_relation,
                    LABEL_PROPERTY,
                    Literal(current_label, datatype=XSD.string)
                ))
                sanskrit_label = ""
                english_label = ""
                if pd.notna(row["sanskrit"]):
                    ontology.add((
                        current_relation,
                        SANSKRIT_NAME_PROPERTY,
                        Literal(row["sanskrit"], datatype=XSD.string)
                    ))
                    sanskrit_label = row["sanskrit"]
                if pd.notna(row["english"]):
                    ontology.add((
                        current_relation,
                        ENGLISH_NAME_PROPERTY,
                        Literal(row["english"], datatype=XSD.string)
                    ))
                    english_label = row["english"]

                # Set domain and range constraints if present in the CSV
                if "domain" in df.columns and pd.notna(row["domain"]):
                    domains = [EX[_domain.strip()] for _domain in row["domain"].split(",")]
                    # add_union_of_classes(ontology, current_relation, domains, "domain")

                if "range" in df.columns and pd.notna(row["range"]):
                    ranges = [EX[_range.strip()] for _range in row["range"].split(",")]
                    # add_union_of_classes(ontology, current_relation, ranges, "range")

                # Build relation tree
                if current_label not in RELATION_DICT:
                    RELATION_DICT[current_label] = Node(
                        current_label,
                        parent=parent_node.get(parent_level),
                        data=VertexData(current_label, sanskrit_label, english_label)
                    )
                current_node = RELATION_DICT[current_label]
                current_node.data.name = current_label

                # Update parents
                parent_node[level] = current_node
                parent_relation[level] = current_relation
                parent_label[level] = current_label


###############################################################################


def aggregate_counts(node, node_stats):
    node.data.children_count = len(node.children)
    node.data.node_count = node_stats.get(node.name, {}).get("node_count", 0)
    node.data.relation_count = node_stats.get(node.name, {}).get("relation_count", 0)

    node.data.total_children_count = len(node.children)
    node.data.total_node_count = node_stats.get(node.name, {}).get("node_count", 0)
    node.data.total_relation_count = node_stats.get(node.name, {}).get("relation_count", 0)

    # Aggregate counts from child nodes
    for child in node.children:
        aggregate_counts(child, node_stats)
        node.data.total_children_count += child.data.total_children_count
        node.data.total_node_count += child.data.total_node_count
        node.data.total_relation_count += child.data.total_relation_count


def add_empirical_counts(root_node, ontology):
    node = EX[root_node.name]

    # Add children, node and relation counts
    ontology.add((node, CHILDREN_COUNT_PROPERTY, Literal(root_node.data.children_count, datatype=XSD.integer)))
    ontology.add((node, NODE_COUNT_PROPERTY, Literal(root_node.data.node_count, datatype=XSD.integer)))
    ontology.add((node, RELATION_COUNT_PROPERTY, Literal(root_node.data.relation_count, datatype=XSD.integer)))

    ontology.add((node, TOTAL_CHILDREN_COUNT_PROPERTY, Literal(root_node.data.total_children_count, datatype=XSD.integer)))
    ontology.add((node, TOTAL_NODE_COUNT_PROPERTY, Literal(root_node.data.total_node_count, datatype=XSD.integer)))
    ontology.add((node, TOTAL_RELATION_COUNT_PROPERTY, Literal(root_node.data.total_relation_count, datatype=XSD.integer)))

    # Process child nodes
    for child in root_node.children:
        add_empirical_counts(child, ontology)


def add_empirical_domain_range(ontology, relation_stats):
    for relation, stats in relation_stats.items():
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

create_node_hierarchy(ONTOLOGY, NODE_DATA)
create_relation_hierarchy(ONTOLOGY, RELATION_DATA)

CLASS_TREE = CLASS_DICT[TOP_LEVEL_CLASS_LABEL]
RELATION_TREE = RELATION_DICT[TOP_LEVEL_RELATION_LABEL]

ROOT_CLASS_NODES = [node for node in CLASS_DICT.values() if node.is_root]
ROOT_RELATION_NODES = [node for node in RELATION_DICT.values() if node.is_root]

for root_node in ROOT_CLASS_NODES:
    aggregate_counts(root_node, NODE_STATS)
    add_empirical_counts(root_node, ONTOLOGY)
for root_node in ROOT_RELATION_NODES:
    aggregate_counts(root_node, RELATION_STATS)
    add_empirical_counts(root_node, ONTOLOGY)

add_empirical_domain_range(ONTOLOGY, RELATION_STATS)

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
