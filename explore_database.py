#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Explore Database
"""

###############################################################################

import re
from datetime import datetime

from flask import Flask
from sqlalchemy.orm import class_mapper

# Local
from models_sqla import db
from models_sqla import User, Role
from models_sqla import Corpus, Chapter, Verse, Line, Analysis
from models_sqla import Lexicon, NodeLabel, RelationLabel, Node, Relation

from settings import app

###############################################################################

webapp = Flask(__name__)
webapp.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
webapp.config['SQLALCHEMY_DATABASE_URI'] = app.sqla['database_uri']
webapp.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_pre_ping": True,
}
db.init_app(webapp)
webapp.app_context().push()

###############################################################################

MODELS = {}

for model in [User, Role, Corpus, Chapter, Verse, Line, Analysis,
              Lexicon, NodeLabel, RelationLabel, Node, Relation]:
    name = re.sub(r'(?<!^)(?=[A-Z])', '_', model.__name__).lower()
    MODELS[name] = model

###############################################################################


def model_to_dict(
    obj,
    max_depth: int = 1,
    visited_children: set = None,
    back_relationships: set = None,
):
    """SQLAlchmey objects as python `dict`

    Parameters
    ----------
    obj : SQLAlchemy model object
        Similar to an instance returned by declarative_base()
    max_depth : int, optional
        Maximum depth for recursion on relationships.
        The default is 1.
    visited_children : set, optional
        Set of children already visited.
        The default is None.
        Primary use of this attribute is for recursive calls, and a user
        usually does not explicitly set this.
    back_relationships : set, optional
        Set of back relationships already explored.
        The default is None.
        Primary use of this attribute is for recursive calls, and a user
        usually does not explicitly set this.

    Returns
    -------
    dict
        Python `dict` representation of the SQLAlchemy object
    """
    if visited_children is None:
        visited_children = set()
    if back_relationships is None:
        back_relationships = set()

    mapper = class_mapper(obj.__class__)
    columns = [column.key for column in mapper.columns]
    get_key_value = (
        lambda c: (c, getattr(obj, c).isoformat())
        if isinstance(getattr(obj, c), datetime) else
        (c, getattr(obj, c))
    )
    data = dict(map(get_key_value, columns))

    if max_depth > 0:
        for name, relation in mapper.relationships.items():
            if name in back_relationships:
                continue

            if relation.backref:
                back_relationships.add(name)

            relationship_children = getattr(obj, name)
            if relationship_children is not None:
                if relation.uselist:
                    children = []
                    for child in (
                        c
                        for c in relationship_children
                        if c not in visited_children
                    ):
                        visited_children.add(child)
                        children.append(model_to_dict(
                            child,
                            max_depth=max_depth-1,
                            visited_children=visited_children,
                            back_relationships=back_relationships
                        ))
                    data[name] = children
                else:
                    data[name] = model_to_dict(
                        relationship_children,
                        max_depth=max_depth-1,
                        visited_children=visited_children,
                        back_relationships=back_relationships
                    )

    return data

###############################################################################


def define_getter(model_name: str):
    def model_getter(model_id, as_dict=False, max_depth=1):
        f'Get {model_name}'
        result = MODELS.get(model_name).query.get(model_id)
        if as_dict:
            return model_to_dict(result, max_depth=max_depth)
        return result
    return model_getter


globals().update({
    f'get_{model_name}': define_getter(model_name) for model_name in MODELS
})


###############################################################################


def to_dict(model):
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


def search_node(
    label: str = "%",
    lemma: str = "%",
    line_id: str = "%",
    annotator: str = "%",
    offset: int = 0,
    limit: int = 30
) -> list:
    """Search node annotations"""
    node_query = Node.query.filter(
        Node.label.has(NodeLabel.label.ilike(label)),
        Node.lemma.has(Lexicon.lemma.ilike(lemma)),
        Node.line.has(Line.id.ilike(line_id)),
        Node.annotator.has(User.username.ilike(annotator))
    )
    return [to_dict(n) for n in node_query.offset(offset).limit(limit)]


def search_relation(
    src_lemma: str = "%",
    label: str = "%",
    detail: str = "%",
    dst_lemma: str = "%",
    line_id: str = "%",
    annotator: str = "%",
    offset: int = 0,
    limit: int = 30,
) -> list:
    """Search relation annotations"""
    relation_query = Relation.query.filter(
        Relation.src_lemma.has(Lexicon.lemma.ilike(src_lemma)),
        Relation.label.has(RelationLabel.label.ilike(label)),
        Relation.dst_lemma.has(Lexicon.lemma.ilike(dst_lemma)),
        Relation.detail.ilike(detail),
        Relation.line.has(Line.id.ilike(line_id)),
        Relation.annotator.has(User.username.ilike(annotator))
    )
    return [to_dict(n) for n in relation_query.offset(offset).limit(limit)]
