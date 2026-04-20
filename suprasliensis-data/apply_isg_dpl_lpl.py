import csv, re, unicodedata

def strip_combining(s):
    return ''.join(c for c in s if not unicodedata.category(c).startswith('M'))

updates = {}
with open('i_stem_masc_isg_dpl_lpl.csv', encoding='utf-8-sig', newline='') as f:
    for row in csv.DictReader(f):
        stemtype = row['Stemtype'].strip()
        if not stemtype: continue
        key = (row['Lemma'], row['Number'], row['Case'], strip_combining(row['Form']))
        updates[key] = stemtype

print(f"Loaded {len(updates)} update rules")

NUMBER_MAP = {'s': 'Singular', 'd': 'Dual', 'p': 'Plural'}
CASE_MAP   = {'n': 'Nominative', 'a': 'Accusative', 'g': 'Genitive',
              'd': 'Dative', 'i': 'Instrumental', 'l': 'Locative', 'v': 'Vocative'}
target_slots = {('s','i'), ('p','d'), ('p','l')}

lines = open('suprasliensis.xml', encoding='utf-8').readlines()
changed = 0
skipped = 0

for i, line in enumerate(lines):
    if '<token' not in line: continue
    if 'stem="i stem masc"' not in line: continue
    morph = re.search(r'morph="([^"]*)"', line)
    if not morph: continue
    morph = morph.group(1)
    if len(morph) < 7: continue
    num_code = morph[1]; cas_code = morph[6]
    if (num_code, cas_code) not in target_slots: continue

    def get(attr):
        r = re.search(attr + '="([^"]*)"', line)
        return r.group(1) if r else ''

    lemma = get('lemma'); bform = get('bform'); form = get('form'); cur_st = get('stemtype')
    display = bform if bform else form
    key = (lemma, NUMBER_MAP.get(num_code,''), CASE_MAP.get(cas_code,''), strip_combining(display))
    proposed = updates.get(key)

    if proposed is None:
        skipped += 1; continue
    if cur_st == proposed:
        continue

    new = line
    if cur_st:
        new = re.sub(r'stemtype="[^"]*"', f'stemtype="{proposed}"', new)
    else:
        new = new.replace('/>', f'stemtype="{proposed}" />')
    lines[i] = new
    changed += 1

open('suprasliensis.xml', 'w', encoding='utf-8').writelines(lines)
print(f"Changed: {changed}, Skipped: {skipped}")
