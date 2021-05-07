#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 05 13:48:43 2021

@author: Hrishikesh Terdalkar
"""

import spacy
import json

###############################################################################

corpus_file = ('russian.txt')
output_file = ('russian.json')

###############################################################################

nlp = spacy.load("ru_core_news_sm")

###############################################################################

with open(corpus_file) as f:
    lines = [line.strip() for line in f.read().split('\n')]

###############################################################################
# Prepare basic structure
# Entire text is treated to be in a single verse

data = []
verse_id = 1

for line in lines:
    if line:
        data.append({
            'verse': verse_id,
            'text': line,
            'split': '',
            'analysis': {
                'source': 'spacy',
                'text': '',
                'tokens': []
            }
        })


###############################################################################
# Analysis

for line in data:
    doc = nlp(line['text'])
    analysis_text = []
    for token in doc:
        if token.pos_ != 'PUNCT':
            token_details = {
                'Word': token.text,
                'Lemma': token.lemma_,
                'POS': token.pos_,
                'DEP': token.dep_,
                'Gender': ", ".join(token.morph.get('Gender')),
                'Case': ", ".join(token.morph.get('Case')),
                'Number': ", ".join(token.morph.get('Number'))
            }
            analysis_text.append(token.morph.to_json())
            line['analysis']['tokens'].append(token_details)
    line['analysis']['text'] = ",".join(analysis_text)

###############################################################################

with open(output_file, 'w') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
