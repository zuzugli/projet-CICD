"""Des groupes distincts vérifient que les regroupements ne sont pas confondus."""

from copy import deepcopy
from decimal import Decimal

from src.process_data import ajouter_flags, total_par_iban_origine, total_par_banque_source, total_par_iban_destinataire


def test_regroupements_distincts_et_purete():
    donnees = [
        {"iban_origine": "A", "banque_source": "X", "iban_destinataire": "C", "montant": Decimal("100")},
        {"iban_origine": "B", "banque_source": "X", "iban_destinataire": "C", "montant": Decimal("200")},
        {"iban_origine": "A", "banque_source": "X", "iban_destinataire": "D", "montant": Decimal("50")},
        {"iban_origine": "D", "banque_source": "Y", "iban_destinataire": "C", "montant": Decimal("20")},
    ]
    avant = deepcopy(donnees)
    assert total_par_iban_origine(donnees) == {"A": Decimal("150"), "B": Decimal("200"), "D": Decimal("20")}
    assert total_par_banque_source(donnees) == {"X": Decimal("350"), "Y": Decimal("20")}
    assert total_par_iban_destinataire(donnees) == {"C": Decimal("320"), "D": Decimal("50")}
    assert all(not ligne["flag_montant_eleve"] for ligne in ajouter_flags(donnees))
    assert donnees == avant
