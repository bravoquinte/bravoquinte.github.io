# -*- coding: utf-8 -*-
"""
scorix — moteur de score BravoScout.

Note chaque cheval sur des signaux exploitables, somme ponderee -> classement.
Toutes les features sont normalisees DANS la course (rang relatif), donc le
classement fonctionne meme si une feature est absente pour tous (ex: cotes "-").

Features :
  forme    : musique recente (1er=10, 2e=6, 3e=4, 4e=3, 5e=2, 0=0.25, D=0,
             6+ = 0.5), ponderation 0.85^k sur 6 courses max
  handicap : valeur elevee + poids faible (handicaps plat), sinon 0 pour tous
  corde    : numero bas = avantage, pondere par la distance (sprint >> tenue)
  cote     : probabilite implicite du marche (1/cote), rang dans la course

Ponderations chargees depuis poids-backtest.json (sortie du backtest), sinon
defauts neutres. Modifiable via --weights.
"""
import json
import os
import re

REPO = os.path.dirname(os.path.abspath(__file__))
POIDS_FICHIER = os.path.join(REPO, 'poids-backtest.json')

POIDS_DEFAUT = {'forme': 1.0, 'handicap': 1.0, 'corde': 0.5, 'cote': 1.0}

POINTS_PLACE = {1: 10.0, 2: 6.0, 3: 4.0, 4: 3.0, 5: 2.0}
PT_D = 0.0      # disqualifie
PT_ZERO = 0.25  # 0 = non place
PT_AUTRE = 0.5  # 6e et au-dela
DECROISSANCE = 0.85
MAX_COURSES = 6


def charger_poids(chemin=None):
    p = POIDS_FICHIER if chemin is None else chemin
    if os.path.exists(p):
        try:
            w = json.load(open(p, encoding='utf-8'))
            if 'poids' in w and isinstance(w['poids'], dict):
                w = w['poids']          # format {poids: {...}, metrics...}
            return {k: float(w.get(k, POIDS_DEFAUT[k])) for k in POIDS_DEFAUT}
        except (ValueError, OSError):
            pass
    return dict(POIDS_DEFAUT)


# ---------------------------------------------------------------- musique

_TOK = re.compile(r'\((\d{2})\)|(\d*)([A-Za-z])')


def score_musique(musique):
    """Retourne un score de forme dans [0, 1] (1 = serie parfaite recente)."""
    if not musique or musique == '-':
        return None
    pts = []
    for m in _TOK.finditer(musique):
        if m.group(1):            # separateur d'annee (25) : pas une course
            continue
        num, lettre = m.group(2), m.group(3)
        if num == '' and lettre.upper() != 'D':
            continue              # lettre seule sans place : ignoree
        if lettre.upper() == 'D' or lettre.upper() == 'A' and num == '':
            p = PT_D
        elif num == '':
            p = PT_ZERO
        else:
            n = int(num)
            p = POINTS_PLACE.get(n, PT_AUTRE) if n >= 1 else PT_ZERO
        pts.append(p)
    if not pts:
        return None
    utilises = pts[:MAX_COURSES]
    num = sum(p * (DECROISSANCE ** k) for k, p in enumerate(utilises))
    den = 10.0 * sum(DECROISSANCE ** k for k in range(len(utilises)))
    return num / den if den > 0 else None


# ---------------------------------------------------------------- helpers

def rangs_normalises(valeurs, inverser=False):
    """dict {cle: valeur} -> dict {cle: rang normalise dans [0,1]}.
    1.0 = meilleur. inverser=True : valeur BASSE = meilleur (poids, corde).
    Si aucune donnee utile, tout le monde a 0 (feature neutre)."""
    utiles = {k: v for k, v in valeurs.items() if v is not None}
    if len(utiles) < 2:
        return {k: 0.0 for k in valeurs}
    tries = sorted(utiles, key=lambda k: utiles[k], reverse=not inverser)
    n = len(tries) - 1
    out = {k: 0.0 for k in valeurs}
    for i, k in enumerate(tries):
        out[k] = 1.0 - (i / n) if n > 0 else 0.0
    return out


def _f(nb):
    s = str(nb).replace(',', '.').replace('kg', '').strip()
    try:
        return float(s)
    except ValueError:
        return None


def _dist_m(dist):
    s = str(dist or '').lower().replace(' ', '')
    m = re.search(r'(\d{3,5})', s)
    return int(m.group(1)) if m else None


# ---------------------------------------------------------------- features

def features_course(chevaux, dist=None):
    """chevaux = liste de dicts (numero, nom, musique, cote, poids, corde, valeur).
    Retourne {numero: {feature: valeur [0,1]}} + contexte."""
    ctx = {'dist': _dist_m(dist)}

    forme = {c['numero']: score_musique(c.get('musique')) for c in chevaux}
    valeur = {c['numero']: _f(c.get('valeur')) for c in chevaux}
    poids = {c['numero']: _f(c.get('poids')) for c in chevaux}
    corde = {c['numero']: _f(c.get('corde')) for c in chevaux}
    cote = {c['numero']: _f(c.get('cote')) for c in chevaux}
    cote = {k: v for k, v in cote.items() if v is not None and v > 0}

    f_forme = rangs_normalises(forme)
    # handicap : melange valeur haute + poids bas ; inactif si une seule donnee
    r_val = rangs_normalises(valeur)
    r_pds = rangs_normalises(poids, inverser=True)
    actifs = {k: (r_val[k] + r_pds[k]) / 2 for k in valeur
              if (valeur[k] is not None or poids[k] is not None)}
    f_hand = actifs if len(actifs) >= 2 else {c['numero']: 0.0 for c in chevaux}

    d = ctx['dist']
    facteur = 1.0 if (d and d <= 1700) else (0.7 if (d and d <= 2200) else 0.4)
    r_corde = rangs_normalises(corde, inverser=True)
    f_corde = {k: v * facteur for k, v in r_corde.items()}

    impl = {k: 1.0 / v for k, v in cote.items()}
    f_cote = rangs_normalises(impl)

    feats = {c['numero']: {
        'forme': f_forme.get(c['numero'], 0.0),
        'handicap': f_hand.get(c['numero'], 0.0),
        'corde': f_corde.get(c['numero'], 0.0),
        'cote': f_cote.get(c['numero'], 0.0),
    } for c in chevaux}
    return feats, ctx


def scorer(feats, poids_w):
    """{numero: {feature: x}} -> liste [(numero, score)] triee par score decroissant."""
    out = []
    for num, f in feats.items():
        s = sum(poids_w.get(k, 0.0) * v for k, v in f.items())
        out.append((num, s))
    out.sort(key=lambda t: t[1], reverse=True)
    return out


def selection(scores, n_sel=8, n_top5=5):
    sel = [num for num, _ in scores[:n_sel]]
    return sel, sel[:n_top5], sel[0]
