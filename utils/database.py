#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database Utility Functions
"""

###############################################################################

from typing import List

from models_sqla import User, Role
from models_sqla import Corpus, Chapter, Verse, Line, Analysis
from models_sqla import Lexicon, NodeLabel, RelationLabel, Node, Relation

###############################################################################


def annotation_to_dict(model: Node or Relation) -> dict:
    if isinstance(model, Node):
        return {
            "id": model.id,
            "lemma": model.lemma.lemma,
            "line": {
                "id": model.line_id,
                "english": model.line.text,
                "sanskrit": model.line.analyses[0].parsed[0]['Sanskrit']
            },
            "annotator": {
                "id": model.annotator_id,
                "username": model.annotator.username
            }
        }

    if isinstance(model, Relation):
        return {
            "id": model.id,
            "source": model.src_lemma.lemma,
            "relation_label": {
                "id": model.label.id,
                "label": model.label.label
            },
            "relation_detail": model.detail or "",
            "target": model.dst_lemma.lemma,
            "line": {
                "id": model.line_id,
                "english": model.line.text,
                "sanskrit": model.line.analyses[0].parsed[0]['Sanskrit']
            },
            "annotator": {
                "id": model.annotator_id,
                "username": model.annotator.username
            }
        }

###############################################################################


def search_node(
    label: str = "%",
    lemma: str = "%",
    line_id: str = "%",
    annotator: str = "%",
    is_deleted: bool = False,
    offset: int = 0,
    limit: int = 30,
    convert_to_dict: bool = True
) -> list:
    """Search node annotations"""
    node_query = Node.query.filter(
        Node.label.has(NodeLabel.label.ilike(label)),
        Node.lemma.has(Lexicon.lemma.ilike(lemma)),
        Node.line.has(Line.id.ilike(line_id)),
        Node.annotator.has(User.username.ilike(annotator)),
        Node.is_deleted == is_deleted
    )
    return [
        annotation_to_dict(n) if convert_to_dict else n
        for n in node_query.offset(offset).limit(limit)
    ]


def search_relation(
    src_lemma: str = "%",
    label: str = "%",
    detail: str = "%",
    dst_lemma: str = "%",
    line_id: str = "%",
    annotator: str = "%",
    is_deleted: bool = False,
    offset: int = 0,
    limit: int = 30,
    convert_to_dict: bool = True
) -> list:
    """Search relation annotations"""
    relation_query = Relation.query.filter(
        Relation.src_lemma.has(Lexicon.lemma.ilike(src_lemma)),
        Relation.label.has(RelationLabel.label.ilike(label)),
        Relation.dst_lemma.has(Lexicon.lemma.ilike(dst_lemma)),
        Relation.detail.ilike(detail),
        Relation.line.has(Line.id.ilike(line_id)),
        Relation.annotator.has(User.username.ilike(annotator)),
        Relation.is_deleted == is_deleted
    )
    return [
        annotation_to_dict(r) if convert_to_dict else r
        for r in relation_query.offset(offset).limit(limit)
    ]


###############################################################################


def get_chapter_data(chapter_id: int, user: User) -> dict:
    """Get Chapter Data

    Fetch line data for the lines belonging to the specified chapter.
    Calls `get_line_data()`.

    Parameters
    ----------
    chapter_id : int
        Chapter ID
    user : User
        User object for the user associated with the request
        If the user has `annotate` permissions, annotations will be fetched

    Returns
    -------
    dict
        Line data, keyed by line IDs
    """
    chapter = Chapter.query.get(chapter_id)

    line_ids = [
        line.id
        for verse in chapter.verses
        for line in verse.lines
    ]
    annotator_ids = []
    fetch_nodes = False
    fetch_relations = False
    if user.has_permission('annotate'):
        annotator_ids = [user.id]
        fetch_nodes = True
        fetch_relations = True
    if user.has_permission('curate') or user.has_role('admin'):
        annotator_ids = None
        fetch_nodes = True
        fetch_relations = True
    return get_line_data(
        line_ids,
        annotator_ids=annotator_ids,
        fetch_nodes=fetch_nodes,
        fetch_relations=fetch_relations
    )


def get_line_data(
    line_ids: List[int],
    annotator_ids: List[int] = None,
    fetch_nodes: bool = False,
    fetch_relations: bool = False
) -> dict:
    """Get Line Data

    Fetch content, linguistic information and annotations

    Parameters
    ----------
    line_ids : List[int]
        List of line IDs
    annotator_ids : List[int], optional
        List of user IDs of annotators
        If None, annotations by all the users will be fetched.
        The default is None.
    fetch_nodes : bool, optional
        Fetch node annotations
        The default is False.
    fetch_relations : bool, optional
        Fetch relationship annotations
        The default is False.

    Returns
    -------
    dict
        Line data, keyed by line IDs
    """
    line_object_query = Line.query.filter(Line.id.in_(line_ids))
    data = {
        line.id: {
            'line_id': line.id,
            'verse_id': line.verse_id,
            'line': line.text,
            'split': line.split,
            'analysis': line.analyses.first().parsed,
            'entity': [],
            'relation': [],
            'marked': False
        }
        for line in line_object_query.all()
    }

    if annotator_ids is None:
        node_query = Node.query.filter(
            Node.line_id.in_(line_ids)
        )
        relation_query = Relation.query.filter(
            Relation.line_id.in_(line_ids)
        )
    else:
        node_query = Node.query.filter(
            Node.line_id.in_(line_ids),
            Node.annotator_id.in_(annotator_ids)
        )
        relation_query = Relation.query.filter(
            Relation.line_id.in_(line_ids),
            Relation.annotator_id.in_(annotator_ids)
        )

    if fetch_nodes:
        for node in node_query.all():
            data[node.line_id]['entity'].append({
                'id': node.id,
                'root': node.lemma.lemma,
                'type': node.label.label,
                'annotator': node.annotator.username,
                'is_deleted': node.is_deleted
            })
            data[node.line_id]['marked'] = True

    if fetch_relations:
        for relation in relation_query.all():
            data[relation.line_id]['relation'].append({
                'id': relation.id,
                'source': relation.src_lemma.lemma,
                'target': relation.dst_lemma.lemma,
                'label': relation.label.label,
                'detail': relation.detail,
                'annotator': relation.annotator.username,
                'is_deleted': relation.is_deleted
            })
            data[relation.line_id]['marked'] = True

    return data
