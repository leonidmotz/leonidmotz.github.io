"""
Codex Suprasliensis — Window Contingency Analysis
For each ISg s-stem token tagged analogical or etymological:
  - check whether any token in the ±2 window is also tagged I.Sg
  - build a 2x2 contingency table and run Fisher's exact test
"""

import json, gzip, base64, re
from pathlib import Path
from scipy.stats import fisher_exact

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

def is_case_sg_stems(t, case, stems):
    num, c = decode_morph(t.get('mo', ''))
    if c != case or num != 'Sg':
        return False
    return t.get('s', '') in stems

def is_case_sg_neighbour(t, case):
    """o/jo/ŭ-stem Sg in given case, OR analogical s-stem Sg in given case"""
    mo = t.get('mo', '')
    if len(mo) < 7:
        return False
    num = NUMBER_MAP.get(mo[1], '')
    c   = CASE_MAP.get(mo[6], '')
    if num != 'Sg' or c != case:
        return False
    s = t.get('s', '')
    if s in OJO_U:
        return True
    if s == 's stem' and t.get('st', '') == 'analogical':
        return True
    return False

OJO_U = ('o stem masc', 'o stem neutr', 'jo stem masc', 'jo stem neutr', 'ŭ stem')

WINDOW = 3

def run_analysis(label, target_case, window_filter):
    table = {'analogical': {'has': 0, 'no': 0},
             'etymological': {'has': 0, 'no': 0}}
    details = []

    for idx, t in enumerate(tokens):
        if t.get('s', '') != 's stem':
            continue
        num, case = decode_morph(t.get('mo', ''))
        if case != target_case or num != 'Sg':
            continue
        st = t.get('st', '')
        if st not in ('analogical', 'etymological'):
            continue

        has_neighbour = False
        neighbour_is_s_analog = False  # True if the qualifying neighbour is itself an analogical s-stem
        for pos in range(-WINDOW, WINDOW + 1):
            if pos == 0:
                continue
            widx = idx + pos
            if 0 <= widx < len(tokens) and window_filter(tokens[widx]):
                has_neighbour = True
                wt = tokens[widx]
                if wt.get('s', '') == 's stem' and wt.get('st', '') == 'analogical':
                    neighbour_is_s_analog = True
                break

        key = 'has' if has_neighbour else 'no'
        table[st][key] += 1
        details.append({
            'idx': idx, 'stemtype': st, 'has_neighbour': has_neighbour,
            'neighbour_is_s_analog': neighbour_is_s_analog,
            'form': t.get('f', ''), 'chapter': t.get('c', ''),
            'folio': t.get('fo', ''), 'line': t.get('ln', ''),
        })

    a = table['analogical']['has']
    b = table['analogical']['no']
    c = table['etymological']['has']
    d = table['etymological']['no']
    odds_ratio, p_value = fisher_exact([[a, b], [c, d]], alternative='two-sided')
    rate_a = a / (a + b) if (a + b) > 0 else 0
    rate_e = c / (c + d) if (c + d) > 0 else 0
    return a, b, c, d, odds_ratio, p_value, rate_a, rate_e, details

# ── Three analyses: one per case, target and neighbour matched ────────────────
analyses = [
    ('G.Sg  s-stem target / G.Sg  o/jo/ŭ or analog. s neighbour', 'G',  lambda t: is_case_sg_neighbour(t, 'G')),
    ('Dt.Sg s-stem target / Dt.Sg o/jo/ŭ or analog. s neighbour', 'Dt', lambda t: is_case_sg_neighbour(t, 'Dt')),
    ('I.Sg  s-stem target / I.Sg  o/jo/ŭ or analog. s neighbour', 'I',  lambda t: is_case_sg_neighbour(t, 'I')),
]

out_path = OUT_DIR / 'window_contingency.txt'

