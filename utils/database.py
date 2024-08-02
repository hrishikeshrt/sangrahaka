#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database Utility Functions
"""

###############################################################################

import logging
from typing import List, Dict, Any, Tuple

from sqlalchemy.orm.properties import ColumnProperty
from sqlalchemy.orm.relationships import RelationshipProperty
from sqlalchemy.sql import func

from models_sqla import db, User, Role
from models_sqla import Corpus, Chapter, Verse, Line, Analysis
from models_sqla import Lexicon, NodeLabel, RelationLabel, Node, Relation
from models_sqla import ActionLabel, ActorLabel, Action

from constants import PERMISSION_ANNOTATE, PERMISSION_CURATE, ROLE_ADMIN
from utils.property_graph import PropertyGraph

###############################################################################

LOGGER = logging.getLogger(__name__)

###############################################################################


def add_chapter(
    corpus_id: int,
    chapter_name: str,
    chapter_description: str,
    chapter_data: List[List[Dict]]
):
    """Add Chapter Data

    Parameters
    ----------
    corpus_id : int
        Corpus ID
    chapter_name : str
        Chapter Name
    chapter_description : str
        Chapter Description
    chapter_data : List[List[Dict]]
        Chapter data
    """

    result = {
        "message": None,
        "style": None
    }

    # Assume `chapter_name` to be unique
    # In order to avoid the need to delete entire database when re-running
    # the `bulk_add_chapter` function
    # (otherwise there is unique `line_id` constraint violation)
    if Chapter.query.filter(
        Chapter.name == chapter_name
    ).first():
        result["message"] = f"Chapter '{chapter_name}' already exists."
        result["style"] = "warning"
        return result

    try:
        chapter = Chapter()
        chapter.corpus_id = corpus_id
        chapter.name = chapter_name
        chapter.description = chapter_description

        # Group verses
        verses = []
        last_verse_id = None
        for _line in chapter_data:
            line_verse_id = _line.get('verse')
            if line_verse_id is None or line_verse_id != last_verse_id:
                last_verse_id = line_verse_id
                verses.append([])
            verses[-1].append(_line)

        for _verse in verses:
            verse = Verse()
            verse.chapter = chapter
            for _line in _verse:
                _analysis = _line.get('analysis', {})
                line = Line()
                if _line.get('id'):
                    line.id = _line.get('id')
                line.verse = verse
                line.text = _line.get('text', '')
                line.split = _line.get('split', '')

                analysis = Analysis()
                analysis.line = line

                analysis.source = _analysis.get('source', '')
                analysis.text = _analysis.get('text', '')
                analysis.parsed = _analysis.get('tokens', [])
                db.session.add(analysis)
    except Exception as e:
        result["message"] = "An error occurred while inserting data."
        result["style"] = "danger"
        LOGGER.exception(e)
    else:
        db.session.commit()
        result["message"] = f"Chapter '{chapter_name}' added successfully."
        result["style"] = "success"

    return result


###############################################################################


def annotation_to_dict(model: Node or Relation) -> dict:
    if isinstance(model, Node):
        return {
            "id": model.id,
            "lemma": model.lemma.lemma,
            "node_label": {
                "id": model.label_id,
                "label": model.label.label
            },
            "line": {
                "id": model.line_id,
                "english": model.line.text,
                "sanskrit": model.line.analyses[0].parsed[0]['Sanskrit']
            },
            "annotator": {
                "id": model.annotator_id,
                "username": model.annotator.username
            },
            "is_deleted": model.is_deleted
        }

    if isinstance(model, Relation):
        return {
            "id": model.id,
            "source": {
                "id": model.src_id,
                "lemma": model.src_node.lemma.lemma,
                "label": model.src_node.label.label
            },
            "relation_label": {
                "id": model.label_id,
                "label": model.label.label
            },
            "relation_detail": model.detail or "",
            "target": {
                "id": model.dst_id,
                "lemma": model.dst_node.lemma.lemma,
                "label": model.dst_node.label.label
            },
            "line": {
                "id": model.line_id,
                "english": model.line.text,
                "sanskrit": model.line.analyses[0].parsed[0]['Sanskrit']
            },
            "annotator": {
                "id": model.annotator_id,
                "username": model.annotator.username
            },
            "is_deleted": model.is_deleted
        }

    if isinstance(model, Action):
        return {
            "id": model.id,
            "action_label": {
                "id": model.label_id,
                "label": model.label.label
            },
            "actor_label": {
                "id": model.actor_label_id,
                "label": model.actor_label.label
            },
            "actor": model.actor_lemma.lemma,
            "line": {
                "id": model.line_id,
                "english": model.line.text,
                "sanskrit": model.line.analyses[0].parsed[0]['Sanskrit']
            },
            "annotator": {
                "id": model.annotator_id,
                "username": model.annotator.username
            },
            "is_deleted": model.is_deleted
        }

###############################################################################


def search_model(
    model,
    offset: int = 0,
    limit: int = 30,
    **property_arguments
):
    """Search generic SQLAlchemy models"""
    conditions = []
    for property_name, property_value in property_arguments.items():
        if hasattr(model, property_name):
            attribute = getattr(model, property_name)
            if isinstance(attribute.property, ColumnProperty):
                if attribute.type.python_type is str:
                    conditions.append(attribute.ilike(property_value))
                else:
                    conditions.append(attribute == property_value)
            elif isinstance(attribute.property, RelationshipProperty):
                LOGGER.info(f"'{property_name}' is a 'RelationshipProperty'.")

    return model.query.filter(*conditions).offset(offset).limit(limit)


###############################################################################


def search_node(
    label: str = None,
    lemma: str = None,
    line_id: str = None,
    annotator: str = None,
    is_deleted: bool = False,
    offset: int = 0,
    limit: int = 30,
    convert_to_dict: bool = True
) -> list:
    """Search node annotations"""
    filters = []
    if label is not None:
        filters.append(Node.label.has(NodeLabel.label.ilike(label)))
    if lemma is not None:
        filters.append(Node.lemma.has(Lexicon.lemma.ilike(lemma)))
    if line_id is not None:
        filters.append(Node.line_id.ilike(line_id))
    if annotator is not None:
        filters.append(Node.annotator.has(User.username.ilike(annotator)))
    if is_deleted is not None:
        filters.append(Node.is_deleted == is_deleted)

    node_query = Node.query.filter(*filters)

    return [
        annotation_to_dict(n) if convert_to_dict else n
        for n in node_query.offset(offset).limit(limit)
    ]


def search_relation(
    src_lemma: str = None,
    label: str = None,
    detail: str = None,
    dst_lemma: str = None,
    line_id: str = None,
    annotator: str = None,
    is_deleted: bool = False,
    offset: int = 0,
    limit: int = 30,
    convert_to_dict: bool = True
) -> list:
    """Search relation annotations"""
    filters = []
    if src_lemma is not None:
        filters.append(
            Relation.src_node.lemma.has(
                Lexicon.lemma.ilike(src_lemma)
            )
        )
    if label is not None:
        filters.append(Relation.label.has(RelationLabel.label.ilike(label)))
    if detail is not None:
        filters.append(Relation.detail.ilike(detail))
    if dst_lemma is not None:
        filters.append(
            Relation.dst_node.lemma.has(
                Lexicon.lemma.ilike(dst_lemma)
            )
        )
    if line_id is not None:
        filters.append(Relation.line_id.ilike(line_id))
    if annotator is not None:
        filters.append(Relation.annotator.has(User.username.ilike(annotator)))
    if is_deleted is not None:
        filters.append(Relation.is_deleted == is_deleted)

    relation_query = Relation.query.filter(*filters)
    return [
        annotation_to_dict(r) if convert_to_dict else r
        for r in relation_query.offset(offset).limit(limit)
    ]


# TODO: Add search_action() in a similar manner

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
        If the user has `PERMISSION_ANNOTATE` permissions,
        annotations will be fetched

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
    # fetch_actions = False
    if user.has_permission(PERMISSION_ANNOTATE):
        annotator_ids = [user.id]
        fetch_nodes = True
        fetch_relations = True
        # fetch_actions = True
    if user.has_permission(PERMISSION_CURATE) or user.has_role(ROLE_ADMIN):
        annotator_ids = None
        fetch_nodes = True
        fetch_relations = True
        # fetch_actions = True
    return get_line_data(
        line_ids,
        annotator_ids=annotator_ids,
        fetch_nodes=fetch_nodes,
        fetch_relations=fetch_relations,
        # fetch_actions=fetch_actions
    )


def get_line_data(
    line_ids: List[int],
    annotator_ids: List[int] = None,
    fetch_nodes: bool = False,
    fetch_relations: bool = False,
    # fetch_actions: bool = False,
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
    fetch_actions : bool, optional
        Fetch action annotations
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
            # 'action': [],
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
        # action_query = Action.query.filter(
        #     Action.line_id.in_(line_ids)
        # )
    else:
        node_query = Node.query.filter(
            Node.line_id.in_(line_ids),
            Node.annotator_id.in_(annotator_ids)
        )
        relation_query = Relation.query.filter(
            Relation.line_id.in_(line_ids),
            Relation.annotator_id.in_(annotator_ids)
        )
        # action_query = Action.query.filter(
        #     Action.line_id.in_(line_ids),
        #     Action.annotator_id.in_(annotator_ids)
        # )

    if fetch_nodes:
        for node in node_query.all():
            data[node.line_id]['entity'].append({
                'id': node.id,
                'lemma': {
                    'id': node.lexicon_id,
                    'lemma': node.lemma.lemma
                },
                'label': {
                    'id': node.label_id,
                    'label': node.label.label
                },
                'annotator': {
                    'id': node.annotator_id,
                    'username': node.annotator.username
                },
                'is_deleted': node.is_deleted
            })
            data[node.line_id]['marked'] = True

    if fetch_relations:
        for relation in relation_query.all():
            data[relation.line_id]['relation'].append({
                'id': relation.id,
                'source': {
                    'id': relation.src_id,
                    'lemma': relation.src_node.lemma.lemma,
                    'label': relation.src_node.label.label
                },
                'label': {
                    'id': relation.label_id,
                    'label': relation.label.label
                },
                'detail': relation.detail,
                'target': {
                    'id': relation.dst_id,
                    'lemma': relation.dst_node.lemma.lemma,
                    'label': relation.dst_node.label.label
                },
                'annotator': {
                    'id': relation.annotator_id,
                    'username': relation.annotator.username
                },
                'is_deleted': relation.is_deleted
            })
            data[relation.line_id]['marked'] = True

    # if fetch_actions:
    #     for action in action_query.all():
    #         data[action.line_id]['action'].append({
    #             'id': action.id,
    #             'label': action.label.label,
    #             'actor_label': action.actor_label.label,
    #             'actor': action.actor_lemma.lemma,
    #             'annotator': action.annotator.username,
    #             'is_deleted': action.is_deleted
    #         })
    #         data[action.line_id]['marked'] = True

    return data

###############################################################################


def build_graph(
    graph: PropertyGraph = None,
    line_ids: List[int] = None,
    annotator_ids: List[int] = None,
) -> Tuple[PropertyGraph, List[Dict[str, Any]]]:
    if graph is None:
        graph = PropertyGraph()

    errors = []

    node_conditions = [Node.is_deleted.is_(False)]
    relation_conditions = [Relation.is_deleted.is_(False)]
    if line_ids is not None:
        node_conditions.append(Node.line_id.in_(line_ids))
        relation_conditions.append(Relation.line_id.in_(line_ids))

    if annotator_ids is not None:
        node_conditions.append(Node.annotator_id.in_(annotator_ids))
        relation_conditions.append(Relation.annotator_id.in_(annotator_ids))

    node_query = Node.query.filter(*node_conditions)
    relation_query = Relation.query.filter(*relation_conditions)
    LOGGER.debug(node_query)
    LOGGER.debug(relation_query)
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
                f"(src_node.is_deleted: {src_node.is_deleted}, src_node.line_id = {src_node.line_id})\n"
                f"\t-[{label}]-> \n"
                f"\t(Node {dst_id}) ({dst_node.lemma.lemma}:{dst_node.label.label}) "
                f"(dst_node.is_deleted: {dst_node.is_deleted}, dst_node.line_id = {dst_node.line_id})\n\n"
            )
            error = {
                "relation.id": relationship.id,
                "relation.line_id": relationship.line_id,
                "relation.src_id": src_id,
                "relation.src_node.line_id": src_node.line_id,
                "relation.src_node.lemma.lemma": src_node.lemma.lemma,
                "relation.src_node.label.label": src_node.label.label,
                "relation.src_node.ist_deleted": src_node.is_deleted,
                "relation.label.label": label,
                "relation.dst_id": dst_id,
                "relation.dst_node.line_id": dst_node.line_id,
                "relation.dst_node.lemma.lemma": dst_node.lemma.lemma,
                "relation.dst_node.label.label": dst_node.label.label,
                "relation.dst_node.ist_deleted": dst_node.is_deleted,
            }
            errors.append(error)
            continue

        graph.add_edge(src_id, label, dst_id, properties=properties)

    return graph, errors



###############################################################################

def get_progress(
    chapter_ids: List[int] = None,
    annotator_ids: List[int] = None,
) -> dict:
    """Get Annotation Progress

    Parameters
    ----------
    chapter_ids : List[int], optional
        List of chaper IDs
    annotator_ids : List[int], optional
        List of user IDs of annotators

    Returns
    -------
    dict
    """

    filters = []
    if chapter_ids:
        filters.append(Chapter.id.in_(chapter_ids))
    if annotator_ids:
        filters.append(User.id.in_(annotator_ids))

    verse_annotation_query = (
        Relation.query.join(Line).join(Verse).join(Chapter)
        .filter(*filters)
        .with_entities(
            Chapter.id.label("chapter_id"),
            Chapter.name.label("chapter_name"),
            Verse.id.label("verse_id"),
            func.MIN(func.DATE(Relation.updated_at)).label("start_date"),
            func.MAX(func.DATE(Relation.updated_at)).label("end_date"),
        )
        .group_by(Verse.id)
    )
    verse_annotation_log = verse_annotation_query.all()
    va_subquery = verse_annotation_query.subquery("verse_annotation")

    chapter_annotation_query = (
        db.session.query(va_subquery)
        .with_entities(
            va_subquery.c.chapter_id,
            va_subquery.c.chapter_name,
            func.MIN(va_subquery.c.start_date),
            func.MAX(va_subquery.c.start_date),
            func.MIN(va_subquery.c.end_date),
            func.MAX(va_subquery.c.end_date),
        )
        .group_by(va_subquery.c.chapter_id)
        .order_by(va_subquery.c.chapter_id)
    )
    chapter_annotation_log = chapter_annotation_query.all()

    daily_verse_start_query = (
        db.session.query(va_subquery)
        .with_entities(
            va_subquery.c.chapter_id,
            va_subquery.c.chapter_name,
            va_subquery.c.start_date,
            func.COUNT(va_subquery.c.verse_id).label("verse_count")
        )
        .group_by(va_subquery.c.start_date)
        .order_by(va_subquery.c.chapter_id, va_subquery.c.start_date)
    )
    daily_verse_start_progress = daily_verse_start_query.all()

    daily_verse_end_query = (
        db.session.query(va_subquery)
        .with_entities(
            va_subquery.c.chapter_id,
            va_subquery.c.chapter_name,
            va_subquery.c.end_date,
            func.COUNT(va_subquery.c.verse_id).label("verse_count")
        )
        .group_by(va_subquery.c.end_date)
        .order_by(va_subquery.c.chapter_id, va_subquery.c.end_date)
    )
    daily_verse_end_progress = daily_verse_end_query.all()

    return {
        "verse_annotation_log": verse_annotation_log,
        "chapter_annotation_log": chapter_annotation_log,
        "daily_verse_start_progress": daily_verse_start_progress,
        "daily_verse_end_progress": daily_verse_end_progress,
    }
