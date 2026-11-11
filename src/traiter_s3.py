"""Import des CSV présents dans S3 vers PostgreSQL."""

import argparse

from src.database import inserer_contenu_csv
from src.s3_storage import creer_client_s3, lister_csv, recuperer_csv


def traiter_depuis_s3(nom_base="transactions"):
    client = creer_client_s3()
    cles = lister_csv(client)

    if not cles:
        raise ValueError("Aucun CSV présent dans le bucket.")

    total_insere = 0

    for cle in cles:
        contenu = recuperer_csv(cle, client)

        nombre = inserer_contenu_csv(
            contenu=contenu,
            nom_fichier=cle,
            nom_base=nom_base,
        )

        total_insere += nombre

        if nombre == 0:
            print(f"{cle} : déjà traité")
        else:
            print(f"{cle} : {nombre} transactions insérées")

    print(
        f"Import S3 terminé vers '{nom_base}' : "
        f"{total_insere} nouvelles transactions."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--base",
        choices=["transactions", "transactions_test"],
        default="transactions",
        help="Base PostgreSQL à utiliser.",
    )
    arguments = parser.parse_args()

    traiter_depuis_s3(nom_base=arguments.base)