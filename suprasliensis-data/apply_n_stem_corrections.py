import csv, re, unicodedata

def strip_combining(s):
    return ''.join(c for c in s if not unicodedata.category(c).startswith('M'))

def normalize_status(s):
    s = s.strip()
    if s == 'ambiguos': return 'ambiguous'
    return s

# Key: (folio, line, lemma, stripped_form) -> new stemtype
updates = {}
with open('csv-tagging-helpers/n_stem_all.csv', encoding='utf-8-sig', newline='') as f:
    for row in csv.DictReader(f):
        proposed = normalize_status(row['New Stemtype'])
        if not proposed: continue
        key = (
            row['Folio'].strip(),
            row['Line'].strip(),
            row['Lemma'].strip(),
            strip_combining(row['Form'].strip()),
        )
        updates[key] = proposed

print(f"Loaded {len(updates)} update rules from CSV")

lines = open('suprasliensis.xml', encoding='utf-8').readlines()
changed = 0
skipped = 0
current_folio = ''
current_line  = ''

for i, line in enumerate(lines):
    folio_m = re.search(r'<folio\s[^>]*\bn="([^"]*)"', line)
    if folio_m:
        current_folio = folio_m.group(1)
        continue
    line_m = re.search(r'<line\s[^>]*\bn="([^"]*)"', line)
    if line_m:
        current_line = line_m.group(1)
        continue
    if '<token' not in line or 'stem="n stem"' not in line:
        continue

    def get(attr):
        r = re.search(attr + r'="([^"]*)"', line)
        return r.group(1) if r else ''

    lemma  = get('lemma')
    bform  = get('bform')
    form   = get('form')
    cur_st = get('stemtype')
    display = bform if bform else form

    key = (current_folio, current_line, lemma, strip_combining(display))
    proposed = updates.get(key)

    if proposed is None:
        skipped += 1
        continue
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
print(f"Changed: {changed}, Skipped (no rule): {skipped}")
