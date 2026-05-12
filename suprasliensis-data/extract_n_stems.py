#!/usr/bin/env python3
"""
Extract all n-stem tokens from suprasliensis.xml to a CSV with all token attributes.
Sorted by number then case.

Run from ~/github/leonidmotz.github.io/suprasliensis-data/
  python3 extract_n_stems.py
Output: csv-tagging-helpers/n_stem_all.csv
"""

import re, csv, unicodedata

XML_PATH = "suprasliensis.xml"
OUT_PATH = "csv-tagging-helpers/n_stem_all.csv"

NUMBER_MAP = {'s': 'Singular', 'd': 'Dual', 'p': 'Plural'}
CASE_MAP   = {'n': 'Nominative', 'a': 'Accusative', 'o': 'Oblique',
              'g': 'Genitive', 'c': 'Genitive/Dative', 'd': 'Dative',
              'b': 'Ablative', 'i': 'Instrumental', 'l': 'Locative',
              'v': 'Vocative', 'x': 'Indeterminate'}

NUMBER_ORDER = ['Singular', 'Dual', 'Plural']
CASE_ORDER   = ['Nominative', 'Accusative', 'Oblique', 'Genitive', 'Genitive/Dative',
                'Dative', 'Ablative', 'Instrumental', 'Locative', 'Vocative', 'Indeterminate']

def get(attr, line):
    r = re.search(attr + r'="([^"]*)"', line)
    return r.group(1) if r else ''

rows = []
current_folio = ''
current_line  = ''

for line in open(XML_PATH, encoding='utf-8'):
    folio_m = re.search(r'<folio\s[^>]*\bn="([^"]*)"', line)
    if folio_m:
        current_folio = folio_m.group(1)
        continue
    line_m = re.search(r'<line\s[^>]*\bn="([^"]*)"', line)
    if line_m:
        current_line = line_m.group(1)
        continue
    if '<token' not in line or 'stem="n stem"' not in line:
        continue

    morph = get('morph', line)
    if len(morph) < 7:
        continue
    num_code = morph[1]
    cas_code = morph[6]

    number = NUMBER_MAP.get(num_code, '')
    case   = CASE_MAP.get(cas_code, '')

    if not number or not case:
        print(f"DEBUG unexpected morph: {morph!r} num={num_code!r} case={cas_code!r} lemma={get('lemma', line).strip()}")
        continue

    bform = get('bform', line)
    form  = get('form', line)

    rows.append({
        'Folio':             current_folio,
        'Line':              current_line,
        'Book':              get('book', line),
        'Chapter':           get('chapter', line),
        'Lemma':             get('lemma', line),
        'Number':            number,
        'Case':              case,
        'Form':              bform if bform else form,
        'Morph':             morph,
        'Pos':               get('pos', line),
        'Rel':               get('rel', line),
        'Stemtype':          get('stemtype', line),
        'Stemtype corrected': '',
    })

rows.sort(key=lambda r: (
    NUMBER_ORDER.index(r['Number']) if r['Number'] in NUMBER_ORDER else 99,
    CASE_ORDER.index(r['Case'])     if r['Case']   in CASE_ORDER   else 99,
))

fieldnames = [
    'Folio', 'Line', 'Book', 'Chapter',
    'Lemma', 'Number', 'Case', 'Form', 'Morph', 'Pos', 'Rel',
    'Stemtype', 'Stemtype corrected',
]

with open(OUT_PATH, 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    w.writerows(rows)

print(f"Written {len(rows)} tokens to {OUT_PATH}")
