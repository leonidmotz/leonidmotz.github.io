"""
Codex Suprasliensis — Local Window Analysis
Extracts 3 tokens before and after each ISg s-stem token tagged
analogical or etymological, outputs as CSV and plain text concordance.
"""

import json, gzip, base64, re, csv
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
DATA_JS = Path.home() / 'github/leonidmotz.github.io/suprasliensis-data/data.js'
OUT_DIR = Path.home() / 'github/leonidmotz.github.io/suprasliensis-data/window-analysis'
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Load ──────────────────────────────────────────────────────────────────────
print("Loading data...")
raw = open(DATA_JS).read()
b64 = re.search(r'`([A-Za-z0-9+/=\n]+)`', raw).group(1).replace('\n', '')
data = json.loads(gzip.decompress(base64.b64decode(b64)))
tokens = data['tokens']
print(f"Loaded {len(tokens):,} tokens")

CASE_MAP   = {'n': 'N', 'a': 'A', 'g': 'G', 'd': 'Dt', 'i': 'I', 'l': 'L', 'v': 'V'}
NUMBER_MAP = {'s': 'Sg', 'd': 'Du', 'p': 'Pl'}

def decode_morph(mo):
    if not mo or len(mo) < 7:
        return '', ''
    return NUMBER_MAP.get(mo[1], ''), CASE_MAP.get(mo[6], '')

def token_summary(t):
    mo = t.get('mo', '')
    num, case = decode_morph(mo)
    return {
        'form':     t.get('f', ''),
        'lemma':    t.get('l', ''),
        'stem':     t.get('s', ''),
        'stemtype': t.get('st', ''),
        'case':     case,
        'number':   num,
        'chapter':  t.get('c', ''),
        'folio':    t.get('fo', ''),
        'line':     t.get('ln', ''),
    }

# ── Find target tokens: ISg s-stem, analogical or etymological ────────────────
WINDOW = 3
targets = []
for idx, t in enumerate(tokens):
    if t.get('s', '') != 's stem':
        continue
    mo = t.get('mo', '')
    num, case = decode_morph(mo)
    if case != 'I' or num != 'Sg':
        continue
    st = t.get('st', '')
    if st not in ('analogical', 'etymological'):
        continue
    targets.append((idx, st))

print(f"Found {len(targets)} target tokens "
      f"({sum(1 for _, s in targets if s == 'analogical')} analogical, "
      f"{sum(1 for _, s in targets if s == 'etymological')} etymological)")

# ── Build CSV ─────────────────────────────────────────────────────────────────
csv_rows = []
for target_idx, target_st in targets:
    t = tokens[target_idx]
    target_info = token_summary(t)

    for pos in range(-WINDOW, WINDOW + 1):
        widx = target_idx + pos
        if widx < 0 or widx >= len(tokens):
            continue
        w = token_summary(tokens[widx])
        csv_rows.append({
            'target_idx':      target_idx,
            'target_stemtype': target_st,
            'target_form':     target_info['form'],
            'target_lemma':    target_info['lemma'],
            'target_chapter':  target_info['chapter'],
            'target_folio':    target_info['folio'],
            'target_line':     target_info['line'],
            'position':        pos,
            'is_target':       pos == 0,
            'form':            w['form'],
            'lemma':           w['lemma'],
            'stem':            w['stem'],
            'stemtype':        w['stemtype'],
            'case':            w['case'],
            'number':          w['number'],
            'chapter':         w['chapter'],
            'folio':           w['folio'],
            'line':            w['ln'] if 'ln' in w else w['line'],
        })

csv_path = OUT_DIR / 'window_isg_s_stem.csv'
with open(csv_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=list(csv_rows[0].keys()))
    writer.writeheader()
    writer.writerows(csv_rows)
print(f"CSV -> {csv_path}")

# ── Build concordance ─────────────────────────────────────────────────────────
conc_path = OUT_DIR / 'window_isg_s_stem.txt'
with open(conc_path, 'w', encoding='utf-8') as f:
    for target_idx, target_st in targets:
        t = tokens[target_idx]
        ti = token_summary(t)

        f.write(f"{'='*70}\n")
        f.write(f"TARGET [{target_st.upper()}]  "
                f"form={ti['form']}  lemma={ti['lemma']}  "
                f"ch={ti['chapter']}  fo={ti['folio']}  ln={ti['line']}\n")
        f.write(f"{'─'*70}\n")

        for pos in range(-WINDOW, WINDOW + 1):
            widx = target_idx + pos
            if widx < 0 or widx >= len(tokens):
                continue
            w = token_summary(tokens[widx])
            marker = '>>>' if pos == 0 else f'  {pos:+d}'
            stem_info = f"{w['stem'] or '—':20s}" if w['stem'] else f"{'—':20s}"
            morph_info = f"{w['case']}.{w['number']}" if w['case'] else '—'
            f.write(
                f"  {marker}  {w['form']:25s}  "
                f"lemma={w['lemma']:25s}  "
                f"stem={stem_info}  "
                f"st={w['stemtype'] or '—':12s}  "
                f"morph={morph_info}\n"
            )
        f.write('\n')

print(f"Concordance -> {conc_path}")
print("Done.")
