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
__copyright__ = "Copyright (C) 2020-2023 Hrishikesh Terdalkar"
__version__ = "3.4.0"

###############################################################################

import os
import re
import csv
import glob
import json
import logging
import datetime
import io
import zipfile

import git
import requests
from flask import (Flask, render_template, redirect, jsonify, url_for,
                   request, flash, session, Response, abort)
from flask_security import (Security, RegisterForm,
                            auth_required, permissions_required,
                            hash_password, current_user,
                            user_registered, user_confirmed,
                            user_authenticated)
from flask_security.utils import uia_email_mapper
from sqlalchemy import or_, and_, func

from flask_admin import Admin, helpers as admin_helpers

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from flask_babelex import Babel
from flask_wtf import CSRFProtect
from flask_mail import Mail
from flask_migrate import Migrate

from indic_transliteration.sanscript import transliterate

from constants import (
    ROLE_OWNER,
    ROLE_ADMIN,
    ROLE_CURATOR,
    ROLE_ANNOTATOR,
    ROLE_QUERIER,
    ROLE_MEMBER,
    ROLE_GUEST,
    ROLE_DEFINITIONS,

    PERMISSION_VIEW_ACP,
    PERMISSION_QUERY,
    PERMISSION_ANNOTATE,
    PERMISSION_CURATE,
    PERMISSION_VIEW_UCP,
    PERMISSION_VIEW_CORPUS,

    # File Types
    FILE_TYPE_PLAINTEXT,
    FILE_TYPE_JSON,
    FILE_TYPE_CSV,
)

from models_sqla import (db, user_datastore, User,
                         CustomLoginForm,
                         Corpus, Chapter, Verse, Line, Analysis,
                         Lexicon, NodeLabel, Node,
                         RelationLabel, Relation,
                         ActionLabel, ActorLabel, Action)
from models_admin import (SecureAdminIndexView,
                          UserModelView, LabelModelView,
                          LexiconModelView, AnnotationModelView)
from settings import app
from utils.reverseproxied import ReverseProxied
from utils.database import (
    add_chapter,
    get_line_data,
    get_chapter_data,
    build_graph
)
from utils.graph import Graph
from utils.property_graph import PropertyGraph
from utils.query import load_queries
from utils.cypher_utils import graph_to_cypher
from utils.plaintext import Tokenizer

###############################################################################

logging.basicConfig(format='[%(asctime)s] %(name)s %(levelname)s: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.INFO,
                    handlers=[logging.FileHandler(app.log_file),
                              logging.StreamHandler()])

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
webapp.url_map.strict_slashes = False

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

# Flask Admin Theme
webapp.config["FLASK_ADMIN_SWATCH"] = "united"

# CSRF Token Expiry
webapp.config['WTF_CSRF_TIME_LIMIT'] = None

###############################################################################
# Flask-Security-Too Configuration

webapp.config['SECURITY_REGISTERABLE'] = True
webapp.config['SECURITY_POST_REGISTER_VIEW'] = 'show_home'
webapp.config['SECURITY_SEND_REGISTER_EMAIL'] = app.smtp_enabled
webapp.config['SECURITY_USER_IDENTITY_ATTRIBUTES'] = [
    {'email': {'mapper': uia_email_mapper}},
    {'username': {'mapper': uia_username_mapper}}
]

webapp.config['SECURITY_CONFIRMABLE'] = app.smtp_enabled
webapp.config['SECURITY_LOGIN_WITHOUT_CONFIRMATION'] = True
webapp.config['SECURITY_POST_CONFIRM_VIEW'] = 'show_home'

webapp.config['SECURITY_RECOVERABLE'] = app.smtp_enabled
webapp.config['SECURITY_CHANGEABLE'] = True
webapp.config['SECURITY_TRACKABLE'] = True
webapp.config['SECURITY_USERNAME_ENABLE'] = True
webapp.config['SECURITY_USERNAME_REQUIRED'] = True
webapp.config['SECURITY_POST_LOGIN_VIEW'] = 'show_home'
webapp.config['SECURITY_POST_LOGOUT_VIEW'] = 'show_home'
webapp.config['SECURITY_UNAUTHORIZED_VIEW'] = 'show_home'

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
security = Security(webapp, user_datastore, login_form=CustomLoginForm,
                    confirm_register_form=RegisterForm)

# NOTE: By default, Flask-Security-Too disables "Confirm Password" prompt if
# `SECURITY_CONFIRMABLE` is set to `True`.
# We want to have both, so `confirm_register_form=flask_security.RegisterForm`
# (Default is confirm_register_form=flask_security.ConfirmRegisterForm)

# flask-admin
admin = Admin(
    webapp,
    name=f"{app.title} Admin",
    index_view=SecureAdminIndexView(
        name="Database",
        url="/admin/database"
    ),
    template_mode="bootstrap4",
    base_template="admin_base.html",
)
admin.add_view(UserModelView(User, db.session))
admin.add_view(LabelModelView(NodeLabel, db.session, category="Ontology"))
admin.add_view(LabelModelView(RelationLabel, db.session, category="Ontology"))
admin.add_view(LexiconModelView(Lexicon, db.session, category="Annotation"))
admin.add_view(AnnotationModelView(Node, db.session, category="Annotation"))
admin.add_view(
    AnnotationModelView(Relation, db.session, category="Annotation")
)

mail = Mail(webapp)
migrate = Migrate(webapp, db)
babel = Babel(webapp)

limiter = Limiter(
    key_func=get_remote_address,
    app=webapp,
    default_limits=["1800 per hour"],
    storage_uri="memory://",
)

###############################################################################
# Neo4j Graph

GRAPH = None


def connect_graph_server():
    try:
        return Graph(
            server=app.neo4j['server'],
            username=app.neo4j['username'],
            password=app.neo4j['password']
        )
    except Exception as e:
        logging.error(f"Graph Database connection failed. ({e})")
        return None


def initialize_graph_connection():
    """Establish graph connection if not connected already"""
    global GRAPH
    if GRAPH is None:
        GRAPH = connect_graph_server()
    return GRAPH is not None


# Initialize Graph Connection
initialize_graph_connection()

###############################################################################

QUERIES = load_queries(app.query_file)

###############################################################################
# Database Utility Functions


