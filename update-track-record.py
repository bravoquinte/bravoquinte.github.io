# -*- coding: utf-8 -*-
"""
Met a jour predictions-ledger.json (ajout des courses du 19 au 26 octobre)
puis regenere track-record.html (tableau + 4 statistiques + meta descriptions).

Definition des metriques (identique a l'historique du site) :
  - selection = 8 chevaux , top5 = 5 premiers de l arrivee
  - presence = |selection(8) inter top5|        -> colonne "Presence n/5"
  - moy selection = moyenne de presence
  - top5_avg    = |selection[:5] inter top5|    -> "nos 5 premiers"
"""
import json, re, sys
from datetime import datetime, timezone

sys.stdout.reconfigure(encoding='utf-8')

LEDGER = 'predictions-ledger.json'
TRACK = 'track-record.html'

# ---------------------------------------------------------------- 1. ledger
d = json.load(open(LEDGER, encoding='utf-8'))

nouvelles = [
    dict(date='2026-10-19', hippo='Deauville', course='Prix de la Foret de Lyons',
         discipline='Plat PSF', dist='1900m', slug='pronostic-quinte-deauville-19-octobre',
         selection=[2, 5, 10, 1, 9, 4, 13, 3], base=2, arrivee=[4, 2, 6, 1, 13]),
    dict(date='2026-10-22', hippo='Auteuil', course='Prix Andre Adele',
         discipline='Galop Obstacle', dist='3600m', slug='pronostic-quinte-auteuil-22-octobre',
         selection=[13, 16, 6, 15, 7, 5, 9, 1], base=13, arrivee=[12, 5, 9, 7, 3]),
    dict(date='2026-10-23', hippo='Paris-Vincennes', course='Prix Orionis',
         discipline='Trot Attele', dist='2850m', slug='pronostic-quinte-vincennes-23-octobre',
         selection=[15, 10, 11, 7, 8, 17, 13, 9], base=15, arrivee=[15, 12, 6, 14, 16]),
    dict(date='2026-10-24', hippo='Compiegne', course='Prix de Beaune',
         discipline='Galop Obstacle', dist='3600m', slug='pronostic-quinte-compiegne-24-octobre',
         selection=[4, 7, 9, 8, 2, 6, 10, 1], base=4, arrivee=[9, 4, 7, 13, 11]),
    dict(date='2026-10-25', hippo='Saint-Cloud', course="Prix de l'Elevage",
         discipline='Galop Plat', dist='2500m', slug='pronostic-quinte-saint-cloud-25-octobre',
         selection=[2, 15, 8, 13, 7, 11, 9, 3], base=2, arrivee=[9, 13, 10, 3, 4]),
    dict(date='2026-10-26', hippo='Chantilly', course='Prix de la Route des Princes',
         discipline='Galop PSF', dist='1600m', slug='pronostic-quinte-chantilly-26-octobre',
         selection=[3, 13, 10, 12, 6, 5, 4, 7], base=3, arrivee=None),
]

def norm_arr(v):
    """Normalise une arrivee en liste d'entiers (5 premiers).
    Formats rencontres : [13, 8, ...] / "13-8-..." / [[13, 'NOM'], ...]"""
    if not v:
        return None
    out = []
    if isinstance(v, list):
        for x in v:
            if isinstance(x, list):
                x = x[0]
            m = re.search(r'\d+', str(x))
            if m:
                out.append(int(m.group(0)))
    else:
        out = [int(x) for x in re.findall(r'\d+', str(v))]
    return out[:5]

# normalise a la volee (sans ecraser les noms de chevaux du ledger)
def get_arr(p):
    return norm_arr(p.get('arrivee') or p.get('resultat'))

preds = d['predictions']

exist = {p['date'] for p in preds}
ajoutees = 0
for n in nouvelles:
    if n['date'] in exist:
        continue
    top5 = n['arrivee'][:5] if n['arrivee'] else []
    pres = len(set(n['selection']) & set(top5)) if top5 else 0
    p = {
        'date': n['date'], 'hippo': n['hippo'], 'course': n['course'],
        'discipline': n['discipline'], 'dist': n['dist'], 'slug': n['slug'],
        'selection': n['selection'], 'base': n['base'],
        'resultat': n['arrivee'], 'arrivee': n['arrivee'],
        'metrics': {
            'top5': top5,
            'selection_in_top5': pres,
            'base_in_top5': (n['base'] in top5) if top5 else None,
            'exact_order': False,
        },
        'statut': 'valide' if n['arrivee'] else 'en_attente',
    }
    preds.append(p)
    ajoutees += 1

preds.sort(key=lambda p: p['date'])
d['predictions'] = preds

