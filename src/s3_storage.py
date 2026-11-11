"""Communication avec le stockage S3 local."""

import time
import os
from pathlib import Path

import boto3
from botocore.config import Config
from botocore.exceptions import (
    ClientError,
    ConnectionClosedError,
    ConnectTimeoutError,
    EndpointConnectionError,
    IncompleteReadError,
    ReadTimeoutError,
    ResponseStreamingError,
)


BUCKET = os.getenv("S3_BUCKET", "transactions-csv")

ERREURS_S3 = (
    ClientError,
    ConnectionClosedError,
    ConnectTimeoutError,
    EndpointConnectionError,
    IncompleteReadError,
    ReadTimeoutError,
    ResponseStreamingError,
)


def creer_client_s3():
    """Crée un client pour communiquer avec SeaweedFS."""
    return boto3.client(
        "s3",
        endpoint_url=os.getenv("S3_ENDPOINT_URL", "http://127.0.0.1:8333"),
        aws_access_key_id=os.getenv("S3_ACCESS_KEY", "pipeline"),
        aws_secret_access_key=os.getenv("S3_SECRET_KEY", "pipeline_s3_local"),
        region_name="us-east-1",
        config=Config(
            signature_version="s3v4",
            s3={"addressing_style": "path"},
            connect_timeout=5,
            read_timeout=10,
            retries={"total_max_attempts": 1},
        ),
    )


def envoyer_csv(chemin, client, bucket=BUCKET):
    """Envoie un fichier et vérifie sa présence et sa taille."""
    chemin = Path(chemin)
    cle = chemin.name

    client.upload_file(
        Filename=str(chemin),
        Bucket=bucket,
        Key=cle,
    )

    informations = client.head_object(Bucket=bucket, Key=cle)

    if informations["ContentLength"] != chemin.stat().st_size:
        raise ValueError(f"Taille incorrecte après envoi : {cle}")

    return cle


def lister_csv(client, bucket=BUCKET):
    """Renvoie les clés des objets CSV présents dans le bucket."""
    cles = []
    paginateur = client.get_paginator("list_objects_v2")

    for page in paginateur.paginate(Bucket=bucket):
        for objet in page.get("Contents", []):
            if objet["Key"].endswith(".csv"):
                cles.append(objet["Key"])

    return sorted(cles)


def recuperer_csv(
    cle,
    client,
    bucket=BUCKET,
    max_tentatives=3,
    delai=2,
):
    """Récupère un objet en réessayant après une erreur temporaire."""
    if max_tentatives < 1:
        raise ValueError("Il faut au moins une tentative.")

    if delai < 0:
        raise ValueError("Le délai ne peut pas être négatif.")

    for tentative in range(1, max_tentatives + 1):
        try:
            reponse = client.get_object(Bucket=bucket, Key=cle)
            flux = reponse["Body"]

            try:
                return flux.read()
            finally:
                flux.close()

        except ERREURS_S3 as erreur:
            if isinstance(erreur, ClientError):
                statut = erreur.response.get(
                    "ResponseMetadata", {}
                ).get("HTTPStatusCode", 0)

                if statut not in (408, 429, 500, 502, 503, 504):
                    print(f"Erreur S3 non réessayée pour {cle} : {erreur}")
                    raise

            print(
                f"Lecture S3 de {cle} : tentative "
                f"{tentative}/{max_tentatives} échouée : {erreur}"
            )

            if tentative == max_tentatives:
                print("Limite de tentatives S3 atteinte : arrêt.")
                raise

            print(f"Nouvelle tentative dans {delai} secondes.")
            time.sleep(delai)


if __name__ == "__main__":
    client = creer_client_s3()
    client.head_bucket(Bucket=BUCKET)

    cles = lister_csv(client)

    if not cles:
        raise ValueError("Aucun CSV présent dans le bucket.")

    for cle in cles:
        contenu = recuperer_csv(cle, client)
        texte = contenu.decode("utf-8")

        print(f"Lecture réussie : {cle} ({len(contenu)} octets)")
        print(f"En-tête : {texte.splitlines()[0]}")
        print()