def get_lexicon(lemma: str) -> int:
    """Fetch id of an existing Lexicon"""
    lexicon = Lexicon.query.filter(Lexicon.lemma == lemma).one_or_none()
    if lexicon:
        return lexicon.id


def create_lexicon(lemma: str, commit: bool = False) -> int:
    """Create a new Lexicon and return its id"""
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

    try:
        db.session.add(lexicon)
    except Exception as e:
        webapp.logger.exception(e)
        db.session.rollback()
        return None
    else:
        if not commit:
            db.session.flush()
        else:
            db.session.commit()
        return lexicon.id


def get_or_create_lexicon(lemma: str) -> int:
    return get_lexicon(lemma) or create_lexicon(lemma)


def update_lexicon(old_lemma: str, new_lemma: str) -> bool:
    """
    Change lemma of a lexicon entry

    It must be ensured that `new_lemma` does not exist already,
    else the uniqueness constraint on `Lexicon.lemma` will be violated.
    Different strategies may be required if the `new_lemma` already exists,
    based on different roles of users trying to use this command.
    e.g., when changing to an existing lemma, we would need to update all the
    `Node` references as well, and this should be limited to secure roles,
    such as `ROLE_CURATOR` or `ROLE_ADMIN`.
    These decisions are left out of scope of this function.
    """
    transliterations = [
        f"##{transliterate(new_lemma, 'devanagari', scheme)}"
        if not new_lemma.startswith(app.config['unnamed_prefix']) else ''
        for scheme in app.config['schemes']
    ]
    transliteration = ''.join(transliterations)
    lexicon = Lexicon.query.filter(Lexicon.lemma == old_lemma).one_or_none()
    if lexicon is None:
        return False

    try:
        lexicon.lemma = new_lemma
        lexicon.transliteration = transliteration
        db.session.add(lexicon)
    except Exception as e:
        webapp.logger.exception(e)
        db.session.rollback()
    else:
        db.session.commit()
        return True

    return False


def update_node_label_id(
    node_id: int, old_label_id: int, new_label_id: int
) -> bool:
    """
    Change node label (label_id) of a node

    If there is already exists a node which has node label `new_label_id`
    and shares `line_id`, `annotator_id`,  `lexicon_id` with `node_id`,
    it'll result in the uniqueness constraint violation on `Node`.

    In case of such an event, transaction will be aborted.

    NOTE: Even if a user with ROLE_CURATOR changes a node, it will not
    change the `annotator_id` associated with it.
    """
    node = Node.query.get(node_id)
    node_label = NodeLabel.query.get(new_label_id)

    if node is None or node_label is None:
        return False

    # sanity check
    if node.label_id != int(old_label_id):
        return False

    try:
        node.label_id = new_label_id
        db.session.add(node)
    except Exception as e:
        webapp.logger.exception(e)
        db.session.rollback()
    else:
        db.session.commit()
        return True

    return False


# --------------------------------------------------------------------------- #


def update_relation_label_id(
    relation_id: int, old_label_id: int, new_label_id: int
) -> bool:
    """
    Change relation label (label_id) of a relation

    In case of the uniqueness constraint violation on `Relation`,
    transaction will be aborted.

    NOTE: Even if a user with ROLE_CURATOR changes a relation, it will not
    change the `annotator_id` associated with it.
    """
    relation = Relation.query.get(relation_id)
    relation_label = NodeLabel.query.get(new_label_id)

    if relation is None or relation_label is None:
        return False

    # sanity check
    if relation.label_id != int(old_label_id):
        return False

    try:
        relation.label_id = new_label_id
        db.session.add(relation)
    except Exception as e:
        webapp.logger.exception(e)
        db.session.rollback()
    else:
        db.session.commit()
        return True

    return False


def update_node_id_in_relations(old_node_id: int, new_node_id: int) -> bool:
    """
    Change all occurrences of `old_node_id` in relations to `new_node_id`
    """
    old_node = Node.query.get(old_node_id)
    new_node = Node.query.get(new_node_id)

    if old_node is None or new_node is None:
        return False

    src_relations = Relation.query.filter(Relation.src_id == old_node_id).all()
    dst_relations = Relation.query.filter(Relation.dst_id == old_node_id).all()

    try:
        for relation in src_relations:
            relation.src_id = new_node_id
            db.session.add(relation)

        for relation in dst_relations:
            relation.dst_id = new_node_id
            db.session.add(relation)
    except Exception as e:
        webapp.logger.exception(e)
        db.session.rollback()
    else:
        db.session.commit()
        return True


###############################################################################
# Hooks


@webapp.before_first_request
def init_database():
    """Initiate database and create admin user"""
    db.create_all()
    role_definitions = sorted(
        ROLE_DEFINITIONS, key=lambda x: x['level'], reverse=True
    )
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
            roles=[
                ROLE_OWNER,
                ROLE_ADMIN,
                ROLE_CURATOR,
                ROLE_ANNOTATOR,
                ROLE_QUERIER,
                ROLE_MEMBER
            ]
        )

    # ----------------------------------------------------------------------- #
    # # Populate various tables if empty
    # # NOTE: Refer to `data/tables/README.md` for format of JSON and CSV

    # objects = []

    # # Labels
    # label_models = [NodeLabel, RelationLabel, ActionLabel, ActorLabel]
    # for label_model in label_models:
    #     if not label_model.query.first():
    #         table_name = label_model.__tablename__
    #         table_json_file = os.path.join(
    #             app.tables_dir, f"{table_name}.json"
    #         )
    #         table_csv_file = os.path.join(
    #             app.tables_dir, f"{table_name}.csv"
    #         )

    #         table_file = None
    #         if os.path.isfile(table_json_file):
    #             table_file = table_json_file
    #             with open(table_json_file, encoding="utf-8") as f:
    #                 table_data = json.load(f)
    #         elif os.path.isfile(table_csv_file):
    #             table_file = table_csv_file
    #             with open(table_csv_file, encoding="utf-8") as f:
    #                 table_data = list(csv.DictReader(f))

    #         if table_file is None:
    #             continue

    #         for idx, label in enumerate(table_data, start=1):
    #             lm = label_model()
    #             lm.label = label["label"]
    #             lm.description = label["description"]
    #             objects.append(lm)

    #         webapp.logger.info(
    #             f"Loaded {idx} items to {table_name} from {table_file}."
    #         )

    # # Save
    # if objects:
    #     db.session.bulk_save_objects(objects)

    # ----------------------------------------------------------------------- #

    db.session.commit()

