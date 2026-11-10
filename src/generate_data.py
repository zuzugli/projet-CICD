"""Génération de fichiers CSV de transactions financières.

Les données ne sont pas totalement aléatoires :
- les comptes (IBAN, pays, banque) viennent d'une liste fixe ;
- les montants viennent d'une liste fixe qui contient des cas limites
  (4999.99, 5000.00, 5000.01) pour tester le flag "montant > 5000" ;
- le générateur aléatoire utilise une graine (seed) : avec la même graine,
  on obtient toujours exactement les mêmes fichiers.
"""
import csv
import os
import random
from datetime import datetime, timedelta

COLONNES = [
    "datetime_transaction",
    "iban_origine",
    "pays_source",
    "banque_source",
    "iban_destinataire",
    "pays_destinataire",
    "montant",
]

# Comptes fixes : toujours les mêmes IBAN, donc les sommes sont faciles à vérifier
COMPTES = [
    {"iban": "FR7630001007941234567890185", "pays": "France", "banque": "BNP Paribas"},
    {"iban": "FR7630004000031234567890143", "pays": "France", "banque": "Societe Generale"},
    {"iban": "DE89370400440532013000", "pays": "Allemagne", "banque": "Deutsche Bank"},
    {"iban": "ES9121000418450200051332", "pays": "Espagne", "banque": "Santander"},
    {"iban": "IT60X0542811101000000123456", "pays": "Italie", "banque": "Intesa Sanpaolo"},
]

# Montants fixes, avec des cas limites autour de 5000
MONTANTS = [100.00, 250.50, 1200.00, 4999.99, 5000.00, 5000.01, 7500.00, 12000.00]


def generer_transaction(rng, date):
    """Crée une transaction (un dictionnaire) entre deux comptes différents."""
    origine, destinataire = rng.sample(COMPTES, 2)
    return {
        "datetime_transaction": date.strftime("%Y-%m-%d %H:%M:%S"),
        "iban_origine": origine["iban"],
        "pays_source": origine["pays"],
        "banque_source": origine["banque"],
        "iban_destinataire": destinataire["iban"],
        "pays_destinataire": destinataire["pays"],
        "montant": f"{rng.choice(MONTANTS):.2f}",
    }


def generer_fichier(chemin, rng, date_depart):
    """Écrit un fichier CSV contenant entre 5 et 10 transactions."""
    nb_transactions = rng.randint(5, 10)
    with open(chemin, "w", newline="", encoding="utf-8") as fichier:
        writer = csv.DictWriter(fichier, fieldnames=COLONNES)
        writer.writeheader()
        for i in range(nb_transactions):
            date = date_depart + timedelta(hours=i)
            writer.writerow(generer_transaction(rng, date))
    return nb_transactions


def generer_fichiers(dossier="data", nb_fichiers=3, seed=42):
    """Génère plusieurs fichiers CSV et renvoie la liste de leurs chemins."""
    os.makedirs(dossier, exist_ok=True)
    rng = random.Random(seed)
    chemins = []
    for numero in range(1, nb_fichiers + 1):
        chemin = os.path.join(dossier, f"transactions_{numero:03d}.csv")
        date_depart = datetime(2026, 1, numero, 9, 0, 0)
        nb = generer_fichier(chemin, rng, date_depart)
        print(f"Fichier généré : {chemin} ({nb} transactions)")
        chemins.append(chemin)
    return chemins


if __name__ == "__main__":
    generer_fichiers()
