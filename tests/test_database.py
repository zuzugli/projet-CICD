import csv
from decimal import Decimal

import psycopg
import pytest

from src.database import connecter, inserer_fichier
from src.load_data import COLONNES_ATTENDUES


@pytest.fixture
def base_test():
    """Prépare puis nettoie uniquement la base de tests."""
    requete_nettoyage = """
        TRUNCATE TABLE
            transactions,
            totaux_iban_origine,
            totaux_banque_source,
            totaux_iban_destinataire,
            processed_files
        RESTART IDENTITY;
    """

    with connecter("transactions_test") as connexion:
        connexion.execute(requete_nettoyage)

    try:
        yield "transactions_test"
    finally:
        with connecter("transactions_test") as connexion:
            connexion.execute(requete_nettoyage)


def test_insertion_flags_totaux_et_doublons(base_test, tmp_path):
    fichier = tmp_path / "exemple.csv"

    with fichier.open("w", newline="", encoding="utf-8") as sortie:
        writer = csv.DictWriter(sortie, fieldnames=COLONNES_ATTENDUES)
        writer.writeheader()

        for montant in ("4999.99", "5000.00", "5000.01"):
            writer.writerow({
                "datetime_transaction": "2026-01-02 09:00:00",
                "iban_origine": "ES9121000418450200051332",
                "pays_source": "Espagne",
                "banque_source": "Santander",
                "iban_destinataire": "FR7630001007941234567890185",
                "pays_destinataire": "France",
                "montant": montant,
            })

    # Premier import : trois insertions.
    assert inserer_fichier(fichier, base_test) == 3

    # Deuxième import : aucune nouvelle insertion.
    assert inserer_fichier(fichier, base_test) == 0

    with connecter(base_test) as connexion:
        lignes = connexion.execute(
            """
            SELECT montant, flag_montant_eleve
            FROM transactions
            ORDER BY id;
            """
        ).fetchall()

        nombre_fichiers = connexion.execute(
            "SELECT COUNT(*) FROM processed_files;"
        ).fetchone()[0]

        totaux_origines = connexion.execute(
            """
            SELECT iban_origine, montant_total
            FROM totaux_iban_origine;
            """
        ).fetchall()

        totaux_banques = connexion.execute(
            """
            SELECT banque_source, montant_total
            FROM totaux_banque_source;
            """
        ).fetchall()

        totaux_destinataires = connexion.execute(
            """
            SELECT iban_destinataire, montant_total
            FROM totaux_iban_destinataire;
            """
        ).fetchall()

    assert lignes == [
        (Decimal("4999.99"), False),
        (Decimal("5000.00"), False),
        (Decimal("5000.01"), True),
    ]
    assert nombre_fichiers == 1

    assert totaux_origines == [
        ("ES9121000418450200051332", Decimal("15000.00"))
    ]
    assert totaux_banques == [
        ("Santander", Decimal("15000.00"))
    ]
    assert totaux_destinataires == [
        ("FR7630001007941234567890185", Decimal("15000.00"))
    ]


def test_echec_insertion_annule_tout(base_test, tmp_path):
    fichier = tmp_path / "erreur_insertion.csv"

    transaction = {
        "datetime_transaction": "2026-01-02 09:00:00",
        "iban_origine": "ES9121000418450200051332",
        "pays_source": "Espagne",
        "banque_source": "Santander",
        "iban_destinataire": "FR7630001007941234567890185",
        "pays_destinataire": "France",
        "montant": "100.00",
    }

    with fichier.open("w", newline="", encoding="utf-8") as sortie:
        writer = csv.DictWriter(sortie, fieldnames=COLONNES_ATTENDUES)
        writer.writeheader()
        writer.writerow(transaction)

        transaction_invalide = transaction.copy()
        transaction_invalide["iban_origine"] = "A" * 35
        writer.writerow(transaction_invalide)

    with pytest.raises(psycopg.errors.StringDataRightTruncation):
        inserer_fichier(fichier, base_test)

    with connecter(base_test) as connexion:
        nombres = connexion.execute(
            """
            SELECT
                (SELECT COUNT(*) FROM transactions),
                (SELECT COUNT(*) FROM processed_files),
                (SELECT COUNT(*) FROM totaux_iban_origine),
                (SELECT COUNT(*) FROM totaux_banque_source),
                (SELECT COUNT(*) FROM totaux_iban_destinataire);
            """
        ).fetchone()

    assert nombres == (0, 0, 0, 0, 0)