###############################################################################
# Signals


@user_registered.connect_via(webapp)
def assign_default_roles(sender, user, **extra):
    """Assign `ROLE_MEMBER` to users after successful registration"""
    user_datastore.add_role_to_user(user, ROLE_MEMBER)
    db.session.commit()


@user_confirmed.connect_via(webapp)
def assign_confirm_roles(sender, user, **extra):
    """Assign `ROLE_QUERIER` to users after email confirmation"""
    user_datastore.add_role_to_user(user, ROLE_QUERIER)
    db.session.commit()


@user_authenticated.connect_via(webapp)
def _after_authentication_hook(sender, user, **extra):
    pass


###############################################################################
# Global Context


@webapp.context_processor
def inject_global_context():
    theme_css_files = glob.glob(
        os.path.join(app.dir, 'static', 'themes', 'css', 'bootstrap.*.min.css')
    )
    theme_js_files = glob.glob(
        os.path.join(app.dir, 'static', 'themes', 'js', 'bootstrap.*.min.js')
    )
    THEMES = {
        "with_css": ['default'] + sorted([
            os.path.basename(theme).split('.')[1]
            for theme in theme_css_files
        ]),
        "with_js": sorted([
            os.path.basename(theme).split('.')[1]
            for theme in theme_js_files
        ])
    }

    ROLES = {
        "owner": ROLE_OWNER,
        "admin": ROLE_ADMIN,
        "curator": ROLE_CURATOR,
        "annotator": ROLE_ANNOTATOR,
        "querier": ROLE_QUERIER,
        "member": ROLE_MEMBER,
        "guest": ROLE_GUEST
    }

    LABELS = {
        'node_labels': NodeLabel.query.filter(
            NodeLabel.is_deleted == False  # noqa # '== False' is required
        ).with_entities(
            NodeLabel.id, NodeLabel.label, NodeLabel.description
        ).all(),
        'relation_labels': RelationLabel.query.filter(
            RelationLabel.is_deleted == False  # noqa # '== False' is required
        ).with_entities(
            RelationLabel.id, RelationLabel.label, RelationLabel.description
        ).all(),
        # 'action_labels': ActionLabel.query.filter(
        #     ActionLabel.is_deleted == False  # noqa # '== False' is required
        # ).with_entities(
        #     ActionLabel.id, ActionLabel.label, ActionLabel.description
        # ).all(),
        # 'actor_labels': ActorLabel.query.filter(
        #     ActorLabel.is_deleted == False  # noqa # '== False' is required
        # ).with_entities(
        #     ActorLabel.id, ActorLabel.label, ActorLabel.description
        # ).all(),
        'admin_labels': [
            {
                "name": "node",
                "title": "Node",
                "object_name": "node_labels"
            },
            {
                "name": "relation",
                "title": "Relation",
                "object_name": "relation_labels"
            },
            # {
            #     "name": "action",
            #     "title": "Action",
            #     "object_name": "action_labels"
            # },
            # {
            #     "name": "actor",
            #     "title": "Actor",
            #     "object_name": "actor_labels"
            # },
        ]
    }
    return {
        'title': app.title,
        'now': datetime.datetime.utcnow(),
        'context_roles': ROLES,
        'context_themes': THEMES,
        'context_labels': LABELS,
        'config': app.config
    }

###############################################################################
# Flask-Admin Context for Flask-Security-Too


@security.context_processor
def security_context_processor():
    return dict(
        admin_base_template=admin.base_template,
        admin_view=admin.index_view,
        h=admin_helpers,
        get_url=url_for
    )

###############################################################################
# Flask-Security-Too Views Context


@security.register_context_processor
def security_register_processor():
    data = {'title': 'Register'}
    return {'data': data}


@security.login_context_processor
def security_login_processor():
    data = {'title': 'Login'}
    return {'data': data}


@security.forgot_password_context_processor
def security_forgot_password_processor():
    data = {'title': 'Forgot Password'}
    return {'data': data}


@security.change_password_context_processor
def security_change_password_processor():
    data = {'title': 'Change Password'}
    return {'data': data}


@security.reset_password_context_processor
def security_reset_password_processor():
    data = {'title': 'Reset Password'}
    return {'data': data}

###############################################################################
# Views


@webapp.route("/admin")
@auth_required()
@permissions_required(PERMISSION_VIEW_ACP)
def show_admin():
    data = {}
    data['title'] = 'Admin'

    user_level = max([role.level for role in current_user.roles])
    annotator_role = user_datastore.find_role('annotator')

    user_model = user_datastore.user_model
    role_model = user_datastore.role_model
    user_query = user_model.query
    role_query = role_model.query

    data['filetypes'] = {
        'chapter': [FILE_TYPE_PLAINTEXT, FILE_TYPE_JSON],
        'ontology': [FILE_TYPE_CSV, FILE_TYPE_JSON]
    }

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


@webapp.route("/settings")
@auth_required()
@permissions_required(PERMISSION_VIEW_UCP)
def show_settings():
    data = {}
    data['title'] = 'Settings'
    return render_template('settings.html', data=data)


@webapp.route("/corpus")
@webapp.route("/corpus/<string:chapter_id>")
@auth_required()
@permissions_required(PERMISSION_VIEW_CORPUS)
def show_corpus(chapter_id=None):
    if chapter_id is None:
        flash("Please select a corpus to view.", "info")
        return redirect(url_for('show_home'))

    data = {}
    data['title'] = 'Corpus'
    data['chapter_id'] = chapter_id
    data['enable_annotation'] = current_user.has_permission(
        PERMISSION_ANNOTATE
    )
    return render_template('corpus.html', data=data)


@webapp.route("/browse")
@auth_required()
@permissions_required(PERMISSION_QUERY)
def show_browse():
    data = {}
    data['title'] = 'Graph Browser'
    data['initial_query'] = (
        'MATCH (node_1)-[edge]->(node_2) RETURN * ORDER BY rand() LIMIT 10'
    )
    data['node_query_template'] = (
        'MATCH (x)-[relation]-(entity) '
        'WHERE entity.lemma =~ "{}" RETURN *'
    )
    return render_template('browse.html', data=data)


