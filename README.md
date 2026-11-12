# Pipeline de transactions financières

Pipeline Python de génération et de traitement de transactions fictives : stockage
S3 local avec SeaweedFS, validation, calculs et insertion dans PostgreSQL. Les sources
image et texte rejoignent le même traitement après extraction avec Tesseract et Qwen.

```text
CSV générés ---------------------+
Image -> Tesseract -> champs -----+-> CSV commun -> S3 -> Validation -> Calculs -> PostgreSQL
Texte -> Qwen local -> champs ----+
```

Les améliorations du niveau 3 sont l'OCR (option 2) et le SLM (option 3).
GitHub Actions automatise les tests et la livraison d'une image Docker après leur
réussite sur `main`. Aucun déploiement automatique en production n'est mis en place.

## Installation

Prérequis : Python 3.13 et Docker Desktop démarré avec les conteneurs Linux.
Commandes PowerShell à exécuter à la racine du dépôt :

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Pipeline CSV

```powershell
.\.venv\Scripts\python.exe -m src.pipeline
```

Cette commande démarre PostgreSQL et SeaweedFS, attend le bucket, crée les tables,
génère trois CSV de 5 à 10 transactions avec une seed fixe, les envoie dans S3,
vérifie leur présence et leur taille, puis traite les objets récupérés depuis S3.

Les sept colonnes sont `datetime_transaction`, `iban_origine`, `pays_source`,
`banque_source`, `iban_destinataire`, `pays_destinataire` et `montant`.
Le chargement contrôle les colonnes, les champs obligatoires, les dates et les montants
positifs à deux décimales au maximum. Les montants utilisent `Decimal` et `NUMERIC`.

Les fonctions de calcul sont pures et séparées des accès aux services. Elles calculent
les sommes par IBAN d'origine, banque source et IBAN destinataire, et ajoutent un flag
pour les transactions strictement supérieures à 5 000. Les totaux sont enregistrés
par fichier ; une agrégation SQL permet d'obtenir les totaux cumulés.

## Image et texte

```powershell
.\.venv\Scripts\python.exe -m src.preparer_demo
.\.venv\Scripts\python.exe -m src.demo verifier
.\.venv\Scripts\python.exe -m src.demo tout
```

La préparation construit `pipeline-data:local` avec Tesseract, démarre PostgreSQL,
SeaweedFS et Ollama, puis télécharge `qwen2.5:0.5b`. Le premier lancement nécessite
plusieurs Go de téléchargements Docker et environ 398 Mo pour le modèle.

`verifier` exécute les moteurs et compare les résultats aux références attendues,
sans insertion SQL. `tout` traite les deux sources jusqu'à PostgreSQL et relit le
bilan en base. Les champs normalisés deviennent des CSV envoyés et relus depuis S3.
Les références JSON servent aux vérifications, jamais à remplacer l'inférence.

```powershell
.\.venv\Scripts\python.exe -m src.demo image
.\.venv\Scripts\python.exe -m src.demo texte
.\.venv\Scripts\python.exe -m src.demo bilan
.\.venv\Scripts\python.exe -m src.demo image --fichier examples/transaction.png
```

Les exemples fournissent 6 200 EUR depuis Santander (flag vrai) et 1 250,50 EUR depuis
BNP Paribas (flag faux). Les traces texte et JSON sont écrites dans `artifacts/`,
non versionné. Une relance des mêmes exemples n'ajoute aucune transaction.

## Stockage et fiabilité

SeaweedFS expose S3 sur `127.0.0.1:8333`, avec le bucket `transactions-csv`.
Ses fichiers persistent dans le volume `seaweedfs_data`, distinct du dossier
`data/` du projet. PostgreSQL possède son propre volume, `postgres_data`.

| Base PostgreSQL | Usage |
|---|---|
| `transactions` | Pipeline CSV principale |
| `transactions_demo` | Parcours image et texte, créée automatiquement |
| `transactions_test` | Tests d'intégration, données nettoyées par les tests |

Le schéma `sql/create_tables.sql` définit cinq tables : `transactions`,
`processed_files`, `totaux_iban_origine`, `totaux_banque_source` et
`totaux_iban_destinataire`.

