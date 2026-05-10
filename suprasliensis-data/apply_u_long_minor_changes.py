import csv, re, unicodedata

def strip_combining(s):
    return ''.join(c for c in s if not unicodedata.category(c).startswith('M'))

def get_attr(attr, line):
    r = re.search(attr + '="([^"]*)"', line)
    return r.group(1) if r else ''

CASE_CODE = {'Nominative': 'n', 'Accusative': 'a', 'Genitive': 'g',
             'Dative': 'd', 'Instrumental': 'i', 'Locative': 'l', 'Vocative': 'v'}
NUMBER_CODE = {'Singular': 's', 'Dual': 'd', 'Plural': 'p'}

CSV_FILE = '/home/leonid/github/leonidmotz.github.io/suprasliensis-data/csv-tagging-helpers/u_long_minor_changes.csv'
XML_FILE = '/home/leonid/github/leonidmotz.github.io/suprasliensis-data/suprasliensis.xml'

# Load changes keyed by (lemma, birnbaum_folio, form_stripped)
changes = {}
with open(CSV_FILE, encoding='utf-8-sig', newline='') as f:
    for row in csv.DictReader(f):
        lemma      = row['LEMMA'].strip()
        birn_raw   = row['BIRNBAUM FOLIO'].strip()
        # Normalize birnbaum: pad number to 3 digits
        m = re.match(r'^0*(\d+)(r|v)(\d+)$', birn_raw)
        if m:
            birn = str(int(m.group(1))).zfill(3) + m.group(2)
            bline = m.group(3).zfill(2)
        else:
            birn = birn_raw; bline = ''
        form       = strip_combining(row['FORM'].strip())
        case_was   = row['CASE'].strip()
        case_must  = row['CASE MUST BE '].strip()
        st_was     = row['STEMTYPE WAS'].strip()
        st_must    = row['STEMTYPE MUST BE'].strip()
        key = (lemma, birn, bline, form)
        changes[key] = {
            'case_was': case_was,
            'case_must': case_must,
            'st_was': st_was,
            'st_must': st_must
        }

print('Loaded', len(changes), 'changes')

cur_folio = None
cur_line  = None
lines = open(XML_FILE, encoding='utf-8').readlines()
changed = 0

for i, line in enumerate(lines):
    fm = re.search(r'<folio\s+n="([^"]*)"', line)
    lm = re.search(r'<line\s+n="([^"]*)"', line)
    if fm: cur_folio = fm.group(1)
    if lm: cur_line  = lm.group(1)
    if '<token' not in line: continue
    if '\u016b stem' not in line: continue

    lemma  = get_attr('lemma', line)
    bform  = get_attr('bform', line)
    form   = get_attr('form', line)
    display = strip_combining(bform if bform else form)
    cur_st = get_attr('stemtype', line)

    # Normalize folio
    m = re.match(r'^0*(\d+)(r|v)$', cur_folio or '')
    birn = (str(int(m.group(1))).zfill(3) + m.group(2)) if m else ''
    bline = (cur_line or '').zfill(2)

    key = (lemma, birn, bline, display)
    ch = changes.get(key)
    if ch is None:
        continue

    new = line

    # Fix case in morph string if needed
    if ch['case_was'] != ch['case_must']:
        new_case_code = CASE_CODE.get(ch['case_must'], '')
        if new_case_code:
            def fix_morph(m):
                mo = list(m.group(1))
                if len(mo) > 6:
                    mo[6] = new_case_code
                return 'morph="' + ''.join(mo) + '"'
            new = re.sub(r'morph="([^"]*)"', fix_morph, new)

    # Fix stemtype only if it hasn't already been corrected
    if ch['st_must'] and cur_st != ch['st_must']:
        if cur_st:
            new = re.sub(r'stemtype="[^"]*"', 'stemtype="' + ch['st_must'] + '"', new)
        else:
            new = new.replace('/>', 'stemtype="' + ch['st_must'] + '" />')

    if new != line:
        lines[i] = new
        changed += 1

open(XML_FILE, 'w', encoding='utf-8').writelines(lines)
print('Changed:', changed)
