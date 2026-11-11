# Résumé des tests

Un test compare le résultat obtenu au résultat attendu. Un test de rejet réussit
si l'erreur attendue est correctement détectée.

| Fichier | Nombre de cas | Ce qu'il vérifie | Services |
|---|---:|---|---|
| `test_load_data.py` | 8 | Colonnes, champs, dates, montants, conversions, fichier vide, absence de mutation | Aucun |
| `test_process_data.py` | 1 | Regroupements distincts par compte, banque et destinataire ; pureté | Aucun |
| `test_retry.py` | 2 | Reprise d'insertion puis arrêt à la limite | Pannes simulées |
| `test_s3_retry.py` | 3 | Reprise de lecture, arrêt après limite, accès refusé sans retry | Pannes simulées |
| `test_database.py` | 4 | Vrais montants, flags, totaux, rollback, S3, doublons, confirmation perdue | PostgreSQL et SeaweedFS |
| `test_extraction.py` | 14 | Format commun, parseur OCR, champs manquants/inventés, JSON invalide | Réponses SLM simulées pour tester les contrôles |
| `test_niveau3_integration.py` | 2 | Vrai Tesseract et vrai Qwen, puis même parcours S3/PostgreSQL | Tous les services et moteurs |

Total : **34 cas de test**. Les paramètres d'un test couvrent plusieurs données
incorrectes sans imposer de nouvelles fonctions à apprendre. Il suffit de savoir
expliquer les familles de tests ci-dessous, pas de mémoriser les 34 cas.

Vérification locale du 11 novembre 2026 : `34 passed, 19 subtests passed` avec
les vrais services et moteurs. Les 19 sous-tests sont des vérifications internes
aux tests existants, pas 19 nouveaux tests à apprendre. La validation GitHub Actions
de cette version reste à confirmer après son push.

`conftest.py` prépare et nettoie uniquement `transactions_test` et les buckets
temporaires des tests. Les bases de démonstration ne sont pas vidées.
La suite complète exécute les deux moteurs réels ; aucune réponse préenregistrée ne
remplace l'inférence dans les tests d'intégration ou la démonstration.

```powershell
.\.venv\Scripts\python.exe -m pytest tests -v
.\.venv\Scripts\python.exe -m pytest tests/test_retry.py tests/test_s3_retry.py -v -s
.\.venv\Scripts\python.exe -m pytest tests/test_niveau3_integration.py -v
```

Les scénarios à expliquer :

1. 5000 n'est pas signalé ; 5000,01 l'est.
2. Deux imports identiques ne créent pas deux jeux de lignes.
3. Une erreur SQL ne laisse pas d'import partiel.
4. Une confirmation perdue après succès ne crée pas de doublon au retry.
5. Une panne temporaire permet une reprise, une panne persistante arrête le programme.
6. Les vrais résultats de l'OCR et du SLM arrivent dans PostgreSQL via S3.

Pour l'oral : « Je combine des tests unitaires rapides pour les règles et les erreurs,
avec des tests d'intégration utilisant les vrais services pour le parcours complet. »
