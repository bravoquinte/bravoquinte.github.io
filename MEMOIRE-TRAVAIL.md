# Mémoire de travail — Bravo Quinté (bravoquinte.github.io)

## Dernière session : 21 octobre 2026

### État du site
- **Site live** : https://bravoquinte.github.io/
- **Dernier article publié** : `pronostic-quinte-toulouse-21-octobre.html` (Toulouse, Grand Prix de la Ville Rose, Trot attelé, 2950m, 13 partants)
- **Vidéo accueil actuelle** : https://youtu.be/GzTSQc1Xawk (remplacée le 21/10)
- **Dernier commit** : `518efb5` — "Remplacer video accueil par GzTSQc1Xawk"
- **Dernier commit pipeline** : `d929e85` — "Daily 2026-10-21: Toulouse Grand Prix de la Ville Rose"

### Workflow de mise à jour quotidienne

#### Étapes (dans l'ordre)
1. **Récupérer les partants** depuis ParisTurf : `https://www.paris-turf.com/quinte/YYYY-MM-DD`
2. **Créer le fichier JSON des chevaux** : `chevaux-<hippo>-<date>.json` (format avec numero, nom, driver, entraineur, musique, cote, poids, corde, age, sexe)
3. **Télécharger la vignette YouTube** → `images/quinte-YYYY-MM-DD.webp` + `images/video-hero.webp`
4. **Lancer daily-pipeline.py** avec tous les arguments
5. **Commit + push** sur main

#### Commande pipeline type
```powershell
cd "C:\Users\brahi\Desktop\bravoquinte"
python daily-pipeline.py `
  --repo "C:\Users\brahi\Desktop\bravoquinte" `
  --video "VIDEO_ID" `
  --date "YYYY-MM-DD" `
  --hippo "Hippodrome" `
  --course "Nom de la course" `
  --discipline "Trot Attelé" (ou "Plat", "Galop Obstacle") `
  --dist "2950m" `
  --dotation "39000" `
  --slug "pronostic-quinte-hippo-DD-mois" `
  --partants 13 `
  --chevaux "@chevaux-hippo-DD-mois.json" `
  --selection "12,10,13,1,7,4,5,8" `
  --top5 "12,10,13,1,7" `
  --base 12 `
  --corde "Corde à droite" `
  --narration "Le scénario.|Paragraphe scenario." `
  --resultat "4-2-6-1-13" `
  --date-prev "YYYY-MM-DD" `
  --hippo-prev "Hippodrome precedent" `
  --course-prev "Course precedente" `
  --discipline-prev "Discipline precedente" `
  --dist-prev "Distance precedente" `
  --chevaux-prev "@chevaux-hippo-prev-DD-mois.json" `
  --commit
```

#### Téléchargement vignette YouTube
```powershell
python -c "
import urllib.request
from PIL import Image
url = 'https://img.youtube.com/vi/VIDEO_ID/maxresdefault.jpg'
urllib.request.urlretrieve(url, 'C:/Users/brahi/AppData/Local/Temp/opencode/yt-thumb.jpg')
img = Image.open('C:/Users/brahi/AppData/Local/Temp/opencode/yt-thumb.jpg')
img.save('C:/Users/brahi/Desktop/bravoquinte/images/quinte-YYYY-MM-DD.webp', 'WEBP')
img.save('C:/Users/brahi/Desktop/bravoquinte/images/video-hero.webp', 'WEBP')
"
```

#### Remplacer vidéo accueil seule
```powershell
cd "C:\Users\brahi\Desktop\bravoquinte"
# 1. Télécharger thumbnail
# 2. Mettre à jour index.html
(Get-Content index.html) -replace 'youtu\.be/ANCIEN_ID','youtu.be/NOUVEAU_ID' | Set-Content index.html
(Get-Content index.html) -replace 'img\.youtube\.com/vi/ANCIEN_ID','img.youtube.com/vi/NOUVEAU_ID' | Set-Content index.html
# 3. Commit + push
git add index.html images/video-hero.webp
git commit -m "Remplacer video accueil par NOUVEAU_ID"
git push origin main
```

### Problèmes rencontrés et solutions

#### 1. GitHub Pages ne se déploie pas (404 sur nouveaux fichiers)
- **Cause** : GitHub Pages n'a pas redéployé automatiquement après les commits
- **Solution tentée** : Ajout `.nojekyll` (commit `7161c9b`) — toujours 404
- **Statut** : Non résolu côté GitHub, les fichiers sont bien sur le repo
- **Vérification** : Les fichiers sont accessibles via raw.githubusercontent.com

#### 2. PowerShell ne supporte pas `&&`
- **Cause** : PowerShell utilise `;` pas `&&`
- **Solution** : Utiliser `;` pour chaîner les commandes

#### 3. `curl` est un alias PowerShell (Invoke-WebRequest)
- **Solution** : Utiliser `curl.exe` au lieu de `curl`

#### 4. `head`, `tail`, `sed`, `wc`, `grep` non disponibles
- **Solution** : Utiliser `Select-Object -First N`, `Select-String`, `Get-Content`

#### 5. Push rejected (fetch first)
- **Solution** : `git pull --rebase origin main` puis `git push origin main`

#### 6. Cotes non fiables (ParisTurf `--`, Equidia PMU vide)
- **Solution** : Utiliser "—" pour toutes les cotes

### Données récentes

#### Résultats enregistrés (RESULTATS)
- 17/10 Auteuil : 1-6-4-11-2
- 16/10 Vincennes : 4-11-7-6-13
- 15/10 Chantilly : 12-11-8-9-15
- 14/10 Reims : 10-15-13-5-9
- 13/10 Longchamp : 9-16-2-14-1
- 12/10 Marseille : 2-10-14-11-12
- 11/10 Auteuil : 15-2-3-12-1
- 19/10 Deauville : 4-2-6-1-13 (ajouté le 21/10)

#### Résultat en attente
- 20/10 Clairefontaine : 5-13-14-3-15 (à ajouter au prochain update)

#### Fichiers chevaux disponibles
- `chevaux-deauville-19-octobre.json` (16 partants)
- `chevaux-toulouse-21-octobre.json` (13 partants)

### Configuration
- **Repo** : `C:\Users\brahi\Desktop\bravoquinte`
- **Remote** : https://github.com/bravoquinte/bravoquinte.github.io.git
- **Branche** : main
- **Python** : 3.13.13
- **PIL** : 12.2.0
- **ImageMagick** : `C:\Program Files\ImageMagick\magick.exe`
- **ffmpeg** : `C:\Users\brahi\ffmpeg\ffmpeg-9.0.1-essentials_build\bin\ffmpeg.exe`

### URLs importantes
- Site : https://bravoquinte.github.io/
- Repo : https://github.com/bravoquinte/bravoquinte.github.io
- ParisTurf partants : https://www.paris-turf.com/quinte/YYYY-MM-DD
- Equidia : https://www.equidia.fr/courses/YYYY-MM-DD/R1/C3
- YouTube thumbnail : https://img.youtube.com/vi/VIDEO_ID/maxresdefault.jpg

### Règles permanentes
- Ton de narration selon le jour de la semaine (Lundi=Audacieux, Mardi=Passionné, Mercredi=Technique, Jeudi=Historique, Vendredi=Élégant, Samedi=Festif, Dimanche=Zen)
- Cotes indisponibles → utiliser "—"
- Montants en toutes lettres dans la narration
- Pas de musiques codées
- Pas de numérotation orale
- Noms complets (pas d'initiales)
- Site écrit "bravoquinté" (pas l'URL)
