#!/usr/bin/env python3
"""Regenere resultats.html a partir du bloc RESULTATS de index.html."""
import io, os, re, sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
REPO = os.path.dirname(os.path.abspath(__file__))

idx = io.open(os.path.join(REPO, 'index.html'), encoding='utf-8').read()
blk = re.search(r'var RESULTATS\s*=\s*\[(.*?)\n\];', idx, re.S)
if not blk:
    sys.exit('ECHEC : bloc RESULTATS introuvable dans index.html')

body = blk.group(1)
entries = re.findall(
    r'\{date:"(?P<date>[^"]+)",hippo:"(?P<hippo>[^"]+)",course:"(?P<course>[^"]+)",'
    r'discipline:"(?P<discipline>[^"]+)",dist:"(?P<dist>[^"]+)",'
    r'arrivee:\[(?P<arr>.*?)\],rapports:', body, re.S)
if not entries:
    sys.exit('ECHEC : aucune entree parsee dans RESULTATS')

rows = []
for m in re.finditer(
        r'\{date:"(?P<date>[^"]+)",hippo:"(?P<hippo>[^"]+)",course:"(?P<course>[^"]+)",'
        r'discipline:"(?P<discipline>[^"]+)",dist:"(?P<dist>[^"]+)",'
        r'arrivee:\[(?P<arr>.*?)\],rapports:', body, re.S):
    e = m.groupdict()
    cheg = re.findall(r'\{n:(\d+),nom:"([^"]*)"\}', e['arr'])
    arr = ' - '.join(f'{n}. {nom}' for n, nom in cheg)
    rows.append(f'<tr><td>{e["date"]}</td><td>{e["hippo"]}</td><td>{e["course"]}</td>'
                f'<td>{e["discipline"]}</td><td>{e["dist"]}</td><td>{arr}</td></tr>')

n = len(rows)
rs = os.path.join(REPO, 'resultats.html')
c = io.open(rs, encoding='utf-8').read()

new_meta = f'<p class="meta">Arrivées officielles des {n} Quintés+ pronostiqués. Sources : PMU.fr</p>'
c2, k = re.subn(r'<p class="meta">Arrivées officielles des \d+ Quintés\+ pronostiqués\. Sources : PMU\.fr</p>',
                lambda m: new_meta, c, count=1)
if k != 1:
    sys.exit('ECHEC : meta "Arrivees officielles" introuvable')

c2, k = re.subn(r'(<tbody>\n)(.*?)(\n</tbody></table>)',
                lambda m: m.group(1) + '\n'.join(rows) + m.group(3), c2, count=1, flags=re.S)
if k != 1:
    sys.exit('ECHEC : tbody introuvable')

io.open(rs, 'w', encoding='utf-8', newline='').write(c2)
print(f'resultats.html : {n} lignes, meta mise a jour')
