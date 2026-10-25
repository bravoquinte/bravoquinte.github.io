#!/usr/bin/env python3
"""
update-quinte-jour.py
=====================
Met à jour la page d'accueil (index.html) pour le Quinté du jour en une seule passe.
Fait aussi : miniature YouTube, BLOG_POSTS, RESULTATS, regen sitemap+resultats, commit+push.

Usage
-----
python update-quinte-jour.py \
  --date        2026-10-26 \
  --video       ABC123xyz \
  --hippo       "Paris-Vincennes" \
  --course      "Prix Ulysse" \
  --discipline  "Trot Attelé" \
  --dist        2850m \
  --dotation    91000 \
  --partants    N \
  --corde       "Corde à droite" \
  --selection   "3,8,1,12,7,5,14,9" \
  --top5        "3,8,1,12,7" \
  --base        3 \
  --slug        pronostic-quinte-vincennes-26-octobre \
  --scenario    "Scénario court affiché dans le bloc analyse." \
  --chevaux     "@chevaux-vincennes-26-octobre.json" \
  --resultat    "5-2-11-8-14"   # arrivée officielle course PRECEDENTE (optionnel)
  --commit                        # commit + push git (optionnel)

Fichier JSON partants (--chevaux @fichier.json) — format :
{
  "1": {"numero":1,"nom":"CHEVAL UN","driver":"Dupont J.","entraineur":"Martin P.","musique":"-","cote":"-","poids":"67 kg","corde":1,"age":5,"sexe":"H"},
  ...
}
"""

import argparse, json, os, re, subprocess, sys, urllib.request
from datetime import datetime

# ── helpers ────────────────────────────────────────────────────────────────────

REPO = os.path.dirname(os.path.abspath(__file__))

def read_file(path):
    with open(path, encoding='utf-8') as f:
        return f.read()

