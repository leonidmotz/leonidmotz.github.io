"""
Codex Suprasliensis — Analogical Rate Heatmaps
Generates one PNG per stem class showing analogical% by case × number slot.
"""

import json, gzip, base64, re, os, sys
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────
DATA_JS   = Path.home() / 'github/leonidmotz.github.io/suprasliensis-data/data.js'
OUT_DIR   = Path.home() / 'github/leonidmotz.github.io/suprasliensis-data/heatmaps-diagrams'
FONT_PATH = '/usr/share/fonts/truetype/charis/CharisSIL-Regular.ttf'
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Font setup ────────────────────────────────────────────────────────────────
if os.path.exists(FONT_PATH):
    fm.fontManager.addfont(FONT_PATH)
    plt.rcParams['font.family'] = 'Charis SIL'
    print(f"Using Charis SIL from {FONT_PATH}")
else:
    # Fallback to best available serif
    for candidate in ['DejaVu Serif', 'Linux Libertine', 'FreeSerif', 'serif']:
        try:
            fm.findfont(fm.FontProperties(family=candidate), fallback_to_default=False)
            plt.rcParams['font.family'] = candidate
            print(f"Charis SIL not found — falling back to: {candidate}")
            break
        except Exception:
            continue

# ── Load data ─────────────────────────────────────────────────────────────────
print(f"Loading {DATA_JS} …")
raw = open(DATA_JS).read()
b64 = re.search(r'`([A-Za-z0-9+/=\n]+)`', raw).group(1).replace('\n', '')
data = json.loads(gzip.decompress(base64.b64decode(b64)))
tokens = data['tokens']
print(f"Loaded {len(tokens):,} tokens")

# ── Decode morph string ───────────────────────────────────────────────────────
# morph is 10 chars, 0-indexed:
#   pos 1 → number  (s=Sg, d=Du, p=Pl)
#   pos 6 → case    (n=N, a=A, g=G, d=Dt, i=I, l=L, v=V)
NUMBER_MAP = {'s': 'Sg', 'd': 'Du', 'p': 'Pl'}
CASE_MAP   = {'n': 'N', 'a': 'A', 'g': 'G', 'd': 'Dt', 'i': 'I', 'l': 'L', 'v': 'V'}

CASES   = ['N', 'A', 'G', 'Dt', 'I', 'L', 'V']
NUMBERS = ['Sg', 'Du', 'Pl']

# ── Stem classes to process (label → stem field value(s)) ────────────────────
# Values match the `s` (stem) field in data.js tokens.
STEM_CLASSES = {
    'o stem masc':   ['o stem masc'],
    'o stem neutr':  ['o stem neutr'],
    'jo stem masc':  ['jo stem masc'],
    'jo stem neutr': ['jo stem neutr'],
    'ŭ stem':        ['ŭ stem'],
    'ū stem':        ['ū stem'],
    'i stem masc':   ['i stem masc'],
    'i stem fem':    ['i stem fem'],
    'tel stem':      ['tel stem'],
    's stem':        ['s stem'],
    'r stems':       ['r stems'],
    't stem':        ['t stem'],
}

# ── Colors ────────────────────────────────────────────────────────────────────
PARCHMENT = '#ffffff'
RUST      = '#8b1a4a'

# ── Title map: stem_label → matplotlib title string
TITLE_MAP = {
    'o stem masc':   '*ŏ-Stämme: Maskulina',
    'o stem neutr':  '*ŏ-Stämme: Neutra',
    'jo stem masc':  '*jŏ-Stämme: Maskulina',
    'jo stem neutr': '*jŏ-Stämme: Neutra',
    'ŭ stem':        '*ŭ-Stämme',
    'ū stem':        '*ū-Stämme',
    'i stem masc':   '*ĭ-Stämme: Maskulina',
    'i stem fem':    '*ĭ-Stämme: Feminina',
    'n stem masc':   '*n-Stämme: Maskulina',
    'n stem neutr':  '*n-Stämme: Neutra',
    's stem':        '*s-Stämme',
    'r stems':       '*r-Stämme',
    'tel stem':      'teľ-Stämme',
}

