#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 18 01:31:47 2021

@author: Hrishikesh Terdalkar

NOTE: This version corresponds to Sangrahaka v2.x
      (where Relationship src_id and dst_id refer to Lexicon.)
"""

import os
import sys
import logging

###############################################################################

script_dir = os.path.dirname(os.path.realpath(__file__))
main_dir = os.path.join(script_dir, '..', '..')

sys.path.insert(0, main_dir)

from models_sqla import Node, Relation, Lexicon  # noqa
from utils.property_graph import PropertyGraph   # noqa

###############################################################################

logger = logging.getLogger(__name__)

###############################################################################

GROUPS = {
    'SUBSTANCE_ALL': [
        'SUBSTANCE', 'PART_OF_SUBSTANCE',
        'COMPOUND_SUBSTANCE', 'PREPARED_SUBSTANCE'
    ],
    'EFFECT_TARGET': [
        'PART_OF_BODY', 'PRODUCT_OF_BODY', 'ANIMAL', 'PLANT'
    ],
    'EFFECT_EXTERNAL': [
        'DISEASE', 'SYMPTOM', 'EFFECT'
    ],
    'EFFECT_ALL': [
        'EFFECT', 'SYMPTOM', 'DISEASE', 'TRIDOSHA'
    ],
    'PROPERTY_TYPE': [
        'PROPERTY'
    ],
    'LOCATION': ['LOCATION'],
    'PERSON': ['PERSON'],
    'ANIMAL': ['ANIMAL'],
    'PLANT': ['PLANT'],
    'SOURCE': ['SOURCE'],
    'ANIMAL_SOURCE': ['ANIMAL_SOURCE'],
    'PLANT_SOURCE': ['PLANT_SOURCE'],
    'QUANTITY': ['QUANTITY'],
    'METHOD': ['METHOD'],
    'USAGE': ['USAGE'],
    'TIME': ['TIME'],
    'SEASON': ['SEASON'],
    'OTHER': ['OTHER']
}

# --------------------------------------------------------------------------- #

COMPATIBILITY = {
    'IS_SYNONYM_OF': {
        'source': GROUPS['SUBSTANCE_ALL'] + ['TRIDOSHA'],
        'target': GROUPS['SUBSTANCE_ALL'] + ['TRIDOSHA'],
    },
    'IS_PROPERTY_OF': {
        'source': GROUPS['PROPERTY_TYPE'],
        'target': GROUPS['SUBSTANCE_ALL']
    },
    'IS_PROPERTY_NOT_OF': {
        'source': GROUPS['PROPERTY_TYPE'],
        'target': GROUPS['SUBSTANCE_ALL']
    },
    'IS_SIMILAR_TO': {
        'source': GROUPS['SUBSTANCE_ALL'],
        'target': GROUPS['SUBSTANCE_ALL']
    },
    'IS_BETTER_THAN': {
        'source': GROUPS['SUBSTANCE_ALL'],
        'target': GROUPS['SUBSTANCE_ALL'],
    },
    'IS_WORSE_THAN': {
        'source': GROUPS['SUBSTANCE_ALL'],
        'target': GROUPS['SUBSTANCE_ALL']
    },
    'IS_NEWER_THAN': {
        'source': GROUPS['SUBSTANCE_ALL'],
        'target': GROUPS['SUBSTANCE_ALL']
    },
    'IS_OLDER_THAN': {
        'source': GROUPS['SUBSTANCE_ALL'],
        'target': GROUPS['SUBSTANCE_ALL']
    },
    'IS_BEST_AMONG': {
        'source': GROUPS['SUBSTANCE_ALL'],
        'target': GROUPS['SUBSTANCE_ALL']
    },
    'IS_MEDIUM_AMONG': {
        'source': GROUPS['SUBSTANCE_ALL'],
        'target': GROUPS['SUBSTANCE_ALL']
    },
    'IS_WORST_AMONG': {
        'source': GROUPS['SUBSTANCE_ALL'],
        'target': GROUPS['SUBSTANCE_ALL']
    },
    'IS_INGREDIENT_OF': {
        'source': GROUPS['SUBSTANCE_ALL'],
        'target': GROUPS['SUBSTANCE_ALL']
    },
    'IS_PART_OF': {
        'source': ['PART_OF_SUBSTANCE'],
        'target': GROUPS['SUBSTANCE_ALL']
    },
    'IS_PART_NOT_OF': {
        'source': ['PART_OF_SUBSTANCE'],
        'target': GROUPS['SUBSTANCE_ALL']
    },
    'IS_TYPE_OF': {
        'source': GROUPS['SUBSTANCE_ALL'],
        'target': GROUPS['SUBSTANCE_ALL']
    },
    'IS_VARIANT_OF': {
        'source': GROUPS['SUBSTANCE_ALL'],
        'target': GROUPS['SUBSTANCE_ALL']
    },
    'IS_DISEASE_OF': {
        'source': ['DISEASE'],
        'target': GROUPS['EFFECT_TARGET']
    },
    'IS_CAUSED_BY': {
        'source': GROUPS['EFFECT_EXTERNAL'],
        'target': GROUPS['SUBSTANCE_ALL']
    },
    'IS_CAUSED_NOT_BY': {
        'source': GROUPS['EFFECT_EXTERNAL'],
        'target': GROUPS['SUBSTANCE_ALL']
    },
    'IS_BENEFITTED_BY': {
        'source': GROUPS['EFFECT_TARGET'],
        'target': GROUPS['SUBSTANCE_ALL']
    },
    'IS_HARMED_BY': {
        'source': GROUPS['EFFECT_TARGET'],
        'target': GROUPS['SUBSTANCE_ALL']
    },
    'IS_PRODUCED_BY': {
        'source': [],
        'target': GROUPS['SUBSTANCE_ALL']
    },
    'IS_REMOVED_BY': {
        'source': [],
        'target': GROUPS['SUBSTANCE_ALL']
    },
    'IS_INCREASED_BY': {
        'source': GROUPS['EFFECT_ALL'],
        'target': GROUPS['SUBSTANCE_ALL']
    },
    'IS_DECREASED_BY': {
        'source': GROUPS['EFFECT_ALL'],
        'target': GROUPS['SUBSTANCE_ALL']
    },
    'IS_PREPARATION_OF': {
        'source': [],
        'target': GROUPS['SUBSTANCE_ALL']
    },
    'IS_PREPARATION_NOT_OF': {
        'source': [],
        'target': GROUPS['SUBSTANCE_ALL']
    },
    'IS_LOCATION_OF': {
        'source': ['LOCATION'],
        'target': []
    },
    'IS_TIME_OF': {
        'source': ['TIME'],
        'target': GROUPS['SUBSTANCE_ALL']
    },
}

# --------------------------------------------------------------------------- #

SYMMETRIC_RELATIONS = ['IS_SYNONYM_OF', 'IS_SIMILAR_TO']

# --------------------------------------------------------------------------- #

###############################################################################


class AyurvedaGraph(PropertyGraph):
    def infer(self, src_id, label, dst_id, properties):
        src_labels = COMPATIBILITY[label]['source']
        dst_labels = COMPATIBILITY[label]['target']
        src_properties = {
            'lemma': self.get_lemma_by_id(src_id),
            'annotator': properties['annotator'],
            'line_id': properties['line_id'],
            'auto': True
        }
        dst_properties = {
            'lemma': self.get_lemma_by_id(dst_id),
            'annotator': properties['annotator'],
            'line_id': properties['line_id'],
            'auto': True
        }
        return src_labels, dst_labels, src_properties, dst_properties

    def get_lemma_by_id(self, node_id):
        return Lexicon.query.filter(Lexicon.id == node_id).first().lemma

    def get_groups(self, relations=None):
        groups = []
        handled = set()
        for node_id in self.nodes:
            if node_id in handled:
                continue
            connected_nodes = self.get_connected_nodes(
                node_id, relations=relations
            )
            if len(connected_nodes) > 1:
                groups.append([
                    (self.nodes[_id],
                     sum(self.nodes[_id].incoming.values()) +
                     sum(self.nodes[_id].outgoing.values()),
                     self.nodes[_id].properties['line_id'])
                    for _id in connected_nodes
                ])
                handled.update(connected_nodes)

        answer = []
        for group in groups:
            answer.append(
                sorted(
                    group,
                    key=lambda x: (
                        x[1], max(x[2])
                        if isinstance(x[2], list)
                        else x[2]
                    ),
                    reverse=True
                )
            )
        return answer

    def add_synonym_edges(self):
        groups = self.get_groups(['IS_SYNONYM_OF'])
        for group in groups:
            main_substance = group[0][0]
            synonyms = [x[0] for x in group[1:]]
            for idx, synonym in enumerate(synonyms):
                print(idx)
                edge_tuple = (synonym.id, 'IS_SYNONYM_OF', main_substance.id)
                reverse_edge = (main_substance.id, 'IS_SYNONYM_OF', synonym.id)
                if edge_tuple not in self.edges:
                    self.add_edge(
                        synonym.id,
                        'IS_SYNONYM_OF',
                        main_substance.id,
                        {'auto': True}
                    )
                    logger.info(
                        "Added synonym edge. "
                        f"({synonym.id}) --> ({main_substance.id})"
                    )
                if reverse_edge in self.edges:
                    logger.info(
                        "Removed synonym edge. "
                        f"({main_substance.id}) --> ({synonym.id})")
                    self.remove_edge(*reverse_edge)

                synonym_edges = [
                    _edge for _tuple, _edge in self.edges.items()
                    if ((_tuple[0] == synonym.id or _tuple[2] == synonym.id)
                        and _tuple[1] != 'IS_SYNONYM_OF')
                ]
                # transfer edges to main substance
                for synonym_edge in synonym_edges:
                    logger.info(
                        "Transferring an edge from "
                        f"{synonym.id} to {main_substance.id}"
                        f" ({synonym_edge.to_json()})"
                    )

                    if synonym_edge.start_id == synonym.id:
                        self.transfer_edge(
                            synonym_edge.start_id,
                            synonym_edge.label,
                            synonym_edge.end_id,
                            new_src=main_substance.id
                        )
                    elif synonym_edge.end_id == synonym.id:
                        self.transfer_edge(
                            synonym_edge.start_id,
                            synonym_edge.label,
                            synonym_edge.end_id,
                            new_dst=main_substance.id
                        )

        return True

###############################################################################


def build_graph():
    graph = AyurvedaGraph()
    node_query = Node.query.filter(Node.is_deleted.is_(False))
    relation_query = Relation.query.filter(Relation.is_deleted.is_(False))
    logger.debug(node_query)
    logger.debug(relation_query)
    nodes = node_query.all()
    relationships = relation_query.all()
    for node in nodes:
        node_id = node.lexicon_id
        labels = [node.label.label]
        properties = {
            'lemma': node.lemma.lemma,
            'annotator': node.annotator.id,
            'line_id': node.line_id
        }
        graph.add_node(node_id=node_id, labels=labels, properties=properties)

    for relationship in relationships:
        label = relationship.label.label
        properties = {
            'annotator': relationship.annotator.id,
            'line_id': relationship.line_id
        }
        if relationship.detail:
            properties['detail'] = relationship.detail
        src_id = relationship.src_id
        dst_id = relationship.dst_id
        graph.add_edge(src_id, label, dst_id, properties=properties)

    return graph

###############################################################################


if __name__ == '__main__':
    from flask import Flask

    from models_sqla import db
    from settings import app

    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.DEBUG)

    # ----------------------------------------------------------------------- #

    save_graph = True

    # ----------------------------------------------------------------------- #

    webapp = Flask(__name__)
    webapp.config['SQLALCHEMY_DATABASE_URI'] = app.sqla['database_uri']
    webapp.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        "pool_pre_ping": True,
    }
    db.init_app(webapp)
    webapp.app_context().push()

    # ----------------------------------------------------------------------- #

    graph = build_graph()
    graph.add_synonym_edges()

    if save_graph:
        with open(os.path.join(main_dir, "output", "graph.jsonl"), "w") as f:
            f.write(graph.to_jsonl())

###############################################################################
