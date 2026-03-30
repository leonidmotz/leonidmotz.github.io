import gzip, json, base64, re
from xml.etree import ElementTree as ET

tree = ET.parse('suprasliensis.xml')
root = tree.getroot()

tokens = []
for folio in root.findall('folio'):
    fo = folio.get('n')
    for line in folio.findall('line'):
        ln = line.get('n')
        for tok in line.findall('token'):
            t = {}
            t['f']  = tok.get('form')
            t['fo'] = fo
            t['ln'] = ln
            if tok.get('bform'):    t['bf']  = tok.get('bform')
            if tok.get('lemma'):    t['l']   = tok.get('lemma')
            if tok.get('pos'):      t['p']   = tok.get('pos')
            if tok.get('morph'):    t['mo']  = tok.get('morph')
            if tok.get('rel'):      t['r']   = tok.get('rel')
            if tok.get('stem'):     t['s']   = tok.get('stem')
            if tok.get('stemtype'): t['st']  = tok.get('stemtype')
            if tok.get('info'):     t['i']   = tok.get('info')
            if tok.get('after'):    t['a']   = tok.get('after')
            if tok.get('book'):     t['bk']  = int(tok.get('book'))
            if tok.get('chapter'):  t['c']   = int(tok.get('chapter'))
            if tok.get('bfolio'):   t['bfo'] = tok.get('bfolio')
            if tok.get('bline'):    t['bln'] = tok.get('bline')
            tokens.append(t)

# Read existing data.js to preserve META, POS_LEGEND etc.
with open('data.js') as f:
    existing = f.read()

# Re-encode
data = {'tokens': tokens, 'meta': {}}
compressed = gzip.compress(json.dumps(data, ensure_ascii=False).encode('utf-8'))
b64 = base64.b64encode(compressed).decode('ascii')

# Replace only the B64 line
new_datajs = re.sub(r'const B64 = `[^`]+`', f'const B64 = `{b64}`', existing)
with open('data.js', 'w') as f:
    f.write(new_datajs)

print(f"Done! {len(tokens)} tokens re-encoded to data.js")
