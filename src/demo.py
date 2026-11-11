"""Démonstration locale des deux options : image OCR et texte SLM."""

import argparse
from datetime import datetime
from decimal import Decimal
import json
from pathlib import Path

from psycopg import sql

from src.database import connecter
from src.ingestion import importer_extraction
from src.normalisation import normaliser_transaction
from src.ocr import extraire_image
from src.pipeline import attendre_s3
from src.s3_storage import creer_client_s3
from src.slm import MODELE, extraire_texte


RACINE = Path(__file__).resolve().parents[1]


def _json(valeur):
    if isinstance(valeur, datetime):
        return valeur.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(valeur, Decimal):
        return f"{valeur:.2f}"
    raise TypeError(type(valeur).__name__)


def initialiser_base(nom_base):
    """Prépare une base de démonstration sans effacer les données existantes."""
    with connecter("postgres") as connexion:
        connexion.autocommit = True
        existe = connexion.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s", (nom_base,)
        ).fetchone()
        if not existe:
            connexion.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(nom_base)))
    with connecter(nom_base) as connexion:
        connexion.execute((RACINE / "sql" / "create_tables.sql").read_text(encoding="utf-8"))


def extraire(source, fichier=None):
    if source == "image":
        chemin = Path(fichier or RACINE / "examples" / "transaction.png")
        texte, transaction = extraire_image(chemin)
        print("Texte reconnu par Tesseract :\n" + texte, flush=True)
    else:
        chemin = Path(fichier or RACINE / "examples" / "transaction.txt")
        texte = chemin.read_text(encoding="utf-8")
        print(f"Texte envoyé au modèle local {MODELE} :\n{texte}", flush=True)
        transaction = extraire_texte(texte)
    print("Transaction extraite et validée :", flush=True)
    print(json.dumps(transaction, ensure_ascii=False, indent=2, default=_json), flush=True)
    dossier = RACINE / "artifacts"
    dossier.mkdir(exist_ok=True)
    (dossier / f"{source}_extraction.json").write_text(
        json.dumps(transaction, ensure_ascii=False, indent=2, default=_json), encoding="utf-8"
    )
    (dossier / f"{source}_source.txt").write_text(texte, encoding="utf-8")
    return transaction


def verifier_exemples():
    """Vérifie les deux moteurs réels ; les attendus servent seulement d'oracle de test."""
    for source, attendu in (("image", "image_attendue.json"), ("texte", "texte_attendu.json")):
        transaction = extraire(source)
        reference = normaliser_transaction(json.loads(
            (RACINE / "examples" / attendu).read_text(encoding="utf-8")
        ))
        if transaction != reference:
            raise ValueError(f"L'extraction {source} diffère de l'exemple attendu : démo non validée.")
        print(f"Vérification {source} : OK", flush=True)


def bilan(nom_base):
    with connecter(nom_base) as connexion:
        lignes = connexion.execute(
            "SELECT datetime_transaction, banque_source, montant, flag_montant_eleve "
            "FROM transactions ORDER BY id"
        ).fetchall()
        totaux = connexion.execute(
            "SELECT banque_source, SUM(montant_total) FROM totaux_banque_source "
            "GROUP BY banque_source ORDER BY banque_source"
        ).fetchall()
    print(f"\nBase {nom_base} : {len(lignes)} transaction(s)", flush=True)
    for date, banque, montant, flag in lignes:
        print(f"{date} | {banque} | {montant:.2f} EUR | flag={flag}")
    print("Totaux envoyés par banque :")
    for banque, total in totaux:
        print(f"{banque} : {total:.2f} EUR")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["image", "texte", "tout", "verifier", "bilan"])
    parser.add_argument("--fichier", help="Image étiquetée ou texte à analyser.")
    parser.add_argument("--base", default="transactions_demo",
                        choices=["transactions_demo", "transactions_test", "transactions"])
    args = parser.parse_args()
    if args.fichier and args.action not in ("image", "texte"):
        parser.error("--fichier s'utilise avec image ou texte.")
    if args.action == "verifier":
        verifier_exemples()
        return
    initialiser_base(args.base)
    if args.action != "bilan":
        client = creer_client_s3()
        attendre_s3(client)
        for source in (["image", "texte"] if args.action == "tout" else [args.action]):
            transaction = extraire(source, args.fichier)
            nombre = importer_extraction(transaction, source, client, nom_base=args.base)
            print(f"S3 -> PostgreSQL : {nombre} nouvelle(s) transaction(s) pour {source}.", flush=True)
    bilan(args.base)


if __name__ == "__main__":
    main()
