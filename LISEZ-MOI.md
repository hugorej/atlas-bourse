# ATLAS V2 — Déploiement sans abonnement

Cette version ajoute un système de rapports automatiques de clôture, MAIS elle **n'est pas encore connectée à ton compte GitHub** et aucune tâche n'a été exécutée. Les graphiques TradingView fonctionnent indépendamment du module des rapports.

## En quatre étapes

1. Crée un compte sur https://github.com si nécessaire, puis un dépôt **public** nommé `atlas-bourse`.
2. Décompresse le ZIP et transfère **le contenu** du dossier `atlas_bourse_v2` à la racine du dépôt. Pour préserver `.github/workflows/markets.yml` (un dossier caché sur Mac), préfère GitHub Desktop ou les outils Git; vérifie la présence de `.github` dans le dépôt.
3. Dans le dépôt : **Settings > Pages > Build and deployment > Deploy from a branch**, puis choisis `main` et `/(root)`. L'URL sera `https://TON-PSEUDO.github.io/atlas-bourse/`.
4. Dans **Actions > ATLAS - Rapports automatiques > Run workflow**, déclenche un premier rapport. Vérifie le résultat dans l'onglet Actions, puis le fichier `data/latest.json`. Les prochains rapports sont planifiés les jours ouvrés à 23h15 Europe/Paris, avec de possibles retards (GitHub Actions n'est pas une horloge garantie).

## Ce qui est et n'est pas fait

- Après mise en ligne et activation du workflow, le serveur GitHub exécute `update_reports.py`, télécharge les cours disponibles, calcule les variations et classements sur **20 titres US et 20 titres Europe** et sauvegarde une page de rapport. Le vendredi il ajoute une comparaison entre instantanés disponibles de la semaine. Un manque de données déclenche une erreur plutôt que de publier un faux rapport.
- Il ne couvre PAS la totalité du S&P 500 ou de l'Euro Stoxx 50; les résultats affichent explicitement l'univers choisi. Le fournisseur `yfinance` est non officiel, ne garantit ni la fiabilité ni les droits de redistribution, et peut cesser de fonctionner. Les cours sont des clôtures, pas du temps réel assuré.
- Ce programme NE génère PAS d'explications causales par IA ni de résumé des actualités : il serait trompeur de les inventer en l'absence de news vérifiées. Le rapport détaillé ChatGPT programmé demeure séparé. Pour la génération IA intégrée, il faudra connecter une source de nouvelles sourcées et une API de modèle (coût à l'usage), en gardant les clés dans **GitHub Actions Secrets**, jamais dans `index.html`.
- Le dépôt public signifie que les rapports sont publics. Ne publie aucune donnée de patrimoine, compte, relevé ou clé secrète dans le dépôt.
- Les workflows planifiés sur certains dépôts publics inactifs peuvent être désactivés après 60 jours d'inactivité; des exécutions planifiées peuvent être retardées. Vérifie de temps à autre l'onglet Actions.

## Coût

0 € de GitHub Pages et GitHub Actions dans les limites de l'offre publique. Le fournisseur non officiel est gratuit mais imparfait. Il faut payer si l'on souhaite des données temps réel garanties/licenciées et éventuellement une génération de texte IA avec API.

## Pour un site privé

GitHub Pages public n'est pas adapté à des données personnelles. Utilise une autre architecture privée avec authentification si tu ajoutes ton portefeuille réel.
