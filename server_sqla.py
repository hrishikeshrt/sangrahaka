#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Annotation Server

Deployment
----------

1. Using Flask-Run

```
$ export FLASK_APP="server:webapp"
$ flask run
```

2. Using gunicorn

```
$ gunicorn -b host:port server:webapp
```

3. Direct (dev only)

```
$ python server.py
```
"""

__author__ = "Hrishikesh Terdalkar"
__copyright__ = "Copyright (C) 2020-2021 Hrishikesh Terdalkar"
__version__ = "1.0"

###############################################################################

import os
import re
import glob
import json
import logging
import datetime

import git
import requests
from flask import (Flask, render_template, redirect, jsonify, url_for,
                   request, flash, session, Response, abort)
from flask_security import (Security, auth_required, permissions_required,
                            hash_password, current_user, user_registered,
                            user_authenticated)
from flask_security.utils import uia_email_mapper
from sqlalchemy import or_, and_

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from flask_babelex import Babel
from flask_wtf import CSRFProtect
from flask_mail import Mail
from flask_migrate import Migrate

from indic_transliteration.sanscript import transliterate

from models_sqla import (db, user_datastore,
                         CustomLoginForm, CustomRegisterForm,
                         Corpus, Chapter, Verse, Line, Analysis,
                         Lexicon,
                         NodeLabel, RelationLabel, Node, Relation,
                         ActionLabel, ActorLabel, Action)
from settings import app
from utils.reverseproxied import ReverseProxied
from utils.database import get_line_data, get_chapter_data
from utils.graph import Graph
from utils.property_graph import PropertyGraph
from utils.query import load_queries
from utils.cypher_utils import graph_to_cypher

###############################################################################

logging.basicConfig(format='[%(asctime)s] %(name)s %(levelname)s: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.INFO,
                    handlers=[logging.FileHandler(app.log_file),
                              logging.StreamHandler()])

###############################################################################

QUERIES = load_queries(app.query_file)

###############################################################################
# UIA Mapper


def uia_username_mapper(identity):
    pattern = r'^(?!_$)(?![0-9_.])(?!.*[_.]{2})[a-zA-Z0-9_.]+(?<![.])$'
    return identity if re.match(pattern, identity) else None


###############################################################################
# Flask Application

webapp = Flask(app.name, static_folder='static')
webapp.config['DEBUG'] = app.debug
webapp.wsgi_app = ReverseProxied(webapp.wsgi_app)


webapp.config['SECRET_KEY'] = app.secret_key
webapp.config['SECURITY_PASSWORD_SALT'] = app.security_password_salt
webapp.config['JSON_AS_ASCII'] = False
webapp.config['JSON_SORT_KEYS'] = False

# SQLAlchemy Config
webapp.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
webapp.config['SQLALCHEMY_DATABASE_URI'] = app.sqla['database_uri']
webapp.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_pre_ping": True,
}

# CSRF Token Expiry
webapp.config['WTF_CSRF_TIME_LIMIT'] = None

###############################################################################
# Flask-Security-Too Configuration

webapp.config['SECURITY_REGISTERABLE'] = True
webapp.config['SECURITY_SEND_REGISTER_EMAIL'] = app.smtp_enabled
webapp.config['SECURITY_USER_IDENTITY_ATTRIBUTES'] = [
    {'email': {'mapper': uia_email_mapper}},
    {'username': {'mapper': uia_username_mapper}}
]

webapp.config['SECURITY_RECOVERABLE'] = app.smtp_enabled
webapp.config['SECURITY_CHANGEABLE'] = True
webapp.config['SECURITY_TRACKABLE'] = True
# NOTE: SECURITY_USERNAME_ still buggy in Flask-Security-Too
# Exercise caution before enabling the following two options
# webapp.config['SECURITY_USERNAME_ENABLE'] = True
# webapp.config['SECURITY_USERNAME_REQUIRED'] = True
webapp.config['SECURITY_POST_LOGIN_VIEW'] = 'show_home'
webapp.config['SECURITY_POST_LOGOUT_VIEW'] = 'show_home'

###############################################################################
# Mail Configuration

if app.smtp_enabled:
    webapp.config['MAIL_SERVER'] = app.smtp['server']
    webapp.config['MAIL_USERNAME'] = app.smtp['username']
    webapp.config['MAIL_DEFAULT_SENDER'] = (app.smtp['name'],
                                            app.smtp['username'])
    webapp.config['MAIL_PASSWORD'] = app.smtp['password']
    webapp.config['MAIL_USE_SSL'] = app.smtp['use_ssl']
    webapp.config['MAIL_USE_TLS'] = app.smtp['use_tls']
    webapp.config['MAIL_PORT'] = app.smtp['port']
    webapp.config['MAIL_DEBUG'] = True

###############################################################################
# Initialize standard Flask extensions

db.init_app(webapp)

csrf = CSRFProtect(webapp)
security = Security(webapp, user_datastore,
                    login_form=CustomLoginForm,
                    register_form=CustomRegisterForm)
mail = Mail(webapp)
migrate = Migrate(webapp, db)
babel = Babel(webapp)

limiter = Limiter(
    webapp,
    key_func=get_remote_address,
    default_limits=["1800 per hour"]
)

###############################################################################
# Neo4j Graph

try:
    GRAPH = Graph(
        server=app.neo4j['server'],
        username=app.neo4j['username'],
        password=app.neo4j['password']
    )
except Exception as e:
    GRAPH = None
    logging.error(f"Graph Database connection failed. ({e})")

###############################################################################
# Database Utlity Functions


def get_lexicon(lemma: str) -> int:
    lexicon = Lexicon.query.filter(Lexicon.lemma == lemma).one_or_none()
    if lexicon:
        return lexicon.id


def create_lexicon(lemma: str) -> int:
    transliterations = [
        f"##{transliterate(lemma, 'devanagari', scheme)}"
        if not lemma.startswith(app.config['unnamed_prefix']) else ''
        for scheme in app.config['schemes']
    ]
    transliteration = ''.join(transliterations)
    lexicon = Lexicon()
    lexicon.lemma = lemma
    if transliteration:
        lexicon.transliteration = transliteration
    db.session.add(lexicon)
    db.session.flush()
    return lexicon.id


def get_or_create_lexicon(lemma: str) -> int:
    return get_lexicon(lemma) or create_lexicon(lemma)

###############################################################################
# Hooks


@webapp.before_first_request
def init_database():
    """Initiate database and create admin user"""
    db.create_all()
    role_definitions = sorted(app.role_definitions,
                              key=lambda x: x['level'],
                              reverse=True)
    for role_definition in role_definitions:
        name = role_definition['name']
        description = role_definition['description']
        permissions = role_definition['permissions']
        level = role_definition['level']
        user_datastore.find_or_create_role(
            name=name,
            description=description,
            level=level,
            permissions=permissions
        )

    if not user_datastore.find_user(username=app.admin['username']):
        user_datastore.create_user(
            username=app.admin['username'],
            email=app.admin['email'],
            password=hash_password(app.admin['password']),
            roles=['owner', 'admin', 'curator',
                   'annotator', 'querier', 'member']
        )
    db.session.commit()


@user_registered.connect_via(webapp)
def assign_default_roles(sender, user, **extra):
    """Assign member role to users after successful registration"""
    user_datastore.add_role_to_user(user, 'member')
    db.session.commit()


@user_authenticated.connect_via(webapp)
def _after_authentication_hook(sender, user, **extra):
    pass

###############################################################################
# Global Context


@webapp.context_processor
def inject_global_constants():
    theme_files = glob.glob(
        os.path.join(app.dir, 'static', 'themes', 'css', 'bootstrap.*.min.css')
    )
    theme_js_files = glob.glob(
        os.path.join(app.dir, 'static', 'themes', 'js', 'bootstrap.*.min.js')
    )
    themes = ['default'] + sorted([os.path.basename(theme).split('.')[1]
                                   for theme in theme_files])
    themes_js = sorted([os.path.basename(theme).split('.')[1]
                        for theme in theme_js_files])

    CONSTANTS = {
        'node_labels': NodeLabel.query.filter(
            NodeLabel.is_deleted == False  # noqa # '== False' is required
        ).with_entities(
            NodeLabel.id, NodeLabel.label, NodeLabel.description
        ).order_by(NodeLabel.label).all(),
        'relation_labels': RelationLabel.query.filter(
            RelationLabel.is_deleted == False  # noqa # '== False' is required
        ).with_entities(
            RelationLabel.id, RelationLabel.label, RelationLabel.description
        ).order_by(RelationLabel.label).all(),
        'action_labels': ActionLabel.query.filter(
            ActionLabel.is_deleted == False  # noqa # '== False' is required
        ).with_entities(
            ActionLabel.id, ActionLabel.label, ActionLabel.description
        ).order_by(ActionLabel.label).all(),
        'actor_labels': ActorLabel.query.filter(
            ActorLabel.is_deleted == False  # noqa # '== False' is required
        ).with_entities(
            ActorLabel.id, ActorLabel.label, ActorLabel.description
        ).all()
    }
    return {
        'title': app.title,
        'now': datetime.datetime.utcnow(),
        'constants': CONSTANTS,
        'themes': themes,
        'themes_js': themes_js,
        'config': app.config
    }

###############################################################################
# Views


@webapp.route("/admin", strict_slashes=False)
@auth_required()
@permissions_required('view_acp')
def show_admin():
    data = {}
    data['title'] = 'Admin'

    user_level = max([role.level for role in current_user.roles])
    annotator_role = user_datastore.find_role('annotator')

    user_model = user_datastore.user_model
    role_model = user_datastore.role_model
    user_query = user_model.query
    role_query = role_model.query

    data['users'] = [user.username for user in user_query.all()]
    data['annotators'] = [user.username for user in user_query.all()
                          if annotator_role in user.roles]
    data['roles'] = [
        role.name
        for role in role_query.order_by(role_model.level).all()
        if role.level < user_level
    ]

    data['corpus_list'] = [
        {'id': corpus.id, 'name': corpus.name, 'chapters': [
            {'id': chapter.id, 'name': chapter.name}
            for chapter in corpus.chapters.all()
        ]}
        for corpus in Corpus.query.all()
    ]

    admin_result = session.get('admin_result', None)
    if admin_result:
        data['result'] = admin_result
        del session['admin_result']
    return render_template('admin.html', data=data)


@webapp.route("/settings", strict_slashes=False)
@auth_required()
@permissions_required('view_ucp')
def show_settings():
    data = {}
    data['title'] = 'Settings'
    return render_template('settings.html', data=data)


@webapp.route("/corpus", strict_slashes=False)
@webapp.route("/corpus/<string:chapter_id>", strict_slashes=False)
@auth_required()
@permissions_required('view_corpus')
def show_corpus(chapter_id=None):
    if chapter_id is None:
        flash("Please select a corpus to view.")
        return redirect(url_for('show_home'))

    data = {}
    data['title'] = 'Corpus'
    data['chapter_id'] = chapter_id
    return render_template('corpus.html', data=data)


@webapp.route("/query", strict_slashes=False)
@auth_required()
@permissions_required('query')
def show_query():
    data = {}
    data['title'] = 'Query'
    query_groups = {}
    for q in QUERIES:
        if q.gid not in query_groups:
            query_groups[q.gid] = {
                'groups': q.groups,
                'queries': []
            }

        query_groups[q.gid]['queries'].append(q.to_dict(
            prefix=app.config['var_prefix'],
            suffix=app.config['var_prefix'],
            debug=False
        ))

    data['query_groups'] = list(query_groups.values())
    data['initial_query'] = (
        'MATCH (node_1)-[edge]->(node_2) RETURN *'
    )
    data['initial_output'] = ['node_1', 'edge', 'node_2']
    return render_template('query.html', data=data)


@webapp.route("/query/builder", strict_slashes=False)
def show_builder():
    data = {'title': 'Graph Query Builder'}
    data['templates'] = app.config['graph_templates']
    return render_template('builder.html', data=data)


@webapp.route("/terms", strict_slashes=False)
def show_terms():
    data = {'title': 'Terms of Use'}
    return render_template('terms.html', data=data)


@webapp.route("/contact", strict_slashes=False)
def show_contact():
    data = {'title': 'Contact Us'}
    contacts = []
    replacement = {'@': 'at', '.': 'dot'}
    for _contact in app.contacts:
        contact = _contact.copy()
        email = (
            _contact['email'].replace('.', ' . ').replace('@', ' @ ').split()
        )
        contact['email'] = []

        for email_part in email:
            contact['email'].append({
                'text': replacement.get(email_part, email_part),
                'is_text': replacement.get(email_part) is None
            })
        contacts.append(contact)
    data['contacts'] = contacts
    return render_template('contact.html', data=data)


@webapp.route("/about", strict_slashes=False)
def show_about():
    data = {
        'title': 'About',
        'about': app.about
    }
    return render_template('about.html', data=data)


@webapp.route("/<page>", strict_slashes=False)
def show_custom_page(page):
    if page in app.custom_pages:
        page_data = app.custom_pages[page]
        data = {
            'title': page_data['title'],
            'card_header': page_data['card_header'],
            'card_body': page_data['card_body']
        }
        return render_template('pages.html', data=data)
    else:
        abort(404)


@webapp.route("/", strict_slashes=False)
@auth_required()
def show_home():
    data = {}
    data['title'] = 'Home'
    data['corpus_list'] = [
        {'id': corpus.id, 'name': corpus.name, 'chapters': [
            {'id': chapter.id, 'name': chapter.name}
            for chapter in corpus.chapters.all()
        ]}
        for corpus in Corpus.query.all()
    ]

    return render_template('home.html', data=data)

###############################################################################
# Action Endpoints


@webapp.route("/api", methods=["POST"], strict_slashes=False)
@auth_required()
def api():
    api_response = {}
    api_response['success'] = False
    try:
        action = request.form['action']
    except KeyError:
        api_response['message'] = "Insufficient parameters in request."
        return jsonify(api_response)

    # ----------------------------------------------------------------------- #
    # Action Authorization

    role_actions = {
        'admin': [],
        'annotator': ['update_entity', 'update_relation', 'update_action'],
        'curator': [],
        'querier': ['query', 'graph_query']
    }
    valid_actions = [
        action for actions in role_actions.values() for action in actions
    ]

    if action not in valid_actions:
        api_response['message'] = "Invalid action."
        return jsonify(api_response)

    for role, actions in role_actions.items():
        if action in actions and not current_user.has_role(role):
            api_response['message'] = "Insufficient permissions."
            return jsonify(api_response)

    # ----------------------------------------------------------------------- #

    api_response['success'] = True

    # ----------------------------------------------------------------------- #

    if action in ['update_entity', 'update_relation', 'update_action']:
        line_id = request.form['line_id']
        annotator_id = current_user.id

        objects_to_update = []

        # ------------------------------------------------------------------- #

        if action == 'update_entity':
            entities_add = request.form['entity_add'].split('##')
            entities_del = request.form['entity_delete'].split('##')
            for entity in entities_add + entities_del:
                if '$' not in entity:
                    continue
                parts = entity.split('$')
                _lexicon_id = get_or_create_lexicon(parts[0])

                label_query = NodeLabel.query.filter(
                    NodeLabel.label == parts[1]
                )
                _label = label_query.first()
                if _label is None:
                    api_response['success'] = False
                    api_response['message'] = 'Invalid node type.'
                    return jsonify(api_response)
                _label_id = _label.id

                node_query = Node.query.filter(and_(
                    Node.line_id == line_id,
                    Node.annotator_id == annotator_id,
                    Node.lexicon_id == _lexicon_id,
                    Node.label_id == _label_id
                ))

                # Curator can edit annotations by others
                # i.e. (no annotator_id check)
                if current_user.has_permission('curate'):
                    node_query = Node.query.filter(and_(
                        Node.line_id == line_id,
                        Node.lexicon_id == _lexicon_id,
                        Node.label_id == _label_id
                    ))
                n = node_query.first()

                if n is None:
                    if entity in entities_add:
                        n = Node()
                        n.line_id = line_id
                        n.annotator_id = annotator_id
                        n.lexicon_id = _lexicon_id
                        n.label_id = _label_id
                        objects_to_update.append(n)
                else:
                    n.is_deleted = (entity in entities_del)
                    objects_to_update.append(n)

        # ------------------------------------------------------------------- #

        if action == 'update_relation':
            relations_add = request.form['relation_add'].split('##')
            relations_del = request.form['relation_delete'].split('##')
            for relation in relations_add + relations_del:
                if '$' not in relation:
                    continue
                parts = relation.split('$')
                _src_id = get_lexicon(parts[0])
                _detail = parts[3] if parts[3].strip() else None
                _dst_id = get_lexicon(parts[2])

                if _src_id is None or _dst_id is None:
                    api_response['success'] = False
                    api_response['message'] = (
                        'Source or Destination entity does not exist.'
                    )
                    return jsonify(api_response)
                label_query = RelationLabel.query.filter(
                    RelationLabel.label == parts[1]
                )
                _label = label_query.first()
                if _label is None:
                    api_response['success'] = False
                    api_response['message'] = 'Invalid relation type.'
                    return jsonify(api_response)
                _label_id = _label.id

                relation_query = Relation.query.filter(and_(
                    Relation.line_id == line_id,
                    Relation.annotator_id == annotator_id,
                    Relation.src_id == _src_id,
                    Relation.dst_id == _dst_id,
                    Relation.label_id == _label_id,
                    Relation.detail == _detail
                ))

                # Curator can edit annotations by others
                # i.e. (no annotator_id check)
                if current_user.has_permission('curate'):
                    relation_query = Relation.query.filter(and_(
                        Relation.line_id == line_id,
                        Relation.src_id == _src_id,
                        Relation.dst_id == _dst_id,
                        Relation.label_id == _label_id,
                        Relation.detail == _detail
                    ))
                r = relation_query.first()

                if r is None:
                    if relation in relations_add:
                        r = Relation()
                        r.line_id = line_id
                        r.annotator_id = annotator_id
                        r.src_id = _src_id
                        r.dst_id = _dst_id
                        r.label_id = _label_id
                        r.detail = _detail
                        objects_to_update.append(r)
                else:
                    r.is_deleted = (relation in relations_del)
                    objects_to_update.append(r)

        # ------------------------------------------------------------------- #

        if action == 'update_action':
            actions_add = request.form['action_add'].split('##')
            actions_del = request.form['action_delete'].split('##')
            for action in actions_add + actions_del:
                if '$' not in action:
                    continue
                parts = action.split('$')
                _actor_id = get_lexicon(parts[2])

                if _actor_id is None:
                    api_response['success'] = False
                    api_response['message'] = (
                        'Actor entity does not exist.'
                    )
                    return jsonify(api_response)

                label_query = ActionLabel.query.filter(
                    ActionLabel.label == parts[0]
                )
                _label = label_query.first()
                if _label is None:
                    api_response['success'] = False
                    api_response['message'] = 'Invalid action type.'
                    return jsonify(api_response)

                actor_label_query = ActorLabel.query.filter(
                    ActorLabel.label == parts[1]
                )
                _actor_label = actor_label_query.first()
                if _actor_label is None:
                    api_response['success'] = False
                    api_response['message'] = 'Invalid actor type.'
                    return jsonify(api_response)

                _label_id = _label.id
                _actor_label_id = _actor_label.id

                action_query = Action.query.filter(and_(
                    Action.line_id == line_id,
                    Action.label_id == _label_id,
                    Action.annotator_id == annotator_id,
                    Action.actor_label_id == _actor_label_id,
                    Action.actor_id == _actor_id,
                ))

                # Curator can edit annotations by others
                # i.e. (no annotator_id check)
                if current_user.has_permission('curate'):
                    action_query = Action.query.filter(and_(
                        Action.line_id == line_id,
                        Action.label_id == _label_id,
                        Action.actor_label_id == _actor_label_id,
                        Action.actor_id == _actor_id,
                    ))
                a = action_query.first()

                if a is None:
                    if action in actions_add:
                        a = Action()
                        a.line_id = line_id
                        a.annotator_id = annotator_id
                        a.label_id = _label_id
                        a.actor_id = _actor_id
                        a.actor_label_id = _actor_label_id
                        objects_to_update.append(a)
                else:
                    a.is_deleted = (action in actions_del)
                    objects_to_update.append(a)

        # ------------------------------------------------------------------- #

        try:
            if objects_to_update:
                db.session.bulk_save_objects(objects_to_update)
                db.session.commit()
                api_response['message'] = 'Successfully updated!'
            else:
                api_response['message'] = 'No changes were submitted.'
            api_response['success'] = True
        except Exception as e:
            print(e)
            print(request.form)
            api_response['success'] = False
            api_response['message'] = 'Something went wrong.'
        return jsonify(api_response)

    # ----------------------------------------------------------------------- #

    if action == 'query':
        if GRAPH is None:
            api_response['success'] = False
            api_response['message'] = 'Graph Database is not connected.'
            return jsonify(api_response)

        cypher_query = request.form['query']

        # ------------------------------------------------------------------- #
        # Naive sanitize-query
        # Move to graph.py ??

        pattern = r'[.,;*\s)(]'
        query_words = re.split(pattern, cypher_query.upper())

        # limit handling
        query_limit = app.config['query_limit']
        try:
            limit_index = query_words.index('LIMIT')
            limit = int(query_words[limit_index + 1])
            if limit > query_limit:
                limit_pattern = re.compile(f'LIMIT {limit}', re.IGNORECASE)
                cypher_query = re.sub(
                    limit_pattern, f'LIMIT {query_limit}', cypher_query
                )
                api_response['warning'] = f'LIMIT reset to {query_limit}'
                logging.warning(f"Limit exceeded. ({limit} > {query_limit}).")
        except ValueError:
            cypher_query = f'{cypher_query} LIMIT {query_limit}'

        # bad-words
        must_have = ['MATCH', 'RETURN']
        must_avoid = ['DETACH', 'DELETE', 'UPDATE', 'SET', 'MERGE']

        absent_goodwords = [w for w in must_have if w not in query_words]
        present_badwords = [w for w in must_avoid if w in query_words]

        if absent_goodwords:
            goodword = absent_goodwords[0]
            api_response['success'] = False
            api_response['message'] = f'Query must contain: {goodword}.'
            return jsonify(api_response)
        if present_badwords:
            badword = present_badwords[0]
            api_response['success'] = False
            api_response['message'] = f'Query must not contain {badword}.'
            return jsonify(api_response)

        # ------------------------------------------------------------------- #

        try:
            logging.debug(cypher_query)
            matches, nodes, edges = GRAPH.run_query(cypher_query)
            api_response['matches'] = matches
            api_response['nodes'] = nodes
            api_response['edges'] = edges
            api_response['message'] = (
                f'Query executed successfully. ({len(matches)} results)'
            )
        except Exception as e:
            api_response['success'] = False
            api_response['message'] = f'Something went wrong. ({e})'

        return jsonify(api_response)

    if action == 'graph_query':
        graph_data = json.loads(request.form['data'])
        graph = PropertyGraph()
        for node in graph_data['nodes']:
            graph.add_node(
                node_id=node['id'],
                labels=[node['label']] if node['label'] else [],
                properties=node['properties']
            )
        for edge in graph_data['edges']:
            graph.add_edge(
                src_id=edge['source'],
                label=edge['label'],
                dst_id=edge['target'],
                properties=edge['properties']
            )

        non_conditionals = {
            'lemma': ["?", ""],
            'query': [True, False, None],
        }
        cypher_query = graph_to_cypher(
            graph=graph,
            non_conditionals=non_conditionals
        )

        api_response['success'] = True
        api_response['message'] = 'Query built successfully.'
        api_response['cypher'] = cypher_query
        return jsonify(api_response)

    if action == 'custom_action':
        api_response['data'] = None
        return jsonify(api_response)


@webapp.route("/api/corpus/<int:chapter_id>", strict_slashes=False)
@auth_required()
def api_corpus(chapter_id):
    chapter = Chapter.query.get(chapter_id)
    if chapter is None:
        return jsonify({
            'title': 'Invalid Chapter ID',
            'data': []
        })

    data = get_chapter_data(chapter_id, current_user)
    response = {
        'title': f"{chapter.corpus.name} - {chapter.name}",
        'data': list(data.values())
    }
    return jsonify(response)

# --------------------------------------------------------------------------- #


@webapp.route("/api/suggest", strict_slashes=False)
@limiter.limit("60 per minute")
def suggest():
    word = request.args.get('q')

    response = []
    if all([
        word and len(word) < 3,
        not word.startswith(app.config['unnamed_prefix'])
    ]):
        return jsonify(response)

    search_query = Lexicon.query.with_entities(Lexicon.lemma).filter(or_(
        Lexicon.transliteration.like(f"%##{word}%"),
        Lexicon.lemma.startswith(word)
    )).limit(1000)
    response = [r for r, in search_query.all()]
    return jsonify(response)


###############################################################################


@webapp.route("/action", methods=["POST"], strict_slashes=False)
@auth_required()
def action():
    status = False
    try:
        action = request.form['action']
    except KeyError:
        flash("Insufficient paremeters in request.")
        return redirect(request.referrer)

    # ----------------------------------------------------------------------- #
    # Admin Actions

    role_actions = {
        'owner': [
            'application_info', 'application_update', 'application_reload'
        ],
        'admin': [
            'user_role_add', 'user_role_remove',

            # Ontology
            'node_type_add', 'node_type_remove',
            'relation_type_add', 'relation_type_remove',

            # Data
            'corpus_add', 'chapter_add',
            'annotation_download'
        ],
        'curator': [],
        'annotator': [],
        'member': ['update_settings']
    }
    valid_actions = [
        action for actions in role_actions.values() for action in actions
    ]

    if action not in valid_actions:
        flash("Invalid action.")
        return redirect(request.referrer)

    for role, actions in role_actions.items():
        if action in actions and not current_user.has_role(role):
            flash("You are not authorized to perform that action.", "danger")
            return redirect(request.referrer)

    # ----------------------------------------------------------------------- #
    # Show Application Information

    if action in [
        'application_info', 'application_update', 'application_reload'
    ] and not app.pa_enabled:
        flash("PythonAnywhere configuration incomplete or missing.")
        return redirect(request.referrer)

    if action == 'application_info':
        info_url = app.pa_api_url + app.pa_api_actions['info']
        response = requests.get(info_url, headers=app.pa_headers)
        if response.status_code == 200:
            pretty_info = json.dumps(
                json.loads(response.content.decode()),
                indent=2
            )
            session['admin_result'] = pretty_info
        else:
            print(response.content.decode())
            flash("Something went wrong.")
        return redirect(request.referrer)

    # Perform git-pull
    if action == 'application_update':
        try:
            repo = git.cmd.Git(app.dir)
            result = repo.pull()
        except Exception as e:
            result = f'Error\n{e}'
        session['admin_result'] = result

        if result == 'Already up-to-date.':
            flash("Already up-to-date.")
        elif 'Updating' in result and 'changed,' in result:
            flash("Application code has been updated.", "success")
        else:
            flash("Something went wrong.")
        return redirect(request.referrer)

    # API App Reload
    if action == 'application_reload':
        reload_url = app.pa_api_url + app.api_actions['reload']
        response = requests.post(reload_url, headers=app.pa_headers)
        if response.status_code == 200:
            flash("Application has been reloaded.", "success")
            return Response("Success")
        else:
            print(response.content.decode())
            flash("Something went wrong.")
            return Response("Failure")

    # ----------------------------------------------------------------------- #
    # Manage User Role

    if action in ['user_role_add', 'user_role_remove']:
        target_user = request.form['target_user']
        target_role = request.form['target_role']
        target_action = action.split('_')[-1]

        _user = user_datastore.find_user(username=target_user)
        _role = user_datastore.find_role(target_role)

        user_level = max([role.level for role in current_user.roles])
        target_level = max([role.level for role in _user.roles])

        valid_update = True
        if _user == current_user:
            if _role.level == user_level:
                flash("You cannot modify your highest role.")
                valid_update = False
        else:
            if user_level <= target_level:
                flash(f"You cannot modify '{target_user}'.", "danger")
                valid_update = False

        if valid_update:
            if target_action == 'add':
                status = user_datastore.add_role_to_user(_user, _role)
                message = "Added role '{}' to user '{}'."
            if target_action == 'remove':
                status = user_datastore.remove_role_from_user(_user, _role)
                message = "Removed role '{}' from user '{}'."

            if status:
                db.session.commit()
                flash(message.format(target_role, target_user), "info")
            else:
                flash("No changes were made.")

        return redirect(request.referrer)

    # ----------------------------------------------------------------------- #
    # Ontology

    if action in ['node_type_add', 'node_type_remove']:
        node_label = request.form['node_label']
        node_label_desc = request.form.get('node_label_description')
        target_action = action.split('_')[-1]

        _node_label = NodeLabel.query.filter(
            NodeLabel.label == node_label
        ).first()

        if target_action == 'add':
            message = f"Added Node label '{node_label}'."
            if _node_label is None:
                _node_label = NodeLabel()
                _node_label.label = node_label
                _node_label.description = node_label_desc
                _node_label.is_deleted = False
                status = True
                db.session.add(_node_label)
            else:
                if _node_label.is_deleted:
                    _node_label.is_deleted = False
                    status = True
                    db.session.add(_node_label)
                else:
                    message = f"Node label '{node_label}' already exists."

        if target_action == 'remove':
            message = f"Node label '{node_label}' does not exists."
            if _node_label is not None and not _node_label.is_deleted:
                nodes_with_given_label = [
                    node
                    for node in _node_label.nodes
                    if not node.is_deleted
                ]
                if nodes_with_given_label:
                    message = f"Node label '{node_label}' is being used."
                else:
                    _node_label.is_deleted = True
                    db.session.add(_node_label)
                    status = True
                    message = f"Removed node label '{node_label}'."

        if status:
            db.session.commit()
            flash(message, "info")
        else:
            flash(message)
        return redirect(request.referrer)

    if action in ['relation_type_add', 'relation_type_remove']:
        relation_label = request.form['relation_label']
        relation_label_desc = request.form.get('relation_label_description')
        target_action = action.split('_')[-1]

        _relation_label = RelationLabel.query.filter(
            RelationLabel.label == relation_label
        ).first()

        if target_action == 'add':
            message = f"Added relation label '{relation_label}'."
            if _relation_label is None:
                _relation_label = RelationLabel()
                _relation_label.label = relation_label
                _relation_label.description = relation_label_desc
                _relation_label.is_deleted = False
                status = True
                db.session.add(_relation_label)
            else:
                if _relation_label.is_deleted:
                    _relation_label.is_deleted = False
                    status = True
                    db.session.add(_relation_label)
                else:
                    message = (
                        f"Relation label '{relation_label}' already exists."
                    )

        if target_action == 'remove':
            message = f"Relation label '{relation_label}' does not exists."
            if _relation_label is not None and not _relation_label.is_deleted:
                relations_with_given_label = [
                    relation
                    for relation in _relation_label.relations
                    if not relation.is_deleted
                ]
                if relations_with_given_label:
                    message = (
                        f"Relation label '{relation_label}' is being used."
                    )
                else:
                    _relation_label.is_deleted = True
                    db.session.add(_relation_label)
                    status = True
                    message = f"Removed relation label '{relation_label}'."

        if status:
            db.session.commit()
            flash(message, "info")
        else:
            flash(message)
        return redirect(request.referrer)

    # ----------------------------------------------------------------------- #
    # Corpus Add

    if action in ['corpus_add']:
        corpus_name = request.form['corpus_name']
        corpus_description = request.form['corpus_description']
        try:
            corpus = Corpus()
            corpus.name = corpus_name
            corpus.description = corpus_description
            db.session.add(corpus)
            db.session.commit()
            flash((f"Created corpus '{corpus_name}' successfully."
                   f" (ID: {corpus.id})"), "success")
        except Exception:
            flash("Something went wrong during corpus creation.")
        return redirect(request.referrer)

    if action in ['chapter_add']:
        if 'chapter_file' not in request.files:
            flash("No file part found.")
            return redirect(request.referrer)

        corpus_id = request.form['corpus_id']
        chapter_name = request.form['chapter_name']
        chapter_description = request.form['chapter_description']
        chapter_file = request.files['chapter_file']
        chapter_filename = chapter_file.filename

        if chapter_filename == '':
            flash("No file selected.")
            return redirect(request.referrer)

        # Validity
        allowed_extensions = {'json', 'txt'}
        file_extension = chapter_filename.rsplit('.', 1)[1].lower()
        is_valid_filename = (file_extension in allowed_extensions)

        if chapter_file and is_valid_filename:
            corpus_query = Corpus.query.filter(Corpus.id == corpus_id)
            corpus = corpus_query.first()
            if corpus is None:
                flash("No corpus selected.")
                return redirect(request.referrer)

            try:
                data = json.load(chapter_file)
            except json.decoder.JSONDecodeError:
                flash("Invalid file format.")
                return redirect(request.referrer)

            # Group verses
            verses = []
            last_verse_id = None
            for _line in data:
                line_verse_id = _line.get('verse')
                if line_verse_id is None or line_verse_id != last_verse_id:
                    last_verse_id = line_verse_id
                    verses.append([])
                verses[-1].append(_line)

            # --------------------------------------------------------------- #
            # Insert Data
            try:
                chapter = Chapter()
                chapter.corpus_id = corpus.id
                chapter.name = chapter_name
                chapter.description = chapter_description

                for _verse in verses:
                    verse = Verse()
                    verse.chapter = chapter
                    for _line in _verse:
                        _analysis = _line.get('analysis', {})
                        line = Line()
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
                print(e)
                flash("An error occurred while inserting data.", "danger")
            else:
                db.session.commit()
                flash(
                    f"Chapter '{chapter_name}' added successfully.",
                    "success"
                )
            # --------------------------------------------------------------- #
        else:
            flash("Invalid file or file extension.")

        return redirect(request.referrer)

    # ----------------------------------------------------------------------- #
    # Corpus Download

    if action in ["annotation_download"]:
        usernames = request.form.getlist('annotator')
        chapters = request.form.getlist('chapter_id')
        try:
            User = user_datastore.user_model
            _chapters = set(str(chapter.id) for chapter in Chapter.query.all())
            _usernames = set(user.username for user in User.query.all())

            # Conditions for query-optimization
            all_chapters = set(chapters) == _chapters
            all_users = set(usernames) == _usernames
            logging.info(f"{all_chapters=}, {all_users=}")

            # Node and Relation Queries
            # NOTE: 'elif' is important
            if all_chapters and all_users:
                # no condition
                node_query = Node.query.filter(
                    Node.is_deleted == False  # noqa
                )
                relation_query = Relation.query.filter(
                    Relation.is_deleted == False  # noqa
                )
            elif all_users:
                # only chapter condition
                node_query = (
                    Node.query.join(Line).join(Verse).filter(
                        and_(
                            Verse.chapter_id.in_(chapters),
                            Node.is_deleted == False  # noqa
                        )
                    )
                )
                relation_query = (
                    Relation.query.join(Line).join(Verse).filter(
                        and_(
                            Verse.chapter_id.in_(chapters),
                            Relation.is_deleted == False  # noqa
                        )
                    )
                )
            elif all_chapters:
                # only user condition
                node_query = (
                    Node.query.join(User).filter(
                        and_(
                            User.username.in_(usernames),
                            Node.is_deleted == False  # noqa
                        )
                    )
                )
                relation_query = (
                    Relation.query.join(User).filter(
                        and_(
                            User.username.in_(usernames),
                            Relation.is_deleted == False  # noqa
                        )
                    )
                )
            else:
                # both user and chapter conditions
                node_query = (
                    Node.query.join(User).join(Line).join(Verse).filter(
                        and_(
                            User.username.in_(usernames),
                            Verse.chapter_id.in_(chapters),
                            Node.is_deleted == False  # noqa
                        )
                    )
                )
                relation_query = (
                    Relation.query.join(User).join(Line).join(Verse).filter(
                        and_(
                            User.username.in_(usernames),
                            Verse.chapter_id.in_(chapters),
                            Relation.is_deleted == False  # noqa
                        )
                    )
                )

            annotations = {
                'nodes': [
                    {
                        'line_id': node.line_id,
                        'annotator_id': node.annotator_id,
                        'lemma': node.lemma.lemma,
                        'label': node.label.label
                    }
                    for node in node_query.all()
                ],
                'relations': [
                    {
                        'line_id': relation.line_id,
                        'annotator_id': relation.annotator_id,
                        'source': relation.src_lemma.lemma,
                        'relation': relation.label.label,
                        'detail': relation.detail,
                        'target': relation.dst_lemma.lemma
                    }
                    for relation in relation_query.all()
                ]
            }

            filename = 'annotations.json'
            content = json.dumps(annotations, ensure_ascii=False)
            return Response(
                content,
                mimetype='application/json',
                headers={
                    'Content-Disposition': f'attachment;filename={filename}'
                }
            )
        except Exception as e:
            print(e)
            flash("Failed to get annotations.", "danger")
        return redirect(request.referrer)

    # ----------------------------------------------------------------------- #
    # Update Settings

    if action == 'update_settings':
        display_name = request.form['display_name']
        theme = request.form['theme']

        settings = {
            'display_name': display_name,
            'theme': theme
        }
        current_user.settings = settings
        db.session.commit()
        return redirect(request.referrer)

    # ----------------------------------------------------------------------- #
    # Annotator Actions

    # ----------------------------------------------------------------------- #
    # Action Template

    if action == 'custom_action':
        # action code
        status = True  # action_result
        if status:
            flash("Action completed successfully.", "success")

    # ----------------------------------------------------------------------- #

    if not status:
        flash("Action failed.", "danger")

    return redirect(request.referrer)

###############################################################################


if __name__ == '__main__':
    host = 'localhost'
    port = '5000'

    webapp.run(host=host, port=port, debug=True)
