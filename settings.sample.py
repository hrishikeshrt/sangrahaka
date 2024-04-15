#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Mar 07 13:15:21 2021

@author: Hrishikesh Terdalkar
"""

###############################################################################

import os
from utils.configuration import Configuration

###############################################################################

DEBUG = False

APP_NAME = 'Saṅgrāhaka, an Annotation and Querying Framework'
APP_TITLE = 'Saṅgrāhaka'

APP_DIR = os.path.dirname(os.path.realpath(__file__))
LOG_FILE = os.path.join(APP_DIR, 'sangrahaka.log')

# Paths relative to the APP_DIR
# DB_DIR is used for specifying directory containing SQLite3 database
# Query file is placed inside the DATA_DIR

DB_DIR = 'db'
DATA_DIR = 'data'
TABLES_DIR = os.path.join(DATA_DIR, "tables")

QUERY_FILE = 'query.json'

# --------------------------------------------------------------------------- #

APPLICATION_CONFIG = {
    'schemes': [],
    'var_prefix': '#',
    'var_suffix': '#',
    'query_limit': 250,
    'unnamed_prefix': 'X',
    'show_split': False,
    'line_detail_formatter': 'generic',
    'query_languages': ['english'],
    'suggest_min_length': 2,
    'default_query_language': 'english',
    'graph_templates': [
        # TODO: Consider moving to a file
        {'name': 'Blank', 'nodes': [], 'edges': []},
        {'name': 'Single Edge', 'nodes': [1, 2], 'edges': [(1, 2)]}
    ]
}

# --------------------------------------------------------------------------- #

CONTACTS = [
    {
        "name": "Administrator",
        "email": "admin@127.0.0.1",
        "designation": "Student",
        "affiliation": "World",
    }
]

FEEDBACK_URL = ""

# --------------------------------------------------------------------------- #
# HTML About

ABOUT = """
"Saṅgrāhaka" is a framework for annotating nodes and entities towards
construction and subsequent querying of knowledge graphs.
"""

# --------------------------------------------------------------------------- #
# Custom Pages
# * Page under the key "custom" will be served at "/custom"
# * "title" will be used in <head> tag within <title>
# * "card_header" and "card_body" will appear as page content within a card
# * CAUTION: Only safe HTML content should be added.

CUSTOM_PAGES = {
    "custom": {
        "title": "Custom Title",
        "card_header": "Custom Header",
        "card_body": """This is a cusotm page with HTML content."""
    }
}

# --------------------------------------------------------------------------- #
# Security

# Generate a nice key using secrets.token_urlsafe()
SECRET_KEY = os.environ.get('SECRET_KEY', "super-secret-key")

# Bcrypt is set as default SECURITY_PASSWORD_HASH, which requires a salt
# Generate a good salt using: secrets.SystemRandom().getrandbits(128)
SECURITY_PASSWORD_SALT = os.environ.get(
    'SECURITY_PASSWORD_SALT', '57543530952775748518364848535120005763'
)

# --------------------------------------------------------------------------- #
# First User

ADMIN_USER = os.environ.get('ADMIN_USER', 'admin')
ADMIN_PASS = os.environ.get('ADMIN_PASS', 'admin')
ADMIN_MAIL = os.environ.get('ADMIN_MAIL', 'admin@localhost')

# --------------------------------------------------------------------------- #
# Neo4j

NEO4J_SERVER = 'bolt://localhost:7687'
NEO4J_USERNAME = 'admin'
NEO4J_PASSWORD = 'admin'

# --------------------------------------------------------------------------- #
# PythonAnywhere

PA_DOMAIN = os.environ.get('PA_DOMAIN', '')
PA_USERNAME = os.environ.get('PA_USERNAME', '')
PA_TOKEN = os.environ.get('PA_TOKEN', '')

# --------------------------------------------------------------------------- #
# SMTP Config

SMTP_ENABLED = False

SMTP_SENDER_NAME = os.environ.get('SMTP_SENDER_NAME', 'Saṅgrāhaka Admin')
SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
SMTP_USER = os.environ.get('SMTP_USER', '')
SMTP_PASS = os.environ.get('SMTP_PASS', '')
SMTP_PORT = os.environ.get('SMTP_PORT', '587')
SMTP_USE_SSL = os.environ.get('SMTP_USE_SSL', '0')
SMTP_USE_TLS = os.environ.get('SMTP_USE_TLS', '1')

# --------------------------------------------------------------------------- #
# MongoDB Config

MONGO_HOST = os.environ.get('MONGO_HOST', '')
MONGO_USER = os.environ.get('MONGO_USER', '')
MONGO_PASS = os.environ.get('MONGO_PASS', '')
MONGO_DATABASE = os.environ.get('MONGO_DATABASE', '')
MONGO_OPTIONS = os.environ.get('MONGO_OPTIONS', '?retryWrites=true&w=majority')

# --------------------------------------------------------------------------- #
# MySQL Config

MYSQL_USER = os.environ.get('MYSQL_USER', '')
MYSQL_PASS = os.environ.get('MYSQL_PASS', '')
MYSQL_HOST = os.environ.get('MYSQL_HOST', '')
MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE', '')

# --------------------------------------------------------------------------- #
# SQLite Config

SQLITE_DATABASE = os.environ.get('SQLITE_DATABASE', 'main.db')

# --------------------------------------------------------------------------- #

USE_MONGO = False
USE_MYSQL = False
USE_SQLITE = True

###############################################################################
# DO NOT EDIT

app = Configuration()
app.name = APP_NAME
app.title = APP_TITLE
app.debug = DEBUG

# Config
app.config = APPLICATION_CONFIG
app.about = ABOUT
app.custom_pages = CUSTOM_PAGES

# Paths
app.dir = APP_DIR
app.db_dir = os.path.join(APP_DIR, DB_DIR)
app.data_dir = os.path.join(APP_DIR, DATA_DIR)
app.tables_dir = os.path.join(APP_DIR, TABLES_DIR)

app.log_file = LOG_FILE
app.query_file = os.path.join(app.data_dir, QUERY_FILE)

# Security

app.secret_key = SECRET_KEY
app.security_password_salt = SECURITY_PASSWORD_SALT

# Users

app.admin = {
    'username': ADMIN_USER,
    'email': ADMIN_MAIL,
    'password': ADMIN_PASS
}

app.contacts = CONTACTS
app.feedback_url = FEEDBACK_URL

# Neo4j
app.neo4j = {
    'server': NEO4J_SERVER,
    'username': NEO4J_USERNAME,
    'password': NEO4J_PASSWORD
}

# PythonAnywhere
# https://help.pythonanywhere.com/pages/API

app.pa_enabled = bool(PA_DOMAIN and PA_USERNAME and PA_TOKEN)
app.pa_api_actions = {
    'info': f'/webapps/{PA_DOMAIN}/',
    'reload': f'/webapps/{PA_DOMAIN}/reload/',
}

app.pa_api_url = f'https://www.pythonanywhere.com/api/v0/user/{PA_USERNAME}/'
app.pa_headers = {
    'Authorization': f'Token {PA_TOKEN}'
}

# MongoDB

if USE_MONGO:
    app.mongo = {
        'host': (f'mongodb+srv://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}/'
                 f'{MONGO_DATABASE}?retryWrites=true&w=majority'),
        'connect': False,
        'connectTimeoutMS': 30000,
        'socketTimeoutMS': None,
        'socketKeepAlive': True,
        'maxPoolsize': 1
    }

# SMTP

app.smtp_enabled = SMTP_ENABLED
app.smtp = {
    'name': SMTP_SENDER_NAME,
    'server': SMTP_SERVER,
    'username': SMTP_USER,
    'password': SMTP_PASS,
    'port': int(SMTP_PORT),
    'use_ssl': bool(int(SMTP_USE_SSL)),
    'use_tls': bool(int(SMTP_USE_TLS))
}


# MySQL

if USE_MYSQL:
    app.sqla = {
        'database_uri': (
            f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASS}'
            f'@{MYSQL_HOST}/{MYSQL_DATABASE}'
        )
    }

# SQLite

if USE_SQLITE:
    app.sqla = {
        'database_uri': (
            f'sqlite:///{os.path.join(app.db_dir, SQLITE_DATABASE)}'
        )
    }

###############################################################################
