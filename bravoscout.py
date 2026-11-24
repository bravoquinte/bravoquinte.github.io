# -*- coding: utf-8 -*-
"""
bravoscout — assistant de pronostic quotidien (outil prive).

Usage :
  python bravoscout.py --chevaux @chevaux-vincennes-26-novembre.json \
      --dist 2700m \
      --cotes "14: 3.1, 17: 5.4, ..."      (texte colle)
      [--cotes-url https://turfin.fr/...]  (ou une page de cotes)
      [--votre-selection "14,17,13,11,16,12,3,9"]

Le JSON partants reste la source de verite ; les cotes fournies (texte ou URL)
remplacent le champ "cote" du JSON quand elles sont lisibles.
Sortie : tableau score, selection 8, top 5, base, confiance, alertes valeur,
et comparaison avec VOTRE selection (--votre-selection).

Ne decide pas a votre place : il vote et argumente. La decision finale est humaine.
"""
import argparse
import io
import json
import os
import re
import sys
import urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
REPO = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, REPO)
import scorix  # noqa: E402


# ---------------------------------------------------------------- chargement

def charger_chevaux(arg):
    path = arg.lstrip('@')
    if not os.path.isabs(path):
        path = os.path.join(REPO, path)
    data = json.load(open(path, encoding='utf-8'))
    out = []
    for v in data.values():
        if v.get('non_partant'):
            continue
        out.append(v)
    return sorted(out, key=lambda x: int(x['numero']))


# ---------------------------------------------------------------- cotes

def cotes_depuis_texte(txt):
    """Extrait {numero: cote} d'un texte colle (tolerant aux formats)."""
    out = {}
    txt = txt.replace(',', ' ').replace(';', ' ').replace('|', ' ')
    toks = txt.split()
    i = 0
    while i < len(toks):
        t = toks[i]
        if ':' in t:                     # "14:3.1"
            a, b = t.split(':', 1)
            if a.isdigit() and _f_ok(b):
                out[int(a)] = float(b.replace(',', '.'))
                i += 1
                continue
        if t.isdigit() and 1 <= int(t) <= 24 and i + 1 < len(toks):
            nxt = toks[i + 1].replace(',', '.')
            if _f_ok(nxt):
                out[int(t)] = float(nxt)
                i += 2
                continue
        i += 1
    return out


def _f_ok(s):
    try:
        v = float(s.replace(',', '.'))
        return 1.0 <= v <= 300
    except ValueError:
        return False


def cotes_depuis_url(url):
    """Telecharge la page et cherche des paires (numero, cote) plausibles.
    Best-effort : si < 5 cotes trouvees, on prévient et on rend None."""
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    html = urllib.request.urlopen(req, timeout=30).read().decode('utf-8', 'ignore')
    # retire les balises pour avoir le texte, mais garde l'ordre
    txt = re.sub(r'<script.*?</script>', ' ', html, flags=re.S)
    txt = re.sub(r'<style.*?</style>', ' ', txt, flags=re.S)
    txt = re.sub(r'<[^>]+>', ' ', txt)
    txt = txt.replace('&nbsp;', ' ').replace(',', '.')
    pairs = {}
    for m in re.finditer(r'\b(\d{1,2})\b\D{0,24}?\b(\d{1,2}(?:\.\d{1,2})?)\b', txt):
        n, c = int(m.group(1)), float(m.group(2))
        if 1 <= n <= 24 and 1.0 <= c <= 300 and n not in pairs:
            pairs[n] = c
    return (pairs if len(pairs) >= 5 else None), len(pairs)


def fusionner_cotes(chevaux, cotes, source):
    if not cotes:
        return chevaux
    n_ok = 0
    for c in chevaux:
        n = int(c['numero'])
        if n in cotes:
            c['cote'] = cotes[n]
            n_ok += 1
    print(f'cotes [{source}] : {n_ok}/{len(chevaux)} chevaux couverts')
    if n_ok < len(chevaux) // 2:
        print('  [warn] peu de cotes reconnues -> feature cote partiellement neutre')
    return chevaux


# ---------------------------------------------------------------- affichage

NOM_COURT = 22


