#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 05 22:31:54 2021

@author: Hrishikesh Terdalkar
"""

import json
import logging

from collections import Counter

###############################################################################

logger = logging.getLevelName(__name__)

###############################################################################


class PropertyNode:
    def __init__(self, node_id, labels=[], properties={}):
        self.id = node_id
        self.labels = labels
        self.properties = properties
        self.incoming = Counter()
        self.outgoing = Counter()

    def add_incoming(self, neighbour_id):
        self.incoming[neighbour_id] += 1

    def add_outgoing(self, neighbour_id):
        self.outgoing[neighbour_id] += 1

    def remove_incoming(self, neighbour_id):
        self.incoming[neighbour_id] -= 1

    def remove_outgoing(self, neighbour_id):
        self.outgoing[neighbour_id] -= 1

    def update(self, labels, properties):
        self.labels += [label for label in labels if label not in self.labels]
        for k, v in self.properties.items():
            if isinstance(v, list):
                v += [e for e in properties[k] if e not in v]
            else:
                if properties.get(k) and properties.get(k) != v:
                    v = [v]
                    v += [properties.get(k)]
                    logger.warning(f"Property {k} changed into a list.")

    def to_json(self):
        return json.dumps({
            'type': 'node',
            'id': self.id,
            'labels': self.labels,
            'properties': self.properties
        }, ensure_ascii=False)

    def __repr__(self):
        return f'''(id="{self.id}", lemma="{self.properties['lemma']}")'''

# --------------------------------------------------------------------------- #


class PropertyEdge:
    def __init__(self, start_id, label, end_id, properties):
        self.start_id = start_id
        self.end_id = end_id
        self.label = label
        self.properties = properties

    def update(self, properties):
        for k, v in self.properties.items():
            if isinstance(v, list):
                v += [e for e in properties[k] if e not in v]
            else:
                if properties.get(k) and properties.get(k) != v:
                    v = [v]
                    v += [properties[k]]
                    logger.warning(f"Property {k} changed into a list.")

    def to_json(self):
        return json.dumps({
            'type': 'relationship',
            'label': self.label,
            'start': {'id': self.start_id},
            'end': {'id': self.end_id},
            'properties': self.properties
        }, ensure_ascii=False)

# --------------------------------------------------------------------------- #


class PropertyGraph:
    def __init__(self):
        self.nodes = {}
        self.edges = {}

    def add_node(self, node_id, labels, properties):
        if node_id in self.nodes:
            self.nodes[node_id].update(labels, properties)
        else:
            self.nodes[node_id] = PropertyNode(
                node_id=node_id,
                labels=labels,
                properties=properties
            )

        if 'lemma' not in properties:
            print("---", node_id, labels, properties, "---")

    def add_edge(self, src_id, label, dst_id, properties):
        edge_tuple = (src_id, label, dst_id)
        if edge_tuple in self.edges:
            self.edges[edge_tuple].update(properties)
        else:
            if src_id in self.nodes and dst_id in self.nodes:
                self.edges[edge_tuple] = PropertyEdge(
                    start_id=src_id,
                    label=label,
                    end_id=dst_id,
                    properties=properties
                )
            else:
                possible_labels = self.infer_type(label)
                if src_id not in self.nodes:
                    src_properties = {
                        'lemma': self.get_lemma_by_id(src_id),
                        'annotator': properties['annotator'],
                        'line_id': properties['line_id'],
                        'auto': True
                    }
                    possible_src_labels = possible_labels[0]
                    self.add_node(src_id, possible_src_labels, src_properties)
                if dst_id not in self.nodes:
                    dst_properties = {
                        'lemma': self.get_lemma_by_id(dst_id),
                        'annotator': properties['annotator'],
                        'line_id': properties['line_id'],
                        'auto': True
                    }
                    possible_dst_labels = possible_labels[1]
                    self.add_node(dst_id, possible_dst_labels, dst_properties)
                self.edges[edge_tuple] = PropertyEdge(
                    start_id=src_id,
                    label=label,
                    end_id=dst_id,
                    properties=properties
                )
        # At this point, both src_id and dst_id nodes exist in the graph
        self.nodes[dst_id].add_incoming(src_id)
        self.nodes[src_id].add_outgoing(dst_id)

    def remove_edge(self, src_id, label, dst_id):
        edge_tuple = (src_id, label, dst_id)
        if edge_tuple in self.edges:
            del self.edges[edge_tuple]
            self.nodes[src_id].remove_outgoing(dst_id)
            self.nodes[dst_id].remove_incoming(src_id)

    def transfer_edge(self, src_id, label, dst_id, new_src=None, new_dst=None):
        if new_src not in self.nodes and new_dst not in self.nodes:
            return False

        edge_tuple = (src_id, label, dst_id)
        properties = self.edges[edge_tuple].properties
        if new_src in self.nodes:
            self.remove_edge(src_id, label, dst_id)
            self.add_edge(new_src, label, dst_id, properties)
            return True

        if new_dst in self.nodes:
            self.remove_edge(src_id, label, dst_id)
            self.add_edge(src_id, label, new_dst, properties)

    def get_transitive_closure(self, node_id, relations=[]):
        closure = set()
        current_nodes = {node_id}
        while True:
            next_nodes = set()
            for _node_id in current_nodes:
                closure.add(_node_id)
                neighbours = set(self.nodes[_node_id].incoming).union(
                    set(self.nodes[_node_id].outgoing)
                )
                for neighbour in neighbours:
                    if neighbour in closure:
                        continue
                    for relation in relations:
                        if ((neighbour, relation, _node_id) in self.edges or
                                (_node_id, relation, neighbour) in self.edges):
                            next_nodes.add(neighbour)
            current_nodes = next_nodes
            if not current_nodes:
                break
        return closure

    def get_groups(self, relations=[]):
        groups = []
        handled = set()
        for node_id in self.nodes:
            if node_id in handled:
                continue
            closure = self.get_transitive_closure(node_id, relations=[])
            if len(closure) > 1:
                groups.append([
                    (self.nodes[_id],
                     sum(self.nodes[_id].incoming.values()) +
                     sum(self.nodes[_id].outgoing.values()),
                     self.nodes[_id].properties['line_id'])
                    for _id in closure
                ])
                handled.update(closure)

        answer = []
        for group in groups:
            answer.append(
                sorted(group, key=lambda x: (x[1], max(x[2])), reverse=True)
            )
        return answer

    def to_jsonl(self):
        jsonl = []
        for node_id, node in self.nodes.items():
            jsonl.append(node.to_json())

        for (start_id, edge_label, end_id), edge in self.edges.items():
            jsonl.append(edge.to_json())
        return '\n'.join(jsonl)

    # ----------------------------------------------------------------------- #

    def infer_type(self, label):
        raise NotImplementedError

    def get_lemma_by_id(self, id):
        raise NotImplementedError

    # ----------------------------------------------------------------------- #

###############################################################################
