from unittest.mock import patch

import psycopg
import pytest

from src.database import inserer_avec_retry


def test_retry_apres_panne_temporaire():
    with patch("src.database.inserer_fichier") as insertion:
        with patch("src.database.time.sleep") as attente:
            insertion.side_effect = [
                psycopg.OperationalError("Connexion temporairement indisponible"),
                3,
            ]

            resultat = inserer_avec_retry(
                "exemple.csv",
                nom_base="transactions_test",
                max_tentatives=3,
                delai=2,
            )

    assert resultat == 3
    assert insertion.call_count == 2
    attente.assert_called_once_with(2)


def test_retry_arrete_apres_limite():
    with patch("src.database.inserer_fichier") as insertion:
        with patch("src.database.time.sleep") as attente:
            insertion.side_effect = psycopg.OperationalError(
                "Connexion toujours indisponible"
            )

            with pytest.raises(psycopg.OperationalError):
                inserer_avec_retry(
                    "exemple.csv",
                    nom_base="transactions_test",
                    max_tentatives=3,
                    delai=2,
                )

    assert insertion.call_count == 3
    assert attente.call_count == 2