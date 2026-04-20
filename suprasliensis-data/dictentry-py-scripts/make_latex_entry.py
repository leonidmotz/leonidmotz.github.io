import sys, re, csv
from collections import defaultdict

NUMBER_MAP = {'s': 'Sg', 'p': 'Pl', 'd': 'Du'}
CASE_MAP   = {'n': 'N', 'a': 'A', 'g': 'G', 'd': 'Dt', 'i': 'I', 'l': 'L', 'v': 'V'}

CASE_ORDER   = ['N', 'A', 'G', 'Dt', 'I', 'L', 'V']
NUMBER_ORDER = ['Sg', 'Du', 'Pl']
SEV_LOOKUP = {}
with open('foliation_guide.csv', encoding='utf-8') as _f:
    for _row in csv.reader(_f):
        if len(_row) < 3: continue
        _birn = _row[0].strip(); _sev = _row[2].strip()
        if _birn and _sev and _sev.isdigit():
            SEV_LOOKUP[_birn] = int(_sev)


def parse_morph(morph):
    if len(morph) < 7: return None, None
    num  = NUMBER_MAP.get(morph[1])
    case = CASE_MAP.get(morph[6])
    return num, case

def bfolio_to_sev(bfolio, bline):
    m = re.match(r'^0*(\d+)(r|v)$', bfolio)
    if not m: return None, None
    page = SEV_LOOKUP.get(m.group(1) + m.group(2))
    return page, int(bline.lstrip('0') or '0')

def birn_display(bfolio, bline):
    m = re.match(r'^0*(\d+)(r|v)$', bfolio)
    return (m.group(1) + m.group(2) + bline) if m else bfolio + bline

def get_attr(line, attr):
    r = re.search(attr + '="([^"]*)"', line)
    return r.group(1) if r else ''

def main():
    if len(sys.argv) < 2: sys.exit(1)
    lemma = sys.argv[1]
    translation = sys.argv[2] if len(sys.argv) > 2 else '???'

    # num -> case -> [(bfolio, bline, form)]
    data = defaultdict(lambda: defaultdict(list))

    import re as _re
    cur_folio = None; cur_line = None
    with open('suprasliensis.xml', encoding='utf-8') as f:
        for line in f:
            fm = _re.search(r'<folio\s+n="([^"]*)"', line)
            lm = _re.search(r'<line\s+n="([^"]*)"', line)
            if fm: cur_folio = fm.group(1)
            if lm: cur_line  = lm.group(1)
            if 'lemma="' + lemma + '"' not in line or 'stemtype="analogical"' not in line:
                continue
            if not cur_folio or not cur_line: continue
            num, case = parse_morph(get_attr(line, 'morph'))
            if num and case:
                bform = get_attr(line, 'bform'); form = bform if bform else get_attr(line, 'form')
                data[num][case].append((cur_folio, cur_line, form))

    if not data:
        print('% No analogical tokens found for lemma "' + lemma + '"')
        return

    for num in data:
        for case in data[num]:
            data[num][case].sort()

    print('%--------- ' + lemma.upper())
    print('\\noindent\\ocsboldword{' + lemma + '}{' + translation + '} \\LEMMALINE')
    print('\\begin{description}')

    for num in NUMBER_ORDER:
        if num not in data: continue
        case_parts = []
        for case in CASE_ORDER:
            if case not in data[num]: continue
            form_groups = defaultdict(list)
            for bfolio, bline, form in data[num][case]:
                form_groups[form].append((bfolio, bline))
            parts = []
            for form, refs in form_groups.items():
                sup = '\\textsuperscript{(' + str(len(refs)) + ')}'
                refs_tex = []
                for bfolio, bline in refs:
                    sp, sl = bfolio_to_sev(bfolio, bline)
                    refs_tex.append('\\mbox{' + birn_display(bfolio, bline) + '/\\SEV{' + str(sp) + '}{' + str(sl) + '}}')
                parts.append('\\ocs{' + form + '}' + sup + ' ' + ' '.join(refs_tex))
            case_parts.append(case + num + ' ' + ' '.join(parts))
        print('    \\item[] ' + ' \\CASEBREAK '.join(case_parts))

    print('\\end{description}')
    print('% ANMERKUNG')
    print('\\ENTRYEND')
    print('%---------')

if __name__ == '__main__':
    main()
