#!/usr/bin/env python3

"""Regenere archives + feed + track-record depuis index.html + ledger."""

import io, os, re, json



GA_SNIPPET = '''<script async src="https://www.googletagmanager.com/gtag/js?id=G-XQPLYLFL4D"></script>

<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());gtag('config','G-XQPLYLFL4D');</script>'''



BTN = '<p style="text-align:center;margin:2rem 0;"><a href="https://bravoquinte.github.io/" class="btn" style="display:inline-block;background:#16a34a;color:#fff;padding:.75rem 1.5rem;border-radius:8px;text-decoration:none;font-weight:600;">&#8592; Retour à l\'accueil</a></p>\n'

TOP_LINK = '''<a href="https://bravoquinte.github.io/" style="display:inline-block;margin-bottom:1rem;color:#16a34a;text-decoration:none;font-weight:600;">&#8592; Retour à l'accueil</a>'''



import os as _os

REPO = _os.path.dirname(_os.path.abspath(__file__))

repo = REPO

base = 'https://bravoquinte.github.io/'



idx = io.open(os.path.join(repo, 'index.html'), encoding='utf-8').read()

articles = re.findall(r'\{title:"([^"]+)",date:"([^"]+)",slug:"([^"]+)",excerpt:"([^"]*)",img:"([^"]+)"\}', idx)

if not articles:

    articles = re.findall(r"\{title:\"([^\"]+)\",date:\"([^\"]+)\",slug:\"([^\"]+)\"", idx)



# 1. archives.html

NL = chr(10)

# groupement par mois (sections repliables)

MOIS_FR = ['janvier','f&eacute;vrier','mars','avril','mai','juin',

           'juillet','ao&ucirc;t','septembre','octobre','novembre','d&eacute;cembre']

groups = {}

for title, date, slug, excerpt, img in sorted(articles, key=lambda x: x[1], reverse=True):

    groups.setdefault(date[:7], []).append((title, date, slug, excerpt, img))



sections = []

for i, (ym, arts) in enumerate(groups.items()):

    y, m = ym.split('-')

    rows = NL.join(f'<tr><td>{date}</td><td><a href="{base}{slug}.html">{title}</a></td><td>{excerpt}</td></tr>'

                   for title, date, slug, excerpt, img in arts)

    open_attr = ' open' if i == 0 else ''

    n = len(arts)

    sections.append(

        f'<details{open_attr}><summary>{MOIS_FR[int(m)-1][0].upper() + MOIS_FR[int(m)-1][1:]} {y} &#183; {n} pronostic{"s" if n > 1 else ""}</summary>'

        f'<table><thead><tr><th>Date</th><th>Article</th><th>R&eacute;sum&eacute;</th></tr></thead><tbody>'

        + NL + rows + NL + '</tbody></table></details>')



sections_html = NL.join(sections)

