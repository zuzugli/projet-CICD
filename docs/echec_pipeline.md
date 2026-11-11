# Échec de pipeline et correction

## Situation initiale

La CI réussit après l'ajout des tests automatiques.

![Première réussite](captures/01-ci-verte.png)

## Cause et échec

Pendant une modification du seuil du flag, deux instructions Python ont été collées
sur une même ligne dans `ajouter_flags` : le module n'était plus interprétable.

![Échec CI](captures/02-ci-rouge.png)

L'erreur capturée est `SyntaxError: invalid syntax`. L'échec survient à l'étape
« Créer les tables de test » : elle importe `database`, qui importe `process_data`.
Les tests n'ont donc pas été exécutés dans cette exécution. Cette capture ne montre
pas une assertion de test ayant détecté le mauvais seuil.

![Message d'erreur](captures/03-erreur-syntaxe.png)

## Correction et réussite

Les instructions ont été séparées. Le seuil a également été rétabli à `> 5000`.
Après commit et push, le workflow réussit à nouveau.

![Retour au vert](captures/04-ci-corrigee.png)

## Extension S3 (capture facultative)

![CI avec SeaweedFS](captures/05-ci-s3-verte.png)
