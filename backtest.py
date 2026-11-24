# -*- coding: utf-8 -*-
"""
backtest — calibrage honnete de bravoscout sur l'historique du site.

Principe walk-forward : pour chaque jour N (a partir du 15e jour disponible),
les ponderations sont choisies par grille sur les jours ANTERIEURS SEULEMENT,
puis on predit le jour N. Aucune prediction sur du deja-vu.

Comparaison avec la baseline = selections publiees sur le site (ledger).
Metriques : base dans le top 5, presence moyenne /5, gagnant dans la selection.
Sortie : poids-backtest.json (meilleures ponderations + metadonnees).
"""
import glob
import io
import json
import os
import re
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
REPO = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, REPO)
import scorix  # noqa: E402

LEDGER = os.path.join(REPO, 'predictions-ledger.json')
MOIS = {'janvier': 1, 'fevrier': 2, 'février': 2, 'mars': 3, 'avril': 4, 'mai': 5,
        'juin': 6, 'juillet': 7, 'aout': 8, 'août': 8, 'septembre': 9,
        'octobre': 10, 'novembre': 11, 'decembre': 12, 'décembre': 12}

GRILLE = [0.0, 0.5, 1.0, 1.5, 2.0]
DEPART = 15          # nb de jours d'historique minimum avant la 1re prediction
PENALITE_VIDE = -1.0  # score de calibrage si une feature fait tout echouer


def fichier_chevaux(slug):
    """slug pronostic-quinte-<hippo>-JJ-<mois> -> chevaux-<hippo>-JJ-<mois>.json"""
    toks = slug.split('-')
    if len(toks) < 4 or toks[-1] not in MOIS:
        return None
    jour, mois = toks[-2], toks[-1]
    hippo = '-'.join(toks[2:-2])
    exact = os.path.join(REPO, f'chevaux-{hippo}-{jour}-{mois}.json')
    if os.path.exists(exact):
        return exact
    # variante d'orthographe du hippodrome (saint-cloud / saintcloud...)
    cands = glob.glob(os.path.join(REPO, f'chevaux-*-{jour}-{mois}.json'))
    if len(cands) == 1:
        return cands[0]
    # hippo le plus proche en caracteres communs
    def communs(p):
        n = os.path.basename(p).split('-', 1)[1].rsplit('-', 2)[0]
        return sum(1 for a, b in zip(hippo, n) if a == b)
    if cands:
        return max(cands, key=communs)
    return None


def charger_jour(path):
    data = json.load(open(path, encoding='utf-8'))
    return [v for v in data.values() if not v.get('non_partant')]


def arrivee_norm(p):
    a = p.get('arrivee') or p.get('resultat')
    if isinstance(a, dict):
        a = a.get('top5')
    return a[:5] if a else None


def metrics_selection(sel, top5_arr, arrivee):
    base = sel[0]
    return {
        'base_ok': base in top5_arr,
        'presence': len(set(sel) & set(top5_arr)),
        'gagnant': top5_arr[0] in sel,
    }


def evaluer_pond(jours, w, cle='model'):
    tot = {'base': 0, 'pres': 0, 'win': 0, 'n': 0}
    for j in jours:
        feats, _ = scorix.features_course(j['chevaux'], j['dist'])
        scores = scorix.scorer(feats, w)
        sel, _, _ = scorix.selection(scores)
        m = metrics_selection(sel, j['top5_arr'], None)
        tot['base'] += m['base_ok']
        tot['pres'] += m['presence']
        tot['win'] += m['gagnant']
        tot['n'] += 1
    n = tot['n'] or 1
    # score de calibrage : base_top5 * 3 + presence + gagnant (maximise)
    return (tot['base'] / n) * 3 + (tot['pres'] / n) + (tot['win'] / n)


