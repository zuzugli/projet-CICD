"""Les nouvelles sources rejoignent réellement S3 puis l'insertion commune."""

import hashlib

from src.database import inserer_avec_retry
from src.normalisation import vers_csv
from src.s3_storage import BUCKET, recuperer_csv


def importer_extraction(transaction, origine, client, nom_base="transactions_demo", bucket=BUCKET):
    contenu = vers_csv([transaction])
    empreinte = hashlib.sha256(contenu).hexdigest()
    cle = f"extractions/{origine}-{empreinte[:16]}.csv"
    client.put_object(Bucket=bucket, Key=cle, Body=contenu, ContentType="text/csv; charset=utf-8")
    recupere = recuperer_csv(cle, client, bucket=bucket)
    if recupere != contenu:
        raise ValueError("Le contenu récupéré depuis S3 diffère du contenu envoyé.")
    return inserer_avec_retry(chemin=cle, contenu=recupere, nom_base=nom_base)
