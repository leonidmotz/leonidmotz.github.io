"""
Codex Suprasliensis — Lemma Rankings by Analogical Forms
Outputs one CSV per stem class with lemmas ranked by analogical count and rate.
"""

import json, gzip, base64, re, csv
from pathlib import Path
from collections import defaultdict

DATA_JS = Path.home() / 'github/leonidmotz.github.io/suprasliensis-data/data.js'
OUT_DIR = Path.home() / 'github/leonidmotz.github.io/suprasliensis-data/lemma-rankings'
OUT_DIR.mkdir(parents=True, exist_ok=True)

print(f"Loading {DATA_JS} ...")
raw = open(DATA_JS).read()
b64 = re.search(r'`([A-Za-z0-9+/=\n]+)`', raw).group(1).replace('\n', '')
data = json.loads(gzip.decompress(base64.b64decode(b64)))
tokens = data['tokens']
print(f"Loaded {len(tokens):,} tokens\n")

STEM_CLASSES = {
    'o stem masc':   {'stems': ['o stem masc'],   'gender': None},
    'o stem neutr':  {'stems': ['o stem neutr'],   'gender': None},
    'jo stem masc':  {'stems': ['jo stem masc'],   'gender': None},
    'jo stem neutr': {'stems': ['jo stem neutr'],  'gender': None},
    'u-breve stem':  {'stems': ['ŭ stem'],   'gender': None},
    'u-macron stem': {'stems': ['ū stem'],   'gender': None},
    'i stem masc':   {'stems': ['i stem masc'],    'gender': None},
    'i stem fem':    {'stems': ['i stem fem'],     'gender': None},
    'n stem masc':   {'stems': ['n stem'],         'gender': 'm'},
    'n stem neutr':  {'stems': ['n stem'],         'gender': 'n'},
    's stem':        {'stems': ['s stem'],         'gender': None},
    'r stems':       {'stems': ['r stems'],        'gender': None},
    'tel stem':      {'stems': ['tel stem'],       'gender': None},
}

for label, cfg in STEM_CLASSES.items():
    tally = defaultdict(lambda: {'total': 0, 'analogical': 0})

    for t in tokens:
        if t.get('s', '') not in cfg['stems']:
            continue
        if cfg['gender'] is not None:
            mo = t.get('mo', '')
            if len(mo) < 6 or mo[5] != cfg['gender']:
                continue
        lemma = t.get('l', '').strip() or '(unknown)'
        tally[lemma]['total'] += 1
        if t.get('st', '') == 'analogical':
            tally[lemma]['analogical'] += 1

    if not tally:
        print(f"  !! No tokens for '{label}' — skipping")
        continue

    rows = [
        {'lemma': lemma, 'analogical': c['analogical'], 'total': c['total'],
         'rate': c['analogical'] / c['total'] if c['total'] else 0.0}
        for lemma, c in tally.items()
    ]
    
    rows = [r for r in rows if r['analogical'] > 0]

    rows_abs = sorted(rows, key=lambda r: (-r['analogical'], -r['rate'], r['lemma']))
    rows_rel = sorted(rows, key=lambda r: (-r['rate'], -r['analogical'], r['lemma']))

    abs_rank = {r['lemma']: i + 1 for i, r in enumerate(rows_abs)}
    rel_rank = {r['lemma']: i + 1 for i, r in enumerate(rows_rel)}

    out_path = OUT_DIR / f'lemma_ranking_{label.replace(" ", "_")}.csv'
    with open(out_path, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['rank_absolute', 'rank_relative', 'lemma',
                    'analogical', 'total', 'rate_pct'])
        for row in rows_abs:
            w.writerow([
                abs_rank[row['lemma']],
                rel_rank[row['lemma']],
                row['lemma'],
                row['analogical'],
                row['total'],
                f"{row['rate'] * 100:.1f}%",
            ])

    print(f"  v  {label:20s} — {len(rows):3d} lemmas -> {out_path.name}")

print("\nDone.")
