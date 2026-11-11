"""Chargement et validation des transactions CSV."""

import csv
from datetime import datetime
from decimal import Decimal, InvalidOperation
from io import StringIO


COLONNES_ATTENDUES = [
    "datetime_transaction",
    "iban_origine",
    "pays_source",
    "banque_source",
    "iban_destinataire",
    "pays_destinataire",
    "montant",
]


def valider_ligne(ligne, numero_ligne):
    """Vérifie une ligne et convertit sa date et son montant."""
    if None in ligne:
        raise ValueError(
            f"Ligne {numero_ligne} : trop de valeurs dans la ligne CSV."
        )

    for colonne in COLONNES_ATTENDUES:
        valeur = ligne.get(colonne)

        if valeur is None or not valeur.strip():
            raise ValueError(
                f"Ligne {numero_ligne} : "
                f"champ '{colonne}' vide ou absent."
            )

    transaction = {
        colonne: ligne[colonne].strip()
        for colonne in COLONNES_ATTENDUES
    }

    try:
        transaction["datetime_transaction"] = datetime.strptime(
            transaction["datetime_transaction"],
            "%Y-%m-%d %H:%M:%S",
        )
    except ValueError as erreur:
        raise ValueError(
            f"Ligne {numero_ligne} : date invalide, "
            "format attendu AAAA-MM-JJ HH:MM:SS."
        ) from erreur

    try:
        montant = Decimal(transaction["montant"])
    except InvalidOperation as erreur:
        raise ValueError(
            f"Ligne {numero_ligne} : montant invalide."
        ) from erreur

    if not montant.is_finite() or montant <= 0:
        raise ValueError(
            f"Ligne {numero_ligne} : "
            "le montant doit être fini et positif."
        )

    try:
        montant_au_centime = montant.quantize(Decimal("0.01"))
    except InvalidOperation as erreur:
        raise ValueError(
            f"Ligne {numero_ligne} : montant trop grand."
        ) from erreur

    if montant != montant_au_centime:
        raise ValueError(
            f"Ligne {numero_ligne} : "
            "le montant doit être exprimé au centime."
        )

    transaction["montant"] = montant
    return transaction


def charger_contenu_csv(contenu):
    """Valide des octets CSV et renvoie les transactions Python."""
    texte = contenu.decode("utf-8")
    transactions = []

    with StringIO(texte, newline="") as flux:
        lecteur = csv.DictReader(flux)
        colonnes = lecteur.fieldnames

        if (
            colonnes is None
            or len(colonnes) != len(COLONNES_ATTENDUES)
            or set(colonnes) != set(COLONNES_ATTENDUES)
        ):
            raise ValueError(
                "En-tête CSV invalide. Colonnes attendues : "
                + ", ".join(COLONNES_ATTENDUES)
            )

        for ligne in lecteur:
            transaction = valider_ligne(ligne, lecteur.line_num)
            transactions.append(transaction)

    if not transactions:
        raise ValueError(
            "Le fichier CSV ne contient aucune transaction."
        )

    return transactions


def charger_csv(chemin):
    """Lit un fichier local puis délègue sa validation."""
    with open(chemin, "rb") as fichier:
        contenu = fichier.read()

    return charger_contenu_csv(contenu)


if __name__ == "__main__":
    transactions = charger_csv("data/transactions_002.csv")

    print(f"Nombre de transactions chargées : {len(transactions)}")

    for transaction in transactions:
        print(
            f"{transaction['datetime_transaction']} | "
            f"{transaction['banque_source']} | "
            f"{transaction['montant']:.2f} EUR"
        )