# Projet Intégration Continue — Pipeline Data

Pipeline automatisée : CSV, images OCR et texte SLM, stockage S3 local,
validation, traitements purs et insertion dans PostgreSQL.
GitHub Actions exécute les tests à chaque push sur `main` et pull request.
Après réussite des tests sur `main`, il construit et publie l'image Docker dans
GitHub Container Registry : c'est la livraison continue.

Les deux améliorations du niveau 3 sont **l'option 2 (OCR)** et **l'option 3 (SLM)**.
Les options de déploiement en production et de Terraform cloud ne sont pas choisies.

```text
CSV générés ---------------------+
Image -> Tesseract -> champs -----+-> CSV commun -> S3 -> Validation -> Traitement -> PostgreSQL
Texte -> Qwen local -> champs ----+
```

## Préparation et démonstration (PowerShell)

Prérequis : Python 3.13 et Docker Desktop démarré avec les conteneurs Linux.
À la racine du dépôt :

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m src.preparer_demo
```

La préparation construit l'image Docker `pipeline-data:local` avec Tesseract,
démarre les services et télécharge le vrai modèle `qwen2.5:0.5b` dans Ollama.
Les images Docker représentent plusieurs Go et le modèle environ 398 Mo : préparer
les outils **avant** l'oral. Le modèle reste dans un volume Docker, sans compte cloud.

```powershell
.\.venv\Scripts\python.exe -m src.demo verifier
.\.venv\Scripts\python.exe -m src.demo image
.\.venv\Scripts\python.exe -m src.demo texte
.\.venv\Scripts\python.exe -m src.demo tout
```

`verifier` exécute les deux moteurs réels puis compare aux exemples attendus.
Les références JSON sont des oracles de test, jamais des réponses de remplacement.
La base `transactions_demo` est créée automatiquement et séparée des autres bases.
Les exemples représentent 6200 EUR (flag vrai) et 1250,50 EUR (flag faux).
Après les deux premiers imports, `tout` ne doit ajouter aucune transaction.
Les extractions lisibles sont aussi enregistrées dans `artifacts/`, non versionné.

```powershell
.\.venv\Scripts\python.exe -m src.demo bilan
.\.venv\Scripts\python.exe -m src.demo image --fichier examples/transaction.png
.\.venv\Scripts\python.exe -m src.pipeline
```

La dernière commande lance la pipeline CSV complète : démarrage des services,
création des tables, génération, upload puis traitement depuis S3.

## Tests et CI

```powershell
.\.venv\Scripts\python.exe -c "from src.demo import initialiser_base; initialiser_base('transactions_test')"
.\.venv\Scripts\python.exe -m pytest tests -v
```

La suite complète nécessite les services préparés et teste aussi le vrai OCR et le
vrai SLM, jusqu'à S3 et PostgreSQL. La CI prépare ces mêmes outils et n'ignore pas les
deux tests d'extraction réels. Les bases de démonstration ne sont pas vidées par les tests.
Pour les tests rapides sans services :

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_load_data.py tests/test_process_data.py tests/test_retry.py tests/test_s3_retry.py tests/test_extraction.py -v
```

## Comprendre et présenter

- [Guide oral et scénario de démo](docs/presentation.md)
- [Résumé des tests](docs/tests.md)
- [Correspondance avec la consigne](docs/conformite.md)
- [Échec CI et correction avec captures](docs/echec_pipeline.md)
- [Livraison Docker automatique et vérification](docs/livraison.md)

## Périmètre annoncé

- Une transaction par image étiquetée ou texte ; l'OCR n'interprète pas tous les relevés.
- Les sept champs doivent être disponibles. Les extractions incomplètes sont refusées.
- Le SLM peut se tromper : schéma JSON, validation et contrôle de présence des valeurs
  réduisent les erreurs sans garantir la compréhension de tous les textes.
- La forme des IBAN est vérifiée, pas leur clé bancaire modulo 97.
- L'anti-doublon reconnaît le même CSV normalisé, pas toute description différente
  d'un même virement réel.
- L'inférence est locale et peut être lente au premier chargement.
- La CI est automatisée ; aucun déploiement de production n'est revendiqué.

Sources : [Tesseract](https://tesseract-ocr.github.io/tessdoc/Command-Line-Usage.html),
[Ollama Docker](https://docs.ollama.com/docker),
[JSON structuré](https://docs.ollama.com/capabilities/structured-outputs),
[Qwen2.5 0.5B](https://ollama.com/library/qwen2.5:0.5b).

## Structure

| Dossier / fichier | Rôle |
|---|---|
| `src/` | Code Python de la pipeline |
| `tests/` | Tests automatiques (pytest) |
| `sql/` | Création des tables de la base |
| `data/` | Fichiers CSV générés (non versionnés) |
| `.github/workflows/` | Pipeline CI GitHub Actions |
| `requirements.txt` | Librairies Python nécessaires |
| `compose.yaml` | PostgreSQL, SeaweedFS et Ollama local optionnel |
| `examples/` | Image, texte et résultats attendus pour les tests |
| `Dockerfile` | Outil OCR local avec Tesseract |

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
Les tables sont définies dans `sql/create_tables.sql`.
Les identifiants présents dans Compose sont réservés à la démonstration locale.
Les ports ne sont publiés que sur l'interface locale.

Les connexions Python acceptent `PGHOST`, `PGPORT`, `PGUSER`, `PGPASSWORD`,
`S3_ENDPOINT_URL`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `S3_BUCKET`, `OLLAMA_URL`,
`SLM_MODEL` et `TESSERACT_CMD`.

Pour arrêter le service en conservant les données :

```powershell
docker compose --profile niveau3 stop
```
