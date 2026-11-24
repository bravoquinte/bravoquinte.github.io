# BRAVOSCOUT — flux quotidien (instruction permanente)

## Regle etablie par l'utilisateur (24/11/2026)

**Chaque jour, des que les partants du quinte sont fournis (+ cotes si disponibles),
l'agent lance bravoscout AUTOMATIQUEMENT et propose la selection.
La selection finale est validee par l'utilisateur AVANT toute publication.
Apres validation, le flux habituel du site s'execute (update-quinte-jour.py,
article, archives, push — sans redemander le push).**

## Sequence quotidienne

1. L'utilisateur fournit : partants (JSON `chevaux-<hippo>-<JJ>-<mois>.json`),
   cotes (texte colle ou URL), video YouTube, narration, arrivee de la veille.
2. L'agent lance :
   ```
   py -3.13 bravoscout.py --chevaux @chevaux-<hippo>-<JJ>-<mois>.json \
       --dist Xm --cotes "n: cote, n: cote, ..." \
       [--votre-selection "n,n,..."]
   ```
   (--cotes-url si l'utilisateur donne une URL de cotes a la place)
3. L'agent PRESENTE la proposition : SELECTION 8 / TOP 5 / BASE + confiance,
   alertes VALUE/SURCOTE, et le differentiel si l'utilisateur a aussi propose
   sa propre selection.
4. L'utilisateur valide ou corrige la selection.
5. L'agent execute le flux site complet avec la selection validee :
   ```
   py -3.13 update-quinte-jour.py --date ... --video ... --selection "..."
     --top5 "..." --base N --chevaux "@..." --resultat "..." --commit
   ```
   puis l'article blog (ton selon le jour), puis PUSH IMMEDIAT sans demander
   (regle utilisateur), puis verification live.

## Regles du score

- Ponderations : `poids-backtest.json` (calibre par `py -3.13 backtest.py`,
  walk-forward honnete — ne jamais calibrer sur des donnees futures).
- Cotes manquantes : feature neutre, le pronostic tourne quand meme (alerte).
- Comparaison humain vs outil : tracee chaque jour via le track record ;
  le tool sert d'assistant, la decision finale reste humaine.
