#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
The Property Graph Data Model

Conforms to specification from,
https://neo4j.com/developer/graph-database/#property-graph

Nodes are the entities in the graph.
They can hold any number of attributes (key-value pairs) called properties.
Nodes can be tagged with labels, representing their different roles in a
specific domain. Node labels may also serve to attach metadata (such as index
or constraint information) to certain nodes.

Relationships provide directed, named, semantically-relevant connections
between two node entities.
A relationship always has a direction, a type, a start node, and an end node.
Like nodes, relationships can also have properties. I

Primary classes provided here are,
* `PropertyNode` - to model a node in a Property Graph
* `PropertyEdge` - to model a relationship (or an edge) in a Property Graph
* `PropertyGraph` - to model a Property Graph

@author: Hrishikesh Terdalkar
"""

import json
import logging

from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd

###############################################################################

logger = logging.getLogger(__name__)

###############################################################################


class PropertyNode:
    """Node in a Property Graph"""

    def __init__(self, node_id, labels=None, properties=None):
        """
        Create an instance of `PropertyNode`

        Recommended to use `PropertyGraph.add_node()` method,
        which will create an instance instead of doing so explicitly.
        """
        self.id = node_id
        if isinstance(labels, list):
            self.labels = labels
        elif isinstance(labels, str):
            self.labels = [labels]
        else:
            self.labels = []

        self.properties = {}
        if isinstance(properties, dict):
            self.update([], properties)

        # track incoming and outgoing neighbours
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
        """
        Update labels and properties of a node.

        The labels will be extended, not replaced.
        Similarly, properties will be extended.
        In case a property key exists, and the value is not a list, value will
        be converted to a list containing the current and the new value.
        """
        self.labels += [label for label in labels if label not in self.labels]
        for k, v in properties.items():
            valid_property = (
                isinstance(k, str)
                and isinstance(v, (int, float, bool, str))
            )
            if not valid_property:
                logger.warning(
                    f"Ignored invalid property '{k}' ({type(k)}) "
                    f"with value '{v}' ({type(v)})."
                )
                continue

            # If a property does not exist, set it
            if self.properties.get(k) is None:
                self.properties[k] = v
                continue

            # Property exists
            if isinstance(self.properties[k], list):
                if v not in self.properties[k]:
                    self.properties[k] += [v]
            elif isinstance(self.properties[k], (int, float, bool, str)):
                if v != self.properties[k]:
                    self.properties[k] = [self.properties[k], v]
                    logger.warning(
                        f"Property '{k}' changed into a list for {self}."
                    )

    def to_json(self):
        """Return a JSON representation of the node compatible with neo4j."""
        return json.dumps({
            'type': 'node',
            'id': self.id,
            'labels': self.labels,
            'properties': self.properties
        }, ensure_ascii=False)

    def __repr__(self):
        return f'{self.__class__.__name__}(id="{self.id}")'


# --------------------------------------------------------------------------- #


class PropertyEdge:
    """Relationship in a Property Graph"""

    def __init__(self, start_id, label, end_id, properties=None):
        """
        Create an instance of `PropertyEdge`

        An edge represents a relationship, and is always directed.

        Recommended to use `PropertyGraph.add_edge()` method,
        which will create an instance instead of doing so explicitly.
        """
        self.start_id = start_id
        self.end_id = end_id
        self.label = label
        self.properties = properties if properties is not None else {}

        self.properties = {}
        if isinstance(properties, dict):
            self.update(properties)

    def update(self, properties):
        """
        Update properties of an edge.

        Properties will be extended.
        In case a property key exists, and the value is not a list, value will
        be converted to a list containing the current and the new value.
        """
        for k, v in properties.items():
            valid_property = (
                isinstance(k, str)
                and isinstance(v, (int, float, bool, str))
            )
            if not valid_property:
                logger.warning(
                    f"Ignored invalid property '{k}' ({type(k)}) "
                    f"with value '{v}' ({type(v)})."
                )
                continue

            # If a property does not exist, set it
            if self.properties.get(k) is None:
                self.properties[k] = v
                continue

            # Property exists
            if isinstance(self.properties[k], list):
                if v not in self.properties[k]:
                    self.properties[k] += [v]
            elif isinstance(self.properties[k], (int, float, bool, str)):
                if v != self.properties[k]:
                    self.properties[k] = [self.properties[k], v]
                    logger.warning(
                        f"Property '{k}' changed into a list for {self}."
                    )

    def to_json(self):
        """Return a JSON representation of the edge compatible with neo4j."""
        return json.dumps({
            'type': 'relationship',
            'label': self.label,
            'start': {'id': self.start_id},
            'end': {'id': self.end_id},
            'properties': self.properties
        }, ensure_ascii=False)

    def __repr__(self):
        return (
            f'{self.__class__.__name__}'
            f'(start="{self.start_id}", '
            f'label="{self.label}", '
            f'end="{self.end_id}")'
        )

# --------------------------------------------------------------------------- #


class PropertyGraph:
    """Property Graph"""

    def __init__(self):
        """Create an instance of a property graph."""
        self.nodes = {}
        self.edges = {}

    def add_node(self, node_id, labels=None, properties=None):
        """
        Add a node to the graph.

        If the node already exists, its labels and properties will be
        updated.

        Parameters
        ----------
        node_id : str
            Unique ID for a node, w.r.t to the graph
        labels : list, optional
            List of string labels to represent roles of the node.
            The default is None.
        properties : dict, optional
            Properties in the form of key-value pairs (dict).
            The default is None.
        """
        if labels is None:
            labels = []
        if properties is None:
            properties = {}

        if node_id in self.nodes:
            self.nodes[node_id].update(labels, properties)
        else:
            self.nodes[node_id] = PropertyNode(
                node_id=node_id,
                labels=labels,
                properties=properties
            )

    def add_edge(self, src_id, label, dst_id, properties=None):
        """
        Add an edge (i.e. a relationship) to the graph.

        Ideally, both source and destination nodes should exist in the graph
        prior to adding an edge between them. In case any of the nodes don't
        exist, they will be created. Labels and properties of the nodes
        are inferred using a stub `PropertyGraph.infer()` method.

        By default, the infer method doesn't actually infer anything and
        nodes will have no labels and a single property `auto` set to `True` to
        indicate that the node was added automatically.

        It is highly recommended to do one of the following,
        1. Ensure that both the nodes already exist in the graph
        2. Implement a domain-relevant infer() function

        If the edge already exists, its properties will be updated.

        Parameters
        ----------
        start_id : str
            ID of the source node
        label : str
            Type of the relationship
        end_id : str
            ID of the destination node
        properties : dict, optional
            Properties in the form of key-value pairs (dict).
            The default is None.
        """
        if properties is None:
            properties = {}

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
                _r = self.infer(src_id, label, dst_id, properties)
                src_labels, dst_labels, src_properties, dst_properties = _r

                if src_id not in self.nodes:
                    self.add_node(src_id, src_labels, src_properties)
                if dst_id not in self.nodes:
                    self.add_node(dst_id, dst_labels, dst_properties)
                self.edges[edge_tuple] = PropertyEdge(
                    start_id=src_id,
                    label=label,
                    end_id=dst_id,
                    properties=properties
                )
        # At this point, both src_id and dst_id nodes exist in the graph
        self.nodes[src_id].add_outgoing(dst_id)
        self.nodes[dst_id].add_incoming(src_id)

    def remove_edge(self, src_id, label, dst_id):
        """Remove an edge"""
        edge_tuple = (src_id, label, dst_id)
        if edge_tuple in self.edges:
            del self.edges[edge_tuple]
            self.nodes[src_id].remove_outgoing(dst_id)
            self.nodes[dst_id].remove_incoming(src_id)

    def transfer_edge(self, src_id, label, dst_id, new_src=None, new_dst=None):
        """
        Transfer an edge to a new source OR destination.

        Exactly one of `new_src` or `new_dst` must be provided.
        If none are provided, no action will be performed.
        If both are provided, `new_dst` argument will be ignored.

        Parameters
        ----------
        src_id : str
            ID of the source node of the edge to be transferred
        label : TYPE
            Label of the edge to be transferred
        dst_id : str
            ID of the destination node of the edge to be transferred
        new_src : str, optional
            ID of the new source node.
            The default is None.
        new_dst : str, optional
            ID of the new source node.
            The default is None.

        Returns
        -------
        bool
            Success of the transfer operation
        """
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
            return True

    def get_connected_nodes(self, node_id, relations=None):
        """
        Get all nodes connected to the specified node by paths only containing
        the relations belonging to specified relations.
        """
        connected_nodes = set()
        current_nodes = {node_id}
        if relations is None:
            relations = []

        while True:
            next_nodes = set()
            for _node_id in current_nodes:
                connected_nodes.add(_node_id)
                neighbours = set(self.nodes[_node_id].incoming).union(
                    set(self.nodes[_node_id].outgoing)
                )
                for neighbour in neighbours:
                    if neighbour in connected_nodes:
                        continue
                    for relation in relations:
                        if ((neighbour, relation, _node_id) in self.edges or
                                (_node_id, relation, neighbour) in self.edges):
                            next_nodes.add(neighbour)
            current_nodes = next_nodes
            if not current_nodes:
                break
        return connected_nodes

    def to_jsonl(self, path: str or Path = None) -> str:
        """
        Return a JSONL representation of the graph compatible with neo4j.

        JSONL corresponds to JSON-Lines, wherein every line is a valid JSON.
        All the nodes will appear first, followed by all the relationships.

        Parameters
        ----------
        path : str or Path (optional)
            If provided, the JSONL will be written to the specified location
            The default is None.

        Returns
        -------
        str
            Valid JSONL representation of the entire graph
        """

        jsonl = []
        for node_id, node in self.nodes.items():
            jsonl.append(node.to_json())

        for (start_id, edge_label, end_id), edge in self.edges.items():
            jsonl.append(edge.to_json())

        jsonl_content = "\n".join(jsonl)
        if path:
            return Path(path).write_text(jsonl_content)

        return jsonl_content

    # ----------------------------------------------------------------------- #

    def to_csv(self, prefix: str = None) -> Dict[str, str]:
        """
        Return a CSV representation of the graph compatible with neo4j.

        Output can be used with Neo4j's `apoc.import.csv()`
        Command:
        ```
        call apoc.import.csv(
            [{fileName: 'prefix_nodes.csv', labels: []}],
            [{fileName: 'prefix_edges.csv', type: null}],
            {ignoreDuplicateNodes: true, ignoreBlankString: true}
        )
        ```

        CSV Format:
        https://neo4j.com/docs/operations-manual/current/tools/neo4j-admin/neo4j-admin-import/#import-tool-header-format/

        Parameters
        ----------

        prefix : str (optional)
            If provided, two CSV Files can be written, `prefix`_nodes.csv and
            `prefix`_edges.csv
            The prefix should include absolute parent path, in case the desired
            location is not the current directory.

        Returns
        -------
        Dict[str, str]
            Dictionary containing two keys, `nodes` and `edges` with values
            being the valid CSV strings for nodes and edges.
        """
        nodes = []
        edges = []
        for node_id, node in self.nodes.items():
            node_row = {
                ":ID": node_id,
                ":LABEL": ";".join(node.labels),
            }
            for k, v in node.properties.items():
                if isinstance(v, list):
                    val = ";".join(map(str, v))
                else:
                    val = v
                node_row[k] = val
            nodes.append(node_row)

        for (start_id, edge_label, end_id), edge in self.edges.items():
            edge_row = {
                ":START_ID": start_id,
                ":TYPE": edge_label,
                ":END_ID": end_id,
            }
            for k, v in edge.properties.items():
                if isinstance(v, list):
                    val = ";".join(map(str, v))
                else:
                    val = v
                edge_row[k] = val
            edges.append(edge_row)

        nodes_data = pd.DataFrame(nodes)
        edges_data = pd.DataFrame(edges)

        csv_data = {
            "nodes": nodes_data.to_csv(index=False),
            "edges": edges_data.to_csv(index=False)
        }

        if prefix:
            nodes_data.to_csv(f"{prefix}_nodes.csv", index=False)
            edges_data.to_csv(f"{prefix}_edges.csv", index=False)

        return csv_data

    # ----------------------------------------------------------------------- #

    def _to_schema_csv(self) -> Dict[str, List[Tuple[str, str]]]:
        """
        Return a CSV representation of the graph compatible with neo4j.

        Several CSV files are generated, one for every unique property schema

        CSV Format:
        https://neo4j.com/docs/operations-manual/current/tools/neo4j-admin/neo4j-admin-import/#import-tool-header-format/
        """
        node_csv = []
        edge_csv = []

        node_property_sets = defaultdict(list)
        for node_id, node in self.nodes.items():
            property_set = tuple(node.properties.keys())
            node_property_sets[property_set].append(node_id)

        for header, node_ids in node_property_sets.items():
            csv_header = ",".join([":ID", ":LABEL", *header])
            csv_body_list = []
            for node_id in node_ids:
                csv_row_list = [
                    node_id,
                    ";".join(self.nodes[node_id].labels),
                ]
                for k, v in self.nodes[node_id].properties.items():
                    if isinstance(v, list):
                        val = ";".join(map(str, v))
                    else:
                        val = v
                    csv_row_list.append(f'"{val}"')

                csv_row = ",".join(csv_row_list)
                csv_body_list.append(csv_row)
            csv_body = "\n".join(csv_body_list)
            node_csv.append((csv_header, csv_body))

        edge_property_sets = defaultdict(list)
        for (start_id, edge_label, end_id), edge in self.edges.items():
            edge_property_sets[tuple(edge.properties.keys())].append(
                (start_id, edge_label, end_id)
            )

        for header, edge_ids in edge_property_sets.items():
            csv_header = ",".join([":START_ID", ":END_ID", ":TYPE", *header])
            csv_body_list = []
            for edge_id in edge_ids:
                start_id, edge_type, end_id = edge_id
                csv_row_list = [
                    start_id,
                    end_id,
                    edge_type
                ]
                for k, v in self.edges[edge_id].properties.items():
                    if isinstance(v, list):
                        val = ";".join(map(str, v))
                    else:
                        val = v
                    csv_row_list.append(f'"{val}"')

                csv_row = ",".join(csv_row_list)
                csv_body_list.append(csv_row)
            csv_body = "\n".join(csv_body_list)
            edge_csv.append((csv_header, csv_body))

        return {"nodes": node_csv, "edges": edge_csv}

    def _write_schema_csv(
        self,
        path: str or Path = ".",
        header_prefix: str = "header",
        content_prefix: str = "content",
        node_prefix: str = "node",
        edge_prefix: str = "edge"
    ):
        """
        Write Several CSV Files, one for every unique property schema

        Generated using `.to_schema_csv()`

        Can be used with neo4j-admin import tool.
        """
        base_path = Path(path)
        base_path.mkdir(parents=True, exist_ok=True)

        csv_data = self._to_schema_csv()
        for content_type, csv_content in csv_data.items():
            if content_type == "nodes":
                prefix = node_prefix
            if content_type == "edges":
                prefix = edge_prefix

            for idx, (header, content) in enumerate(csv_content):
                header_file = (
                    base_path / f"{prefix}_{header_prefix}_{idx}.csv"
                )
                without_header_content_file = (
                    base_path / f"{prefix}_{content_prefix}_{idx}.csv"
                )
                with_header_content_file = (
                    base_path / f"{prefix}_{idx}.csv"
                )
                (header_file).write_text(header)
                (without_header_content_file).write_text(content)
                (with_header_content_file).write_text(f"{header}\n{content}")

            logger.info(f"Written {len(csv_content)} {content_type} tables.")

    # ----------------------------------------------------------------------- #

    def infer(self, src_id, label, dst_id, properties):
        """
        Stub to infer label and properties of src and dst nodes.

        Recommended to implement a suitable domain-relevant mechanism to infer
        the labels and  properties of source and destination nodes

        Returns
        -------
        src_labels : list
            List of inferred labels for the source node.
        dst_labels : list
            List of inferred labels for the destination node.
        src_properties : dict
            Inferred properties for the source node.
        dst_properties : dict
            Inferred properties for the destination node.
        """
        src_labels = []
        dst_labels = []
        src_properties = {'auto': True}
        dst_properties = {'auto': True}
        return src_labels, dst_labels, src_properties, dst_properties

###############################################################################


def main():
    pass

###############################################################################


if __name__ == '__main__':
    main()