# ---------------------------------------------------------------- 2. stats
val = [p for p in preds if get_arr(p) and p.get('statut') != 'en_attente']
tot = len(val)


def pres_of(p):
    arr = get_arr(p)[:5]
    return len(set(p['selection']) & set(arr))


base_ok = sum(1 for p in val if p['base'] in get_arr(p)[:5])
base_win = sum(1 for p in val if p['base'] == get_arr(p)[0])
pres_sum = sum(pres_of(p) for p in val)
moy = pres_sum / tot
win_in = sum(1 for p in val if get_arr(p)[0] in p['selection'])
ge3 = sum(1 for p in val if pres_of(p) >= 3)
top5_sum = sum(len(set(p['selection'][:5]) & set(get_arr(p)[:5])) for p in val)
top5_avg = top5_sum / tot

d['stats'] = {
    'total_validated': tot,
    'base_in_top5_rate': f'{base_ok}/{tot}',
    'base_wins_rate': f'{base_win}/{tot}',
    'selection_avg_in_top5': f'{moy:.1f}/5',
    'winner_in_selection_rate': f'{win_in}/{tot}',
    'top3_in_top5_rate': f'{ge3}/{tot}',
    'desordre_rate': f'0/{tot}',
    'top5_avg_in_top5': f'{top5_avg:.1f}/5',
}
d['generated'] = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.000Z')

print(f'courses ajoutees : {ajoutees}   total validees : {tot}')
print('stats :', json.dumps(d['stats'], ensure_ascii=False))

json.dump(d, open(LEDGER, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

# ---------------------------------------------------------------- 3. html
html = open(TRACK, encoding='utf-8').read()

# 3a. stats cards
cards = [
    (f"{base_ok}/{tot}", 'Base dans le top 5'),
    (f'{moy:.1f}/5', 'Sélection dans le top 5 (moy.)'),
    (f'{win_in}/{tot}', 'Gagnant dans notre sélection'),
    (f'{ge3}/{tot}', '3 chevaux ou + dans le top 5'),
]
for val_txt, label in cards:
    html = re.sub(
        r'(<p class="stat-value">)[^<]*(</p>\s*<p class="stat-label">' + re.escape(label) + r')',
        r'\g<1>' + val_txt + r'\g<2>', html, count=1)

# 3b. lignes du tableau
def ligne(p):
    d8, arr = p['date'], get_arr(p)
    sel5 = ', '.join(str(x) for x in p['selection'][:5])
    if not arr:
        return (f'<tr><td>{d8}</td>'
                f'<td><a href="https://bravoquinte.github.io/{p["slug"]}.html">{p["hippo"]}</a></td>'
                f'<td>{p["course"]}</td>'
                f'<td><strong>{p["base"]}</strong> <span class="wait">&#8230;</span></td>'
                f'<td>{sel5}</td><td>&#8212;</td><td><strong>&#8212;</strong></td>'
                f'<td><span class="badge badge-wait">En attente</span></td></tr>')
    top5 = arr[:5]
    pres = len(set(p['selection']) & set(top5))
    ok = p['base'] in top5
    mark = '<span class="ok">&#10003;</span>' if ok else '<span class="miss">&#10007;</span>'
    return (f'<tr><td>{d8}</td>'
            f'<td><a href="https://bravoquinte.github.io/{p["slug"]}.html">{p["hippo"]}</a></td>'
            f'<td>{p["course"]}</td>'
            f'<td><strong>{p["base"]}</strong> {mark}</td>'
            f'<td>{sel5}</td><td>{", ".join(str(x) for x in top5)}</td>'
            f'<td><strong>{pres}</strong>/5</td>'
            f'<td><span class="badge badge-ok">Validé</span></td></tr>')

rows = '\n'.join(ligne(p) for p in sorted(preds, key=lambda p: p['date'], reverse=True))
html = re.sub(r'(<tbody>).*?(</tbody>)', lambda m: m.group(1) + '\n' + rows + '\n' + m.group(2),
              html, count=1, flags=re.S)

# 3c. meta descriptions
desc = (f'Statistiques publiques : {base_ok}/{tot} base dans le top 5, '
        f'{top5_avg:.1f}/5 nos 5 premiers dans le top 5.')
html = re.sub(r'(<meta name="description" content=")[^"]*(">)', r'\g<1>' + desc + r'\g<2>', html, count=1)
html = re.sub(r'(<meta property="og:description" content=")[^"]*("/>)', r'\g<1>' + desc + r'\g<2>', html, count=1)
html = re.sub(r'(<meta name="twitter:description" content=")[^"]*("/>)', r'\g<1>' + desc + r'\g<2>', html, count=1)

open(TRACK, 'w', encoding='utf-8').write(html)
print('track-record.html regenere')
print('meta:', desc)
