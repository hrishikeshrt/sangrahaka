#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Global Constants

@author: Hrishikesh Terdalkar
"""
###############################################################################
# Roles

ROLE_OWNER = "owner"
ROLE_ADMIN = "admin"
ROLE_CURATOR = "curator"
ROLE_ANNOTATOR = "annotator"
ROLE_QUERIER = "querier"
ROLE_MEMBER = "member"
ROLE_GUEST = "guest"

# --------------------------------------------------------------------------- #
# Permissions

PERMISSION_VIEW_UCP = "view_ucp"
PERMISSION_VIEW_CORPUS = "view_corpus"
PERMISSION_QUERY = "query"
PERMISSION_ANNOTATE = "annotate"
PERMISSION_CURATE = "curate"
PERMISSION_VIEW_ACP = "view_acp"

# --------------------------------------------------------------------------- #
# Role Definitions

ROLE_DEFINITIONS = [
    {
        "name": ROLE_GUEST,
        "level": 1,
        "description": "Guest",
        "permissions": []
    },
    {
        "name": ROLE_MEMBER,
        "level": 5,
        "description": "Member",
        "permissions": [PERMISSION_VIEW_UCP, PERMISSION_VIEW_CORPUS]
    },
    {
        "name": ROLE_QUERIER,
        "level": 10,
        "description": 'Querier',
        "permissions": [PERMISSION_QUERY]
    },
    {
        "name": ROLE_ANNOTATOR,
        "level": 50,
        "description": "Annotator",
        "permissions": [PERMISSION_ANNOTATE],
    },
    {
        "name": ROLE_CURATOR,
        "level": 75,
        "description": "Curator",
        "permissions": [PERMISSION_ANNOTATE, PERMISSION_CURATE]
    },
    {
        "name": ROLE_ADMIN,
        "level": 100,
        "description": "Administrator",
        "permissions": [PERMISSION_VIEW_ACP]
    },
    {
        "name": ROLE_OWNER,
        "level": 1000,
        "description": "Owner",
        "permissions": [PERMISSION_VIEW_ACP]
    },
]

###############################################################################
# File Type

FILE_TYPE_JSON = {
    "value": "json",
    "description": "JSON",
    "extensions": ["json"]
}
FILE_TYPE_CSV = {
    "value": "csv",
    "description": "CSV",
    "extensions": ["csv"]
}
FILE_TYPE_PLAINTEXT = {
    "value": "plaintext",
    "description": "Plain Text",
    "extensions": ["txt"]
}

###############################################################################