archives_html = f'''<!DOCTYPE html>

<html lang="fr"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">

{GA_SNIPPET}<title>Archives - Pronostics Quinté+ Bravo Quinté</title>

<meta name="description" content="Archives des pronostics Quinté+ publiés sur Bravo Quinté.">

<link rel="canonical" href="{base}archives.html">

<style>:root{{--primary:#16a34a;--dark:#0f172a;--gray:#64748b;--border:#e2e8f0}}body{{font-family:'Inter',system-ui,sans-serif;margin:0;padding:0;color:var(--dark);background:#fff;line-height:1.6}}.container{{max-width:900px;margin:0 auto;padding:1.5rem}}h1{{font-size:2rem;margin:1rem 0}}.meta{{color:var(--gray);font-size:.9rem;margin-bottom:1.5rem}}table{{width:100%;border-collapse:collapse;margin:1rem 0;font-size:.9rem}}th{{background:var(--dark);color:#fff;padding:.75rem;text-align:left}}td{{padding:.75rem;border-bottom:1px solid var(--border)}}tr:nth-child(even){{background:#f8fafc}}a{{color:var(--primary)}}details{{margin:.75rem 0;border:1px solid #e2e8f0;border-radius:10px;background:#fff;overflow:hidden}}summary{{cursor:pointer;padding:.85rem 1rem;font-weight:700;background:#f1f5f9;list-style:none}}summary::after{{content:'›';color:#16a34a;display:inline-block;font-size:1.1em;transition:transform .15s}}details[open]>summary::after{{transform:rotate(90deg)}}details[open]>summary{{background:#dcfce7;color:#15803d}}details table{{margin:0}} footer{{text-align:center;padding:2rem;color:var(--gray);font-size:.85rem;border-top:1px solid var(--border);margin-top:2rem}}</style></head><body>

<div class="container">

<a href="https://bravoquinte.github.io/" style="display:inline-block;margin-bottom:1rem;color:#16a34a;text-decoration:none;font-weight:600;">&#8592; Retour à l'accueil</a>

<h1>Archives des pronostics</h1>

<p class="meta">{len(articles)} pronostics publiés</p>

{sections_html}</div>

{BTN}

<footer><p><strong>Bravo Quinté</strong> &#8212; publication écrite de la chaîne <a href="https://www.youtube.com/@bravoturf" rel="noopener" target="_blank">Bravoturf</a> &#183; <a href="https://www.instagram.com/bravoturf" rel="noopener" target="_blank">Instagram</a> &#183; <a href="https://www.facebook.com/profile.php?id=100092648388721" rel="noopener" target="_blank">Facebook</a> &#183; <a href="https://www.tiktok.com/@bravo.quinte" rel="noopener" target="_blank">TikTok</a></p><p><a href="methodologie.html">Méthodologie</a> &#183; <a href="mentions-legales.html">Mentions légales</a> &#183; <a href="apropos.html">À propos</a> &#183; <a href="https://bravoquinte.github.io/presse.html">Presse</a> &#183; <a href="track-record.html">Track Record</a> &#183; <a href="feed.xml">RSS</a></p><p>Jeu responsable : 09 74 75 13 13</p></footer>

</body></html>'''

io.open(os.path.join(repo, 'archives.html'), 'w', encoding='utf-8', newline='').write(archives_html)

print(f'archives.html: {len(articles)} articles')



# 1bis. blog.html : hub des guides + liste des articles (vraie URL indexable)

guides_html = (

    '<div class="guide-card"><a href="' + base + 'guide-lire-pronostic-quinte.html">'

    '<strong>Comment lire un pronostic de quint&eacute;</strong><br>'

    'Musique, base, tocard, corde, cotes : le guide complet.</a></div>'

    '<div class="guide-card"><a href="' + base + 'jouer-quinte-regles-mises-tickets.html">'

    '<strong>Comment jouer le Quint&eacute;+</strong><br>'

    'R&egrave;gles, mises minimales, champ r&eacute;duit, Multi, 2sur4, tickets.</a></div>'

    '<div class="guide-card"><a href="' + base + 'ferrure-trot-d4-dp-deferre-signification.html">'

    '<strong>D&eacute;ferr&eacute; D4, DP : la ferrure au trot</strong><br>'

    'Sigles, plaquage, cale : d&eacute;coder le programme et l&#8217;intention de course.</a></div>'

)

rows_blog = NL.join(

    f'<div class="bravo-post"><h3 class="post-title"><a href="{base}{slug}.html">{title}</a></h3>'

    f'<p class="post-meta">{date}</p><p class="post-excerpt">{excerpt}</p></div>'

    for title, date, slug, excerpt, img in sorted(articles, key=lambda x: x[1], reverse=True))

css_blog = (':root{--primary:#16a34a;--dark:#0f172a;--gray:#64748b;--border:#e2e8f0}'

            'body{font-family:Inter,system-ui,sans-serif;margin:0;padding:0;color:var(--dark);background:#fff;line-height:1.6}'

            '.container{max-width:900px;margin:0 auto;padding:1.5rem}'

            'h1{font-size:2rem;margin:1rem 0}.meta{color:var(--gray);font-size:.9rem;margin-bottom:1.5rem}'

            '.guide-card{border:1px solid var(--border);border-left:4px solid var(--primary);border-radius:10px;padding:1rem 1.25rem;margin:1rem 0;background:#f8fafc}'

            '.guide-card a{text-decoration:none;color:var(--primary)}'

            '.bravo-post{padding:1.25rem 0;border-bottom:1px solid var(--border)}'

            '.post-title a{text-decoration:none;color:var(--dark);font-weight:600}'

            '.post-title a:hover{color:var(--primary)}'

            '.post-meta{font-size:.8rem;color:var(--gray);margin:.25rem 0}'

            '.post-excerpt{margin:0;font-size:.95rem;color:#334155}'

            'footer{text-align:center;padding:2rem;color:var(--gray);font-size:.85rem;border-top:1px solid var(--border);margin-top:2rem}')

