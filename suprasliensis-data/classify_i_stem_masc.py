#!/usr/bin/env python3
"""
Classifier for i stem masc tokens in suprasliensis.xml.
Classifies each token as analogical, etymological, or ambiguous
based on its ending in the given Number+Case slot.

Usage:
  python3 classify_i_stem_masc.py            # apply changes + write preview CSV
  python3 classify_i_stem_masc.py --dry-run  # preview only, no XML changes
"""

import sys, re, csv, unicodedata
from collections import defaultdict

RULES = {
    # Singular
    ('s','a'): {'ь': 'ambiguous'},
    ('s','g'): {'а': 'analogical', 'ꙗ': 'analogical', 'ѣ': 'analogical',
                'и': 'etymological', 'ї': 'etymological'},
    ('s','d'): {'еви': 'analogical', 'оу': 'analogical', 'ю': 'analogical', 'ꙋ': 'analogical',
                'и': 'etymological', 'ї': 'etymological'},
    ('s','i'): {'eмь': 'ambiguous', 'eмъ': 'ambiguous',
                'ьмь': 'etymological', 'ьмъ': 'etymological'},
    ('s','l'): {'и': 'ambiguous', 'ї': 'ambiguous'},
    ('s','n'): {'ь': 'ambiguous'},
    ('s','v'): {'оу': 'analogical', 'ю': 'analogical', 'ꙋ': 'analogical',
                'и': 'etymological', 'ї': 'etymological'},
    # Dual
    ('d','n'): {'а': 'analogical', 'ꙗ': 'analogical',
                'и': 'etymological', 'ї': 'etymological'},
    ('d','a'): {'а': 'analogical', 'ꙗ': 'analogical',
                'и': 'etymological'},
    ('d','g'): {'оу': 'analogical', 'ю': 'analogical', 'ꙋ': 'analogical',
                'иоу': 'etymological', 'ию': 'etymological',
                'ьоу': 'etymological', 'ью': 'etymological',
                'їоу': 'etymological', 'їю': 'etymological'},
    ('d','d'): {'ема': 'analogical',
                'ьма': 'etymological', 'ма': 'etymological'},
    ('d','i'): {'ема': 'analogical',
                'ьма': 'etymological', 'ма': 'etymological'},
    ('d','l'): {'оу': 'analogical', 'ю': 'analogical', 'ꙋ': 'analogical',
                'иоу': 'etymological', 'ию': 'etymological',
                'ьоу': 'etymological', 'ью': 'etymological',
                'їоу': 'etymological', 'їю': 'etymological'},
    ('d','v'): {'а': 'analogical', 'ꙗ': 'analogical',
                'и': 'etymological', 'ї': 'etymological'},
    # Plural
    ('p','n'): {'и': 'analogical', 'еве': 'analogical',
                'иѥ': 'etymological', 'їѥ': 'etymological', 'ьѥ': 'etymological'},
    ('p','a'): {'ѧ': 'analogical', 'ѩ': 'analogical', 'ꙙ': 'analogical',
                'и': 'etymological', 'ї': 'etymological'},
    ('p','g'): {'ь': 'analogical', 'евъ': 'analogical',
                'ьи': 'etymological', 'ии': 'etymological', 'иї': 'etymological'},
    ('p','d'): {'eмъ': 'ambiguous',
                'ьмъ': 'etymological'},
    ('p','i'): {'и': 'analogical', 'ї': 'analogical',
                'ьми': 'etymological'},
    ('p','l'): {'ихъ': 'analogical', 'їхъ': 'analogical',
                'ьхъ': 'etymological', 'ехъ': 'etymological'},
    ('p','v'): {'и': 'analogical', 'ї': 'analogical',
                'иѥ': 'etymological', 'ьѥ': 'etymological'},
}

NUMBER_MAP = {'s': 'Singular', 'd': 'Dual', 'p': 'Plural'}
CASE_MAP   = {'n': 'Nominative', 'a': 'Accusative', 'g': 'Genitive',
              'd': 'Dative', 'i': 'Instrumental', 'l': 'Locative', 'v': 'Vocative'}

def strip_combining(s):
    """Remove all Unicode combining characters (superscripts, diacritics)."""
    return ''.join(c for c in s if not unicodedata.category(c).startswith('M'))

def classify(form, bform, num_code, cas_code):
    rules = RULES.get((num_code, cas_code), {})
    if not rules:
        return None
    f = strip_combining(bform if bform else form)
    for ending in sorted(rules.keys(), key=len, reverse=True):
        if f.endswith(ending):
            return rules[ending]
    return None

def get_attr(line, attr):
    r = re.search(attr + '="([^"]*)"', line)
    return r.group(1) if r else ''

def main():
    dry_run = '--dry-run' in sys.argv
    csv_out = 'i_stem_masc_preview.csv'

    lines = open('suprasliensis.xml', encoding='utf-8').readlines()
    stats = defaultdict(int)
    changed = 0

    with open(csv_out, 'w', encoding='utf-8', newline='') as csvf:
        writer = csv.writer(csvf)
        writer.writerow(['Lemma', 'Number', 'Case', 'Form', 'Current Status', 'Proposed Status', 'Action'])

        for i, line in enumerate(lines):
            if '<token' not in line: continue
            if 'stem="i stem masc"' not in line: continue

            morph = get_attr(line, 'morph')
            if len(morph) < 7: continue
            num_code = morph[1]
            cas_code = morph[6]
            if num_code not in 'sdp' or cas_code not in 'nagdilv': continue

            form   = get_attr(line, 'form')
            bform  = get_attr(line, 'bform')
            lemma  = get_attr(line, 'lemma')
            cur_st = get_attr(line, 'stemtype')
            display = bform if bform else form

            proposed = classify(form, bform, num_code, cas_code)

            if proposed is None:
                action = 'UNMATCHED'
                stats['unmatched'] += 1
            elif cur_st == proposed:
                action = 'unchanged'
                stats['unchanged'] += 1
            elif not cur_st:
                action = 'SET'
                stats[proposed] += 1
                changed += 1
            else:
                action = 'CHANGE'
                stats[proposed] += 1
                changed += 1

            writer.writerow([
                lemma,
                NUMBER_MAP.get(num_code, num_code),
                CASE_MAP.get(cas_code, cas_code),
                display,
                cur_st,
                proposed or '',
                action
            ])

            if not dry_run and action in ('SET', 'CHANGE'):
                if cur_st:
                    lines[i] = re.sub(r'stemtype="[^"]*"', f'stemtype="{proposed}"', line)
                else:
                    lines[i] = line.replace('/>', f'stemtype="{proposed}" />')

    if not dry_run and changed:
        open('suprasliensis.xml', 'w', encoding='utf-8').writelines(lines)
        print(f"XML updated.")

    print(f"Preview written to {csv_out}")
    print(f"\nSummary:")
    for k, v in sorted(stats.items()):
        print(f"  {k}: {v}")
    print(f"  total changes: {changed}")

if __name__ == '__main__':
    main()
