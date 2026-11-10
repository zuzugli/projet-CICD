"""Vérifications du chargement sur des fichiers temporaires indépendants."""

import csv
from copy import deepcopy
from datetime import datetime
from decimal import Decimal
from pathlib import Path
import tempfile
import unittest

from src.load_data import COLONNES_ATTENDUES, charger_csv, valider_ligne


class TestChargementCSV(unittest.TestCase):
    def setUp(self):
        self.ligne = {
            "datetime_transaction": "2026-01-02 09:00:00",
            "iban_origine": "ES9121000418450200051332",
            "pays_source": "Espagne",
            "banque_source": "Santander",
            "iban_destinataire": "FR7630001007941234567890185",
            "pays_destinataire": "France",
            "montant": "5000.01",
        }
        self.dossier = tempfile.TemporaryDirectory()
        self.addCleanup(self.dossier.cleanup)
        self.chemin = Path(self.dossier.name) / "transactions.csv"

    def ecrire_csv(self, colonnes, lignes):
        with self.chemin.open("w", newline="", encoding="utf-8") as fichier:
            writer = csv.writer(fichier)
            writer.writerow(colonnes)
            writer.writerows(lignes)

    def test_fichier_valide_et_conversion(self):
        self.ecrire_csv(COLONNES_ATTENDUES, [list(self.ligne.values())])
        resultat = charger_csv(self.chemin)
        self.assertEqual(len(resultat), 1)
        self.assertEqual(resultat[0]["montant"], Decimal("5000.01"))
        self.assertEqual(resultat[0]["datetime_transaction"], datetime(2026, 1, 2, 9))

    def test_entete_invalide(self):
        for colonnes in (COLONNES_ATTENDUES[:-1], COLONNES_ATTENDUES + ["autre"],
                         COLONNES_ATTENDUES[:-1] + ["iban_origine"]):
            with self.subTest(colonnes=colonnes):
                self.ecrire_csv(colonnes, [])
                with self.assertRaisesRegex(ValueError, "En-tête CSV invalide"):
                    charger_csv(self.chemin)

    def test_fichier_vide_ou_sans_transactions(self):
        self.chemin.write_text("", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "En-tête CSV invalide"):
            charger_csv(self.chemin)
        self.ecrire_csv(COLONNES_ATTENDUES, [])
        with self.assertRaisesRegex(ValueError, "aucune transaction"):
            charger_csv(self.chemin)

    def test_champs_vides(self):
        for colonne in COLONNES_ATTENDUES:
            with self.subTest(colonne=colonne):
                ligne = dict(self.ligne, **{colonne: " "})
                with self.assertRaisesRegex(ValueError, "Ligne 2.*vide ou absent"):
                    valider_ligne(ligne, 2)

    def test_date_invalide(self):
        self.ligne["datetime_transaction"] = "2026-02-30 09:00:00"
        with self.assertRaisesRegex(ValueError, "Ligne 2.*date invalide"):
            valider_ligne(self.ligne, 2)

    def test_montants_invalides(self):
        for montant in ("abc", "-1", "0", "NaN", "Infinity", "1.001", "1e100"):
            with self.subTest(montant=montant):
                self.ligne["montant"] = montant
                with self.assertRaisesRegex(ValueError, "Ligne 2.*montant"):
                    valider_ligne(self.ligne, 2)

    def test_nombre_de_valeurs_incorrect(self):
        valeurs = list(self.ligne.values())
        for ligne in (valeurs[:-1], valeurs + ["en trop"]):
            with self.subTest(ligne=ligne):
                self.ecrire_csv(COLONNES_ATTENDUES, [ligne])
                with self.assertRaisesRegex(ValueError, "Ligne 2"):
                    charger_csv(self.chemin)

    def test_validation_ne_modifie_pas_entree(self):
        avant = deepcopy(self.ligne)
        resultat = valider_ligne(self.ligne, 2)
        self.assertEqual(self.ligne, avant)
        self.assertIsNot(resultat, self.ligne)


if __name__ == "__main__":
    unittest.main()