def write_file(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def run(cmd, **kw):
    return subprocess.run(cmd, shell=True, cwd=REPO, **kw)

# ── miniature YouTube ──────────────────────────────────────────────────────────

def download_thumb(video_id):
    url  = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
    tmp  = os.path.join(os.environ.get('TEMP', '/tmp'), f"yt-thumb-{video_id}.jpg")
    dest_dated = os.path.join(REPO, 'images', f"quinte-{args.date}.webp")
    dest_hero  = os.path.join(REPO, 'images', 'video-hero.webp')
    urllib.request.urlretrieve(url, tmp)
    try:
        from PIL import Image
        img = Image.open(tmp)
        img.save(dest_dated, 'WEBP')
        img.save(dest_hero,  'WEBP')
        print(f"  miniature OK  {img.size}  ->  {dest_dated}")
    except ImportError:
        print("  [warn] Pillow absent — miniature non convertie")

# ── lire partants JSON ─────────────────────────────────────────────────────────

def load_chevaux(chevaux_arg):
    """Retourne une liste de dicts triée par numéro."""
    if not chevaux_arg:
        return []
    path = chevaux_arg.lstrip('@')
    if not os.path.isabs(path):
        path = os.path.join(REPO, path)
    data = json.loads(read_file(path))
    return sorted(data.values(), key=lambda x: int(x['numero']))

# ── construire le bloc JS chevaux ──────────────────────────────────────────────

def build_js_chevaux(chevaux_list):
    items = []
    for h in chevaux_list:
        nom = h['nom'].replace('"', "'")
        drv = h.get('driver', '-').replace('"', "'")
        ent = h.get('entraineur', '-').replace('"', "'")
        cote = h.get('cote', '-')
        musique = h.get('musique', '-')
        items.append(
            f'{{num:{h["numero"]},nom:"{nom}",driver:"{drv}",'
            f'entraineur:"{ent}",musique:"{musique}",cote:"{cote}"}}'
        )
    return 'var chevaux=[' + ','.join(items) + '];'

# ── construire le tableau HTML partants ────────────────────────────────────────

def build_html_partants(chevaux_list, selection_nums):
    rows = []
    for h in chevaux_list:
        n   = int(h['numero'])
        nom = h['nom']
        drv = h.get('driver', '-')
        ent = h.get('entraineur', '-')
        pds = h.get('poids', '-')
        is_base = n == selection_nums[0] if selection_nums else False
        is_sel  = n in selection_nums
        statut  = '<strong style=\'color:#16a34a;\'>BASE</strong>' if is_base else '&#8212;'
        td_num  = f"<td style='font-weight:700;color:#15803d'>{n}</td>" if is_base else f"<td>{n}</td>"
        td_nom  = f"<td style='color:#15803d;font-weight:500'>{nom}</td>" if is_sel else f"<td>{nom}</td>"
        rows.append(f"<tr>{td_num}{td_nom}<td>{drv}</td><td>{ent}</td><td>{pds}</td><td>{statut}</td></tr>")
    return '\n'.join(rows)

# ── construire la section Quinté du jour ───────────────────────────────────────

def build_quinte_section(args, chevaux_list, sel, top5):
    nb      = len(chevaux_list) if chevaux_list else args.partants
    sel_str = ' &#8212; '.join(str(n) for n in top5)  # top5 dans le simple
    sel8    = ' &#8212; '.join(str(n) for n in sel)

    # --- tickets ---
    base1, base2, base3 = sel[0], sel[1] if len(sel)>1 else sel[0], sel[2] if len(sel)>2 else sel[0]
    couple_str = f"{base1} / {base2} / {base3}"

    # --- tableau partants ---
    if chevaux_list:
        col_header = '<th>Poids</th>'
        tbody      = build_html_partants(chevaux_list, sel)
    else:
        col_header = '<th>Cote</th>'
        tbody      = f'<tr><td colspan="6"><em>Partants non disponibles</em></td></tr>'

    # --- liste sélection ---
    def sel_item(n):
        nom = next((h['nom'] for h in chevaux_list if int(h['numero'])==n), f'#{n}')
        label = f'{n} - {nom}' + (' (BASE)' if n==sel[0] else '')
        return f'<li><strong>{n}</strong> - {nom}{"&nbsp;<em style=\'color:#16a34a\'>(BASE)</em>" if n==sel[0] else ""}</li>'

    sel_items  = '\n'.join(sel_item(n) for n in sel)
    top5_items = '\n'.join(
        f'<div style="margin:.5rem 0;"><strong>{n}</strong> - {next((h["nom"] for h in chevaux_list if int(h["numero"])==n), f"#{n}")} (cote -)</div>'
        for n in top5
    )

    scenario = args.scenario or f"Ce Quinté+ réunit {nb} partants sur {args.dist} à {args.hippo}. Notre sélection s'articule autour de la base {sel[0]} complétée par {len(sel)-1} chevaux de valeur."

    return f"""<!-- ========== PAGE QUINTE DU JOUR ========== -->
<section class='page' data-page-id='quinte-du-jour'>
<div class='container' style='padding:2rem 1rem 4rem;'>
<nav class='breadcrumb'>
<a data-page='accueil' href='#accueil'>Accueil</a><span>&#8250;</span>
<span style='color:#0f172a;font-weight:500;'>Quinté du jour</span>
</nav>
<h2 class='font-display' style='font-size:2rem;color:#0f172a;margin:0 0 .5rem;'>{args.course} &#8212; Quinté+</h2>
<p style='color:#475569;margin:0 0 2rem;'>{args.hippo} &#8226; {args.discipline} &#8226; {args.dist} &#8226; {args.corde} &#8226; {nb} partants</p>
<div class='grid-4' style='margin-bottom:3rem;'>
<div class='kpi-card'><p class='kpi-label'>Hippodrome</p><p class='kpi-value'>{args.hippo}</p></div>
<div class='kpi-card'><p class='kpi-label'>Type</p><p class='kpi-value'>{args.discipline}</p></div>
<div class='kpi-card'><p class='kpi-label'>Distance</p><p class='kpi-value'>{args.dist}</p></div>
<div class='kpi-card'><p class='kpi-label'>Allocation</p><p class='kpi-value'>{args.dotation} &#8364;</p></div>
</div>
<section style='margin-bottom:3rem;'>
<h2 class='font-display' style='font-size:1.75rem;margin:0 0 1rem;'>Analyse du scénario</h2>
<div class='card' style='background:#f8fafc;'>
<h3>Le scénario.</h3>
<p>{scenario}</p>
</div>
</section>
<section style='margin-bottom:3rem;'>
<h2 class='font-display' style='font-size:1.75rem;margin:0 0 1rem;'>Les {nb} partants</h2>
<div class='table-wrap'>
<table>
<thead><tr><th>N°</th><th>Cheval</th><th>Jockey</th><th>Entraîneur</th>{col_header}<th>Statut</th></tr></thead>
<tbody id='partants-tbody'>
{tbody}
</tbody>
</table>
</div>
</section>
<section class='grid-2' style='margin-bottom:3rem;'>
<div>
<h2 class='font-display' style='font-size:1.5rem;margin:0 0 1rem;'>Sélection ({len(sel)})</h2>
<ul id='selection-list'>
{sel_items}
</ul>
</div>
<div>
<h2 class='font-display' style='font-size:1.5rem;margin:0 0 1rem;'>Top 5</h2>
<div id='top5-list'>
{top5_items}
</div>
</div>
</section>
<section style='margin-bottom:3rem;'>
<h2 class='font-display' style='font-size:1.75rem;margin:0 0 1rem;'>Tickets prêts à jouer</h2>
<div class='grid-3'>
<article class='ticket-card' style='border-color:#22c55e;'>
<div class='ticket-header' style='background:#22c55e;'><h3>Petit budget</h3><p style='margin:0;font-size:.875rem;'>&#8776;5 &#8364;</p></div>
<div class='ticket-body'>
<div class='ticket-line'><h4>Couplé placé</h4><code>{couple_str}</code></div>
<p style='margin:.5rem 0 0;color:#64748b;font-size:.875rem;'>3 tickets &#215; 1,50 &#8364; = 4,50 &#8364;</p>
</div>
</article>
<article class='ticket-card' style='border-color:#f59e0b;'>
<div class='ticket-header' style='background:#f59e0b;'><h3>Budget moyen</h3><p style='margin:0;font-size:.875rem;'>&#8776;15 &#8364;</p></div>
<div class='ticket-body'>
<div class='ticket-line'><h4>Quinté+ simple</h4><code>{sel_str}</code></div>
<div class='ticket-line'><h4>Couplé base</h4><code>{couple_str}</code></div>
<p style='margin:.5rem 0 0;color:#64748b;font-size:.875rem;'>&#8776; 15 &#8364;</p>
</div>
</article>
<article class='ticket-card' style='border-color:#3b82f6;'>
<div class='ticket-header' style='background:#3b82f6;'><h3>Ambitieux</h3><p style='margin:0;font-size:.875rem;'>&#8776;70 &#8364;</p></div>
<div class='ticket-body'>
<div class='ticket-line'><h4>Multi 4/5/6 ({len(sel)} chevaux)</h4><code>{sel8}</code></div>
<p style='margin:.5rem 0 0;color:#64748b;font-size:.875rem;'>35 tickets &#215; 2 &#8364; &#8776; 70 &#8364;</p>
</div>
</article>
</div>
</section>
<div class='alert alert-warning'>
<p style='margin:0;'><strong>&#9888; Jeu responsable</strong> Ne jouez que l'argent que vous pouvez perdre. <a href='https://joueurs-info-service.fr' rel='noopener' target='_blank'>Joueurs Info Service : 09 74 75 13 13</a></p>
</div>
</div>
</section>
"""

# ── RESULTATS : ajouter l'arrivée précédente ───────────────────────────────────

def add_resultat(html, args, chevaux_prev):
    """Insère un nouveau résultat en tête de var RESULTATS."""
    if not args.resultat:
        return html
    nums = [int(x.strip()) for x in args.resultat.split('-')]
    # Noms depuis le fichier JSON partants si fourni, sinon generique
    def nom(n):
        if chevaux_prev:
            h = next((x for x in chevaux_prev if int(x['numero'])==n), None)
            return h['nom'].upper() if h else f'#{n}'
        return f'#{n}'
    arrivee = ','.join(
        f'{{n:{n},nom:"{nom(n)}"}}' for n in nums
    )
    # date = date du jour précédent = args.date - 1 jour
    from datetime import date, timedelta
    d = date.fromisoformat(args.date) - timedelta(days=1)
    new_entry = (
        f'{{date:"{d}",hippo:"{args.hippo_prev or args.hippo}",'
        f'course:"{args.course_prev or args.course}",'
        f'discipline:"{args.discipline_prev or args.discipline}",'
        f'dist:"{args.dist_prev or args.dist}",'
        f'arrivee:[{arrivee}],'
        f'rapports:"https://www.pmu.fr/turf/"}},'
    )
    return html.replace('var RESULTATS=[', 'var RESULTATS=[\n' + new_entry, 1)

# ── BLOG_POSTS : insérer l'article du jour en tête ────────────────────────────

def add_blog_post(html, args):
    title   = f"Pronostic Quinté {args.hippo} {args.date_fr} - {args.course}"
    excerpt = f"Analyse complète du Quinté du jour : {args.course} à {args.hippo}."
    img     = f"images/quinte-{args.date}.webp"
    entry   = (
        f'{{title:"{title}",date:"{args.date}",'
        f'slug:"{args.slug}",excerpt:"{excerpt}",img:"{img}"}},'
    )
    return html.replace('var BLOG_POSTS=[', 'var BLOG_POSTS=[' + entry + '\n', 1)

# ── main ───────────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(description='Mise à jour quotidienne Bravo Quinté')
    p.add_argument('--date',         required=True,  help='YYYY-MM-DD')
    p.add_argument('--video',        required=True,  help='ID YouTube (11 chars)')
    p.add_argument('--hippo',        required=True)
    p.add_argument('--course',       required=True)
    p.add_argument('--discipline',   required=True)
    p.add_argument('--dist',         required=True)
    p.add_argument('--dotation',     required=True)
    p.add_argument('--partants',     type=int, default=0)
    p.add_argument('--corde',        default='Corde à gauche')
    p.add_argument('--selection',    required=True,  help='ex: 4,7,9,8,2,6,10,1')
    p.add_argument('--top5',         required=True,  help='ex: 4,7,9,8,2')
    p.add_argument('--base',         type=int, default=0)
    p.add_argument('--slug',         required=True)
    p.add_argument('--scenario',     default='',     help='Texte court du scénario')
    p.add_argument('--chevaux',      default='',     help='@fichier.json ou vide')
    # résultat course précédente
    p.add_argument('--resultat',     default='',     help='ex: 5-2-11-8-14')
    p.add_argument('--hippo-prev',   default='')
    p.add_argument('--course-prev',  default='')
    p.add_argument('--discipline-prev', default='')
    p.add_argument('--dist-prev',    default='')
    # options
    p.add_argument('--commit',       action='store_true')
    p.add_argument('--no-thumb',     action='store_true', help='Ne pas télécharger la miniature')
    return p.parse_args()

if __name__ == '__main__':
    args = parse_args()

    # Formatage date lisible
    try:
        dt = datetime.strptime(args.date, '%Y-%m-%d')
        jours_fr = ['lundi','mardi','mercredi','jeudi','vendredi','samedi','dimanche']
        mois_fr  = ['','janvier','février','mars','avril','mai','juin',
                    'juillet','août','septembre','octobre','novembre','décembre']
        args.date_fr = f"{dt.day} {mois_fr[dt.month]} {dt.year}"
    except Exception:
        args.date_fr = args.date

    # Listes numériques
    sel  = [int(x) for x in args.selection.split(',')]
    top5 = [int(x) for x in args.top5.split(',')]
    if args.base and args.base not in sel:
        sel.insert(0, args.base)

    # Partants
    chevaux_list = load_chevaux(args.chevaux) if args.chevaux else []
    if chevaux_list and args.partants == 0:
        args.partants = len(chevaux_list)

    print(f"\n=== Quinté {args.date} — {args.course} ({args.hippo}) ===")
    print(f"  base: {sel[0]} | sélection: {','.join(str(x) for x in sel)} | top5: {','.join(str(x) for x in top5)}")

    # 1. Miniature YouTube
    if not args.no_thumb:
        print("1. Téléchargement miniature...")
        download_thumb(args.video)

    # 2. Lire index.html
    print("2. Mise à jour index.html...")
    idx_path = os.path.join(REPO, 'index.html')
    html = read_file(idx_path)

    # 3. Remplacer section Quinté du jour (HTML statique)
    section_start = '<!-- ========== PAGE QUINTE DU JOUR ========== -->'
    section_end   = '<!-- ========== PAGE RESULTATS ========== -->'
    i1 = html.find(section_start)
    i2 = html.find(section_end)
    if i1 == -1 or i2 == -1:
        print("  [erreur] balises de section introuvables dans index.html")
        sys.exit(1)
    nouvelle_section = build_quinte_section(args, chevaux_list, sel, top5)
    html = html[:i1] + nouvelle_section + html[i2:]

    # 4. Mettre à jour les variables JS
    new_js_chevaux = build_js_chevaux(chevaux_list) if chevaux_list else None
    if new_js_chevaux:
        html = re.sub(r'var chevaux=\[.*?\];', new_js_chevaux, html)
    html = re.sub(r'var selection=\[.*?\];', f'var selection=[{",".join(str(x) for x in sel)}];', html)
    html = re.sub(r'var top5=\[.*?\];',      f'var top5=[{",".join(str(x) for x in top5)}];',    html)

    # 5. Base highlight dans renderPartants
    bases_js = '||'.join(f'c.num==={n}' for n in [sel[0]])
    html = re.sub(r'c\.num===\d+(\|\|c\.num===\d+)*', bases_js, html, count=1)

    # 6. Vidéo hero
    html = re.sub(r'https://youtu\.be/[A-Za-z0-9_-]{11}',
                  f'https://youtu.be/{args.video}', html, count=1)

    # 7. BLOG_POSTS
    html = add_blog_post(html, args)

    # 8. RESULTATS (arrivée précédente)
    if args.resultat:
        html = add_resultat(html, args, chevaux_list)

    # 9. Écrire index.html
    write_file(idx_path, html)
    print("  index.html OK")

    # 10. Regen sitemap + resultats
    print("3. Régénération sitemap + résultats...")
    for script in ['regen-resultats.py', 'gen-sitemap.py']:
        sp = os.path.join(REPO, script)
        if os.path.exists(sp):
            r = run(f'python "{sp}"', capture_output=True, text=True)
            print(f"  {script}: {r.stdout.strip() or r.stderr.strip()}")

    # 11. Commit + push
    if args.commit:
        print("4. Commit + push...")
        msg = f"Daily {args.date}: {args.hippo} {args.course} - video + pronostics"
        if args.resultat:
            msg += f" + résultat {args.resultat}"
        run(f'git add -A')
        run(f'git commit -m "{msg}"')
        r = run('git push origin main', capture_output=True, text=True)
        output = r.stdout + r.stderr
        if 'main -> main' in output:
            print("  push OK")
        else:
            print("  push output:", output[-200:])

    print("\n=== DONE ===")
    print(f"  Article    : {args.slug}.html")
    print(f"  Sélection  : {' - '.join(str(x) for x in sel)}")
    print(f"  Top 5      : {' - '.join(str(x) for x in top5)}")
    if args.resultat:
        print(f"  Résultat J-1: {args.resultat}")