L'empreinte SHA-256 du CSV est unique dans `processed_files`. L'empreinte,
les transactions et les totaux sont confirmés dans une seule transaction SQL ;
une erreur annule l'import. Le même contenu déjà importé ajoute zéro ligne,
même renommé ou lors d'un retry après perte de confirmation.

Les lectures S3 et insertions SQL disposent de trois tentatives maximum et de
deux secondes d'attente entre les essais. L'échec final est propagé. Les erreurs
S3 non temporaires, comme un accès refusé, ne sont pas réessayées.

## Tests et CI/CD

Après préparation des services :

```powershell
.\.venv\Scripts\python.exe -c "from src.demo import initialiser_base; initialiser_base('transactions_test')"
.\.venv\Scripts\python.exe -m pytest tests -v
```

Les 34 tests couvrent les validations, les calculs, la pureté, le seuil du flag,
les reprises, le rollback et les doubles imports. Les tests d'intégration utilisent
SeaweedFS et PostgreSQL ; deux parcours exécutent aussi réellement Tesseract et Qwen.

Tests rapides sans services :

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_load_data.py tests/test_process_data.py tests/test_retry.py tests/test_s3_retry.py tests/test_extraction.py -v
```

Le workflow `.github/workflows/ci.yml` lance les tests sur les pushs vers `main`
et les pull requests vers `main`. Après réussite sur `main`, le job `livraison`
construit l'image, vérifie son démarrage et publie
`ghcr.io/zuzugli/projet-mlops:latest` et un tag `sha-<commit>`.
Les pull requests ne publient pas d'image. Le workflow utilise `GITHUB_TOKEN`,
avec `packages: write` uniquement pour le job de livraison.

L'image contient le code, les dépendances, Tesseract et les exemples. Les services
PostgreSQL, SeaweedFS, Ollama et les poids du modèle restent séparés. Un package
GHCR privé nécessite une authentification pour son téléchargement.

Le [scénario d'échec et de correction](docs/echec_pipeline.md) présente les captures
demandées : cause, message d'erreur, échec et retour au vert.

## Configuration et arrêt

PostgreSQL écoute sur `127.0.0.1:5432`, avec l'utilisateur `pipeline` et le mot de
passe local `pipeline_local`. Les identifiants de Compose sont réservés à
l'environnement local. Les ports publiés sont limités à l'interface locale.

Variables acceptées : `PGHOST`, `PGPORT`, `PGUSER`, `PGPASSWORD`, `S3_ENDPOINT_URL`,
`S3_ACCESS_KEY`, `S3_SECRET_KEY`, `S3_BUCKET`, `OLLAMA_URL`, `SLM_MODEL`, `TESSERACT_CMD`.

Arrêt des services en conservant les volumes et les données :

```powershell
docker compose --profile niveau3 stop
```

## Limites

- Une transaction par image étiquetée ou texte ; l'OCR supporte le format d'avis fourni.
- Les extractions incomplètes ou invalides sont refusées. Les contrôles du SLM
  réduisent les erreurs sans garantir la compréhension de tous les textes.
- La forme des IBAN extraits est contrôlée, pas leur clé modulo 97.
- L'anti-doublon porte sur le fichier : un CSV modifié est un nouvel import et peut
  répéter des transactions présentes dans un autre fichier.
- Les fichiers sont chargés en mémoire. Les performances à plusieurs millions de
  lignes n'ont pas été mesurées ; une lecture en flux et un chargement par lots
  avec `COPY` seraient à envisager.

## Structure

| Chemin | Contenu |
|---|---|
| `src/` | Génération, chargement, calculs, stockage et orchestration |
| `tests/` | Tests unitaires et d'intégration |
| `sql/` | Schéma PostgreSQL |
| `examples/` | Sources image et texte avec références attendues |
| `docs/` | Scénario d'échec et captures CI |
| `compose.yaml` | Services PostgreSQL, SeaweedFS et Ollama |
| `Dockerfile` | Image de l'application avec Tesseract |
| `.github/workflows/ci.yml` | Tests et livraison Docker automatiques |

Références : [Tesseract](https://tesseract-ocr.github.io/tessdoc/),
[Ollama](https://docs.ollama.com/),
[Qwen2.5 0.5B](https://ollama.com/library/qwen2.5:0.5b).
