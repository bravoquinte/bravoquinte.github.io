"""Met a jour les KPI de presse.html depuis predictions-ledger.json.

Appele par regen-all.py. Peut aussi tourne seul : python update-presse.py
"""
import io, os, re, json

MOIS = ['janvier', 'f\u00e9vrier', 'mars', 'avril', 'mai', 'juin', 'juillet',
        'ao\u00fbt', 'septembre', 'octobre', 'novembre', 'd\u00e9cembre']

import os as _os
REPO = _os.path.dirname(_os.path.abspath(__file__))



def update(repo=REPO):
    L = json.load(io.open(os.path.join(repo, 'predictions-ledger.json'), encoding='utf-8'))
    preds = L['predictions']
    val = [p for p in preds if p.get('metrics')]

    n_val = len(val)
    n_tot = len(preds)
    bw = sum(1 for p in val if p['base'] == p['metrics']['top5'][0])
    b5 = sum(1 for p in val if p['metrics']['base_in_top5'])

    kpi = (
        '<!-- KPI:START -->\n'
        '<div class="kpi">\n'
        f'<div><p class="v">{n_tot}</p><p class="l">courses analys\u00e9es, {n_val} r\u00e9sultats publi\u00e9s</p></div>\n'
        f'<div><p class="v">{bw}</p><p class="l">bases gagnantes sur {n_val} courses</p></div>\n'
        f'<div><p class="v">{b5}</p><p class="l">bases plac\u00e9es dans les 5 premiers, sur {n_val} courses</p></div>\n'
        '<div><p class="v">0</p><p class="l">pronostic corrig\u00e9 apr\u00e8s r\u00e9sultat</p></div>\n'
        '</div>\n'
        '<!-- KPI:END -->'
    )

    # controle de coherence : les stats du ledger doivent correspondre
    st = L['stats']
    erreurs = []
    if st.get('base_wins_rate') != f'{bw}/{n_val}':
        erreurs.append(f"base_wins_rate={st.get('base_wins_rate')} mais {bw}/{n_val}")
    if st.get('base_in_top5_rate') != f'{b5}/{n_val}':
        erreurs.append(f"base_in_top5_rate={st.get('base_in_top5_rate')} mais {b5}/{n_val}")

    d = max(p['date'] for p in preds)
    mois = f'{MOIS[int(d[5:7]) - 1]} {d[:4]}'

    pp = os.path.join(repo, 'presse.html')
    c = io.open(pp, encoding='utf-8').read()
    c2 = re.sub(r'<!-- KPI:START -->.*?<!-- KPI:END -->', lambda _: kpi, c, flags=re.S)
    # la date doit matcher que le marqueur soit present (1er run) ou non (runs suivants)
    DATE_RE = r'Derni\u00e8re mise \u00e0 jour : (?:UPDATED:)?(?:<!--.*?-->)?[^.<]*\.'
    avant = re.search(DATE_RE, c)
    c2 = re.sub(DATE_RE, f'Derni\u00e8re mise \u00e0 jour : {mois}.', c2)
    # ne signaler que si la date n'a pas ete trouvee, pas si le fichier est deja a jour
    if not avant:
        print('  ATTENTION : motif de date introuvable dans presse.html')
    io.open(pp, 'w', encoding='utf-8', newline='').write(c2)

    print(f'presse.html : {n_tot} courses, {n_val} r\u00e9sultats, {bw} bases gagnantes, '
          f'{b5} dans le top 5 \u2014 maj {mois}')
    if erreurs:
        print('  INCOHERENCE LEDGER : ' + ' | '.join(erreurs))
    return not erreurs


if __name__ == '__main__':
    ok = update()
    print('OK' if ok else 'A CORRIGER')
