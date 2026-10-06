#!/usr/bin/env python3
"""Regenere sitemap.xml a partir des pages HTML du depot.

Exclut 404.html, mappe index.html sur la racine, dedoublonne les <loc> et
pose un <lastmod> date du dernier commit touchant le fichier.
"""
import glob
import os
import re
import subprocess
import sys
from datetime import date

REPO = os.path.dirname(os.path.abspath(__file__))
BASE = 'https://bravoquinte.github.io/'
EXCLUDED = {'404.html'}


def last_commit_dates():
    """date ISO du dernier commit par fichier, relatifs au depot."""
    try:
        out = subprocess.run(
            ['git', '-C', REPO, 'log', '--format=%cs', '--name-only', '--', '.'],
            capture_output=True, text=True, encoding='utf-8', errors='replace',
            check=True).stdout
    except Exception:
        return {}
    dates, courant = {}, None
    for ligne in out.splitlines():
        ligne = ligne.strip()
        if not ligne:
            continue
        if re.fullmatch(r'\d{4}-\d{2}-\d{2}', ligne):
            courant = ligne
        elif courant:
            dates.setdefault(os.path.basename(ligne), courant)
    return dates


def main():
    commits = last_commit_dates()
    aujourdhui = date.today().isoformat()

    urls = []
    for path in sorted(glob.glob(os.path.join(REPO, '*.html'))):
        name = os.path.basename(path)
        if name in EXCLUDED:
            continue
        loc = BASE if name == 'index.html' else BASE + name
        lastmod = commits.get(name)
        if not lastmod:
            lastmod = date.fromtimestamp(os.path.getmtime(path)).isoformat()
        urls.append((loc, lastmod))

    # dedoublonne en conservant le lastmod le plus recent
    best = {}
    for loc, lm in urls:
        if loc not in best or lm > best[loc]:
            best[loc] = lm
    items = sorted(best.items(), key=lambda kv: kv[0])

    lignes = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for loc, lm in items:
        lignes.append(f'  <url><loc>{loc}</loc><lastmod>{lm}</lastmod></url>')
    lignes.append('</urlset>')
    lignes.append('')

    out = os.path.join(REPO, 'sitemap.xml')
    with open(out, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(lignes))

    print(f'sitemap.xml : {len(items)} URLs, dernier lastmod '
          f'{max(lm for _, lm in items)} (defaut {aujourdhui})')
    return 0


if __name__ == '__main__':
    sys.exit(main())
