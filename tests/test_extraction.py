"""Tests rapides de validation des nouvelles sources, sans inférence simulée en production."""

from copy import deepcopy
from datetime import datetime
from decimal import Decimal
from io import StringIO
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from src.load_data import charger_contenu_csv
from src.normalisation import normaliser_transaction, vers_csv
from src.ocr import extraire_champs_ocr
from src.slm import extraire_texte, verifier_presence_source


EXEMPLES = Path(__file__).resolve().parents[1] / "examples"


def reference(nom="image_attendue.json"):
    return json.loads((EXEMPLES / nom).read_text(encoding="utf-8"))


def test_format_commun_et_purete():
    champs = reference()
    champs["montant"] = "6 200,00 EUR"
    champs["datetime_transaction"] = "2026-11-11T09:00:00"
    avant = deepcopy(champs)
    transaction = normaliser_transaction(champs)
    assert champs == avant
    assert transaction["montant"] == Decimal("6200.00")
    assert transaction["datetime_transaction"] == datetime(2026, 11, 11, 9)
    assert charger_contenu_csv(vers_csv([transaction])) == [transaction]
    assert vers_csv([transaction]) == vers_csv([normaliser_transaction(reference())])


@pytest.mark.parametrize("champ,valeur", [
    ("montant", "-1"), ("montant", "NaN"), ("montant", "1.001"),
    ("banque_source", None), ("iban_origine", "inconnu"),
    ("datetime_transaction", "2026-02-30 10:00:00"),
])
def test_extraction_invalide_refusee(champ, valeur):
    champs = reference()
    champs[champ] = valeur
    with pytest.raises(ValueError):
        normaliser_transaction(champs)


def test_ocr_parse_le_format_annonce():
    texte = """AVIS DE VIREMENT
Date: 2026-11-11 09:00:00
IBAN origine: ES9121000418450200051332
Pays source: Espagne
Banque source: Santander
IBAN destinataire: FR7630001007941234567890185
Pays destinataire: France
Montant: 6200.00 EUR
"""
    assert extraire_champs_ocr(texte) == normaliser_transaction(reference())
    with pytest.raises(ValueError, match="incomplète"):
        extraire_champs_ocr("Montant: 100.00")
    with pytest.raises(ValueError, match="double"):
        extraire_champs_ocr(texte + "Montant: 1.00\n")


def test_slm_sortie_validee_et_source_verifiee():
    texte = (EXEMPLES / "transaction.txt").read_text(encoding="utf-8")
    reponse = json.dumps({"message": {"content": json.dumps(reference("texte_attendu.json"))}})
    with patch("src.slm.urlopen", return_value=StringIO(reponse)) as appel:
        resultat = extraire_texte(texte)
    assert resultat == normaliser_transaction(reference("texte_attendu.json"))
    corps = json.loads(appel.call_args.args[0].data)
    assert corps["messages"][-1]["content"] == texte
    assert set(corps["format"]["required"]) == set(reference())


def test_slm_refuse_champ_invente():
    texte = (EXEMPLES / "transaction.txt").read_text(encoding="utf-8")
    champs = reference("texte_attendu.json")
    champs["banque_source"] = "Banque inventée"
    reponse = json.dumps({"message": {"content": json.dumps(champs)}})
    with patch("src.slm.urlopen", return_value=StringIO(reponse)):
        with pytest.raises(ValueError, match="banque_source"):
            extraire_texte(texte)


def test_slm_refuse_reponse_non_json():
    with patch("src.slm.urlopen", return_value=StringIO('{"message":{"content":"bonjour"}}')):
        with pytest.raises(ValueError, match="JSON"):
            extraire_texte("Texte à analyser")


@pytest.mark.parametrize("champ,valeur", [
    ("montant", "1300.00"), ("datetime_transaction", "2026-11-13 14:30:00"),
    ("datetime_transaction", "2026-11-12 15:30:00"),
])
def test_source_refuse_montant_date_heure_inventes(champ, valeur):
    champs = reference("texte_attendu.json")
    champs[champ] = valeur
    with pytest.raises(ValueError):
        verifier_presence_source(normaliser_transaction(champs),
                                 (EXEMPLES / "transaction.txt").read_text(encoding="utf-8"))