@webapp.route("/query")
@auth_required()
@permissions_required(PERMISSION_QUERY)
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
        'MATCH (node_1)-[edge]->(node_2) RETURN * ORDER BY rand() LIMIT 25'
    )
    data['initial_output_order'] = ['node_1', 'edge', 'node_2']
    return render_template('query.html', data=data)


@webapp.route("/query/builder")
@auth_required()
@permissions_required(PERMISSION_QUERY)
def show_builder():
    data = {'title': 'Graph Query Builder'}
    data['templates'] = app.config['graph_templates']
    return render_template('builder.html', data=data)


@webapp.route("/terms")
def show_terms():
    data = {'title': 'Terms of Use'}
    return render_template('terms.html', data=data)


@webapp.route("/contact")
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
    data['feedback_url'] = app.feedback_url
    return render_template('contact.html', data=data)


@webapp.route("/about")
def show_about():
    data = {
        'title': 'About',
        'about': app.about
    }
    return render_template('about.html', data=data)


@webapp.route("/<page>")
@auth_required()
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


@webapp.route("/")
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
# Ontology


@webapp.route("/ontology", methods=["GET"])
@auth_required()
def get_ontology():
    ontology = {
        'node_labels': [
            tuple(nl)
            for nl in NodeLabel.query.filter(
                NodeLabel.is_deleted == False  # noqa # '== False' is required
            ).with_entities(
                NodeLabel.id, NodeLabel.label, NodeLabel.description
            ).all()
        ],
        'relation_labels': [
            tuple(rl)
            for rl in RelationLabel.query.filter(
                RelationLabel.is_deleted == False  # noqa # '== False' is required
            ).with_entities(
                RelationLabel.id, RelationLabel.label, RelationLabel.description
            ).all()
        ],
    }
    return jsonify(ontology)

###############################################################################
# Action Endpoints


