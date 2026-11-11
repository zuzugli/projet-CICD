# Comprendre et présenter le projet

## Pourquoi OCR et SLM ?

« J'ai choisi deux nouvelles sources : les images et le texte. Je les convertis au
même format CSV puis je réutilise le stockage S3, les validations et les traitements
existants. Tout est démontrable localement avec Docker, sans VM cloud partagée. »

Les options choisies sont la 2 et la 3. L'option 1 de déploiement de production n'est
pas réalisée. La CI vérifie automatiquement le code et les deux nouvelles sources.

## Le parcours en mots simples

1. **Source** : un CSV, une image ou une phrase décrivant une transaction.
2. **Extraction** : Tesseract lit les caractères dans l'image ; Qwen extrait les champs
   de la phrase et répond en JSON.
3. **Normalisation** : les dates, montants et champs sont mis au format commun.
4. **S3** : le CSV commun est stocké dans SeaweedFS, puis récupéré depuis ce service.
5. **Validation** : on refuse les données incorrectes ou incomplètes.
6. **Traitement** : les fonctions pures calculent les sommes et les flags.
7. **Base** : PostgreSQL enregistre les transactions et leurs totaux.
8. **Fiabilité** : retry limité pour les pannes temporaires ; hash SHA-256 anti-doublon.

## Avant de passer devant la classe

- Ouvrir Docker Desktop et le terminal à la racine du projet.
- Faire la préparation et ses téléchargements avant le jour J :

```powershell
.\.venv\Scripts\python.exe -m src.preparer_demo
.\.venv\Scripts\python.exe -m src.demo verifier
```

- La vérification utilise les vrais moteurs et ne modifie pas la base.
- Ouvrir `examples/transaction.png`, `examples/transaction.txt` et GitHub Actions.
- Les fichiers JSON attendus servent seulement de corrigés aux tests.

## Démonstration

### Montrer l'image et lancer l'OCR

```powershell
.\.venv\Scripts\python.exe -m src.demo image
```

« Tesseract reconnaît les caractères, puis mon parseur interprète cet avis étiqueté.
Les champs validés rejoignent S3 et PostgreSQL. »

Attendu : Santander, 6200 EUR, flag vrai.

### Montrer la phrase et lancer le SLM

```powershell
.\.venv\Scripts\python.exe -m src.demo texte
```

« Le petit modèle Qwen local extrait les sept champs de cette phrase. Sa réponse
JSON est contrôlée avant d'utiliser la pipeline commune. »

Attendu : BNP Paribas, 1250,50 EUR, flag faux. La première inférence peut être plus lente.

### Montrer l'absence de doublons

```powershell
.\.venv\Scripts\python.exe -m src.demo tout
```

Après les deux imports : 0 nouvelle transaction pour chaque source, toujours deux
transactions dans `transactions_demo`, total 7450,50 EUR. Si les exemples ont déjà
été importés pendant la préparation, un résultat à 0 est normal dès le premier lancement.
On ne supprime pas automatiquement les données pour obtenir artificiellement un premier import.

### Montrer les tests et la CI

```powershell
.\.venv\Scripts\python.exe -m pytest tests -v
```

Montrer la dernière exécution verte après envoi du code, puis les captures de l'échec
de syntaxe et de sa correction. Ne pas réintroduire un bug en direct pendant l'oral.

### Montrer la livraison continue

Dans GitHub Actions, montrer `tests`, puis `Livrer l'image Docker`. Le second job
attend que le premier réussisse. Ouvrir ensuite le package `projet-mlops` sur GitHub.

« Si les tests passent sur main, GitHub construit et publie notre image Docker.
Elle contient le code, ses bibliothèques Python et Tesseract. Chaque version porte
l'identifiant de son commit. PostgreSQL, S3 et Ollama restent des services séparés. »

Voir `livraison.md` pour les commandes de téléchargement et de vérification.

## Questions possibles

**Une fonction pure ?** Elle ne modifie pas ses entrées, ne lit pas d'état externe et
donne le même résultat pour les mêmes données. Ce sont les calculs, pas les accès SQL/S3.

**Pourquoi Decimal ?** Pour des montants décimaux exacts, adaptés aux calculs d'argent.

**Pourquoi séparer chargement et traitement ?** Pour réutiliser les calculs pour les
trois sources et pouvoir les tester indépendamment du réseau ou des fichiers.

**Un retry ?** Une nouvelle tentative après une panne temporaire, avec attente et limite.

**Un rollback ?** L'annulation de toutes les modifications d'une transaction SQL si
une étape échoue. L'empreinte et les résultats sont confirmés ensemble.

**Confirmation perdue après succès ?** Le retry retrouve l'empreinte déjà enregistrée
et n'ajoute aucun doublon. Un test couvre ce cas précis.

**OCR et SLM, même chose ?** Non. L'OCR lit des caractères dans des pixels ; le SLM
interprète du texte pour en extraire les informations.

**N'importe quel document ?** Non. L'OCR supporte le format d'avis annoncé. Le SLM
peut se tromper ; une extraction incomplète ou non justifiée est refusée.

**CI/CD ?** La CI teste les changements ; la livraison continue construit et publie
l'image après réussite des tests sur main. Il n'y a pas de déploiement automatique
sur un serveur de production. Les deux options du niveau 3 restent OCR et SLM.