blog_html = ('<!DOCTYPE html>' + NL + '<html lang="fr"><head><meta charset="UTF-8">'

             '<meta name="viewport" content="width=device-width,initial-scale=1.0">' + NL

             + GA_SNIPPET + NL

             + '<title>Blog - Conseils hippiques et m&eacute;thodes Quint&eacute;+ | Bravo Quint&eacute;</title>' + NL

             + '<meta name="description" content="Guides et conseils pour le Quint&eacute;+ : lire un pronostic, la musique d\'un cheval, jouer ses tickets, g&eacute;rer sa bankroll.">' + NL

             + '<link rel="canonical" href="' + base + 'blog.html">' + NL

             + '<style>' + css_blog + '</style></head><body>' + NL

             + '<div class="container">' + NL + TOP_LINK + NL

             + '<h1>Blog &amp; Conseils hippiques</h1>' + NL

             + '<p class="meta">Guides pour mieux lire et mieux jouer le Quint&eacute;+, et tous les articles du site.</p>' + NL

             + guides_html + NL

             + '<h2 style="font-size:1.4rem;margin:2rem 0 0;">Tous les articles</h2>' + NL

             + rows_blog + NL

             + '</div>' + NL + BTN + NL

             + '<footer><p><strong>Bravo Quint&eacute;</strong> &#8212; publication &eacute;crite de la cha&icirc;ne <a href="https://www.youtube.com/@bravoturf" rel="noopener" target="_blank">Bravoturf</a></p>'

             + '<p><a href="' + base + 'archives.html">Archives</a> &#183; <a href="' + base + 'methodologie.html">M&eacute;thodologie</a> &#183; <a href="' + base + 'track-record.html">Track Record</a> &#183; <a href="' + base + 'feed.xml">RSS</a></p>'

             + '<p>Jeu responsable : 09 74 75 13 13</p></footer>'

             + NL + '</body></html>')

io.open(os.path.join(repo, 'blog.html'), 'w', encoding='utf-8', newline='').write(blog_html)

print(f'blog.html : {len(articles)} articles + 2 guides')



# 2. feed.xml

entries = '\n'.join(f'''<entry>

<title>{title}</title>

<link href="{base}{slug}.html"/>

<id>{base}{slug}.html</id>

<published>{date}T08:00:00Z</published>

<updated>{date}T08:00:00Z</updated>

<summary>{excerpt}</summary>

</entry>''' for title, date, slug, excerpt, img in sorted(articles, key=lambda x: x[1], reverse=True))

feed = f'''<?xml version="1.0" encoding="UTF-8"?>

<feed xmlns="http://www.w3.org/2005/Atom">

<title>Bravo Quinté — Pronostics hippiques du jour</title>

<subtitle>Analyses, sélections et tickets pour le Quinté+ du jour.</subtitle>

<link href="{base}" rel="alternate"/>

<link href="{base}feed.xml" rel="self"/>

<id>{base}</id>

<updated>{max(a[1] for a in articles)}T08:00:00Z</updated>

{entries}

</feed>'''

io.open(os.path.join(repo, 'feed.xml'), 'w', encoding='utf-8', newline='').write(feed)

print(f'feed.xml: {len(articles)} entrées')



# 3. track-record.html

ledger = json.load(io.open(os.path.join(repo, 'predictions-ledger.json'), encoding='utf-8'))

stats = ledger['stats']

preds = ledger['predictions']