@webapp.route("/api", methods=["POST"])
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
        ROLE_ADMIN: [],
        ROLE_ANNOTATOR: [
            'update_entity',
            'update_relation',
            # 'update_action',
            'update_lexicon',
            'update_node_label_id',
            'update_relation_label_id',
            'update_node_id_in_relations',
        ],
        ROLE_CURATOR: [],
        ROLE_QUERIER: ['query', 'graph_query']
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
    api_response['style'] = "info"

    # ----------------------------------------------------------------------- #

    if action == 'update_lexicon':
        annotator_id = current_user.id
        current_lemma = request.form['current_lemma']
        replacement_lemma = request.form['replacement_lemma']

        if current_lemma == replacement_lemma:
            api_response["success"] = False
            api_response["message"] = (
                "Replacement text is same as current text."
            )
            return jsonify(api_response)

        replacement_lexicon_id = get_lexicon(replacement_lemma)
        if replacement_lexicon_id:
            # NOTE: One option is to add a replacement strategy for Curators
            # However, it might be best to handle this case-by-case basis and
            # not make an interface for it.
            # # if current_user.has_permission(PERMISSION_CURATE):
            # #     ...
            api_response["success"] = False
            api_response["message"] = "Replacement text already exists."
            api_response["style"] = "warning"
            return jsonify(api_response)

        try:
            status = update_lexicon(current_lemma, replacement_lemma)
            if not status:
                api_response["success"] = False
                api_response["message"] = "Original text not found."
                api_response["style"] = "warning"
            else:
                api_response["success"] = True
                api_response["message"] = "Successfully updated!"
                api_response["style"] = "success"
        except Exception as e:
            print(e)
            api_response["success"] = False
            api_response["message"] = "Something went wrong."
            api_response["style"] = "error"
        return jsonify(api_response)

    if action == 'update_node_label_id':
        annotator_id = current_user.id
        node_id = request.form['node_id']
        old_label_id = request.form['old_label_id']
        new_label_id = request.form['new_label_id']

        if old_label_id == new_label_id:
            api_response["success"] = False
            api_response["message"] = (
                "Replacement node type is same as current node type."
            )
            return jsonify(api_response)

        if False:
            # NOTE: check for conditions such as existence of new/old labels?
            # these checks are already done in update_node_label_id()
            # status returns False if they fail
            api_response["success"] = False
            api_response["message"] = "Error"
            api_response["style"] = "warning"
            return jsonify(api_response)

        try:
            status = update_node_label_id(node_id, old_label_id, new_label_id)
            if not status:
                api_response["success"] = False
                api_response["message"] = "Failed to update."
                api_response["style"] = "warning"
            else:
                api_response["success"] = True
                api_response["message"] = "Successfully updated!"
                api_response["style"] = "success"
        except Exception as e:
            print(e)
            api_response["success"] = False
            api_response["message"] = "Something went wrong."
            api_response["style"] = "error"
        return jsonify(api_response)

    if action == 'update_relation_label_id':
        annotator_id = current_user.id
        relation_id = request.form['relation_id']
        old_label_id = request.form['old_label_id']
        new_label_id = request.form['new_label_id']

        if old_label_id == new_label_id:
            api_response["success"] = False
            api_response["message"] = (
                "Replacement relation type is same as current relation type."
            )
            return jsonify(api_response)

        if False:
            # NOTE: check for conditions such as existence of new/old labels?
            # these checks are already done in update_relation_label_id()
            # status returns False if they fail
            api_response["success"] = False
            api_response["message"] = "Error"
            api_response["style"] = "warning"
            return jsonify(api_response)

        try:
            status = update_relation_label_id(
                relation_id, old_label_id, new_label_id
            )
            if not status:
                api_response["success"] = False
                api_response["message"] = "Failed to update."
                api_response["style"] = "warning"
            else:
                api_response["success"] = True
                api_response["message"] = "Successfully updated!"
                api_response["style"] = "success"
        except Exception as e:
            print(e)
            api_response["success"] = False
            api_response["message"] = "Something went wrong."
            api_response["style"] = "error"
        return jsonify(api_response)

    if action == 'update_node_id_in_relations':
        annotator_id = current_user.id
        old_node_id = request.form['old_node_id']
        new_node_id = request.form['new_node_id']

        if old_node_id == new_node_id:
            api_response["success"] = False
            api_response["message"] = (
                "Replacement node id is same as existing node id."
            )
            return jsonify(api_response)

        if False:
            # NOTE: check for conditions such as existence of new/old nodes?
            # these checks are already done in update_node_id_in_relations()
            # status returns False if they fail
            api_response["success"] = False
            api_response["message"] = "Error"
            api_response["style"] = "warning"
            return jsonify(api_response)

        try:
            status = update_node_id_in_relations(old_node_id, new_node_id)
            if not status:
                api_response["success"] = False
                api_response["message"] = "Failed to update."
                api_response["style"] = "warning"
            else:
                api_response["success"] = True
                api_response["message"] = "Successfully updated!"
                api_response["style"] = "success"
        except Exception as e:
            print(e)
            api_response["success"] = False
            api_response["message"] = "Something went wrong."
            api_response["style"] = "error"
        return jsonify(api_response)

    # ----------------------------------------------------------------------- #

    if action in ['update_entity', 'update_relation']:  # , 'update_action']:
        line_id = request.form['line_id']
        annotator_id = current_user.id

        objects_to_update = []
        objects_untouched = []

        # ------------------------------------------------------------------- #

        if action == 'update_entity':
            entities_add = request.form['entity_add'].split('##')
            entities_del = request.form['entity_delete'].split('##')
            for entity in entities_add + entities_del:
                if '$' not in entity:
                    continue
                parts = entity.split('$')
                entity_lemma = parts[0]
                entity_label = parts[1]
                _lexicon_id = get_or_create_lexicon(entity_lemma)

                label_query = NodeLabel.query.filter(
                    NodeLabel.label == entity_label
                )
                _label = label_query.first()
                if _label is None:
                    api_response['success'] = False
                    api_response['message'] = (
                        f"Invalid node type '{entity_label}'."
                    )
                    api_response['style'] = "warning"
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
                if current_user.has_permission(PERMISSION_CURATE):
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
                    if entity in entities_del:
                        relation_query = Relation.query.filter(
                            or_(
                                Relation.src_id == n.id,
                                Relation.dst_id == n.id
                            ),
                            Relation.is_deleted == False  # noqa
                        )
                        relations_with_n = relation_query.count()
                        if relations_with_n:
                            objects_untouched.append({
                                "node_id": n.id,
                                "reason": (
                                    f"Node {n.id} "
                                    f"({entity_lemma}::{entity_label}) "
                                    f"used in {relations_with_n} relations."
                                )
                            })
                        else:
                            n.is_deleted = True
                            objects_to_update.append(n)
                    else:
                        n.is_deleted = False
                        objects_to_update.append(n)

        # ------------------------------------------------------------------- #

        if action == 'update_relation':
            relations_add = request.form['relation_add'].split('##')
            relations_del = request.form['relation_delete'].split('##')
            for relation in relations_add + relations_del:
                if '$' not in relation:
                    continue
                parts = relation.split('$')
                print(parts)
                try:
                    _src_node_id = int(parts[0])
                except Exception:
                    _src_node_id = None

                try:
                    _relation_label_id = int(parts[1])
                except Exception:
                    _relation_label_id = None

                try:
                    _dst_node_id = int(parts[2])
                except Exception:
                    _dst_node_id = None

                _detail_text = parts[3]
                _detail = _detail_text if _detail_text.strip() else None

                _src_lemma = parts[4]
                _src_label = parts[5]
                _relation_label = parts[6]
                _dst_lemma = parts[7]
                _dst_label = parts[8]

                _src_lexicon_id = get_lexicon(_src_lemma)
                _dst_lexicon_id = get_lexicon(_dst_lemma)

                if _src_node_id is None:
                    objects_untouched.append({
                        "relation": (_src_lemma, _relation_label, _dst_lemma),
                        "reason": (
                            f"Source node ({_src_lemma}::{_src_label}) "
                            "does not exist."
                        )
                    })
                    continue

                if _dst_node_id is None:
                    objects_untouched.append({
                        "relation": (_src_lemma, _relation_label, _dst_lemma),
                        "reason": (
                            f"Target node ({_dst_lemma}::{_dst_label}) "
                            "does not exist."
                        )
                    })
                    continue

                label_query = RelationLabel.query.filter(
                    RelationLabel.label == _relation_label
                )
                _label = label_query.first()
                if _label is None:
                    objects_untouched.append({
                        "relation": (_src_lemma, _relation_label, _dst_lemma),
                        "reason": f"Invalid relation type '{_relation_label}'."
                    })
                    continue
                _label_id = _label.id

                relation_query = Relation.query.filter(and_(
                    Relation.line_id == line_id,
                    Relation.annotator_id == annotator_id,
                    Relation.src_id == _src_node_id,
                    Relation.dst_id == _dst_node_id,
                    Relation.label_id == _label_id,
                    Relation.detail == _detail
                ))

                # Curator can edit annotations by others
                # i.e. (no annotator_id check)
                if current_user.has_permission(PERMISSION_CURATE):
                    relation_query = Relation.query.filter(and_(
                        Relation.line_id == line_id,
                        Relation.src_id == _src_node_id,
                        Relation.dst_id == _dst_node_id,
                        Relation.label_id == _label_id,
                        Relation.detail == _detail
                    ))
                r = relation_query.first()

                if r is None:
                    if relation in relations_add:
                        r = Relation()
                        r.line_id = line_id
                        r.annotator_id = annotator_id
                        r.src_id = _src_node_id
                        r.dst_id = _dst_node_id
                        r.label_id = _label_id
                        r.detail = _detail
                        objects_to_update.append(r)
                else:
                    r.is_deleted = (relation in relations_del)
                    objects_to_update.append(r)

        # ------------------------------------------------------------------- #

        # if action == 'update_action':
        #     actions_add = request.form['action_add'].split('##')
        #     actions_del = request.form['action_delete'].split('##')
        #     for action in actions_add + actions_del:
        #         if '$' not in action:
        #             continue
        #         parts = action.split('$')
        #         _actor_id = get_lexicon(parts[2])

        #         if _actor_id is None:
        #             api_response['success'] = False
        #             api_response['message'] = (
        #                 'Actor entity does not exist.'
        #             )
        #             return jsonify(api_response)

        #         label_query = ActionLabel.query.filter(
        #             ActionLabel.label == parts[0]
        #         )
        #         _label = label_query.first()
        #         if _label is None:
        #             api_response['success'] = False
        #             api_response['message'] = 'Invalid action type.'
        #             return jsonify(api_response)

        #         actor_label_query = ActorLabel.query.filter(
        #             ActorLabel.label == parts[1]
        #         )
        #         _actor_label = actor_label_query.first()
        #         if _actor_label is None:
        #             api_response['success'] = False
        #             api_response['message'] = 'Invalid actor type.'
        #             return jsonify(api_response)

        #         _label_id = _label.id
        #         _actor_label_id = _actor_label.id

        #         action_query = Action.query.filter(and_(
        #             Action.line_id == line_id,
        #             Action.label_id == _label_id,
        #             Action.annotator_id == annotator_id,
        #             Action.actor_label_id == _actor_label_id,
        #             Action.actor_id == _actor_id,
        #         ))

        #         # Curator can edit annotations by others
        #         # i.e. (no annotator_id check)
        #         if current_user.has_permission(PERMISSION_CURATE):
        #             action_query = Action.query.filter(and_(
        #                 Action.line_id == line_id,
        #                 Action.label_id == _label_id,
        #                 Action.actor_label_id == _actor_label_id,
        #                 Action.actor_id == _actor_id,
        #             ))
        #         a = action_query.first()

        #         if a is None:
        #             if action in actions_add:
        #                 a = Action()
        #                 a.line_id = line_id
        #                 a.annotator_id = annotator_id
        #                 a.label_id = _label_id
        #                 a.actor_id = _actor_id
        #                 a.actor_label_id = _actor_label_id
        #                 objects_to_update.append(a)
        #         else:
        #             a.is_deleted = (action in actions_del)
        #             objects_to_update.append(a)

        # ------------------------------------------------------------------- #

        untouched_count = len(objects_untouched)
        api_message = [
            f"No changes were made. ({untouched_count} problematic objects.)",
            ""
        ]
        if objects_untouched:
            api_message.extend(uo["reason"] for uo in objects_untouched)
            print(api_message)
            api_response['message'] = "<br>".join(api_message)
            api_response['success'] = False
            api_response['style'] = 'danger'
            return jsonify(api_response)
        else:
            api_response['success'] = True

        try:
            updated_count = len(objects_to_update)
            print(f"Total objects to update: {updated_count}")
            if objects_to_update:
                db.session.bulk_save_objects(objects_to_update)
                db.session.commit()
                api_response['message'] = f'Updated {updated_count} objects!'
                api_response['style'] = 'success'
            else:
                api_response['message'] = 'No changes were made.'
                api_response['style'] = 'info'
        except Exception as e:
            print(e)
            print(request.form)
            api_response['success'] = False
            api_response['message'] = 'Something went wrong.'
            api_response['style'] = 'danger'
        return jsonify(api_response)

    # ----------------------------------------------------------------------- #

    if action == 'query':
        initialize_graph_connection()
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
            if query_limit > 0 and limit > query_limit:
                limit_pattern = re.compile(f'LIMIT {limit}', re.IGNORECASE)
                cypher_query = re.sub(
                    limit_pattern, f'LIMIT {query_limit}', cypher_query
                )
                api_response['warning'] = f'LIMIT reset to {query_limit}'
                logging.warning(f"Limit exceeded. ({limit} > {query_limit}).")
        except ValueError:
            if query_limit > 0:
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
            api_response['style'] = 'error'

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


