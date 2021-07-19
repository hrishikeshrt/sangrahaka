#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 18 01:31:47 2021

@author: Hrishikesh Terdalkar
"""

import os
import sys
import logging

###############################################################################

script_dir = os.path.dirname(os.path.realpath(__file__))
main_dir = os.path.join(script_dir, '..', '..')

sys.path.insert(0, main_dir)

###############################################################################

from models_sqla import Node, Relation, Lexicon  # noqa
from utils.property_graph import PropertyGraph   # noqa

###############################################################################

logger = logging.getLogger(__name__)

###############################################################################

INFERENCE = {
    'IS_QUALITY_OF': {
        'source': ['QUALITY'],
    },
    'HAPPENS_AFTER': {
        'source': ['EVENT'],
        'target': ['EVENT']
    }
}

###############################################################################


class CustomGraph(PropertyGraph):
    def infer(self, src_id, label, dst_id, properties):
        src_labels = []
        dst_labels = []
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

        if label in INFERENCE:
            inference = INFERENCE.get(label)
            if inference.get('source'):
                src_labels = inference.get('source')
            if inference.get('target'):
                dst_labels = inference.get('target')

        return src_labels, dst_labels, src_properties, dst_properties

    def get_lemma_by_id(self, node_id):
        return Lexicon.query.filter(Lexicon.id == node_id).first().lemma

###############################################################################


def build_graph():
    graph = CustomGraph()
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

    if save_graph:
        with open(os.path.join(main_dir, "output", "epics.jsonl"), "w") as f:
            f.write(graph.to_jsonl())

###############################################################################
