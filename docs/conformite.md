# Correspondance avec la consigne

## Niveau 1

| Exigence | Réalisation |
|---|---|
| Plusieurs CSV de 5 à 10 transactions, données testables | `generate_data.py`, comptes et montants fixes, seed 42 ; cas limites dans les tests |
| Trois sommes et flag strictement supérieur à 5000 | `process_data.py`, fonctions pures ; tests Python et SQL |
| Chargement séparé des calculs | `load_data.py` et `process_data.py` |
| Base et insertion des résultats | PostgreSQL, cinq tables, `database.py` |
| Pipeline automatique | `python -m src.pipeline` |
| Tests d'intégration en CI | Vrais PostgreSQL et S3 dans GitHub Actions |
| Échec avec captures | `echec_pipeline.md` et captures cause/échec/correction/succès |
| Retry SQL, délai et limite | `inserer_avec_retry`, tests temporaire/persistant |
| Pas de double traitement même avec retry | SHA-256, clé primaire, transaction SQL, test de confirmation perdue |

## Niveau 2

| Exigence | Réalisation |
|---|---|
| S3 local | SeaweedFS dans Compose et CI |
| Démarrage et bucket automatique | `pipeline.py`, `S3_BUCKET`, attente explicite |
| Upload et vérification | Existence/taille puis comparaison des octets dans les tests |
| Traitement depuis S3 | `traiter_s3.py`, lecture en mémoire sans CSV local |
| Anti-doublon conservé | Hash indépendant du nom et de l'origine |
| Retry S3 | Erreurs temporaires, délai, limite et transmission de l'erreur |

## Niveau 3 : deux options choisies

- **Option 2 — OCR** : Tesseract lit réellement l'image ; les champs sont normalisés
  puis rejoignent CSV, S3, validation, calculs et PostgreSQL. Test d'intégration réel.
- **Option 3 — SLM** : Qwen2.5 0.5B local extrait les champs d'une phrase ; JSON contraint,
  vérifications, CSV, S3 puis même pipeline. Test d'intégration réel.

La consigne exige « au moins deux » options. Ces deux-là couvrent les branches image
et texte du schéma fourni. Les options 1 (déploiement de production) et 4 (Terraform
cloud) ne sont pas revendiquées.

## Mention générale « démarche CI/CD »

Le workflow automatise les tests (CI), puis construit et publie une image Docker
dans GitHub Container Registry (livraison continue). La publication attend la réussite
des tests et s'exécute uniquement sur `main`, jamais sur une pull request.
Une version liée au commit et un tag `latest` permettent de retrouver la livraison.
La configuration doit être confirmée par une première exécution réussie sur GitHub.

Le déploiement de production avec planification décrit dans l'option 1 n'est pas
réalisé. La livraison d'une image ne lance pas l'application sur un serveur distant.
Voir `livraison.md` pour la vérification et la démonstration.

## Limites

Une transaction par avis étiqueté ou phrase complète. La forme des IBAN est vérifiée,
pas leur clé modulo 97. Les dates sont sans fuseau, comme les CSV initiaux. Un modèle
peut se tromper malgré les contrôles ; les exemples sont vérifiés avant l'oral.
