import hashlib
import time
from pathlib import Path

import psycopg

from src.load_data import charger_contenu_csv
from src.process_data import (
    ajouter_flags,
    total_par_iban_origine,
    total_par_banque_source,
    total_par_iban_destinataire,
)


def connecter(nom_base="transactions"):
    """Ouvre une connexion à PostgreSQL."""
    return psycopg.connect(
        host="127.0.0.1",
        port=5432,
        dbname=nom_base,
        user="pipeline",
        password="pipeline_local",
        connect_timeout=5,
    )


def inserer_totaux(curseur, empreinte, transactions):
    """Calcule et enregistre les trois regroupements du fichier."""
    totaux_origines = total_par_iban_origine(transactions)
    totaux_banques = total_par_banque_source(transactions)
    totaux_destinataires = total_par_iban_destinataire(transactions)

    curseur.executemany(
        """
        INSERT INTO totaux_iban_origine
            (file_hash, iban_origine, montant_total)
        VALUES (%s, %s, %s);
        """,
        [
            (empreinte, iban, total)
            for iban, total in totaux_origines.items()
        ],
    )

    curseur.executemany(
        """
        INSERT INTO totaux_banque_source
            (file_hash, banque_source, montant_total)
        VALUES (%s, %s, %s);
        """,
        [
            (empreinte, banque, total)
            for banque, total in totaux_banques.items()
        ],
    )

    curseur.executemany(
        """
        INSERT INTO totaux_iban_destinataire
            (file_hash, iban_destinataire, montant_total)
        VALUES (%s, %s, %s);
        """,
        [
            (empreinte, iban, total)
            for iban, total in totaux_destinataires.items()
        ],
    )


def inserer_contenu_csv(
    contenu,
    nom_fichier,
    nom_base="transactions",
):
    """Insère des octets CSV et leurs totaux, sans doublon."""
    empreinte = hashlib.sha256(contenu).hexdigest()

    with connecter(nom_base) as connexion:
        with connexion.cursor() as curseur:
            curseur.execute(
                """
                INSERT INTO processed_files (file_hash, nom_fichier)
                VALUES (%s, %s)
                ON CONFLICT (file_hash) DO NOTHING
                RETURNING file_hash;
                """,
                (empreinte, nom_fichier),
            )

            if curseur.fetchone() is None:
                return 0

            transactions = charger_contenu_csv(contenu)
            transactions_traitees = ajouter_flags(transactions)

            curseur.executemany(
                """
                INSERT INTO transactions (
                    datetime_transaction,
                    iban_origine,
                    pays_source,
                    banque_source,
                    iban_destinataire,
                    pays_destinataire,
                    montant,
                    flag_montant_eleve
                )
                VALUES (
                    %(datetime_transaction)s,
                    %(iban_origine)s,
                    %(pays_source)s,
                    %(banque_source)s,
                    %(iban_destinataire)s,
                    %(pays_destinataire)s,
                    %(montant)s,
                    %(flag_montant_eleve)s
                );
                """,
                transactions_traitees,
            )

            inserer_totaux(curseur, empreinte, transactions)

    return len(transactions_traitees)


def inserer_fichier(chemin, nom_base="transactions"):
    """Lit un fichier local puis délègue son insertion."""
    chemin = Path(chemin)
    contenu = chemin.read_bytes()

    return inserer_contenu_csv(
        contenu=contenu,
        nom_fichier=chemin.name,
        nom_base=nom_base,
    )


def inserer_avec_retry(
    chemin,
    nom_base="transactions",
    max_tentatives=3,
    delai=2,
):
    """Réessaie l'insertion locale après une erreur opérationnelle."""
    if max_tentatives < 1:
        raise ValueError("Il faut au moins une tentative.")

    if delai < 0:
        raise ValueError("Le délai ne peut pas être négatif.")

    for tentative in range(1, max_tentatives + 1):
        try:
            return inserer_fichier(chemin, nom_base)

        except psycopg.OperationalError as erreur:
            print(
                f"Tentative {tentative}/{max_tentatives} "
                f"échouée : {erreur}"
            )

            if tentative == max_tentatives:
                print("Nombre maximal de tentatives atteint : arrêt.")
                raise

            print(f"Nouvelle tentative dans {delai} secondes.")
            time.sleep(delai)


if __name__ == "__main__":
    nombre = inserer_avec_retry("data/transactions_002.csv")

    if nombre == 0:
        print("Fichier déjà traité : aucune nouvelle insertion.")
    else:
        print(f"{nombre} transactions insérées avec leurs totaux.")