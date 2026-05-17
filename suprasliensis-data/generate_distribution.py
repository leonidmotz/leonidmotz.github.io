"""
Codex Suprasliensis — Token Distribution Timeline
One row per chapter (1–48). Each matching token is a dot placed at its
proportional position within the chapter (index / total_in_chapter - 1).
Blue = analogical, dark grey = everything else (etymological, ambiguous, untagged).
"""

import json, gzip, base64, re, os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
DATA_JS   = Path.home() / 'github/leonidmotz.github.io/suprasliensis-data/data.js'
OUT_DIR   = Path.home() / 'github/leonidmotz.github.io/suprasliensis-data/heatmaps-diagrams'
FONT_PATH = '/usr/share/fonts/truetype/charis/CharisSIL-Regular.ttf'
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Font ──────────────────────────────────────────────────────────────────────
if os.path.exists(FONT_PATH):
    fm.fontManager.addfont(FONT_PATH)
    plt.rcParams['font.family'] = 'Charis SIL'

# ── Load data ─────────────────────────────────────────────────────────────────
print(f"Loading {DATA_JS} ...")
raw = open(DATA_JS).read()
b64 = re.search(r'`([A-Za-z0-9+/=\n]+)`', raw).group(1).replace('\n', '')
data = json.loads(gzip.decompress(base64.b64decode(b64)))
tokens = data['tokens']
print(f"Loaded {len(tokens):,} tokens")

# ── Morph decoding ────────────────────────────────────────────────────────────
NUMBER_MAP = {'s': 'Sg', 'd': 'Du', 'p': 'Pl'}
CASE_MAP   = {'n': 'N', 'a': 'A', 'g': 'G', 'd': 'Dt', 'i': 'I', 'l': 'L', 'v': 'V'}

# ── Configuration ─────────────────────────────────────────────────────────────
CONFIG = {
    'stem':      'ū stem',   # value of `s` field; None = all stems
    'case':      'A',        # N/A/G/Dt/I/L/V; None = all
    'number':    None,       # Sg/Du/Pl; None = all
    'highlight': 'analogical',
    'color_hi':  '#8b1a4a',  # rust red for analogical
    'color_lo':  '#4a4a4a',  # dark grey for everything else
    'title':     '*\u016b-St\u00e4mme: Akkusativ \u2014 Verteilung der Analogiebildungen',
    'out_file':  'distribution_u-macron_stem_accusative.png',

    # Visual tuning
    'dot_size':  40,
    'dot_alpha': 0.7,
    'row_h':     0.6,
    'row_h':     0.6,   # height of each row in data units
    'fig_w':     16,    # inches
    'fig_h':     10,    # inches
    'dpi':       300,
}

# ── Build chapter index ───────────────────────────────────────────────────────
CHAPTERS = list(range(1, 49))
chapter_all = {c: [] for c in CHAPTERS}

for idx, t in enumerate(tokens):
    try:
        c = int(t.get('c', 0))
    except (TypeError, ValueError):
        continue
    if c in chapter_all:
        chapter_all[c].append(idx)

# ── Filter matching tokens ────────────────────────────────────────────────────
def matches(t):
    mo = t.get('mo', '')
    if len(mo) < 7:
        return False
    if CONFIG['stem'] and t.get('s', '') != CONFIG['stem']:
        return False
    if CONFIG['case'] and CASE_MAP.get(mo[6]) != CONFIG['case']:
        return False
    if CONFIG['number'] and NUMBER_MAP.get(mo[1]) != CONFIG['number']:
        return False
    return True

match_set = {idx for idx, t in enumerate(tokens) if matches(t)}
print(f"Matching tokens: {len(match_set):,}")

# ── Compute proportional dot positions per chapter ────────────────────────────
chapter_dots = {}
for c in CHAPTERS:
    all_idx = chapter_all[c]
    n = len(all_idx)
    if n == 0:
        chapter_dots[c] = []
        continue
    dots = []
    for rank, idx in enumerate(all_idx):
        if idx in match_set:
            x = rank / (n - 1) if n > 1 else 0.5
            is_hi = tokens[idx].get('st', '') == CONFIG['highlight']
            dots.append((x, is_hi))
    chapter_dots[c] = dots

# ── Plot ──────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(CONFIG['fig_w'], CONFIG['fig_h']))
fig.patch.set_facecolor('white')
ax.set_facecolor('white')

row_h = CONFIG['row_h']
n_ch  = len(CHAPTERS)
y_mid = {c: -(i * row_h) for i, c in enumerate(CHAPTERS)}

# Faint baseline per chapter
for c in CHAPTERS:
    ax.hlines(y_mid[c], 0, 1, colors='#e0e0e0', linewidths=0.4, zorder=1)

# Dots: non-highlighted first so highlighted sits on top
for is_hi_pass in [False, True]:
    xs, ys = [], []
    for c in CHAPTERS:
        for x, is_hi in chapter_dots[c]:
            if is_hi == is_hi_pass:
                xs.append(x)
                ys.append(y_mid[c])
    color = CONFIG['color_hi'] if is_hi_pass else CONFIG['color_lo']
    ax.scatter(xs, ys,
               s=CONFIG['dot_size'],
               c=color,
               alpha=CONFIG['dot_alpha'],
               linewidths=0,
               zorder=3 if is_hi_pass else 2)

# Chapter labels
for c in CHAPTERS:
    ax.text(-0.012, y_mid[c], str(c),
            ha='right', va='center',
            fontsize=6, color='#555555')

# Axes limits
ax.set_xlim(-0.05, 1.02)
ax.set_ylim(-(n_ch * row_h) - row_h, row_h * 1.5)
ax.axis('off')

# Title
ax.text(0.5, row_h * 1.1, CONFIG['title'],
        ha='center', va='bottom',
        fontsize=10, fontweight='bold', color='#2a1a0a',
        transform=ax.transData)

# Legend
legend_y = -(n_ch * row_h) - row_h * 0.5
ax.scatter([0.0], [legend_y], s=CONFIG['dot_size'],
           c=CONFIG['color_hi'], linewidths=0, zorder=4)
ax.text(0.015, legend_y, 'analogisch',
        ha='left', va='center', fontsize=7, color='#333333')
ax.scatter([0.15], [legend_y], s=CONFIG['dot_size'],
           c=CONFIG['color_lo'], linewidths=0, zorder=4)
ax.text(0.165, legend_y, 'nicht analogisch / ungetaggt',
        ha='left', va='center', fontsize=7, color='#333333')

# Save
out_path = OUT_DIR / CONFIG['out_file']
fig.savefig(out_path, dpi=CONFIG['dpi'], bbox_inches='tight', facecolor='white')
plt.close(fig)
print(f"Saved -> {out_path}")
