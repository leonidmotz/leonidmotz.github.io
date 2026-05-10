import csv, re, unicodedata

def strip_combining(s):
    return ''.join(c for c in s if not unicodedata.category(c).startswith('M'))

def get_attr(attr, line):
    r = re.search(attr + '="([^"]*)"', line)
    return r.group(1) if r else ''

NUMBER_MAP = {'s': 'Singular', 'd': 'Dual', 'p': 'Plural'}
CASE_MAP   = {'n': 'Nominative', 'a': 'Accusative', 'g': 'Genitive',
              'd': 'Dative', 'i': 'Instrumental', 'l': 'Locative', 'v': 'Vocative'}

CSV_FILE = '/home/leonid/github/leonidmotz.github.io/suprasliensis-data/csv-tagging-helpers/u_long_stem_all_new.csv'
XML_FILE = '/home/leonid/github/leonidmotz.github.io/suprasliensis-data/suprasliensis.xml'

updates = {}
with open(CSV_FILE, encoding='utf-8-sig', newline='') as f:
    for row in csv.DictReader(f):
        must_be  = row['must be'].strip()
        stemtype = row['Stemtype'].strip()
        proposed = must_be if must_be else stemtype
        if not proposed:
            continue
        key = (row['Lemma'], row['Number'], row['Case'], strip_combining(row['Form']))
        updates[key] = proposed

print('Loaded', len(updates), 'update rules')

lines = open(XML_FILE, encoding='utf-8').readlines()
changed = 0
skipped = 0

for i, line in enumerate(lines):
    if '<token' not in line:
        continue
    if '\u016b stem' not in line:
        continue
    morph = get_attr('morph', line)
    if len(morph) < 7:
        continue
    num_code = morph[1]
    cas_code = morph[6]
    if num_code not in 'sdp' or cas_code not in 'nagdilv':
        continue
    lemma   = get_attr('lemma', line)
    bform   = get_attr('bform', line)
    form    = get_attr('form', line)
    cur_st  = get_attr('stemtype', line)
    display = bform if bform else form
    key     = (lemma, NUMBER_MAP.get(num_code, ''), CASE_MAP.get(cas_code, ''), strip_combining(display))
    proposed = updates.get(key)
    if proposed is None:
        skipped += 1
        continue
    if cur_st == proposed:
        continue
    if cur_st:
        new = re.sub(r'stemtype="[^"]*"', 'stemtype="' + proposed + '"', line)
    else:
        new = line.replace('/>', 'stemtype="' + proposed + '" />')
    lines[i] = new
    changed += 1

open(XML_FILE, 'w', encoding='utf-8').writelines(lines)
print('Changed:', changed, 'Skipped:', skipped)