def main():
    ledger = json.load(open(LEDGER, encoding='utf-8'))
    jours = []
    ignores = 0
    for p in sorted(ledger['predictions'], key=lambda x: x['date']):
        arr = arrivee_norm(p)
        path = fichier_chevaux(p['slug'])
        if not arr:
            ignores += 1
            continue
        if not path:
            ignores += 1
            continue
        chevaux = charger_jour(path)
        if len(chevaux) < 10:
            ignores += 1
            continue
        jours.append({'date': p['date'], 'chevaux': chevaux, 'dist': p.get('dist', ''),
                      'top5_arr': arr, 'baseline_sel': p['selection']})

    print(f'jours exploitables: {len(jours)} (ignores: {ignores} sans arrivee ou sans partants)')
    if len(jours) <= DEPART:
        sys.exit('pas assez de jours pour le walk-forward')

    # baseline sur EXACTEMENT les memes jours que le walk-forward
    b = {'base': 0, 'pres': 0, 'win': 0, 'n': 0}
    for j in jours[DEPART:]:
        m = metrics_selection(j['baseline_sel'], j['top5_arr'], None)
        b['base'] += m['base_ok']
        b['pres'] += m['presence']
        b['win'] += m['gagnant']
        b['n'] += 1
    nb = b['n']
    print(f'BASELINE site ({nb} jours)  : base top5 {b["base"]}/{nb} ({b["base"]/nb*100:.0f}%)  '
          f'presence {b["pres"]/nb:.2f}/5  gagnant {b["win"]}/{nb} ({b["win"]/nb*100:.0f}%)')
    print(f'  (historique complet {len(jours)} jours: base {sum(metrics_selection(j["baseline_sel"], j["top5_arr"], None)["base_ok"] for j in jours)}/{len(jours)})')

    w_courant = dict(scorix.POIDS_DEFAUT)
    pred = {'base': 0, 'pres': 0, 'win': 0, 'n': 0}
    par_jour = []
    for i in range(DEPART, len(jours)):
        passe = jours[:i]
        cible = jours[i]
        meilleur, score_m = None, PENALITE_VIDE
        for wf in GRILLE:
            for wh in GRILLE:
                for wc in GRILLE:
                    w = {'forme': wf, 'handicap': wh, 'corde': wc, 'cote': w_courant['cote']}
                    s = evaluer_pond(passe, w)
                    if s > score_m:
                        score_m, meilleur = s, w
        feats, _ = scorix.features_course(cible['chevaux'], cible['dist'])
        scores = scorix.scorer(feats, meilleur)
        sel, _, _ = scorix.selection(scores)
        m = metrics_selection(sel, cible['top5_arr'], None)
        pred['base'] += m['base_ok']
        pred['pres'] += m['presence']
        pred['win'] += m['gagnant']
        pred['n'] += 1
        par_jour.append((cible['date'], m))
        w_courant = meilleur

    n = pred['n']
    print(f'BRAVOSCOUT (wf) : base top5 {pred["base"]}/{n} ({pred["base"]/n*100:.0f}%)  '
          f'presence {pred["pres"]/n:.2f}/5  gagnant {pred["win"]}/{n} ({pred["win"]/n*100:.0f}%)')
    print('dernieres ponderations retenues :', {k: round(v, 2) for k, v in meilleur.items()})

    out = {
        'commentaire': 'ponderations calibrees par backtest walk-forward sur le ledger',
        'date_run': jours[-1]['date'],
        'n_jours': n,
        'metrics_model': {k: pred[k] for k in ('base', 'pres', 'win')},
        'metrics_baseline': {k: b[k] for k in ('base', 'pres', 'win')},
        'poids': meilleur,
    }
    json.dump(out, open(os.path.join(REPO, 'poids-backtest.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print('poids-backtest.json ecrit')

    print()
    print('detail par jour (model: B=base ok, P=presence, G=gagnant):')
    for d, m in par_jour[-15:]:
        print(f"  {d}  B{'+' if m['base_ok'] else '-'} P{m['presence']}/5 G{'+' if m['gagnant'] else '-'}")


if __name__ == '__main__':
    main()
