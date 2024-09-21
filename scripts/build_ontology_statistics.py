#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build Ontology Statistics

Created on Sat Sep 14 11:47:12 2024

@author: Hrishikesh Terdalkar
"""

###############################################################################

import json
from pathlib import Path
from collections import defaultdict, Counter

from flask import Flask
from flask_security import Security

# Local
from models_sqla import CustomLoginForm
from models_sqla import db, user_datastore
from models_sqla import User, Chapter, NodeLabel, RelationLabel, Node, Relation

from settings import app

###############################################################################

webapp = Flask(__name__)
webapp.config['SECRET_KEY'] = app.secret_key
webapp.config['SECURITY_PASSWORD_SALT'] = app.security_password_salt
webapp.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
webapp.config['SQLALCHEMY_DATABASE_URI'] = app.sqla['database_uri']
webapp.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_pre_ping": True,
}
db.init_app(webapp)
security = Security(webapp, user_datastore, login_form=CustomLoginForm)
webapp.app_context().push()

###############################################################################

PROJECT_DIR = Path(__file__).parent.parent
DATA_DIR = PROJECT_DIR / "data"

###############################################################################


def get_ontology_statistics():
    stats = {
        "chapter_node": defaultdict(Counter),
        "node_chapter": defaultdict(Counter),
        "chapter_relation": defaultdict(Counter),
        "relation_chapter": defaultdict(Counter),
        "relation_node": defaultdict(Counter),
        "node_relation": defaultdict(Counter),
        "relation_source_node": defaultdict(Counter),
        "source_node_relation": defaultdict(Counter),
        "relation_destination_node": defaultdict(Counter),
        "destination_node_relation": defaultdict(Counter),
    }

    for node in Node.query.filter(
        Node.is_deleted == False
    ):
        chapter_name = node.line.verse.chapter.name
        node_label = node.label.label
        stats["chapter_node"]["total"][node_label] += 1
        stats["chapter_node"][chapter_name][node_label] += 1
        stats["node_chapter"][node_label][chapter_name] += 1

    for relation in Relation.query.filter(
        Relation.is_deleted == False
    ):
        chapter_name = relation.line.verse.chapter.name
        relation_label = relation.label.label
        src_label = relation.src_node.label.label
        dst_label = relation.dst_node.label.label

        stats["chapter_relation"]["total"][relation_label] += 1
        stats["chapter_relation"][chapter_name][relation_label] += 1
        stats["relation_chapter"][relation_label][chapter_name] += 1

        stats["relation_node"][relation_label][src_label] += 1
        stats["relation_node"][relation_label][dst_label] += 1
        stats["relation_source_node"][relation_label][src_label] += 1
        stats["relation_destination_node"][relation_label][dst_label] += 1

        stats["node_relation"][src_label][relation_label] += 1
        stats["node_relation"][dst_label][relation_label] += 1
        stats["source_node_relation"][src_label][relation_label] += 1
        stats["destination_node_relation"][dst_label][relation_label] += 1


    chapter_stats = {}
    node_label_stats = {}
    relation_label_stats = {}

    for chapter in Chapter.query.all():
        chapter_name = chapter.name
        chapter_stats[chapter_name] = {
            "node_count": stats["chapter_node"][chapter_name].total(),
            "relation_count": stats["chapter_relation"][chapter_name].total(),
            "nodes": stats["chapter_node"][chapter_name].most_common(),
            "relations": stats["chapter_relation"][chapter_name].most_common(),
        }

    for node in Node.query.filter(Node.is_deleted == False):
        node_label = node.label.label
        node_label_stats[node_label] = {
            "node_count": stats["node_chapter"][node_label].total(),
            "chapters": stats["node_chapter"][node_label].most_common(),
            "relation_count": stats["node_relation"][node_label].total(),
            "relation_count_as_source": stats["source_node_relation"][node_label].total(),
            "relation_count_as_destination": stats["destination_node_relation"][node_label].total(),
            "relations": stats["node_relation"][node_label].most_common(),
            "relations_as_source": stats["source_node_relation"][node_label].most_common(),
            "relations_as_destination": stats["destination_node_relation"][node_label].most_common(),
        }

    for relation in Relation.query.filter(Relation.is_deleted == False):
        relation_label = relation.label.label
        src_label = relation.src_node.label.label
        dst_label = relation.dst_node.label.label
        relation_label_stats[relation_label] = {
            "relation_count": stats["relation_chapter"][relation_label].total(),
            "chapters": stats["relation_chapter"][relation_label].most_common(),
            "node_count": stats["relation_node"][relation_label].total(),
            # "source_node_count": stats["relation_source_node"][relation_label].total(),            # obsolete; equal to node_count/2
            # "destination_node_count": stats["relation_destination_node"][relation_label].total(),  # obsolete; equal to node_count/2
            "nodes": stats["relation_node"][relation_label].most_common(),
            "source_nodes": stats["relation_source_node"][relation_label].most_common(),
            "destination_nodes": stats["relation_destination_node"][relation_label].most_common(),
        }

    return {
        "stats": stats,
        "chapter": chapter_stats,
        "node_label": node_label_stats,
        "relation_label": relation_label_stats,
    }

###############################################################################

STATS = get_ontology_statistics()

with open(DATA_DIR / "chapter_stats.json", "w") as f:
    json.dump(STATS["chapter"], f, ensure_ascii=False, indent=2)

with open(DATA_DIR / "node_label_stats.json", "w") as f:
    json.dump(STATS["node_label"], f, ensure_ascii=False, indent=2)

with open(DATA_DIR / "relation_label_stats.json", "w") as f:
    json.dump(STATS["relation_label"], f, ensure_ascii=False, indent=2)

###############################################################################