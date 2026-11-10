"""Traitements purs des transactions, séparés de la lecture des fichiers."""

from decimal import Decimal


def ajouter_flags(transactions):
    """Signale les montants supérieurs à 5000 sans modifier les entrées."""
    resultat = []

    for transaction in transactions:
        copie = transaction.copy()
        copie["flag_montant_eleve"] = transaction["montant"] >= Decimal("5000")        resultat.append(copie)

    return resultat


def total_par_iban_origine(transactions):
    """Additionne les montants envoyés par compte, sans modifier les entrées."""
    totaux = {}

    for transaction in transactions:
        iban = transaction["iban_origine"]
        montant = transaction["montant"]

        if iban not in totaux:
            totaux[iban] = Decimal("0")

        totaux[iban] += montant

    return totaux


def total_par_banque_source(transactions):
    """Additionne les montants envoyés par banque, sans modifier les entrées."""
    totaux = {}

    for transaction in transactions:
        banque = transaction["banque_source"]
        montant = transaction["montant"]

        if banque not in totaux:
            totaux[banque] = Decimal("0")

        totaux[banque] += montant

    return totaux


def total_par_iban_destinataire(transactions):
    """Additionne les montants reçus par compte, sans modifier les entrées."""
    totaux = {}

    for transaction in transactions:
        iban = transaction["iban_destinataire"]
        montant = transaction["montant"]

        if iban not in totaux:
            totaux[iban] = Decimal("0")

        totaux[iban] += montant

    return totaux


if __name__ == "__main__":
    from load_data import charger_csv

    transactions = charger_csv("data/transactions_002.csv")
    transactions_traitees = ajouter_flags(transactions)

    for transaction in transactions_traitees:
        print(
            f"{transaction['montant']:.2f} EUR | "
            f"Montant élevé : {transaction['flag_montant_eleve']}"
        )

    print("\nTotaux envoyés par IBAN d'origine :")
    totaux = total_par_iban_origine(transactions)
    for iban, total in totaux.items():
        print(f"{iban} : {total:.2f} EUR")

    print("\nTotaux envoyés par banque :")
    totaux_banques = total_par_banque_source(transactions)
    for banque, total in totaux_banques.items():
        print(f"{banque} : {total:.2f} EUR")

    print("\nTotaux reçus par IBAN destinataire :")
    totaux_destinataires = total_par_iban_destinataire(transactions)
    for iban, total in totaux_destinataires.items():
        print(f"{iban} : {total:.2f} EUR")