def make_heatmap(stem_label, stem_values, gender=None):
    """Build and save a heatmap PNG for one stem class."""

    # Filter tokens to this stem class (and optionally by gender at morph pos 5)
    stem_tokens = [
        t for t in tokens
        if t.get('s', '') in stem_values
        and (gender is None or t.get('mo', '')[5:6] == gender)
    ]
    if not stem_tokens:
        print(f"  !! No tokens found for '{stem_label}' — skipping")
        return

    # Build a per-slot tally: total, analogical, tagged
    # tagged = has a stemtype value that is not empty/None
    tally = {
        (case, num): {'total': 0, 'analogical': 0, 'tagged': 0}
        for case in CASES for num in NUMBERS
    }

    for t in stem_tokens:
        mo = t.get('mo', '')
        if len(mo) < 7:
            continue
        num_ch  = mo[1]
        case_ch = mo[6]
        num  = NUMBER_MAP.get(num_ch)
        case = CASE_MAP.get(case_ch)
        if num is None or case is None:
            continue

        slot = (case, num)
        st = t.get('st', '')          # stemtype: 'etymological', 'analogical', 'ambiguous', or ''

        tally[slot]['total'] += 1
        if st:                        # any non-empty stemtype = tagged
            tally[slot]['tagged'] += 1
        if st == 'analogical':
            tally[slot]['analogical'] += 1

    # Build matrices
    val_matrix   = pd.DataFrame(index=CASES, columns=NUMBERS, dtype=float)
    annot_matrix = pd.DataFrame(index=CASES, columns=NUMBERS, dtype=object)
    mask_matrix  = pd.DataFrame(index=CASES, columns=NUMBERS, dtype=bool)

    for case in CASES:
        for num in NUMBERS:
            d = tally[(case, num)]
            total    = d['total']
            tagged   = d['tagged']
            analog   = d['analogical']

            if total == 0 or tagged == 0:
                # No data or entirely untagged
                val_matrix.loc[case, num]   = np.nan
                annot_matrix.loc[case, num] = ''
                mask_matrix.loc[case, num]  = True
            else:
                rate = analog / total        # analogical / ALL tokens
                val_matrix.loc[case, num]   = rate
                pct = int(round(rate * 100))
                annot_matrix.loc[case, num] = f'{pct}%\n{analog}/{total}'
                mask_matrix.loc[case, num]  = False

    # ── Plot ──────────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(5.5, 6.5))
    fig.patch.set_facecolor(PARCHMENT)
    ax.set_facecolor(PARCHMENT)

    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list(
        'parchment_rust', [PARCHMENT, RUST]
    )

    # Draw main heatmap — no seaborn grid lines; we draw all borders manually
    sns.heatmap(
        val_matrix.astype(float),
        ax=ax,
        cmap=cmap,
        vmin=0, vmax=1,
        annot=annot_matrix,
        fmt='',
        mask=mask_matrix,
        linewidths=0,
        cbar_kws={'shrink': 0.7, 'pad': 0.02,
                  'label': 'Analogierate (analogisch / gesamt)'},
        annot_kws={'size': 11, 'va': 'center'},
    )

    # Draw uniform borders and no-data fills for every cell
    for ci, case in enumerate(CASES):
        for ni, num in enumerate(NUMBERS):
            if mask_matrix.loc[case, num]:
                ax.add_patch(plt.Rectangle(
                    (ni, ci), 1, 1,
                    facecolor='white', edgecolor='#b8b0a8',
                    lw=1.2, zorder=2
                ))
                ax.text(
                    ni + 0.5, ci + 0.5, 'keine Daten',
                    ha='center', va='center',
                    fontsize=7, color='#aaaaaa',
                    fontvariant='small-caps',
                )
            else:
                ax.add_patch(plt.Rectangle(
                    (ni, ci), 1, 1,
                    facecolor='none', edgecolor='#b8b0a8',
                    lw=1.2, zorder=2
                ))

    # Colorbar styling
    cbar = ax.collections[0].colorbar
    if cbar is not None:
        cbar.ax.tick_params(labelsize=8)
        cbar.set_label('Analogierate (analogisch / gesamt)', size=8)
        cbar.set_ticks([0, 0.25, 0.5, 0.75, 1.0])
        cbar.set_ticklabels(['0%', '25%', '50%', '75%', '100%'])

    title_str = TITLE_MAP.get(stem_label, stem_label)
    ax.set_title(title_str, fontsize=14, fontweight='bold',
                 pad=12, color='#2a1a0a')
    ax.set_xlabel('Numerus', fontsize=10, labelpad=6)
    ax.set_ylabel('Kasus', fontsize=10, labelpad=6)
    ax.tick_params(axis='both', labelsize=9)
    ax.xaxis.tick_top()
    ax.xaxis.set_label_position('top')

    plt.tight_layout()

    safe_name = stem_label.replace(' ', '_').replace('ŭ', 'u-breve').replace('ū', 'u-macron')
    out_path  = OUT_DIR / f'heatmap_{safe_name}.png'
    fig.savefig(out_path, dpi=300, bbox_inches='tight',
                facecolor=PARCHMENT)
    plt.close(fig)

    tagged_slots = sum(1 for c in CASES for n in NUMBERS if not mask_matrix.loc[c, n])
    print(f"  ✓  {stem_label:20s} — {len(stem_tokens):5,} tokens, {tagged_slots}/21 cells with tagged data → {out_path.name}")

# ── Main ──────────────────────────────────────────────────────────────────────
print(f"\nGenerating heatmaps → {OUT_DIR}\n")
for label, values in STEM_CLASSES.items():
    make_heatmap(label, values)

make_heatmap('n stem masc',  ['n stem'], gender='m')
make_heatmap('n stem neutr', ['n stem'], gender='n')

print("\nDone.")
