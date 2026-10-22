lines = open('index.html').read().split(chr(10))
for l in lines:
    if 'RESULTATS' in l or 'date:"2026-10-2' in l:
        print(l.strip()[:150])
"