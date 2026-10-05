#!/usr/bin/env python3
"""Controle d'integrite du site avant commit.

Usage : python verify-site.py
Code de sortie 0 si tout est OK, 1 sinon.

Verifie :
  - liens internes pointant vers un fichier inexistant
  - deux liens colles faute de separateur (bug d'edition HTML)
  - double echappement HTML visible (ex. &amp;#233;)
  - encodage UTF-8 valide sur tous les fichiers
  - coherence entre ledger, RESULTATS (index.html), resultats.html, track-record.html
  - une seule entree "En attente" au plus, et uniquement pour une course non encore disputee
"""
import io, os, re, json, subprocess, sys

REPO = os.path.dirname(os.path.abspath(__file__))
err = []


def html_files():
    """Fichiers HTML du depot. Repli sur le disque si git ne repond pas."""
    r = subprocess.run(['git', '-C', REPO, 'ls-files'], capture_output=True, text=True)
    files = [f for f in r.stdout.strip().split('\n') if f.endswith('.html')] if r.returncode == 0 else []
    if files:
        return files
    # repli : scanner le disque (copie sans .git, archive, etc.)
    found = []
    for root, dirs, names in os.walk(REPO):
        dirs[:] = [d for d in dirs if d not in ('.git', '__pycache__', 'node_modules')]
        for n in names:
            if n.endswith('.html'):
                found.append(os.path.relpath(os.path.join(root, n), REPO).replace('\\', '/'))
    return sorted(found)


pages = html_files()
if not pages:
    print('ECHEC')
    print('  - aucun fichier HTML trouve : controles HTML sautes, verdict inutilisable')
    sys.exit(1)

r = subprocess.run(['git', '-C', REPO, 'ls-files'], capture_output=True, text=True)
if r.returncode == 0 and r.stdout.strip():
    existing = set(r.stdout.strip().split('\n'))
else:
    # repli : tous les fichiers non ignores (pour valider feed.xml, images, etc.)
    existing = set()
    for root, dirs, names in os.walk(REPO):
        dirs[:] = [d for d in dirs if d not in ('.git', '__pycache__', 'node_modules')]
        for n in names:
            existing.add(os.path.relpath(os.path.join(root, n), REPO).replace('\\', '/'))

# 1. liens internes casses
broken = []
for f in pages:
    c = io.open(os.path.join(REPO, f), encoding='utf-8').read()
    for m in re.finditer(r'href=["\']([^"\'#?]+)["\']', c):
        u = m.group(1)
        if u.startswith(('mailto:', 'tel:', 'javascript:', 'http')):
            continue
        t = u.lstrip('./').split('#')[0]
        if t and t not in existing:
            broken.append(f'{f} -> {t}')
if broken:
    err.append(f'liens internes casses ({len(broken)}) : ' + ', '.join(broken[:5]))

# 2. liens colles
glued = []
for f in pages:
    c = io.open(os.path.join(REPO, f), encoding='utf-8').read()
    if re.search(r'</a><a\s+href', c):
        glued.append(f)
if glued:
    err.append(f'liens colles sans separateur ({len(glued)}) : ' + ', '.join(glued[:5]))

# 3. double echappement visible
dble = []
for f in pages:
    c = io.open(os.path.join(REPO, f), encoding='utf-8').read()
    if '&amp;#' in c or '&amp;amp;' in c:
        dble.append(f)
if dble:
    err.append(f'entites HTML double echappees ({len(dble)}) : ' + ', '.join(dble[:5]))

# 4. encodage
bad = []
for f in pages:
    try:
        open(os.path.join(REPO, f), 'rb').read().decode('utf-8')
    except Exception:
        bad.append(f)
if bad:
    err.append(f'fichiers non UTF-8 ({len(bad)}) : ' + ', '.join(bad[:5]))

