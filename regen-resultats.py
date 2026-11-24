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

NL = chr(10)
MOIS_FR = ['janvier','février','mars','avril','mai','juin',
           'juillet','août','septembre','octobre','novembre','décembre']
groups = {}
for row in rows:
    date = row.split('<td>')[1][:10]
    groups.setdefault(date[:7], []).append(row)

sections = []
for i, (ym, items) in enumerate(groups.items()):
    y, mm = ym.split('-')
    label = MOIS_FR[int(mm)-1][0].upper() + MOIS_FR[int(mm)-1][1:]
    open_attr = ' open' if i == 0 else ''
    n_m = len(items)
    body = NL.join(items)
    arr_word = 'arrivées' if n_m > 1 else 'arrivée'
    sections.append(
        '<details' + open_attr + '><summary>' + label + ' ' + y + ' · ' + str(n_m) + ' ' + arr_word + '</summary>' +
        '<table><thead><tr><th>Date</th><th>Hippodrome</th><th>Course</th><th>Discipline</th>'
        '<th>Distance</th><th>Arrivée</th></tr></thead><tbody>' + NL + body + NL + '</tbody></table></details>')

sections_html = NL.join(sections)

n = len(rows)
rs = os.path.join(REPO, 'resultats.html')
c = io.open(rs, encoding='utf-8').read()

new_meta = f'<p class="meta">Arrivées officielles des {n} Quintés+ pronostiqués. Sources : PMU.fr</p>'
c2, k = re.subn(r'<p class="meta">Arrivées officielles des \d+ Quintés\+ pronostiqués\. Sources : PMU\.fr</p>',
                lambda m: new_meta, c, count=1)
if k != 1:
    sys.exit('ECHEC : meta "Arrivees officielles" introuvable')

BEGIN = '<!-- RESULTS:BEGIN -->'
END = '<!-- RESULTS:END -->'
b = c2.find(BEGIN); e2 = c2.find(END)
if b > 0 and e2 > b:
    b2 = b + len(BEGIN)
    c2 = c2[:b2] + NL + sections_html + NL + c2[e2:]
else:
    s0 = c2.find('<div class="card"><table>')
    e0 = c2.find('</tbody></table></div>', s0)
    if s0 < 0 or e0 < 0:
        sys.exit('ECHEC : tableau resultats introuvable')
    e0 += len('</tbody></table></div>')
    c2 = c2[:s0] + '<div class="card">' + BEGIN + NL + sections_html + NL + END + '</div>' + c2[e0:]

# CSS repliables (une seule fois)
if 'details{margin' not in c2:
    idx = c2.find('</style>')
    if idx > 0:
        css = ('details{margin:.75rem 0;border:1px solid #e2e8f0;border-radius:10px;background:#fff;overflow:hidden}'
               'summary{cursor:pointer;padding:.85rem 1rem;font-weight:700;background:#f1f5f9;list-style:none}'
               "summary::after{content:'›';color:#16a34a;display:inline-block;font-size:1.1em;transition:transform .15s}"
               'details[open]>summary::after{transform:rotate(90deg)}'
               'details[open]>summary{background:#dcfce7;color:#15803d}'
               'details table{margin:0}details td,details th{font-size:.85rem}')
        c2 = c2[:idx] + css + c2[idx:]

io.open(rs, 'w', encoding='utf-8', newline='').write(c2)
print(f'resultats.html : {n} lignes, meta mise a jour')
