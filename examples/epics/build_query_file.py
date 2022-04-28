#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 17 23:23:58 2021

@author: Hrishikesh Terdalkar
"""

###############################################################################

import json
import pandas as pd

###############################################################################


def read_excel(filepath):
    converters = {
        'input': lambda x: [
            {"id": y.split(':')[0], "type": y.split(':')[1]}
            for y in x.split(',') if x
        ],
        'output': lambda x: x.split(',') if x else []
    }
    df = pd.read_excel(filepath,
                       converters={'gid': str},
                       keep_default_na=False)
    queries = df.to_dict(orient='records')
    for query in queries:
        for key, func in converters.items():
            query[key] = func(query[key])

    for query in queries:
        languages = [key.split('_', 1)[1]
                     for key in query.keys()
                     if key.startswith('text_') or key.startswith('group_')]

        query['texts'] = {}
        query['groups'] = {}

        for language in languages:
            if query.get(f'text_{language}'):
                query['texts'][language] = query[f'text_{language}']
                del query[f'text_{language}']

            if query.get(f'group_{language}'):
                query['groups'][language] = query[f'group_{language}']
                del query[f'group_{language}']

            for key in [f'text_{language}', f'group_{language}']:
                if query.get(key):
                    del query[key]

    return queries

###############################################################################


if __name__ == '__main__':
    queries = read_excel("NLQ_Epics.xlsx")

    with open("query_epics.json", "w") as f:
        json.dump(queries, f, ensure_ascii=False, indent=2)