@webapp.route("/api/chapter/<int:chapter_id>")
@auth_required()
def api_chapter(chapter_id):
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


@webapp.route("/api/line/<int:line_id>")
@auth_required()
def api_line(line_id):
    line = Line.query.get(line_id)
    if line is None:
        return jsonify({})

    annotator_ids = []
    if current_user.has_permission(PERMISSION_ANNOTATE):
        annotator_ids = [current_user.id]
    if (
        current_user.has_permission(PERMISSION_CURATE) or
        current_user.has_role(ROLE_ADMIN)
    ):
        annotator_ids = None

    data = get_line_data(
        [line_id],
        annotator_ids=annotator_ids,
        fetch_nodes=True,
        fetch_relations=True
    )
    return jsonify(data)

# --------------------------------------------------------------------------- #


@webapp.route("/api/suggest-node")
@limiter.limit("60 per minute")
def suggest_node():
    # Parse q (category search starting ':')
    # e.g. Sample q values => "maz", ":SUB", "maz :SUB", ... etc.

    query = request.args.get('q')
    words = query.split(':')
    min_length = app.config['suggest_min_length']

    lexicon_query_term = words[0].strip()
    node_label_query_term = words[1].strip() if len(words) > 1 else ""

    response = []
    if all([
        lexicon_query_term and len(lexicon_query_term) < min_length,
        not lexicon_query_term.startswith(app.config['unnamed_prefix'])
    ]):
        return jsonify(response)

    search_query = Node.query.join(Lexicon, NodeLabel).with_entities(
        func.min(Node.id), Lexicon.lemma, NodeLabel.label
    ).filter(
        or_(
            Lexicon.transliteration.like(f"%##{lexicon_query_term}%"),
            Lexicon.lemma.startswith(lexicon_query_term)
        ),
        NodeLabel.label.like(f"{node_label_query_term}%"),
        Node.is_deleted == False  # noqa
    ).group_by(
        Node.lexicon_id, Node.label_id
    ).order_by(
        func.count(Node.id).desc()
    ).limit(1000)

    response = [
        {
            "value": node_id,
            "text": f"{node_lemma}::{node_label}",
            "html": (
                f"<b class='float-left'>{node_lemma}</b> "
                f"<small class='text-muted float-right'>{node_label}</small>"
            )
        }
        for node_id, node_lemma, node_label in search_query.all()
    ]
    return jsonify(response)


