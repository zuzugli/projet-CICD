"""Les vrais moteurs OCR et SLM rejoignent le même parcours S3/PostgreSQL."""

import json
from pathlib import Path

import pytest

from src.database import connecter
from src.ingestion import importer_extraction
from src.normalisation import normaliser_transaction
from src.ocr import extraire_image
from src.slm import extraire_texte


EXEMPLES = Path(__file__).resolve().parents[1] / "examples"


@pytest.mark.parametrize("source,attendu", [
    ("image", "image_attendue.json"), ("texte", "texte_attendu.json"),
])
def test_moteur_reel_s3_postgresql(source, attendu, base_test, bucket_s3_test):
    if source == "image":
        texte, transaction = extraire_image(EXEMPLES / "transaction.png")
        assert "6200" in texte
    else:
        transaction = extraire_texte((EXEMPLES / "transaction.txt").read_text(encoding="utf-8"))
    reference = normaliser_transaction(json.loads((EXEMPLES / attendu).read_text(encoding="utf-8")))
    assert transaction == reference
    client, bucket = bucket_s3_test
    assert importer_extraction(transaction, source, client, base_test, bucket) == 1
    assert importer_extraction(transaction, source, client, base_test, bucket) == 0
    # Changer le nom/la source ne permet pas de réimporter le même CSV normalisé.
    assert importer_extraction(transaction, "copie", client, base_test, bucket) == 0
    with connecter(base_test) as connexion:
        lignes = connexion.execute(
            "SELECT montant, flag_montant_eleve FROM transactions"
        ).fetchall()
        totaux = connexion.execute(
            "SELECT (SELECT SUM(montant_total) FROM totaux_iban_origine), "
            "(SELECT SUM(montant_total) FROM totaux_banque_source), "
            "(SELECT SUM(montant_total) FROM totaux_iban_destinataire), "
            "(SELECT COUNT(*) FROM processed_files)"
        ).fetchone()
    montant = reference["montant"]
    assert lignes == [(montant, montant > 5000)]
    assert totaux == (montant, montant, montant, 1)
