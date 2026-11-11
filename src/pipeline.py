"""Exécution complète de la pipeline avec stockage S3."""

import subprocess
import time
from pathlib import Path

from botocore.exceptions import ClientError

from src.database import connecter
from src.generate_data import generer_fichiers
from src.s3_storage import (
    BUCKET,
    ERREURS_S3,
    creer_client_s3,
    envoyer_csv,
)
from src.traiter_s3 import traiter_depuis_s3


def attendre_s3(client, max_tentatives=30):
    """Attend que le bucket soit accessible au démarrage."""
    for tentative in range(1, max_tentatives + 1):
        try:
            client.head_bucket(Bucket=BUCKET)
            return

        except ERREURS_S3 as erreur:
            if isinstance(erreur, ClientError):
                statut = erreur.response.get(
                    "ResponseMetadata", {}
                ).get("HTTPStatusCode", 0)

                if statut not in (404, 408, 429, 500, 502, 503, 504):
                    raise

            if tentative == max_tentatives:
                raise

            print(
                f"Attente du bucket S3 : "
                f"{tentative}/{max_tentatives}",
                flush=True,
            )
            time.sleep(1)


def lancer_pipeline():
    racine = Path(__file__).resolve().parents[1]

    print("1/5 - Démarrage de PostgreSQL et SeaweedFS", flush=True)
    subprocess.run(
        [
            "docker",
            "compose",
            "up",
            "-d",
            "--wait",
            "postgres",
            "seaweedfs",
        ],
        cwd=racine,
        check=True,
    )

    client = creer_client_s3()
    attendre_s3(client)

    print("2/5 - Création des tables", flush=True)
    fichier_sql = racine / "sql" / "create_tables.sql"

    with connecter() as connexion:
        connexion.execute(fichier_sql.read_text(encoding="utf-8"))

    print("3/5 - Génération des fichiers CSV", flush=True)
    chemins = generer_fichiers(
        dossier=racine / "data",
        nb_fichiers=3,
        seed=42,
    )

    print("4/5 - Envoi et vérification dans S3", flush=True)
    for chemin in chemins:
        cle = envoyer_csv(chemin, client)
        print(f"Envoi vérifié : {cle}")

    print("5/5 - Traitement des objets depuis S3", flush=True)
    traiter_depuis_s3()

    print("Pipeline S3 terminée avec succès.")


if __name__ == "__main__":
    lancer_pipeline()