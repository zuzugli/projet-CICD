"""Génère un avis de virement lisible pour une démonstration OCR reproductible."""

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


RACINE = Path(__file__).resolve().parents[1]


def _police(taille):
    for nom in ("C:/Windows/Fonts/consola.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", "DejaVuSansMono.ttf"):
        try:
            return ImageFont.truetype(nom, taille)
        except OSError:
            continue
    raise RuntimeError("Installer une police monospace Consolas ou DejaVu Sans Mono.")


def generer_image(destination=None):
    destination = Path(destination or RACINE / "examples" / "transaction.png")
    champs = json.loads((RACINE / "examples" / "image_attendue.json").read_text(encoding="utf-8"))
    image = Image.new("RGB", (1600, 800), "white")
    dessin = ImageDraw.Draw(image)
    dessin.text((70, 45), "AVIS DE VIREMENT - EXEMPLE PEDAGOGIQUE", font=_police(34), fill="black")
    libelles = [("Date", "datetime_transaction"), ("IBAN origine", "iban_origine"),
                ("Pays source", "pays_source"), ("Banque source", "banque_source"),
                ("IBAN destinataire", "iban_destinataire"),
                ("Pays destinataire", "pays_destinataire"), ("Montant", "montant")]
    for numero, (libelle, cle) in enumerate(libelles):
        valeur = champs[cle] + (" EUR" if cle == "montant" else "")
        dessin.text((70, 155 + numero * 75), f"{libelle}: {valeur}", font=_police(30), fill="black")
    destination.parent.mkdir(parents=True, exist_ok=True)
    image.save(destination)
    return destination


if __name__ == "__main__":
    print(generer_image())
