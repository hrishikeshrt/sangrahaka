#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 24 23:22:31 2021

@author: Hrishikesh Terdalkar
"""

###############################################################################

import logging
import pypher

from utils.property_graph import PropertyGraph

###############################################################################

logger = logging.getLogger(__name__)

###############################################################################


def graph_to_cypher(graph, non_conditionals=None,
                    use_where=False, use_labels=True, use_directions=True,
                    node_prefix="n", relation_prefix="r"):
    """
    Convert a graph (set of nodes and edges) into a Cypher query.

    Subgraph is to be provided as a list of nodes and a list of edges

    Parameters
    ----------
    graph : PropertyGraph or dict
        If dict, it should contain two keys, 'nodes' and 'edges', indicating
        - List of nodes in (node-id, labels, properties) format
        - List of edges in (src-id, relation_label, dst-id, properties) format
    non_conditionals : dict, optional
        Dictionary of property names and list of values for which the
        conditions will not be added
        The default is None
    use_where : bool, optional
        If True,
            Use WHERE conditions instead of specifying properties with nodes
        The default is False.
    use_labels : bool, optional
        If True,
            Use node labels and relation labels in conditions
        The default is True.
    use_directions : bool, optional
        If True,
            Query patterns use directed edges wherever available.
            If the 'dir' property on the edge is set to 'both', query pattern
            will use undirected edge.
        The default is False.
    node_prefix : str, optional
        Prefix for nodes in the generated Cypher qury
        The default is 'n'.
    relation_prefix : str, optional
        Prefix for relations in the generated Cypher qury
        The default is 'r'.

    Returns
    -------
    query : str
        Cypher Query
    """
    if isinstance(graph, PropertyGraph):
        nodes = [(node.id, node.labels, node.properties)
                 for node in graph.nodes.values()]
        edges = [(edge.start_id, edge.label, edge.end_id, edge.properties)
                 for edge in graph.edges.values()]
    elif isinstance(graph, dict):
        nodes = graph['nodes']
        edges = graph['edges']
    else:
        logger.error("Invalid input type.")
        return None

    _rid = 0

    p = pypher.Pypher()

    _edges = []
    _returns = []

    # _returns = [
    #     f'{node_prefix}{node_id}'
    #     for node_id, labels, properties in nodes
    #     if properties.get('return')
    # ]

    nodes = {
        node_id: {'labels': labels, 'properties': properties}
        for node_id, labels, properties in nodes
    }

    # remove non-conditionals
    if isinstance(non_conditionals, dict):
        for node_id in nodes:
            properties = nodes[node_id]['properties']
            mark_for_deletion = []
            for _property, _value in properties.items():
                if isinstance(non_conditionals.get(_property), list):
                    if _value in non_conditionals.get(_property):
                        mark_for_deletion.append(_property)

            for _property in mark_for_deletion:
                del properties[_property]
                logger.info(
                    f"Removed non-conditional '{_property}' '{_value}' "
                    f"from {node_prefix}{node_id}"
                )
    else:
        if non_conditionals is not None:
            logger.warning(
                f"'non_conditionals' must be a 'dict', "
                f"not '{type(non_conditionals)}'"
            )

    for _src_id, relation, _dst_id, _properties in edges:
        _rid += 1
        src_var = f'{node_prefix}{_src_id}'
        dst_var = f'{node_prefix}{_dst_id}'
        rel_var = f'{relation_prefix}{_rid}'

        # if _properties.get('return'):
        #     _returns.append(f'{relation_prefix}{_rid}')

        src_labels = nodes[_src_id].get('labels')
        dst_labels = nodes[_dst_id].get('labels')

        src_properties = None
        dst_properties = None

        if not use_where:
            src_properties = nodes[_src_id]['properties']
            dst_properties = nodes[_dst_id]['properties']

        if src_properties is None:
            src_properties = {}
        if dst_properties is None:
            dst_properties = {}

        if not use_labels:
            src_labels = []
            dst_labels = []
            relation = None

        is_undirected = any([
            not use_directions,
            'dir' in _properties and _properties.get('dir').lower() == 'both'
        ])

        if is_undirected:
            edge = pypher.__.node(
                src_var, src_labels, **src_properties
            ).rel(
                rel_var, relation
            ).node(
                dst_var, dst_labels, **dst_properties
            )
        else:
            edge = pypher.__.node(
                src_var, src_labels, **src_properties
            ).rel_out(
                rel_var, relation
            ).node(
                dst_var, dst_labels, **dst_properties
            )

        _edges.append(edge)

    p.Match(*_edges)

    # ----------------------------------------------------------------------- #

    if use_where:
        conditions = []

        for node_id in nodes:
            properties = nodes[node_id]['properties']

            _var = f'{node_prefix}{node_id}'
            for _property, _value in properties.items():
                conditions.append(
                    pypher.__().raw(_var).property(_property) == _value
                )

        p.WHERE(pypher.__.ConditionalAND(*conditions))

    # ----------------------------------------------------------------------- #

    if not _returns:
        _returns = ['*']

    p.Return(', '.join(_returns))

    query = str(p)
    params = p.bound_params
    for param_name, param_value in params.items():
        query = query.replace(f'${param_name}', f'"{param_value}"')
    return query

###############################################################################
