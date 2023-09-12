#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Feb 19 23:05:16 2023

@author: Hrishikesh Terdalkar

This version corresponds to Nodes of the form Lemma::NodeLabel Relationship
src_id and dst_id refer to node ids

Additionally, this makes use of hierarchical ontology, adding top level labels
to lower levels that belong to them (i.e. a node with RASA_PROPERTY label will
also get the label PROPERTY and so on)
"""

import os
import sys
import logging

from collections import defaultdict

###############################################################################

script_dir = os.path.dirname(os.path.realpath(__file__))
main_dir = os.path.join(script_dir, '..', '..')

sys.path.insert(0, main_dir)

from models_sqla import Node, Relation, Lexicon  # noqa
from utils.property_graph import PropertyGraph   # noqa

###############################################################################

logger = logging.getLogger(__name__)

###############################################################################


def read_ontology(node_ontology_file: str):
    with open(node_ontology_file, encoding="utf-8") as f:
        content = [
            line.split(",")
            for line in f.read().split("\n")[1:]
            if line
        ]

    level = 0
    parents = defaultdict(list)
    current_parents = []
    for row in content:
        for idx, cell in enumerate(row):
            if cell.strip():
                _level = idx
                break

        if _level == 0:
            current_parents = [cell]
            continue

        if _level > level:
            level = _level
            parents[cell.strip()].extend(current_parents.copy())
            # TODO: check for current_parents reference by pointer
            # .copy() should handle this, but is this required?
            current_parents.append(cell.strip())
        elif _level == level:
            current_parents.pop()
            parents[cell.strip()].extend(current_parents.copy())
            current_parents.append(cell.strip())
        else:
            while _level <= level:
                print(_level, level, cell)
                if current_parents:
                    current_parents.pop()
                level -= 1
            parents[cell.strip()].extend(current_parents.copy())
            current_parents.append(cell.strip())

    # TODO: INCORRECT
    # FIX

    return parents


###############################################################################


class AyurvedaGraph(PropertyGraph):

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


def build_graph() -> PropertyGraph:
    graph = AyurvedaGraph()
    errors = []
    node_query = Node.query.filter(Node.is_deleted.is_(False))
    relation_query = Relation.query.filter(Relation.is_deleted.is_(False))
    logger.debug(node_query)
    logger.debug(relation_query)
    nodes = node_query.all()
    relationships = relation_query.all()
    for node in nodes:
        node_id = node.id
        labels = [node.label.label]
        properties = {
            'lemma': node.lemma.lemma,
            'annotator': node.annotator.id,
            'line_id': node.line_id,
            'line_text': node.line.text,
        }
        graph.add_node(node_id=node_id, labels=labels, properties=properties)

    for relationship in relationships:
        label = relationship.label.label
        properties = {
            'annotator': relationship.annotator.id,
            'line_id': relationship.line_id,
            'line_text': relationship.line.text,
        }
        if relationship.detail:
            properties['detail'] = relationship.detail

        src_id = relationship.src_id
        dst_id = relationship.dst_id
        src_node = relationship.src_node
        dst_node = relationship.dst_node
        if src_node.is_deleted or dst_node.is_deleted:
            error_message = (
                f"Line: {relationship.line_id}):: "
                f"(Relationship {relationship.id}):\n"
                f"\t(Node {src_id}) ({src_node.lemma.lemma}:{src_node.label.label}) "
                f"(is_deleted: {src_node.is_deleted}, src_node.line_id = {src_node.line_id})\n"
                f"\t-[{label}]-> \n"
                f"\t(Node {dst_id}) ({dst_node.lemma.lemma}:{dst_node.label.label}) "
                f"(is_deleted: {dst_node.is_deleted}, dst_node.line_id = {dst_node.line_id})\n\n"
            )
            error_csv = (
                f"{relationship.id},"
                f"{relationship.line_id},"
                f"{src_id},{src_node.line_id},{src_node.lemma.lemma} :: {src_node.label.label},"
                f"{src_node.is_deleted},"
                f"{label},"
                f"{dst_id},{dst_node.line_id},{dst_node.lemma.lemma} :: {dst_node.label.label},"
                f"{dst_node.is_deleted}"
            )
            errors.append(error_csv)
            continue

        graph.add_edge(src_id, label, dst_id, properties=properties)

    return graph, errors

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

    graph, errors = build_graph()
    graph.add_synonym_edges()

    if save_graph:
        with open(os.path.join(main_dir, "output", "graph.jsonl"), "w") as f:
            f.write(graph.to_jsonl())

        graph_csv = graph.to_csv()
        with open(os.path.join(main_dir, "output", "graph_nodes.csv"), "w") as f:
            f.write(graph_csv["nodes"])

        with open(os.path.join(main_dir, "output", "graph_edges.csv"), "w") as f:
            f.write(graph_csv["edges"])

###############################################################################
