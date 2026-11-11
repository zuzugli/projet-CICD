# Livraison continue de l'image Docker

## Le principe

```text
Push sur main -> tests -> construction Docker -> vérification --help -> publication GHCR
```

Le job `livraison` utilise `needs: tests` : si les tests échouent, aucune image n'est
publiée. Une pull request exécute les tests uniquement. Un lancement manuel depuis
l'onglet Actions publie également si la branche sélectionnée est `main`.

GitHub Container Registry (GHCR) stocke l'image à l'adresse
`ghcr.io/zuzugli/projet-mlops`. Deux tags sont publiés :

- `sha-<identifiant complet du commit>` identifie le code livré ;
- `latest` désigne la dernière livraison réussie.

Le jeton `GITHUB_TOKEN` est fourni automatiquement au workflow par GitHub.
La permission `packages: write` est accordée uniquement au job de livraison.
Aucun jeton personnel n'est à créer ni à mettre dans le dépôt.

## Première validation sur GitHub

1. Envoyer les fichiers du projet, notamment le Dockerfile, les exemples et le workflow.
2. Ouvrir **Actions**, puis **CI/CD - Tests et livraison Docker**.
3. Vérifier que `tests` et `Livrer l'image Docker` sont verts.
4. Ouvrir le résumé de livraison : il affiche le nom et la version exacte de l'image.
5. Dans le dépôt, ouvrir **Packages**, puis le package `projet-mlops`.

La configuration locale n'est pas une preuve de publication : seule une exécution
réussie et le package présent sur GitHub la confirment.

Une nouvelle image GHCR peut être privée même si le dépôt est public. Pour permettre
un téléchargement sans connexion, son propriétaire peut choisir **Package settings
-> Change visibility -> Public**. Cette modification est facultative pour montrer
la livraison depuis son propre compte. En cas de refus de publication, lire l'erreur
du job et vérifier les droits du package et les règles du dépôt avant de relancer.

## Démonstration courte

Après une publication réussie, si le package est public :

```powershell
docker pull ghcr.io/zuzugli/projet-mlops:latest
docker run --rm --network none ghcr.io/zuzugli/projet-mlops:latest
```

Le conteneur affiche l'aide de la démo. Pour montrer le vrai OCR dans l'image livrée,
sans connexion aux autres services :

```powershell
docker run --rm --network none ghcr.io/zuzugli/projet-mlops:latest python -c "from src.ocr import extraire_image; print(extraire_image('examples/transaction.png')[1])"
```

Ces commandes vérifient le contenu de l'image livrée. La démonstration complète
avec S3, PostgreSQL et Ollama suit `presentation.md`, avec les services locaux préparés.
L'image contient Python, les dépendances du projet, Tesseract, le code et les exemples.
Elle ne contient pas les bases de données ni les poids du SLM : ces services sont séparés.

## Formulation pour l'oral

« La CI vérifie le projet. Si elle réussit sur main, la livraison continue construit
et publie une image Docker associée au commit. On peut télécharger cette version
et retrouver le code livré. Je réalise une livraison continue, sans déploiement
automatique en production. Mes deux améliorations sont l'OCR et le SLM. »

Références officielles :
[publication avec GitHub Actions](https://docs.github.com/en/actions/tutorials/publish-packages/publish-docker-images),
[accès et visibilité GHCR](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry).
