# Projet Intégration Continue — Pipeline Data

Pipeline data automatisée : génération de transactions financières (CSV),
chargement, traitement, puis insertion dans une base PostgreSQL.
Objectif à venir : chaque push sur GitHub déclenchera la pipeline CI
(GitHub Actions) et les tests.

## Structure

| Dossier / fichier | Rôle |
|---|---|
| `src/` | Code Python de la pipeline |
| `tests/` | Tests automatiques (pytest) |
| `sql/` | Création des tables de la base |
| `data/` | Fichiers CSV générés (non versionnés) |
| `.github/workflows/` | Pipeline CI GitHub Actions |
| `requirements.txt` | Librairies Python nécessaires |
| `compose.yaml` | Service PostgreSQL local et stockage persistant |

## Démarrer PostgreSQL en local

Ouvrir Docker Desktop, puis exécuter à la racine du projet :

```powershell
docker compose up -d --wait postgres
docker compose ps
docker compose exec -T postgres psql -U pipeline -d transactions -c "SELECT current_database(), current_user;"
```

La base `transactions` est accessible sur `127.0.0.1:5432`, avec l'utilisateur
`pipeline` et le mot de passe de démonstration `pipeline_local`.
Les données sont conservées dans le volume Docker `postgres_data`.
Les tables et l'insertion Python seront ajoutées lors des prochaines étapes.

Pour arrêter le service en conservant les données :

```powershell
docker compose stop postgres
```
