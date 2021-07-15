#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 10 13:27:53 2021

@author: Hrishikesh Terdalkar
"""

import json
import py2neo
import logging

###############################################################################


def find_entity_type(entities, entity_type):
    for entity in entities:
        if isinstance(entity, entity_type):
            yield entity
        elif isinstance(entity, (list, tuple, set)):
            yield from find_entity_type(entity, entity_type)
        elif isinstance(entity, py2neo.data.Path):
            yield from find_entity_type(entity.nodes, entity_type)
            yield from find_entity_type(entity.relationships, entity_type)

###############################################################################


class Graph:
    def __init__(self, server, username, password):
        self.__username = username
        self.__password = password
        self.__server = server
        self.graph = py2neo.Graph(
            self.__server + '/data/',
            username=self.__username,
            password=self.__password
        )
        self.__logger = logging.getLogger(self.__class__.__name__)

    def run_query(self, query):
        result = self.graph.run(query)
        matches = result.data()
        nodes = set()
        edges = set()
        for match in matches:
            nodes = nodes.union(
                find_entity_type(match.values(), py2neo.data.Node)
            )
            edges = edges.union(
                find_entity_type(match.values(), py2neo.data.Relationship)
            )

        final_nodes = {
            self.repr_entity(node): self.format_node(node) for node in nodes
        }
        final_edges = {
            self.repr_entity(edge): self.format_edge(edge) for edge in edges
        }
        final_matches = [
            {
                self.repr_entity(k): self.repr_entity(v)
                for k, v in match.items()
            }
            for match in matches
        ]
        return final_matches, final_nodes, final_edges

    def repr_entity(self, entity, jsonify=False):
        """
        Return a representation of an entity

        For Node and Relationship, the `identity' of it is returned, which
        can be used in combination with the formatted node and edge objects

        For other types, some kind of string representation for direct display
        """
        if isinstance(entity, py2neo.data.Node):
            return f"N:{entity.identity}"
        if isinstance(entity, py2neo.data.Relationship):
            return f"R:{entity.identity}"
        if isinstance(entity, py2neo.data.Path):
            return (self.repr_entity(entity.start_node),
                    self.repr_entity(entity.relationships),
                    self.repr_entity(entity.end_node))
        if isinstance(entity, (list, tuple)):
            return [self.repr_entity(e) for e in entity]
        if isinstance(entity, (str, int, float, bool)):
            return entity

        # Really? Not one of the above?
        self.__logger.warning(f"Entity of type {type(entity)} encountered.")
        return str(entity)

    def format_node(self, node, jsonify=False):
        node_dict = {
            'id': self.repr_entity(node),
            'type': 'node',
            'labels': list(node._labels),
            'properties': {
                'lemma': node.get('lemma'),
                'line_id': node.get('line_id'),
                'annotator': node.get('annotator')
            }
        }
        return (
            json.dumps(node_dict, ensure_ascii=False)
            if jsonify else
            node_dict
        )

    def format_edge(self, edge, jsonify=False):
        edge_dict = {
            'id': self.repr_entity(edge),
            'type': 'relationship',
            'label': type(edge).__name__,
            'start': {
                'id': self.repr_entity(edge.start_node)
            },
            'end': {
                'id': self.repr_entity(edge.end_node)
            },
            'properties': {
                'line_id': edge.get('line_id'),
                'annotator': edge.get('annotator'),
                'detail': edge.get('detail')
            }
        }
        return (
            json.dumps(edge_dict, ensure_ascii=False)
            if jsonify else
            edge_dict
        )
