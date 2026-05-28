"""
Codex Suprasliensis — Distribution chart: ŭ-stem flexion vs. other flexion.
For each lemma present in the CSV, finds ALL tokens of that lemma in the
target case+number slots (Dt.Sg, G.Pl, N.Pl) in the corpus.
Red  = token is in the CSV (*ŭ-Stamm-Flexion)
Grey = token of same lemma in same slot but not in CSV (keine *ŭ-Stamm-Flexion)
Saves both PNG and PDF for each plot.
"""

import json, gzip, base64, re, os, csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from pathlib import Path
from collections import defaultdict

plt.rcParams['pdf.fonttype'] = 42  # embed TrueType fonts in PDF

# ── Paths ─────────────────────────────────────────────────────────────────────
DATA_JS   = Path.home() / 'github/leonidmotz.github.io/suprasliensis-data/data.js'
CSV_PATH  = Path.home() / 'github/leonidmotz.github.io/suprasliensis-data/u-stem-morphology.csv'
OUT_DIR   = Path.home() / 'github/leonidmotz.github.io/suprasliensis-data/heatmaps-diagrams'
FONT_PATH = '/usr/share/fonts/truetype/charis/CharisSIL-Regular.ttf'
OUT_DIR.mkdir(parents=True, exist_ok=True)

if os.path.exists(FONT_PATH):
    fm.fontManager.addfont(FONT_PATH)
    plt.rcParams['font.family'] = 'Charis SIL'

# ── Load data.js ──────────────────────────────────────────────────────────────
print(f"Loading {DATA_JS} ...")
raw = open(DATA_JS).read()
b64 = re.search(r'`([A-Za-z0-9+/=\n]+)`', raw).group(1).replace('\n', '')
data = json.loads(gzip.decompress(base64.b64decode(b64)))
tokens = data['tokens']
print(f"Loaded {len(tokens):,} tokens")

CASE_MAP   = {'n': 'N', 'a': 'A', 'g': 'G', 'd': 'Dt', 'i': 'I', 'l': 'L', 'v': 'V'}
NUMBER_MAP = {'s': 'Sg', 'd': 'Du', 'p': 'Pl'}

TARGET_SLOTS = {('Dt', 'Sg'), ('G', 'Pl'), ('N', 'Pl')}

CHAPTERS = list(range(1, 49))
chapter_all = {c: [] for c in CHAPTERS}
for idx, t in enumerate(tokens):
    try:
        c = int(t.get('c', 0))
    except (TypeError, ValueError):
        continue
    if c in chapter_all:
        chapter_all[c].append(idx)

token_pos = {}
for c, idxs in chapter_all.items():
    n = len(idxs)
    for rank, idx in enumerate(idxs):
        token_pos[idx] = (c, rank, n)

