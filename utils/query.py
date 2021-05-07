#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 09 23:59:05 2021

@author: Hrishikesh Terdalkar
"""

import json
from dataclasses import dataclass
from typing import List, Dict

###############################################################################


@dataclass
class Input:
    id: str
    type: str  # 'entity', 'entity_type', 'relation', 'relation_detail'


@dataclass
class Query:
    gid: str
    groups: Dict[str, str]
    texts: Dict[str, str]
    cypher: str
    input: List[Input]
    output: List[str]

    @classmethod
    def from_dict(self, d, /):
        return self(
            gid=d['gid'],
            groups=d['groups'],
            texts=d['texts'],
            cypher=d['cypher'],
            input=[Input(**i) for i in d['input']],
            output=d['output']
        )

    @classmethod
    def from_json(self, json_text, /):
        return self.from_dict(json.loads(json_text))

    def to_dict(self, prefix='__', suffix='__', debug=False):
        result = {}
        replace_in_text = tuple([
            (f"({prefix}{i.id}{suffix}:{i.type})"
             if debug else
             f"{prefix}{i.id}{suffix}")
            for i in self.input
        ])
        replace_in_cypher = tuple([
            f"{prefix}{i.id}{suffix}" for i in self.input
        ])

        result['groups'] = self.groups
        result['texts'] = {}
        for language in self.texts:
            result['texts'][language] = self.texts[language].format(*replace_in_text)  # noqa

        result['cypher'] = self.cypher.format(*replace_in_cypher)
        result['input'] = [i.__dict__ for i in self.input]
        result['output'] = self.output
        return result

    def to_json(self, *args, **kwargs):
        return json.dumps(self.to_dict(), *args, **kwargs)

###############################################################################


def load_queries(query_file):
    with open(query_file) as f:
        queries = json.load(f)
    return [Query.from_dict(q) for q in queries]

###############################################################################
