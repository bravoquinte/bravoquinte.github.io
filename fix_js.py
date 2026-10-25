c = open('index.html', encoding='utf-8').read()

# 1. Remplacer var chevaux (chercher par regex pour etre sur)
import re

new_chevaux = 'var chevaux=[{num:1,nom:"Agile",driver:"Velon M.",entraineur:"Beguigne J-M.",musique:"-",cote:"-"},{num:2,nom:"Shrihara",driver:"Hamelin A.",entraineur:"Fey C.",musique:"-",cote:"-"},{num:3,nom:"Maia Star",driver:"Boudot P-C.",entraineur:"Dubois J-P.",musique:"-",cote:"-"},{num:4,nom:"American Glory",driver:"Lemaitre A.",entraineur:"Perret N.",musique:"-",cote:"-"},{num:5,nom:"Hasapiko",driver:"Bachelot T.",entraineur:"Wattel S.",musique:"-",cote:"-"},{num:6,nom:"Weemagatee",driver:"Grandin M.",entraineur:"Andreu J.",musique:"-",cote:"-"},{num:7,nom:"Ame d Or",driver:"Barzalona M.",entraineur:"Graffard F-H.",musique:"-",cote:"-"},{num:8,nom:"Cristabel",driver:"d Andigne O.",entraineur:"Couetil A.",musique:"-",cote:"-"},{num:9,nom:"Marinaleda",driver:"Lecoeuvre C.",entraineur:"Baratti M.",musique:"-",cote:"-"},{num:10,nom:"Britania",driver:"Mendizabal I.",entraineur:"Rohaut F.",musique:"-",cote:"-"},{num:11,nom:"Golden Belle",driver:"Guyon M.",entraineur:"Fouassier A.",musique:"-",cote:"-"},{num:12,nom:"Foxey Lady",driver:"Favriaux M.",entraineur:"Beguigne J-M.",musique:"-",cote:"-"},{num:13,nom:"Nancy des Places",driver:"Hardouin E.",entraineur:"Fey C.",musique:"-",cote:"-"},{num:14,nom:"Teardrop Explodes",driver:"Veron F.",entraineur:"Boutin C.",musique:"-",cote:"-"},{num:15,nom:"Janah",driver:"Pasquier S.",entraineur:"Clement N.",musique:"-",cote:"-"},{num:16,nom:"Gareya",driver:"Madamet A.",entraineur:"Delzangles M.",musique:"-",cote:"-"}];'

new_sel   = 'var selection=[2,15,8,13,7,11,9,3];'
new_top   = 'var top5=[2,15,8,13,7];'

# Remplacer via regex pour ne pas se battre avec les quotes
c = re.sub(r'var chevaux=\[.*?\];', new_chevaux, c)
c = re.sub(r'var selection=\[.*?\];', new_sel, c)
c = re.sub(r'var top5=\[.*?\];', new_top, c)

# Remplacer base highlight num===4 -> num===2 || num===15
c = c.replace('c.num===4', 'c.num===2||c.num===15')

# Verifier
print('chevaux Shrihara:', 'Shrihara' in c)
print('selection 2,15:', '[2,15,8,13,7,11,9,3]' in c)
print('top5 2,15:', '[2,15,8,13,7]' in c)

open('index.html', 'w', encoding='utf-8').write(c)
print('OK - index.html mis a jour')
