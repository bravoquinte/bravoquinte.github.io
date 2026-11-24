# -*- coding: utf-8 -*-
"""
Synchronise predictions-ledger.json avec la realite du site.

1. Complete les entrees "en_attente" qui ont une arrivee dans resultats.html
   (ex: 26/10 => arrivee renseignee, metrics recalculees, statut "valide").
2. Ajoute les dates publiees (articles pronostic-quinte-*.html) absentes du
   ledger, avec selection, base, arrivee et metrics.

Conventions (identiques a update-track-record.py) :
  - selection = 8 chevaux, top5 = 5 premiers de l'arrivee
  - selection_in_top5 = |selection(8) inter top5|
  - base_in_top5 = base in top5, statut = "valide" si arrivee sinon "en_attente"

Parse SANS regex : decoupage de chaines + strip de balises. Detecte les trois
mecanismes d'affichage de selection rencontres sur le site :
  a) <div class="selection">16 - 10 - ...</div>           (gabarit actuel)
  b) <strong>PRONOSTIC : 8 - 3 - ...</strong>             (ancien gabarit)
  c) sequence de 8 nombres dans la prose PRONOSTIC        (laval 01/11)

Appele automatiquement par update-quinte-jour.py avant update-track-record.py.
"""
import glob
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
REPO = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(REPO, 'predictions-ledger.json')

MOIS = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet',
        'août', 'septembre', 'octobre', 'novembre', 'décembre']

PUNC = ' ?!,;:()[]{}"“”‘’…'


def strip_tags(t):
    """Retire toutes les balises <...> du texte (sans regex)."""
    out = []
    i = 0
    while i < len(t):
        if t[i] == '<':
            j = t.find('>', i)
            if j < 0:
                break
            i = j + 1
        else:
            out.append(t[i])
            i += 1
    return ''.join(out)


def clean_tokens(txt):
    """Tokens propres : coupe au debut de toute balise residuelle, retire la ponctuation."""
    out = []
    for t in txt.split():
        t = t.split('<')[0]
        t = t.strip(PUNC + '…')
        if t:
            out.append(t)
    return out


def seq_at(tokens, start, min_len):
    """Sequence nombre / tiret / nombre ... commencant a start (token chiffre)."""
    seq = []
    i = start
    while i < len(tokens):
        t = tokens[i]
        if t.isdigit():
            seq.append(int(t))
            i += 1
            if i < len(tokens) and tokens[i] in ('-', '–', '—'):
                i += 1
                continue
            break
        break
    return seq if len(seq) >= min_len else []


def first_seq(txt, min_len):
    toks = clean_tokens(txt)
    for k in range(len(toks)):
        if toks[k].isdigit():
            s = seq_at(toks, k, min_len)
            if s:
                return s
    return None


def extract_selection(html):
    # a) gabarit actuel : contenu exact de la div .selection
    i = html.find('class="selection">')
    if i > 0:
        start = i + len('class="selection">')
        end = html.find('</div>', start)
        if end > start:
            s = first_seq(html[start:end], 5)
            if s:
                return s
    # b) ancien gabarit : <strong>PRONOSTIC : 8 - 3 - ...</strong>
    i = html.find('PRONOSTIC :')
    if i > 0:
        start = i + len('PRONOSTIC :')
        end = html.find('</strong>', start)
        if end > start:
            s = first_seq(html[start:end], 5)
            if s:
                return s
    # c) premiere longue sequence (>= 8 nombres) dans le corps visible
    body = html[html.find('<body'):]
    return first_seq(strip_tags(body), 8)


def extract_base(html, selection):
    toks = clean_tokens(strip_tags(html[html.find('<body'):]))
    for k, t in enumerate(toks):
        if t.endswith('Base'):
            for j in range(k + 1, min(k + 4, len(toks))):
                if toks[j].isdigit():
                    return int(toks[j])
    return selection[0] if selection else None


def parse_articles():
    """date ISO -> dict(selection, base, slug, hippo, course)

    La date vient TOUJOURS du slug (pronostic-quinte-<hippo>-JJ-<mois>) :
    la mention "Publié le" peut etre ecrite la veille de la course.
    Les slugs sans mois sont des pages hors quotidien et sont ignores.
    """
    out = {}
    for path in glob.glob(os.path.join(REPO, 'pronostic-quinte-*.html')):
        slug = os.path.splitext(os.path.basename(path))[0]
        toks = slug.split('-')
        last = toks[-1]
        if last not in MOIS or len(toks) < 3:
            continue  # pages non quotidiennes (ex: pronostic-quinte-du-jour-...)
        try:
            day = int(toks[-2].rstrip('er'))
        except ValueError:
            continue
        month = MOIS.index(last) + 1
        h = io.open(path, encoding='utf-8', errors='replace').read()
        sel = extract_selection(h)
        if not sel or len(sel) < 5:
            continue  # format de selection non reconnu (anciens articles deja au ledger)
        base = extract_base(h, sel)
        hippo = course = ''
        a2 = h.find('<h1>')
        if a2 > 0:
            h1 = strip_tags(h[a2:h.find('</h1>', a2)]).strip()
            if ' - ' in h1:
                course = h1.split(' - ')[0].strip()
                hippo = h1.split(' - ')[1].split(',')[0].strip()
        out[f'2026-{month:02d}-{day:02d}'] = dict(
            selection=sel, base=base, slug=slug, hippo=hippo, course=course)
    return out


