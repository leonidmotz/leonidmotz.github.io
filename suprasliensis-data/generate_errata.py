import csv, re, unicodedata

def strip_combining(s):
    return ''.join(c for c in s if not unicodedata.category(c).startswith('M'))

def get_attr(attr, line):
    r = re.search(attr + '="([^"]*)"', line)
    return r.group(1) if r else ''

NUMBER_MAP = {'s': 'Singular', 'd': 'Dual', 'p': 'Plural'}
CASE_MAP   = {'n': 'Nominative', 'a': 'Accusative', 'g': 'Genitive',
              'd': 'Dative', 'i': 'Instrumental', 'l': 'Locative', 'v': 'Vocative'}

CSV_FILE    = '/home/leonid/github/leonidmotz.github.io/suprasliensis-data/csv-tagging-helpers/u_long_stem_all_new.csv'
XML_FILE    = '/home/leonid/github/leonidmotz.github.io/suprasliensis-data/suprasliensis.xml'
ERRATA_FILE = '/home/leonid/github/leonidmotz.github.io/suprasliensis-data/errata_list.csv'
FOL_FILE    = '/home/leonid/github/leonidmotz.github.io/suprasliensis-data/foliation_guide.csv'

SEV_LOOKUP = {}
with open(FOL_FILE, encoding='utf-8') as f:
    for row in csv.reader(f):
        if len(row) < 3: continue
        birn = row[0].strip(); sev = row[2].strip()
        if birn and sev and sev.isdigit():
            SEV_LOOKUP[birn] = int(sev)

def sev_ref(folio, line):
    m = re.match(r'^0*(\d+)(r|v)$', folio or '')
    if not m: return ''
    page = SEV_LOOKUP.get(m.group(1) + m.group(2))
    ln = int(line.lstrip('0') or '0') if line else ''
    return f'{page}\\textsubscript{{{ln}}}' if page else ''

def birn_display(folio, line):
    m = re.match(r'^0*(\d+)(r|v)$', folio or '')
    return (m.group(1) + m.group(2) + line) if m else ''

changes = []
with open(CSV_FILE, encoding='utf-8-sig', newline='') as f:
    for row in csv.DictReader(f):
        must_be = row['must be'].strip()
        if not must_be: continue
        changes.append({
            'lemma': row['Lemma'],
            'number': row['Number'],
            'case': row['Case'],
            'form': strip_combining(row['Form']),
            'fuit': row['Stemtype'].strip(),
            'recte': must_be
        })

print(f'Loaded {len(changes)} changes')

cur_folio = None
cur_line  = None
tok_idx   = 0
results   = []

with open(XML_FILE, encoding='utf-8') as f:
    for line in f:
        fm = re.search(r'<folio\s+n="([^"]*)"', line)
        lm = re.search(r'<line\s+n="([^"]*)"', line)
        if fm: cur_folio = fm.group(1)
        if lm: cur_line  = lm.group(1)
        if '<token' not in line: continue
        tok_idx += 1
        if '\u016b stem' not in line: continue
        morph = get_attr('morph', line)
        if len(morph) < 7: continue
        num_code = morph[1]; cas_code = morph[6]
        lemma   = get_attr('lemma', line)
        bform   = get_attr('bform', line)
        form    = get_attr('form', line)
        display = strip_combining(bform if bform else form)
        num_label = NUMBER_MAP.get(num_code, '')
        cas_label = CASE_MAP.get(cas_code, '')
        for ch in changes:
            if (ch['lemma'] == lemma and ch['number'] == num_label and
                ch['case'] == cas_label and ch['form'] == display):
                results.append([
                    tok_idx,
                    bform if bform else form,
                    lemma,
                    birn_display(cur_folio, cur_line),
                    sev_ref(cur_folio, cur_line),
                    ch['fuit'],
                    ch['recte']
                ])

print(f'Found {len(results)} tokens')

with open(ERRATA_FILE, 'a', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    for r in results:
        writer.writerow(r)

print('Done — appended to errata_list.csv')