def afficher(chevaux, scores, feats, sel, top5, base, votre_sel):
    by_num = {int(c['numero']): c for c in chevaux}
    max_s = max(s for _, s in scores) or 1.0
    print()
    print(f"{'Score':>6} {'N°':>3} {'Cheval':<{NOM_COURT}} {'Corde':>5} {'Val':>5} {'Cote':>6}")
    print('-' * 56)
    for num, s in scores:
        c = by_num[num]
        print(f"{s:>6.2f} {num:>3} {c.get('nom','-')[:NOM_COURT]:<{NOM_COURT}} "
              f"{str(c.get('corde','-'))[:5]:>5} {str(c.get('valeur','-'))[:5]:>5} "
              f"{str(c.get('cote','-')):>6}")
    print()
    print('SELECTION :', ' - '.join(map(str, sel)))
    print('TOP 5     :', ' - '.join(map(str, top5)))
    top5_scores = [s for n, s in scores[:5]]
    share = (top5_scores[0] / (sum(top5_scores) or 1)) * 100
    print(f'BASE      : {base} {by_num[base].get("nom","")}  (confiance {share:.0f}%)')

    # alertes valeur : ecart rang marche vs rang modele
    rang_model = {num: i for i, (num, _) in enumerate(scores)}
    impl = []
    for c in chevaux:
        v = scorix._f(c.get('cote'))
        if v and v > 0:
            impl.append((int(c['numero']), 1.0 / v))
    impl.sort(key=lambda t: t[1], reverse=True)
    rang_marche = {n: i for i, (n, _) in enumerate(impl)}
    alerts = []
    for num in rang_model:
        if num in rang_marche:
            d = rang_marche[num] - rang_model[num]
            if d >= 4:
                alerts.append(f'VALUE     : N°{num} {by_num[num].get("nom","")}'
                              f' — marché {rang_marche[num]+1}e, modèle {rang_model[num]+1}e (cote élevée, score haut)')
            elif d <= -4:
                alerts.append(f'SURCOTE   : N°{num} {by_num[num].get("nom","")}'
                              f' — marché {rang_marche[num]+1}e, modèle {rang_model[num]+1}e')
    for a in alerts[:8]:
        print(a)

    if votre_sel:
        vs = [int(x) for x in re.findall(r'\d+', votre_sel)]
        communs = [n for n in vs if n in sel]
        seulement_v = [n for n in vs if n not in sel]
        seulement_m = [n for n in sel if n not in vs]
        print()
        print(f'VOTRE sélection : {" - ".join(map(str, vs))}')
        print(f'  communs        : {len(communs)}/{"8" if len(sel)==8 else len(sel)} -> {" ".join(map(str, communs))}')
        print(f'  seulement vous : {" ".join(map(str, seulement_v)) or "-"}')
        print(f'  seulement scout: {" ".join(map(str, seulement_m)) or "-"}')
        for n in seulement_v:
            r = rang_model.get(n)
            print(f'    N°{n} {by_num[n].get("nom","")}: modèle = {"absent" if r is None else f"rang {r+1}"}')
        for n in seulement_m:
            print(f'    N°{n} {by_num[n].get("nom","")}: rang modèle {rang_model[n]+1}')


# ---------------------------------------------------------------- main

def main():
    p = argparse.ArgumentParser(description='BravoScout — assistant pronostic')
    p.add_argument('--chevaux', required=True, help='@chevaux-hippodrome-DD-mois.json')
    p.add_argument('--dist', default='', help='ex: 2700m (pondere la corde)')
    p.add_argument('--cotes', default='', help='cotes en texte : "14: 3.1, 17: 5.4, ..."')
    p.add_argument('--cotes-url', dest='cotes_url', default='', help='page de cotes a parser')
    p.add_argument('--votre-selection', dest='votre_selection', default='',
                   help='votre pronostic humain pour comparaison')
    p.add_argument('--weights', default=None, help='fichier ponderations (defaut poids-backtest.json)')
    args = p.parse_args()

    chevaux = charger_chevaux(args.chevaux)
    print(f'{len(chevaux)} partants actifs')

    if args.cotes_url:
        cotes, n = cotes_depuis_url(args.cotes_url)
        if cotes:
            chevaux = fusionner_cotes(chevaux, cotes, 'URL')
        else:
            print(f'[warn] URL: seulement {n} paires plausibles -> ignoree')
    if args.cotes:
        cotes = cotes_depuis_texte(args.cotes)
        if cotes:
            chevaux = fusionner_cotes(chevaux, cotes, 'texte')
        else:
            print('[warn] texte cotes illisible -> ignore')

    feats, ctx = scorix.features_course(chevaux, args.dist)
    w = scorix.charger_poids(args.weights)
    print('ponderations:', {k: round(v, 2) for k, v in w.items()})
    scores = scorix.scorer(feats, w)
    sel, top5, base = scorix.selection(scores)

    afficher(chevaux, scores, feats, sel, top5, base, args.votre_selection)


if __name__ == '__main__':
    main()
