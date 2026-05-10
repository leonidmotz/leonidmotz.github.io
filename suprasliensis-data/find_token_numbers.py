import csv, re, unicodedata

def strip_combining(s):
    return ''.join(c for c in s if not unicodedata.category(c).startswith('M'))

def get_attr(attr, line):
    r = re.search(attr + '="([^"]*)"', line)
    return r.group(1) if r else ''

def parse_birn(s):
    m = re.match(r'^0*(\d+)(r|v)(\d+)$', s.strip())
    if m:
        folio = str(int(m.group(1))).zfill(3) + m.group(2)
        line  = m.group(3).zfill(2)
        return folio, line
    return None, None

CSV_FILE = '/home/leonid/github/leonidmotz.github.io/suprasliensis-data/csv-tagging-helpers/u_long_minor_changes.csv'
XML_FILE = '/home/leonid/github/leonidmotz.github.io/suprasliensis-data/suprasliensis.xml'

changes = []
with open(CSV_FILE, encoding='utf-8-sig', newline='') as f:
    for row in csv.DictReader(f):
        folio, line = parse_birn(row['BIRNBAUM FOLIO'])
        changes.append({
            'lemma': row['LEMMA'].strip(),
            'folio': folio,
            'line': line,
            'form': strip_combining(row['FORM'].strip()),
            'case_was': row['CASE'].strip(),
            'case_must': row['CASE MUST BE '].strip(),
            'birn_raw': row['BIRNBAUM FOLIO'].strip()
        })

cur_folio = None
cur_line  = None
tok_idx   = 0
found     = 0

with open(XML_FILE, encoding='utf-8') as f:
    for xmlline in f:
        fm = re.search(r'<folio\s+n="([^"]*)"', xmlline)
        lm = re.search(r'<line\s+n="([^"]*)"', xmlline)
        if fm: cur_folio = fm.group(1)
        if lm: cur_line  = lm.group(1)
        if '<token' not in xmlline: continue
        tok_idx += 1

        lemma   = get_attr('lemma', xmlline)
        bform   = get_attr('bform', xmlline)
        form    = get_attr('form', xmlline)
        display = strip_combining(bform if bform else form)

        for ch in changes:
            if (ch['lemma'] == lemma and
                ch['folio'] == cur_folio and
                ch['line']  == cur_line and
                ch['form']  == display):
                print(f"{tok_idx}\t{bform if bform else form}\t{lemma}\t{ch['birn_raw']}\t{ch['case_was']}\t{ch['case_must']}")
                found += 1

print(f"\nFound {found} of {len(changes)} tokens")
