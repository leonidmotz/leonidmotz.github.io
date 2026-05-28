"""
Export specific token sets to CSV with full corpus information.
Targets:
  - o stem masc, analogical, in Dt.Sg / G.Pl / N.Pl
  - ŭ stem, etymological, in Dt.Sg / G.Pl / N.Pl
  - jo stem masc, analogical, in Dt.Sg / G.Pl / N.Pl
  - i stem masc, analogical, in Dt.Sg / G.Pl / N.Pl
"""

import json, gzip, base64, re, csv
from pathlib import Path

DATA_JS = Path.home() / 'github/leonidmotz.github.io/suprasliensis-data/data.js'
OUT_DIR = Path.home() / 'github/leonidmotz.github.io/suprasliensis-data'
OUT_DIR.mkdir(parents=True, exist_ok=True)

print("Loading data...")
raw = open(DATA_JS).read()
b64 = re.search(r'`([A-Za-z0-9+/=\n]+)`', raw).group(1).replace('\n', '')
data = json.loads(gzip.decompress(base64.b64decode(b64)))
tokens = data['tokens']
print(f"Loaded {len(tokens):,} tokens")

CASE_MAP   = {'n': 'N', 'a': 'A', 'g': 'G', 'd': 'Dt', 'i': 'I', 'l': 'L', 'v': 'V'}
NUMBER_MAP = {'s': 'Sg', 'd': 'Du', 'p': 'Pl'}
GENDER_MAP = {'m': 'masc', 'f': 'fem', 'n': 'neutr', 'o': 'neutr'}

TARGET_SLOTS = {('Dt', 'Sg'), ('G', 'Pl'), ('N', 'Pl')}

TARGETS = [
    {'stem': 'o stem masc',  'stemtype': 'analogical'},
    {'stem': 'ŭ stem',       'stemtype': 'etymological'},
    {'stem': 'jo stem masc', 'stemtype': 'analogical'},
    {'stem': 'i stem masc',  'stemtype': 'analogical'},
]

rows = []
for idx, t in enumerate(tokens):
    mo = t.get('mo', '')
    if len(mo) < 7:
        continue

    num  = NUMBER_MAP.get(mo[1], '')
    case = CASE_MAP.get(mo[6], '')
    if (case, num) not in TARGET_SLOTS:
        continue

    stem     = t.get('s', '')
    stemtype = t.get('st', '')

    matched = False
    for tgt in TARGETS:
        if stem == tgt['stem'] and stemtype == tgt['stemtype']:
            matched = True
            break
    if not matched:
        continue

    if t.get('l', '') == 'жидовинъ':
        continue

    gender = GENDER_MAP.get(mo[5], '') if len(mo) > 5 else ''

    rows.append({
        'token_idx':   idx,
        'form':        t.get('f', ''),
        'bform':       t.get('bf', ''),
        'lemma':       t.get('l', ''),
        'pos':         t.get('p', ''),
        'morph':       mo,
        'case':        case,
        'number':      num,
        'gender':      gender,
        'stem':        stem,
        'stemtype':    stemtype,
        'rel':         t.get('r', ''),
        'info':        t.get('i', ''),
        'after':       t.get('a', ''),
        'book':        t.get('bk', ''),
        'chapter':     t.get('c', ''),
        'folio':       t.get('fo', ''),
        'line':        t.get('ln', ''),
        'bfolio':      t.get('bfo', ''),
        'bline':       t.get('bln', ''),
    })

rows.sort(key=lambda r: (r['stem'], r['stemtype'], r['case'], r['number'],
                          int(r['book']) if r['book'] else 0,
                          int(r['chapter']) if r['chapter'] else 0))

out_path = OUT_DIR / 'case_slot_tokens.csv'
fieldnames = ['token_idx', 'form', 'bform', 'lemma', 'pos', 'morph',
              'case', 'number', 'gender', 'stem', 'stemtype',
              'rel', 'info', 'after', 'book', 'chapter',
              'folio', 'line', 'bfolio', 'bline']

with open(out_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"Exported {len(rows):,} tokens → {out_path}")
for tgt in TARGETS:
    n = sum(1 for r in rows if r['stem'] == tgt['stem'] and r['stemtype'] == tgt['stemtype'])
    print(f"  {tgt['stem']:20s} {tgt['stemtype']:12s}: {n}")