kpis = f'''<div class="container">

<a href="https://bravoquinte.github.io/" style="display:inline-block;margin-bottom:1rem;color:#16a34a;text-decoration:none;font-weight:600;">&#8592; Retour à l'accueil</a>

<h1>Transparence des pronostics</h1>

<div class="card"><p><strong>Statistiques publiques</strong> — mises à jour après chaque course pronostiquée. Chaque donnée est vérifiable : le tableau ci-dessous reprend chaque prédiction et son résultat.</p></div>

<div style="text-align:center;margin:1.5rem 0;">

<div class="stat"><p class="stat-value">{stats["base_in_top5_rate"]}</p><p class="stat-label">Base dans le top 5</p></div>

<div class="stat"><p class="stat-value">{stats["selection_avg_in_top5"]}</p><p class="stat-label">Sélection dans le top 5 (moy.)</p></div>

<div class="stat"><p class="stat-value">{stats["winner_in_selection_rate"]}</p><p class="stat-label">Gagnant dans notre sélection</p></div>

<div class="stat"><p class="stat-value">{stats["top3_in_top5_rate"]}</p><p class="stat-label">3 chevaux ou + dans le top 5</p></div>

</div>'''



rows = []

for p in sorted(preds, key=lambda x: x['date'], reverse=True):

    sel = ', '.join(str(x) for x in p['selection'][:5])

    mm = p.get('metrics') or {}

    if mm.get('top5'):

        top5 = ', '.join(str(x) for x in mm['top5'])

        bm = '<span class="ok">&#10003;</span>' if mm['base_in_top5'] else '<span class="miss">&#10007;</span>'

        sm = f'<strong>{mm["selection_in_top5"]}</strong>/5'

        st = '<span class="badge badge-ok">Validé</span>'

    else:

        top5 = '&#8212;'; bm = '<span class="wait">&#9203;</span>'; sm = '<span class="wait">&#9203;</span>'; st = '<span class="badge badge-wait">En attente</span>'

    rows.append(f'<tr><td>{p["date"]}</td><td><a href="{base}{p["slug"]}.html">{p["hippo"]}</a></td><td>{p["course"]}</td><td><strong>{p["base"]}</strong> {bm}</td><td>{sel}</td><td>{top5}</td><td>{sm}</td><td>{st}</td></tr>')



table = f'''<h2>Historique des prédictions</h2>

<div class="card" style="overflow-x:auto;">

<table><thead><tr><th>Date</th><th>Hippodrome</th><th>Course</th><th>Base</th><th>Sélection</th><th>Top 5 arrivé</th><th>Présence</th><th>Statut</th></tr></thead><tbody>

{''.join(rows)}

</tbody></table></div>'''



method = '''<h2>Comment lire ces chiffres</h2>

<div class="card"><ul>

<li><strong>Base dans le top 5</strong> : le cheval que nous avons mis en premier est-il dans les 5 premiers à l'arrivée ?</li>

<li><strong>Sélection dans le top 5 (moy.)</strong> : en moyenne, combien de nos chevaux (notés sur 5) figurent parmi les 5 premiers à l'arrivée.</li>

<li><strong>Gagnant dans notre sélection</strong> : le vainqueur de la course faisait-il partie de notre sélection ?</li>

<li><strong>3 chevaux ou + dans le top 5</strong> : nombre de courses où au moins 3 de nos chevaux terminent dans les 5 premiers.</li>

</ul></div>

<p><strong>Intégrité :</strong> chaque prédiction est enregistrée avant publication des résultats. Rien n'est modifié rétroactivement.</p>

<p style="text-align:center;margin:2rem 0;"><a href="https://bravoquinte.github.io/" class="btn">Retour à l'accueil</a></p>

<footer style="text-align:center;padding:2rem;color:var(--gray);font-size:.85rem;border-top:1px solid var(--border);margin-top:2rem;"><p><strong>Bravo Quinté</strong> &#8212; publication écrite de la chaîne <a href="https://www.youtube.com/@bravoturf" rel="noopener" target="_blank">Bravoturf</a> &#183; <a href="https://www.instagram.com/bravoturf" rel="noopener" target="_blank">Instagram</a> &#183; <a href="https://www.facebook.com/profile.php?id=100092648388721" rel="noopener" target="_blank">Facebook</a> &#183; <a href="https://www.tiktok.com/@bravo.quinte" rel="noopener" target="_blank">TikTok</a></p><p><a href="methodologie.html">Méthodologie</a> &#183; <a href="mentions-legales.html">Mentions légales</a> &#183; <a href="apropos.html">À propos</a> &#183; <a href="https://bravoquinte.github.io/presse.html">Presse</a> &#183; <a href="track-record.html">Track Record</a> &#183; <a href="feed.xml">RSS</a></p><p>Jeu responsable : 09 74 75 13 13</p></footer>

</div></body></html>'''