def write_table(f, label, a, b, c, d, OR, pv, ra, re_, details):
    f.write(f"{'='*65}\n")
    f.write(f"{label}\n")
    f.write(f"{'='*65}\n\n")
    f.write(f"{'':25s}  {'has neighbour':>14s}  {'no neighbour':>13s}  {'total':>6s}\n")
    f.write(f"{'─'*65}\n")
    f.write(f"{'analogical':25s}  {a:>14d}  {b:>13d}  {a+b:>6d}\n")
    f.write(f"{'etymological':25s}  {c:>14d}  {d:>13d}  {c+d:>6d}\n")
    f.write(f"{'─'*65}\n")
    f.write(f"{'total':25s}  {a+c:>14d}  {b+d:>13d}  {a+b+c+d:>6d}\n\n")
    f.write(f"Odds ratio:  {OR:.4f}\n")
    f.write(f"p-value:     {pv:.4f} (Fisher's exact, two-sided)\n\n")
    f.write(f"Rate | analogical:   {ra:.1%} ({a}/{a+b})\n")
    f.write(f"Rate | etymological: {re_:.1%} ({c}/{c+d})\n\n")
    if details is not None:
        f.write("Analogical tokens with neighbour:\n")
        mutual = 0
        for d_ in details:
            if d_['stemtype'] == 'analogical' and d_['has_neighbour']:
                flag = '  [mutual s-stem]' if d_['neighbour_is_s_analog'] else ''
                f.write(f"  {d_['form']:20s}  ch={d_['chapter']}  fo={d_['folio']}  ln={d_['line']}{flag}\n")
                if d_['neighbour_is_s_analog']:
                    mutual += 1
        if mutual:
            f.write(f"  --> {mutual} of the above have an analogical s-stem as qualifying neighbour (potential mutual counting)\n")
        f.write("\nEtymological tokens with neighbour:\n")
        for d_ in details:
            if d_['stemtype'] == 'etymological' and d_['has_neighbour']:
                f.write(f"  {d_['form']:20s}  ch={d_['chapter']}  fo={d_['folio']}  ln={d_['line']}\n")
    f.write('\n')

with open(out_path, 'w', encoding='utf-8') as f:
    # Per-case tables
    pool = {'analogical': {'has': 0, 'no': 0}, 'etymological': {'has': 0, 'no': 0}}
    for label, target_case, filt in analyses:
        a, b, c, d, OR, pv, ra, re_, details = run_analysis(label, target_case, filt)
        write_table(f, label, a, b, c, d, OR, pv, ra, re_, details)
        print(f"\n{label}")
        print(f"  analogical:   {a} with / {b} without  (rate {ra:.1%})")
        print(f"  etymological: {c} with / {d} without  (rate {re_:.1%})")
        print(f"  OR={OR:.4f}  p={pv:.4f}")
        # Accumulate for pooled table
        pool['analogical']['has'] += a
        pool['analogical']['no']  += b
        pool['etymological']['has'] += c
        pool['etymological']['no']  += d

    # Pooled table
    pa = pool['analogical']['has']
    pb = pool['analogical']['no']
    pc = pool['etymological']['has']
    pd = pool['etymological']['no']
    por, ppv = fisher_exact([[pa, pb], [pc, pd]], alternative='two-sided')
    pra = pa / (pa + pb) if (pa + pb) > 0 else 0
    pre = pc / (pc + pd) if (pc + pd) > 0 else 0
    write_table(f, 'POOLED G+Dt+I.Sg (same-case o/jo/ŭ neighbour)',
                pa, pb, pc, pd, por, ppv, pra, pre, None)
    print(f"\nPOOLED G+Dt+I.Sg")
    print(f"  analogical:   {pa} with / {pb} without  (rate {pra:.1%})")
    print(f"  etymological: {pc} with / {pd} without  (rate {pre:.1%})")
    print(f"  OR={por:.4f}  p={ppv:.4f}")

print(f"\nFull report -> {out_path}")