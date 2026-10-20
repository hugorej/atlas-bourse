# ATLAS Bourse — V3 (français)

## Ce qui change

- Panorama US et européen avec vrais chiffres datés, remplis depuis `data/latest.json` (et **pas en temps réel**). Si un cours manque, l'interface l'indique au lieu d'afficher un faux chiffre.
- Classement des 5 hausses et 5 baisses parmi 20 **grandes entreprises connues** aux États-Unis et 20 en Europe, avec filtre de secteur.
- Comparatif sectoriel calculé sur les entreprises de cette sélection ; **ce ne sont pas des indices sectoriels officiels**.
- Une liste d'actualités en français depuis un flux Google Actualités RSS lors de la génération du rapport, sans payer de clé API. La récupération n'est pas garantie, certains titres peuvent manquer ; en cas d'échec, des liens de médias français restent disponibles.
- La carte thermique TradingView et la watchlist sont conservées.
- Un débrief de chiffres est généré par GitHub. **Les explications détaillées par IA ne sont pas incluses dans le site**. Ton brief ChatGPT à 21 h est une tâche séparée.

## Installer sur le GitHub déjà créé

1. Ouvrir `https://github.com/hugorej/atlas-bourse` puis **Code > Add file > Upload files**.
2. Depuis le dossier V3 décompressé, déposer ces **trois fichiers seulement** à la racine : `index.html`, `update_reports.py` et `requirements.txt`. Cela remplace les versions précédentes. Cliquer sur **Commit changes**.
3. Dans ton dépôt, ouvrir `.github/workflows/markets.yml` (ou suivre le lien `https://github.com/hugorej/atlas-bourse/blob/main/.github/workflows/markets.yml`), cliquer sur le crayon, puis modifier la ligne `cron` à `cron: '15 23 * * 1-5'` et vérifier la ligne suivante `timezone: Europe/Paris`. Cette programmation lance le rapport du site vers **23 h 15 Paris** pour respecter la clôture américaine. Cliquer sur **Commit changes**. Ou remplacer le fichier complet par celui du ZIP au même emplacement.
4. Cliquer sur **Actions > ATLAS - Rapports automatiques > Run workflow > Run workflow** pour tester. La coche verte confirme l'exécution du code, puis vérifier le fichier `data/latest.json` dans **Code**.
5. Ouvrir `https://hugorej.github.io/atlas-bourse/` et actualiser. Les titres d'actualités en français apparaîtront après un lancement réussi de **V3**. Le site peut mettre un peu de temps à publier les changements.

Remarque : si le script échoue à cause d'une limite Yahoo Finance ou Google RSS, GitHub affichera une croix rouge et le précédent `latest.json` restera disponible. Les cours ne sont ni garantis ni utilisables pour passer des ordres.

### Vérification des noms de fichiers

À la racine GitHub, tu dois voir `index.html`, `update_reports.py` et `requirements.txt`. Le workflow doit être dans le **dossier** `.github/workflows/markets.yml` : ce nom n'est pas un fichier racine. `data/latest.json` est généré par le programme, pas à téléverser.

### Coût

Aucun coût supplémentaire prévu avec GitHub Pages/Actions (dépôt public, selon les quotas applicables), widgets et flux RSS gratuits. Données différées et limitées. Une future synthèse IA directement sur le site nécessiterait une connexion à un service IA, parfois payant.