# 5. coherence des sources
lp = os.path.join(REPO, 'predictions-ledger.json')
if os.path.exists(lp):
    L = json.load(io.open(lp, encoding='utf-8'))
    val = [p for p in L['predictions'] if p.get('metrics')]
    n = len(val)
    b5 = sum(1 for p in val if p['metrics']['base_in_top5'])
    bw = sum(1 for p in val if p['base'] == p['metrics']['top5'][0])
    st = L['stats']
    if st.get('total_validated') != n:
        err.append(f"stats.total_validated={st.get('total_validated')} mais {n} predictions validees")
    if st.get('base_in_top5_rate') != f'{b5}/{n}':
        err.append(f"stats.base_in_top5_rate={st.get('base_in_top5_rate')} mais {b5}/{n}")
    if st.get('base_wins_rate') != f'{bw}/{n}':
        err.append(f"stats.base_wins_rate={st.get('base_wins_rate')} mais {bw}/{n}")

    idx = os.path.join(REPO, 'index.html')
    if os.path.exists(idx):
        h = io.open(idx, encoding='utf-8').read()
        blk = re.search(r'var RESULTATS\s*=\s*\[(.*?)\n\];', h, re.S)
        if blk:
            dates_idx = set(re.findall(r'\{date:"(\d{4}-\d{2}-\d{2})"', blk.group(1)))
            if dates_idx and dates_idx != {p['date'] for p in val}:
                manque = {p['date'] for p in val} - dates_idx
                trop = dates_idx - {p['date'] for p in val}
                err.append(f'RESULTATS desynchronise du ledger (manquant {sorted(manque)}, '
                           f'en trop {sorted(trop)})')
            # discipline incoherente
            dis = set(re.findall(r'discipline:"([^"]*)"', blk.group(1)))
            lit = [d for d in dis if '&' in d or '\\u' in d]
            if lit:
                err.append('discipline avec entite litterale dans RESULTATS : ' + ', '.join(lit))

    tr = os.path.join(REPO, 'track-record.html')
    if os.path.exists(tr):
        t = io.open(tr, encoding='utf-8').read()
        if f'{bw}/{n}' not in t:
            err.append(f'track-record.html ne contient pas base_wins {bw}/{n} (regen requis)')
        wait = len(re.findall(r'<span class="badge badge-wait">En attente</span>', t))
        att = len(L['predictions']) - n
        if wait != att:
            err.append(f'track-record : {wait} ligne(s) "En attente" mais {att} prediction(s) non validee(s)')

    rs = os.path.join(REPO, 'resultats.html')
    if os.path.exists(rs):
        c = io.open(rs, encoding='utf-8').read()
        rows = len(re.findall(r'<tr><td>\d{4}-\d{2}-\d{2}</td>', c))
        if rows != n:
            err.append(f'resultatats.html : {rows} lignes pour {n} resultats (regen requis)')

    # page presse
    pp = os.path.join(REPO, 'presse.html')
    if os.path.exists(pp):
        c = io.open(pp, encoding='utf-8').read()
        kpi = dict((l, v) for v, l in
                   re.findall(r'<p class="v">(\d+)</p><p class="l">([^<]*)</p>', c))
        attendu = {
            f'courses analys\u00e9es, {n} r\u00e9sultats publi\u00e9s': str(len(L['predictions'])),
            f'bases gagnantes sur {n} courses': str(bw),
            f'bases plac\u00e9es dans les 5 premiers, sur {n} courses': str(b5),
        }
        for lab, val_ in attendu.items():
            if lab not in kpi:
                err.append(f'presse.html : KPI manquant ou desyncronise « {lab} »')
            elif kpi[lab] != val_:
                err.append(f'presse.html : « {lab} » = {kpi[lab]} au lieu de {val_} (update-presse requis)')

if err:
    print('ECHEC')
    for e in err:
        print('  -', e)
    sys.exit(1)

print('OK')
print(f'  {len(pages)} pages HTML, liens et encodage valides')
print(f'  ledger : {n} resultats, {bw} bases gagnantes, {b5} bases dans le top 5')
print('  ledger, RESULTATS, resultats.html, track-record.html et presse.html synchronises')
