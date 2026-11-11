"""Format commun aux extractions OCR et SLM, avant le flux CSV habituel."""

import csv
from io import StringIO
import re

from src.load_data import COLONNES_ATTENDUES, valider_ligne


def normaliser_transaction(champs):
    """Refuse les champs manquants et convertit les valeurs sans inventer de donnée."""
    if not isinstance(champs, dict) or set(champs) != set(COLONNES_ATTENDUES):
        raise ValueError("Extraction incomplète : les sept champs sont obligatoires.")
    if any(not isinstance(valeur, str) or not valeur.strip() for valeur in champs.values()):
        raise ValueError("Extraction incomplète : valeur vide ou inconnue.")

    ligne = {cle: valeur.strip() for cle, valeur in champs.items()}
    # Le séparateur ISO « T » et l'espace représentent la même date/heure.
    ligne["datetime_transaction"] = ligne["datetime_transaction"].replace("T", " ")
    for cle in ("iban_origine", "iban_destinataire"):
        ligne[cle] = re.sub(r"\s+", "", ligne[cle]).upper()
        if not re.fullmatch(r"[A-Z]{2}[0-9]{2}[A-Z0-9]{11,30}", ligne[cle]):
            raise ValueError(f"Format IBAN invalide pour {cle}.")

    montant = ligne["montant"].replace("\u00a0", "").replace(" ", "")
    montant = re.sub(r"(?:EUR|euros?|€)$", "", montant, flags=re.IGNORECASE)
    if not re.fullmatch(r"[0-9]+(?:[,.][0-9]{1,2})?", montant):
        raise ValueError("Montant extrait invalide.")
    ligne["montant"] = montant.replace(",", ".")
    return valider_ligne(ligne, 2)


def vers_csv(transactions):
    """Produit un CSV UTF-8 stable pour le stockage S3 et le hash anti-doublon."""
    flux = StringIO(newline="")
    writer = csv.DictWriter(flux, fieldnames=COLONNES_ATTENDUES, lineterminator="\n")
    writer.writeheader()
    for transaction in transactions:
        ligne = dict(transaction)
        ligne["datetime_transaction"] = transaction["datetime_transaction"].strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        ligne["montant"] = f"{transaction['montant']:.2f}"
        writer.writerow(ligne)
    return flux.getvalue().encode("utf-8")