# ── Load CSV ──────────────────────────────────────────────────────────────────
print(f"Loading {CSV_PATH} ...")
csv_idx_set = set()
csv_lemmas  = set()
with open(CSV_PATH, newline='', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        csv_idx_set.add(int(row['token_idx']))
        csv_lemmas.add(row['lemma'])
print(f"CSV: {len(csv_idx_set)} tokens, {len(csv_lemmas)} lemmas: {sorted(csv_lemmas)}")

# ── Find all corpus tokens for those lemmas in target slots ───────────────────
plot_tokens = []
for idx, t in enumerate(tokens):
    if t.get('l', '') not in csv_lemmas:
        continue
    mo = t.get('mo', '')
    if len(mo) < 7:
        continue
    case = CASE_MAP.get(mo[6], '')
    num  = NUMBER_MAP.get(mo[1], '')
    if (case, num) not in TARGET_SLOTS:
        continue
    if idx not in token_pos:
        continue
    c, rank, n = token_pos[idx]
    x = rank / (n - 1) if n > 1 else 0.5
    plot_tokens.append({
        'token_idx': idx,
        'chapter':   c,
        'x':         x,
        'case':      case,
        'number':    num,
        'lemma':     t.get('l', ''),
        'form':      t.get('f', ''),
        'in_csv':    idx in csv_idx_set,
    })

n_csv    = sum(1 for t in plot_tokens if t['in_csv'])
n_notcsv = sum(1 for t in plot_tokens if not t['in_csv'])
print(f"Total corpus tokens for these lemmas in target slots: {len(plot_tokens)}")
print(f"  in CSV (*ŭ-Stamm-Flexion):    {n_csv}")
print(f"  not in CSV (andere Flexion):   {n_notcsv}")

COLOR_CSV    = '#8b1a4a'  # rust red — *ŭ-Stamm-Flexion
COLOR_NOCSV  = '#b0b0b0'  # light grey — keine *ŭ-Stamm-Flexion

# ── Plot function ─────────────────────────────────────────────────────────────
def make_plot(subset, title, out_file,
              dot_size=40, dot_alpha=0.8, row_h=0.6,
              fig_w=16, fig_h=10, dpi=300):

    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')

    n_ch  = len(CHAPTERS)
    y_mid = {c: -(i * row_h) for i, c in enumerate(CHAPTERS)}

    for c in CHAPTERS:
        ax.hlines(y_mid[c], 0, 1, colors='#e0e0e0', linewidths=0.4, zorder=1)

    # Grey first, red on top
    for in_csv in [False, True]:
        xs = [t['x'] for t in subset if t['in_csv'] == in_csv]
        ys = [y_mid[t['chapter']] for t in subset if t['in_csv'] == in_csv]
        color = COLOR_CSV if in_csv else COLOR_NOCSV
        if xs:
            ax.scatter(xs, ys, s=dot_size, c=color,
                       alpha=dot_alpha, linewidths=0,
                       zorder=3 if in_csv else 2)

    # Chapter labels and counts
    by_chapter = defaultdict(lambda: {'in': 0, 'total': 0})
    for t in subset:
        by_chapter[t['chapter']]['total'] += 1
        if t['in_csv']:
            by_chapter[t['chapter']]['in'] += 1

    for c in CHAPTERS:
        ax.text(-0.012, y_mid[c], str(c),
                ha='right', va='center', fontsize=6, color='#555555')
        d = by_chapter[c]
        if d['total'] > 0:
            ax.text(1.012, y_mid[c], f"{d['in']}/{d['total']}",
                    ha='left', va='center', fontsize=6, color='#555555')

    ax.set_xlim(-0.05, 1.08)
    ax.set_ylim(-(n_ch * row_h) - row_h * 2, row_h * 1.5)
    ax.axis('off')

    ax.text(0.5, row_h * 1.1, title,
            ha='center', va='bottom',
            fontsize=10, fontweight='bold', color='#2a1a0a',
            transform=ax.transData)

    legend_y = -(n_ch * row_h) - row_h * 0.8
    for color, label, lx in [
        (COLOR_CSV,   '*ŭ-Stamm-Flexion',       0.0),
        (COLOR_NOCSV, 'keine *ŭ-Stamm-Flexion',  0.2),
    ]:
        ax.scatter([lx], [legend_y], s=dot_size, c=color,
                   linewidths=0, zorder=4)
        ax.text(lx + 0.015, legend_y, label,
                ha='left', va='center', fontsize=7, color='#333333')

    # Save PNG
    out_path = OUT_DIR / out_file
    fig.savefig(out_path, dpi=dpi, bbox_inches='tight',
                pad_inches=0.1, facecolor='white')
    print(f"Saved -> {out_path}  ({len(subset)} tokens)")

    # Save PDF
    out_path_pdf = OUT_DIR / out_file.replace('.png', '.pdf')
    fig.savefig(out_path_pdf, bbox_inches='tight',
                pad_inches=0.1, facecolor='white', backend='pdf')
    print(f"Saved -> {out_path_pdf}  ({len(subset)} tokens)")

    plt.close(fig)

# ── Three plots ───────────────────────────────────────────────────────────────
make_plot(
    plot_tokens,
    title='Dt.Sg, G.Pl, N.Pl — *ŭ-Stamm-Flexion vs. andere Flexion',
    out_file='distribution_u_flexion_all.png',
)

make_plot(
    [t for t in plot_tokens if t['case'] == 'Dt' and t['number'] == 'Sg'],
    title='DtSg — *ŭ-Stamm-Flexion vs. andere Flexion',
    out_file='distribution_u_flexion_dtsg.png',
)

make_plot(
    [t for t in plot_tokens if t['number'] == 'Pl'],
    title='GPl und NPl — *ŭ-Stamm-Flexion vs. andere Flexion',
    out_file='distribution_u_flexion_gpl_npl.png',
)

# ── Lemma rankings ────────────────────────────────────────────────────────────
STEM_LABEL = {
    'o stem masc':  r'\rec{ŏ}-',
    'jo stem masc': r'\rec{jŏ}-',
    'i stem masc':  r'\rec{ĭ}-',
    'ŭ stem':       r'\rec{ŭ}-',
}

# Build lemma -> stem lookup from CSV
lemma_stem_map = {}
with open(CSV_PATH, newline='', encoding='utf-8') as f:
    for row in csv.DictReader(f):
        lemma_stem_map[row['lemma']] = row['stem']

def lemma_stats(subset):
    tally = defaultdict(lambda: {'u': 0, 'total': 0})
    for t in subset:
        tally[t['lemma']]['total'] += 1
        if t['in_csv']:
            tally[t['lemma']]['u'] += 1
    rows = []
    for lemma, d in tally.items():
        rate = d['u'] / d['total'] if d['total'] else 0.0
        stem = lemma_stem_map.get(lemma, '')
        rows.append({'lemma': lemma, 'stem': stem,
                     'stem_label': STEM_LABEL.get(stem, ''),
                     'u_stem': d['u'], 'total': d['total'], 'rate': rate})
    rows_abs = sorted(rows, key=lambda r: (-r['u_stem'], -r['rate'], r['lemma']))
    rows_rel = sorted(rows, key=lambda r: (-r['rate'], -r['u_stem'], r['lemma']))
    abs_rank = {r['lemma']: i + 1 for i, r in enumerate(rows_abs)}
    rel_rank = {r['lemma']: i + 1 for i, r in enumerate(rows_rel)}
    return rows_abs, abs_rank, rel_rank

SLOTS = {
    'all':       plot_tokens,
    'DtSg':      [t for t in plot_tokens if t['case'] == 'Dt' and t['number'] == 'Sg'],
    'GPl_NPl':   [t for t in plot_tokens if t['number'] == 'Pl'],
}

OUT_STATS = Path.home() / 'github/leonidmotz.github.io/suprasliensis-data/window-analysis'
OUT_STATS.mkdir(parents=True, exist_ok=True)

report_lines = []

for slot_label, subset in SLOTS.items():
    total_u     = sum(1 for t in subset if t['in_csv'])
    total_other = sum(1 for t in subset if not t['in_csv'])
    total_all   = len(subset)

    report_lines.append(f"\n{'='*60}")
    report_lines.append(f"Slot: {slot_label}")
    report_lines.append(f"{'='*60}")
    report_lines.append(f"*ŭ-Stamm-Flexion:      {total_u:4d} / {total_all} ({total_u/total_all*100:.1f}%)" if total_all else "no data")
    report_lines.append(f"andere Flexion:        {total_other:4d} / {total_all} ({total_other/total_all*100:.1f}%)" if total_all else "")

    rows_abs, abs_rank, rel_rank = lemma_stats(subset)

    report_lines.append(f"\n{'Lemma':20s}  {'rank_abs':>8s}  {'rank_rel':>8s}  {'u_stem':>6s}  {'total':>6s}  {'rate':>6s}")
    report_lines.append('─' * 62)
    for row in rows_abs:
        report_lines.append(
            f"{row['lemma']:20s}  {abs_rank[row['lemma']]:>8d}  "
            f"{rel_rank[row['lemma']]:>8d}  {row['u_stem']:>6d}  "
            f"{row['total']:>6d}  {row['rate']*100:>5.1f}%"
        )

    # Save CSV
    csv_out = OUT_STATS / f'u_flexion_ranking_{slot_label}.csv'
    with open(csv_out, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['rank_absolute', 'rank_relative',
                                               'lemma', 'stem_label',
                                               'u_stem', 'total', 'rate_pct'])
        writer.writeheader()
        for row in rows_abs:
            writer.writerow({
                'rank_absolute': abs_rank[row['lemma']],
                'rank_relative': rel_rank[row['lemma']],
                'lemma':         row['lemma'],
                'stem_label':    row['stem_label'],
                'u_stem':        row['u_stem'],
                'total':         row['total'],
                'rate_pct':      f"{round(row['rate']*100)} \\%",
            })
    report_lines.append(f"\nCSV -> {csv_out}")

# Print and save report
report = '\n'.join(report_lines)
print(report)
report_path = OUT_STATS / 'u_flexion_rankings.txt'
with open(report_path, 'w', encoding='utf-8') as f:
    f.write(report)
print(f"\nReport -> {report_path}")