def parse_resultats():
    """date ISO -> dict(hippo, course, discipline, dist, arrivee[int x5])"""
    c = io.open(os.path.join(REPO, 'resultats.html'), encoding='utf-8').read()
    out = {}
    for row in c.split('<tr><td>')[1:]:
        cells = row.split('</td><td>')
        if len(cells) < 6:
            continue
        date = cells[0]
        if len(date) != 10 or date[4] != '-':
            continue
        arr_txt = cells[5].split('</td>')[0]
        nums = []
        for part in arr_txt.split(' - '):
            n = part.split('.')[0].strip()
            if n.isdigit():
                nums.append(int(n))
        out[date] = dict(hippo=cells[1], course=cells[2], discipline=cells[3],
                         dist=cells[4], arrivee=nums[:5])
    return out


def build_metrics(sel, base, arr):
    top5 = arr[:5] if arr else []
    return {
        'top5': top5,
        'selection_in_top5': len(set(sel) & set(top5)) if top5 else 0,
        'base_in_top5': (base in top5) if top5 else None,
        'exact_order': False,
    }


def main():
    ledger = json.load(io.open(LEDGER, encoding='utf-8'))
    preds = ledger['predictions']
    arts = parse_articles()
    res = parse_resultats()
    by_date = {p['date']: p for p in preds}

    print(f'sources: {len(arts)} articles, {len(res)} arrivees, ledger: {len(preds)} entrees')

    # reparer les dates publiees la veille de la course (slug = date reelle)
    by_date = {p['date']: p for p in preds}
    repaires = 0
    for p in list(preds):
        toks = p['slug'].split('-')
        if len(toks) >= 3 and toks[-1] in MOIS:
            try:
                d = (int(toks[-2].rstrip('er')), MOIS.index(toks[-1]) + 1, 2026)
            except ValueError:
                continue
            real = f'{d[2]:04d}-{d[1]:02d}-{d[0]:02d}'
            if real != p['date']:
                if real in by_date:
                    preds.remove(p)
                    del by_date[p['date']]
                    print(f'  duplique supprime: {p["date"]} (course reelle {real})')
                else:
                    p['date'] = real
                    by_date[real] = p
                repaires += 1

    completed = 0
    for p in preds:
        r = res.get(p['date'])
        arr = p.get('arrivee') or p.get('resultat')
        if r and r['arrivee'] and not arr:
            a = r['arrivee']
            p['resultat'] = a
            p['arrivee'] = a
            p['metrics'] = build_metrics(p['selection'], p['base'], a)
            p['statut'] = 'valide'
            completed += 1
            print(f'  complete {p["date"]}: arrivee {a}')

    added = 0
    no_art = []
    for date in sorted((set(arts) | set(res)) - set(by_date)):
        art = arts.get(date)
        r = res.get(date)
        if not art:
            no_art.append(date)
            continue
        arr = r['arrivee'] if r else None
        p = {
            'date': date,
            'hippo': (r['hippo'] if r else '') or art['hippo'],
            'course': (r['course'] if r else '') or art['course'],
            'discipline': r['discipline'] if r else '-',
            'dist': r['dist'] if r else '-',
            'slug': art['slug'],
            'selection': art['selection'], 'base': art['base'],
            'resultat': arr, 'arrivee': arr,
            'metrics': build_metrics(art['selection'], art['base'], arr),
            'statut': 'valide' if arr else 'en_attente',
        }
        preds.append(p)
        by_date[date] = p
        added += 1
        state = ('arrivee ' + str(arr)) if arr else 'en attente'
        print(f'  + {date}: {state:24} sel={art["selection"][:5]} base={art["base"]}')

    for p in preds:  # anciennes entrees sans champ statut
        if 'statut' not in p:
            p['statut'] = 'valide' if p.get('arrivee') else 'en_attente'

    preds.sort(key=lambda x: x['date'])
    ledger['predictions'] = preds
    json.dump(ledger, open(LEDGER, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    if no_art:
        print('dates sans article (ignorees):', ', '.join(no_art))
    print(f'completees: {completed} | ajoutees: {added} | total: {len(preds)}')


if __name__ == '__main__':
    main()