html = f'''<!DOCTYPE html>

<html lang="fr"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">

{GA_SNIPPET}<title>Track Record — Transparence des pronostics Bravo Quinté</title>

<meta name="description" content="Statistiques publiques : {stats['base_in_top5_rate']} base dans le top 5, {stats['top5_avg_in_top5']} nos 5 premiers dans le top 5.">

<link rel="canonical" href="{base}track-record.html">

<meta property="og:type" content="website"/>

<meta property="og:title" content="Track Record — Transparence des pronostics Bravo Quinté"/>

<meta property="og:description" content="Statistiques publiques : {stats['base_in_top5_rate']} base dans le top 5, {stats['top5_avg_in_top5']} nos 5 premiers dans le top 5."/>

<meta property="og:url" content="{base}track-record.html"/>

<meta property="og:locale" content="fr_FR"/>

<meta name="twitter:card" content="summary"/>

<meta name="twitter:title" content="Track Record — Transparence des pronostics Bravo Quinté"/>

<style>:root{{--primary:#16a34a;--dark:#0f172a;--gray:#64748b;--border:#e2e8f0}}body{{font-family:'Inter',system-ui,sans-serif;margin:0;padding:0;color:var(--dark);background:#fff;line-height:1.6}}.container{{max-width:900px;margin:0 auto;padding:1.5rem}}h1{{font-size:2rem;margin:1rem 0}}h2{{font-size:1.4rem;margin:2rem 0 .5rem;border-bottom:2px solid var(--primary);padding-bottom:.4rem}}.meta{{color:var(--gray);font-size:.9rem;margin-bottom:1.5rem}}.card{{background:#f8fafc;border:1px solid var(--border);border-radius:12px;padding:1.5rem;margin:1rem 0}}.btn{{display:inline-block;background:var(--primary);color:#fff;padding:.75rem 1.5rem;border-radius:8px;text-decoration:none;font-weight:600}}a{{color:var(--primary)}}table{{width:100%;border-collapse:collapse;margin:1rem 0;font-size:.9rem}}th{{background:var(--dark);color:#fff;padding:.75rem;text-align:left}}td{{padding:.75rem;border-bottom:1px solid var(--border)}}tr:nth-child(even){{background:#f8fafc}}footer{{text-align:center;padding:2rem;color:var(--gray);font-size:.85rem;border-top:1px solid var(--border);margin-top:2rem}}.stat{{display:inline-block;background:#f0fdf4;border:2px solid #86efac;border-radius:12px;padding:1rem 1.5rem;text-align:center;margin:.5rem}}.stat-value{{font-size:2rem;font-weight:700;color:var(--primary);margin:0}}.stat-label{{font-size:.85rem;color:var(--gray);margin:0}}.ok{{color:#16a34a}}.miss{{color:#dc2626}}.wait{{color:#d97706}}.badge{{display:inline-block;font-size:.75rem;font-weight:700;padding:.25rem .5rem;border-radius:9999px}}.badge-ok{{background:#dcfce7;color:#15803d}}.badge-wait{{background:#fef3c7;color:#92400e}}</style></head><body>

{kpis}

{table}

{method}'''



io.open(os.path.join(repo, 'track-record.html'), 'w', encoding='utf-8', newline='').write(html)

print(f'track-record.html régénéré ({len(preds)} prédictions)')



# 4. presse.html : KPI et date depuis le ledger

import importlib.util

_spec = importlib.util.spec_from_file_location(

    'update_presse', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'update-presse.py'))

_up = importlib.util.module_from_spec(_spec)

_spec.loader.exec_module(_up)

if not _up.update(repo):

    print('ATTENTION : incohérence entre le ledger et les stats, à vérifier')



# 5. sitemap.xml : pages HTML reellement presentes

import subprocess, sys as _sys

_sp = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gen-sitemap.py')

if os.path.exists(_sp):

    subprocess.run([_sys.executable, _sp], check=True)

else:

    print('ATTENTION : gen-sitemap.py introuvable')