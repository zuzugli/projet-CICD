"""Exécution complète de la pipeline locale."""

import subprocess
from pathlib import Path

from src.database import connecter, inserer_avec_retry
from src.generate_data import generer_fichiers


def lancer_pipeline():
    racine = Path(__file__).resolve().parents[1]

    print("1/4 - Démarrage de PostgreSQL", flush=True)
    subprocess.run(
        ["docker", "compose", "up", "-d", "--wait", "postgres"],
        cwd=racine,
        check=True,
    )

    print("2/4 - Création des tables", flush=True)
    fichier_sql = racine / "sql" / "create_tables.sql"

    with connecter() as connexion:
        connexion.execute(fichier_sql.read_text(encoding="utf-8"))

    print("3/4 - Génération des fichiers CSV", flush=True)
    chemins = generer_fichiers(
        dossier=racine / "data",
        nb_fichiers=3,
        seed=42,
    )

    print("4/4 - Chargement, validation, traitement et insertion", flush=True)
    total_insere = 0

    for chemin in chemins:
        nombre = inserer_avec_retry(chemin)
        total_insere += nombre

        if nombre == 0:
            print(f"{Path(chemin).name} : déjà traité")
        else:
            print(f"{Path(chemin).name} : {nombre} transactions insérées")

    print(
        f"Pipeline terminée : "
        f"{total_insere} nouvelles transactions insérées."
    )


if __name__ == "__main__":
    lancer_pipeline()