"""
Codex Suprasliensis — Analogical rate by text part class/genre
Three analyses:
  1. s stems — all cases/numbers, analogical vs etymological
  2. CSV stems (u-stem-morphology.csv) — Dt.Sg: in_csv vs not
  3. CSV stems — G.Pl + N.Pl: in_csv vs not
"""

import json, gzip, base64, re, csv
import pandas as pd
from pathlib import Path
from collections import defaultdict

# ── Paths ─────────────────────────────────────────────────────────────────────
DATA_JS  = Path.home() / 'github/leonidmotz.github.io/suprasliensis-data/data.js'
CSV_PATH = Path.home() / 'github/leonidmotz.github.io/suprasliensis-data/u-stem-morphology.csv'
ODS_PATH = Path.home() / 'github/leonidmotz.github.io/suprasliensis-data/text-part-classification.ods'

# ── Load text part classification ─────────────────────────────────────────────
tp_df = pd.read_excel(ODS_PATH, engine='odf')
tp_genre = {int(row['Text part']): str(row['Genre']).strip() for _, row in tp_df.iterrows()}
tp_class = {int(row['Text part']): str(row['Class']).strip()  for _, row in tp_df.iterrows()}

# ── Load data.js ──────────────────────────────────────────────────────────────
print("Loading data.js ...")
raw = open(DATA_JS).read()
b64 = re.search(r'`([A-Za-z0-9+/=\n]+)`', raw).group(1).replace('\n', '')
data = json.loads(gzip.decompress(base64.b64decode(b64)))
tokens = data['tokens']
print(f"Loaded {len(tokens):,} tokens\n")

CASE_MAP   = {'n': 'N', 'a': 'A', 'g': 'G', 'd': 'Dt', 'i': 'I', 'l': 'L', 'v': 'V'}
NUMBER_MAP = {'s': 'Sg', 'd': 'Du', 'p': 'Pl'}

def decode_morph(mo):
    if len(mo) < 7:
        return '', ''
    return CASE_MAP.get(mo[6], ''), NUMBER_MAP.get(mo[1], '')

# ── Load CSV token index ───────────────────────────────────────────────────────
csv_idx_set = set()
csv_lemmas  = set()
with open(CSV_PATH, newline='', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        csv_idx_set.add(int(row['token_idx']))
        csv_lemmas.add(row['lemma'])

TARGET_SLOTS_PL  = {('G', 'Pl'), ('N', 'Pl')}
TARGET_SLOT_DTSG = {('Dt', 'Sg')}

# ── Report helper ─────────────────────────────────────────────────────────────
def print_table(title, group_label, tally, total_key='analog', denom_key='total'):
    """
    tally: dict of group -> {'analog': n, 'total': n}
    """
    print(f"\n{'='*65}")
    print(f"  {title}")
    print(f"{'='*65}")
    print(f"  {'Group':20s}  {'analog':>7s}  {'total':>7s}  {'rate':>7s}")
    print(f"  {'─'*52}")
    
    grand_analog = sum(v['analog'] for v in tally.values())
    grand_total  = sum(v['total']  for v in tally.values())
    
    for group in sorted(tally.keys()):
        d = tally[group]
        rate = d['analog'] / d['total'] * 100 if d['total'] else 0
        print(f"  {group:20s}  {d['analog']:>7d}  {d['total']:>7d}  {rate:>6.1f}%")
    print(f"  {'─'*52}")
    grand_rate = grand_analog / grand_total * 100 if grand_total else 0
    print(f"  {'TOTAL':20s}  {grand_analog:>7d}  {grand_total:>7d}  {grand_rate:>6.1f}%")

# ══════════════════════════════════════════════════════════════════════════════
# ANALYSIS 1: s stems, all cases/numbers, analogical vs etymological
# ══════════════════════════════════════════════════════════════════════════════
s_by_genre = defaultdict(lambda: {'analog': 0, 'total': 0})
s_by_class = defaultdict(lambda: {'analog': 0, 'total': 0})

for t in tokens:
    if t.get('s', '') != 's stem':
        continue
    st = t.get('st', '')
    if st not in ('analogical', 'etymological'):
        continue
    try:
        chapter = int(t.get('c', 0))
    except (TypeError, ValueError):
        continue
    genre = tp_genre.get(chapter, '?')
    cls   = tp_class.get(chapter, '?')
    
    s_by_genre[genre]['total'] += 1
    s_by_class[cls]['total']   += 1
    if st == 'analogical':
        s_by_genre[genre]['analog'] += 1
        s_by_class[cls]['analog']   += 1

print_table('s-Stämme — alle Kasus/Numeri (by Genre)', 'Genre', s_by_genre)
print_table('s-Stämme — alle Kasus/Numeri (by Class)', 'Class', s_by_class)

# ══════════════════════════════════════════════════════════════════════════════
# ANALYSIS 2 & 3: CSV stems, DtSg and NPl/GPl
# ══════════════════════════════════════════════════════════════════════════════
dtsg_by_genre  = defaultdict(lambda: {'analog': 0, 'total': 0})
dtsg_by_class  = defaultdict(lambda: {'analog': 0, 'total': 0})
pl_by_genre    = defaultdict(lambda: {'analog': 0, 'total': 0})
pl_by_class    = defaultdict(lambda: {'analog': 0, 'total': 0})

for idx, t in enumerate(tokens):
    if t.get('l', '') not in csv_lemmas:
        continue
    mo = t.get('mo', '')
    case, num = decode_morph(mo)
    slot = (case, num)
    try:
        chapter = int(t.get('c', 0))
    except (TypeError, ValueError):
        continue
    genre = tp_genre.get(chapter, '?')
    cls   = tp_class.get(chapter, '?')
    in_csv = idx in csv_idx_set

    if slot in TARGET_SLOT_DTSG:
        dtsg_by_genre[genre]['total'] += 1
        dtsg_by_class[cls]['total']   += 1
        if in_csv:
            dtsg_by_genre[genre]['analog'] += 1
            dtsg_by_class[cls]['analog']   += 1

    if slot in TARGET_SLOTS_PL:
        pl_by_genre[genre]['total'] += 1
        pl_by_class[cls]['total']   += 1
        if in_csv:
            pl_by_genre[genre]['analog'] += 1
            pl_by_class[cls]['analog']   += 1

print_table('CSV-Stämme Dt.Sg — *ŭ-Flexion (by Genre)', 'Genre', dtsg_by_genre)
print_table('CSV-Stämme Dt.Sg — *ŭ-Flexion (by Class)', 'Class', dtsg_by_class)
print_table('CSV-Stämme G.Pl/N.Pl — *ŭ-Flexion (by Genre)', 'Genre', pl_by_genre)
print_table('CSV-Stämme G.Pl/N.Pl — *ŭ-Flexion (by Class)', 'Class', pl_by_class)

print()
