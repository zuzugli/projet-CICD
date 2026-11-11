"""Tesseract lit l'image ; un parseur explicite interprète l'avis de virement."""

import os
from pathlib import Path
import re
import shutil
import subprocess
import unicodedata

from src.normalisation import normaliser_transaction


LABELS = {
    "date": "datetime_transaction",
    "iban origine": "iban_origine",
    "pays source": "pays_source",
    "banque source": "banque_source",
    "iban destinataire": "iban_destinataire",
    "pays destinataire": "pays_destinataire",
    "montant": "montant",
}


def extraire_champs_ocr(texte):
    """Supporte les avis étiquetés de démonstration, pas tous les relevés bancaires."""
    champs = {}
    for ligne in texte.splitlines():
        if ":" not in ligne:
            continue
        etiquette, valeur = ligne.split(":", 1)
        etiquette = "".join(
            c for c in unicodedata.normalize("NFKD", etiquette) if not unicodedata.combining(c)
        )
        etiquette = re.sub(r"\s+", " ", etiquette.strip().lower())
        if etiquette in LABELS:
            cle = LABELS[etiquette]
            if cle in champs:
                raise ValueError(f"Champ OCR en double : {etiquette}.")
            champs[cle] = valeur.strip()
    return normaliser_transaction(champs)


def lire_image(chemin):
    """Utilise Tesseract installé, ou l'image Docker locale pipeline-data:local."""
    chemin = Path(chemin).resolve(strict=True)
    executable = shutil.which(os.getenv("TESSERACT_CMD", "tesseract"))
    if executable:
        commande = [executable, str(chemin), "stdout", "-l", "fra+eng", "--psm", "6"]
    else:
        commande = [
            "docker", "run", "--rm", "--network", "none",
            "--mount", f"type=bind,source={chemin.parent},target=/entree,readonly",
            "pipeline-data:local", "tesseract", f"/entree/{chemin.name}",
            "stdout", "-l", "fra+eng", "--psm", "6",
        ]
    try:
        resultat = subprocess.run(
            commande, capture_output=True, text=True, encoding="utf-8", timeout=90,
            check=True,
        )
    except (OSError, subprocess.SubprocessError) as erreur:
        raise RuntimeError(
            "OCR indisponible. Exécuter d'abord : python -m src.preparer_demo"
        ) from erreur
    return resultat.stdout


def extraire_image(chemin):
    texte = lire_image(chemin)
    return texte, extraire_champs_ocr(texte)