@webapp.route("/api/suggest-lexicon")
@limiter.limit("60 per minute")
def suggest_lexicon():
    word = request.args.get('q')
    min_length = app.config['suggest_min_length']

    response = []
    if all([
        word and len(word) < min_length,
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


@webapp.route("/action", methods=["POST"])
@auth_required()
def perform_action():
    status = False
    try:
        action = request.form['action']
    except KeyError:
        flash("Insufficient parameters in request.", "error")
        return redirect(request.referrer)

    # ----------------------------------------------------------------------- #
    # Admin Actions

    role_actions = {
        ROLE_OWNER: [
            'application_info', 'application_update', 'application_reload'
        ],
        ROLE_ADMIN: [
            'user_role_add', 'user_role_remove',

            # Add/Remove/Upload Labels

            # - Node Label
            'node_label_add',
            'node_label_remove',
            'node_label_upload',

            # - Relation Label
            'relation_label_add',
            'relation_label_remove',
            'relation_label_upload',

            # # - Action Label
            # 'action_label_add',
            # 'action_label_remove',
            # 'action_label_upload',

            # # - Actor Label
            # 'actor_label_add',
            # 'actor_label_remove',
            # 'actor_label_upload',

            # Data
            'corpus_add', 'chapter_add',
            'annotation_download',
            'download_property_graph_csv',
            'download_property_graph_jsonl',
        ],
        ROLE_CURATOR: [],
        ROLE_ANNOTATOR: [],
        ROLE_MEMBER: ['update_settings']
    }
    valid_actions = [
        action for actions in role_actions.values() for action in actions
    ]

    if action not in valid_actions:
        flash(f"Invalid action. ({action})", "error")
        return redirect(request.referrer)

    for role, actions in role_actions.items():
        if action in actions and not current_user.has_role(role):
            flash("You are not authorized to perform that action.", "error")
            return redirect(request.referrer)

    # ----------------------------------------------------------------------- #
    # Show Application Information

    if action in [
        'application_info', 'application_update', 'application_reload'
    ] and not app.pa_enabled:
        flash("PythonAnywhere configuration incomplete or missing.", "error")
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
            flash("Already up-to-date.", "info")
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
                flash(f"You cannot modify '{target_user}'.", "error")
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
                flash(message.format(target_role, target_user), "success")
            else:
                flash("No changes were made.", "info")

        return redirect(request.referrer)

    # ----------------------------------------------------------------------- #
    # Ontology

    if action in [
        'node_label_add', 'node_label_remove', 'node_label_upload',
        'relation_label_add', 'relation_label_remove', 'relation_label_upload',
        # 'action_label_add', 'action_label_remove', 'action_label_upload',
        # 'actor_label_add', 'actor_label_remove', 'actor_label_upload',
    ]:
        action_parts = action.split('_label_')

        object_name = action_parts[0]
        target_action = action_parts[-1]

        MODELS = {
            'node': (NodeLabel, Node, 'label_id'),
            'relation': (RelationLabel, Relation, 'label_id'),
            # 'action': (ActionLabel, Action, 'label_id'),
            # 'actor': (ActorLabel, Action, 'actor_label_id')
        }
        _model, _annotation_model, _attribute = MODELS[object_name]

        _model_name = _model.__name__

        if target_action == 'add':
            _label_text = request.form[f'{object_name}_label_text']
            _label_description = request.form[f'{object_name}_label_desc']

            _instance = _model.query.filter(
                _model.label == _label_text
            ).first()

            message = f"Added {_model_name} '{_label_text}'."
            if _instance is None:
                _instance = _model()
                _instance.label = _label_text
                _instance.description = _label_description
                _instance.is_deleted = False
                status = True
                db.session.add(_instance)
            else:
                if _instance.is_deleted:
                    _instance.is_deleted = False
                    status = True
                    db.session.add(_instance)
                else:
                    message = f"{_model_name} '{_label_text}' already exists."

        if target_action == 'remove':
            _label_text = request.form[f'{object_name}_label_text']

            _instance = _model.query.filter(
                _model.label == _label_text
            ).first()

            message = f"{_model_name} '{_label_text}' does not exists."
            if _instance is not None and not _instance.is_deleted:
                objects_with_given_label = _annotation_model.query.filter(
                    getattr(_annotation_model, _attribute) == _instance.id,
                    _annotation_model.is_deleted == False  # noqa
                ).all()
                if objects_with_given_label:
                    message = (
                        f"{_model_name} '{_label_text}' is used in annotation."
                    )
                else:
                    _instance.is_deleted = True
                    db.session.add(_instance)
                    status = True
                    message = f"Removed {_model_name} '{_label_text}'."

        if target_action == 'upload':
            # Labels
            # NOTE: Refer to `data/tables/README.md` for format of JSON and CSV
            _label_file = request.files['label_file']
            _upload_format = request.form['upload_format']

            _existing_labels = {
                _instance.label: _instance
                for _instance in _model.query.all()
            }

            _label_file_content = _label_file.read().decode()
            if _upload_format == FILE_TYPE_JSON["value"]:
                try:
                    table_data = json.loads(_label_file_content)
                except json.decoder.JSONDecodeError as e:
                    webapp.logger.exception(e)
                    flash("Invalid JSON file format.", "error")
                    return redirect(request.referrer)
            elif _upload_format == FILE_TYPE_CSV["value"]:
                try:
                    table_data = list(
                        csv.DictReader(_label_file_content.splitlines())
                    )
                except csv.Error as e:
                    webapp.logger.exception(e)
                    flash("Invalid CSV file format.", "error")
                    return redirect(request.referrer)

            _add_count = 0
            _undelete_count = 0
            _ignore_count = 0
            objects_to_update = []
            for idx, label in enumerate(table_data, start=1):
                _label_identifier = label["label"]
                if _label_identifier in _existing_labels:
                    _instance = _existing_labels[_label_identifier]
                    if _instance.is_deleted:
                        _instance.is_deleted = False
                        _undelete_count += 1
                        objects_to_update.append(_instance)
                    else:
                        _ignore_count += 1
                else:
                    _instance = _model()
                    _instance.label = label["label"]
                    _instance.description = label["description"]
                    _add_count += 1
                    objects_to_update.append(_instance)

            if objects_to_update:
                db.session.bulk_save_objects(objects_to_update)
                status = True
                _total = _add_count + _undelete_count
                message = (
                    f"Added {_total} {_model_name}s "
                    f"({_add_count} + {_undelete_count}). "
                    f"Ignored {_ignore_count}."
                )
            else:
                message = f"No new {_model_name}s were added."

        if status:
            db.session.commit()
            flash(message, "success")
        else:
            flash(message, "info")
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
        chapter_format = request.form['chapter_format']

        if chapter_filename == '':
            flash("No file selected.")
            return redirect(request.referrer)

        # Validity
        if chapter_format == FILE_TYPE_JSON["value"]:
            allowed_extensions = FILE_TYPE_JSON["extensions"]
        elif chapter_format == FILE_TYPE_PLAINTEXT["value"]:
            allowed_extensions = FILE_TYPE_PLAINTEXT["extensions"]
        else:
            flash("Invalid chapter file type.", "error")
            return redirect(request.referrer)

        file_extension = chapter_filename.rsplit('.', 1)[1].lower()
        is_valid_filename = (file_extension in allowed_extensions)

        if chapter_file and is_valid_filename:
            corpus_query = Corpus.query.filter(Corpus.id == corpus_id)
            corpus = corpus_query.first()
            if corpus is None:
                flash("No corpus selected.")
                return redirect(request.referrer)

            try:
                if chapter_format == FILE_TYPE_JSON["value"]:
                    chapter_data = json.load(chapter_file)
                if chapter_format == FILE_TYPE_PLAINTEXT["value"]:
                    file_content = chapter_file.read().decode()

                    # Plaintext Processor
                    # TODO: Move to `plaintext.py`

                    verse_sep_regex = r'\s*\n\s*\n\s*'
                    line_sep_regex = r'\s*\n\s*'
                    word_sep_regex = r'\s+'

                    verse_tokenizer = Tokenizer(verse_sep_regex)
                    line_tokenizer = Tokenizer(line_sep_regex)
                    word_tokenizer = Tokenizer(word_sep_regex)

                    chapter_data = [
                        {
                            "verse": _verse_idx,
                            "text": _line,
                            "split": "",
                            "analysis": {
                                "source": "plaintext",
                                "text": "",
                                "tokens": [
                                    {
                                        "Word": _word,
                                    }
                                    for _word in word_tokenizer.tokenize(_line)
                                ]
                            }
                        }
                        for _verse_idx, _verse in enumerate(
                            verse_tokenizer.tokenize(file_content),
                            start=1
                        )
                        for _line_idx, _line in enumerate(
                            line_tokenizer.tokenize(_verse),
                            start=1
                        )
                    ]
            except json.decoder.JSONDecodeError:
                flash("Invalid file format.", "error")
                return redirect(request.referrer)

            # --------------------------------------------------------------- #
            # Insert

            result = add_chapter(
                corpus_id=corpus.id,
                chapter_name=chapter_name,
                chapter_description=chapter_description,
                chapter_data=chapter_data
            )
            flash(result["message"], result["style"])

            # --------------------------------------------------------------- #
        else:
            flash("Invalid file or file extension.", "error")

        return redirect(request.referrer)

    # ----------------------------------------------------------------------- #
    # Graph Download

    if action in ["download_property_graph_csv", "download_property_graph_jsonl"]:
        usernames = request.form.getlist('annotator')
        chapters = request.form.getlist('chapter_id')

        request_time = datetime.datetime.utcnow().strftime("%Y_%m_%d")
        file_prefix = "graph"
        file_extension = action.rsplit('_', 1)[1].lower()

        try:
            User = user_datastore.user_model
            annotator_ids = None
            line_ids = None

            if usernames:
                annotator_ids =  [
                    user.id
                    for user in User.query.filter(User.username.in_(usernames))
                ]
            if chapters:
                line_ids = [
                    line.id
                    for chapter in Chapter.query.filter(Chapter.id.in_(chapters))
                    for verse in chapter.verses
                    for line in verse.lines
                ]

            graph, errors = build_graph(
                line_ids=line_ids,
                annotator_ids=annotator_ids
            )

            if file_extension == "jsonl":
                filename = f'{file_prefix}_{request_time}.{file_extension}'
                jsonl_content = graph.to_jsonl()
                return Response(
                    jsonl_content,
                    mimetype='application/json',
                    headers={
                        'Content-Disposition': f'attachment;filename={filename}'
                    }
                )
            if file_extension == "csv":
                csv_content = graph.to_csv()
                filename = f'{file_prefix}_{request_time}.zip'
                nodes_content = csv_content["nodes"]
                edges_content = csv_content["edges"]
                nodes_filename = f'{file_prefix}_nodes_{request_time}.{file_extension}'
                edges_filename = f'{file_prefix}_edges_{request_time}.{file_extension}'
                files = {
                    nodes_filename: nodes_content,
                    edges_filename: edges_content
                }
                zip_buffer = io.BytesIO()
                # create a ZipFile object
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    for _filename, _content in files.items():
                        # write each file to the zip archive
                        zip_file.writestr(_filename, _content)

                # Seek to the beginning of the BytesIO object to read its content
                zip_buffer.seek(0)

                return Response(
                    zip_buffer.read(),
                    mimetype='application/zip',
                    headers={
                        'Content-Disposition': f'attachment;filename={filename}'
                    }
                )

        except Exception as e:
            print(e)
            flash("Failed to export graph.", "error")
            return redirect(request.referrer)

    # ----------------------------------------------------------------------- #

    # ----------------------------------------------------------------------- #
    # Annotations Download

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
                        'source': relation.src_node.lemma.lemma,
                        'relation': relation.label.label,
                        'detail': relation.detail,
                        'target': relation.dst_node.lemma.lemma
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
            flash("Failed to get annotations.", "error")
        return redirect(request.referrer)

    # ----------------------------------------------------------------------- #
    # Update Settings

    if action == 'update_settings':
        display_name = request.form['display_name']
        sort_labels = bool(request.form.getlist('sort_labels'))
        theme = request.form['theme']

        settings = {
            'display_name': display_name,
            'sort_labels': sort_labels,
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
        flash("Action failed.", "error")

    return redirect(request.referrer)

###############################################################################


if __name__ == '__main__':
    import argparse
    import socket

    hostname = socket.gethostname()
    default_host = socket.gethostbyname(hostname)
    default_port = '5000'

    parser = argparse.ArgumentParser(description="Sangrahaka Server")
    parser.add_argument("-H", "--host", help="Hostname", default=default_host)
    parser.add_argument("-P", "--port", help="Port", default=default_port)
    args = vars(parser.parse_args())

    host = args["host"]
    port = args["port"]

    webapp.run(host=host, port=port, debug=True)
