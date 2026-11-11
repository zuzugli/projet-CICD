"""Préparation unique des outils locaux ; la démonstration ne télécharge pas de modèle."""

import argparse
from pathlib import Path
import subprocess

from src.generer_exemples import generer_image
from src.slm import MODELE, attendre_ollama


def preparer(sans_modele=False):
    racine = Path(__file__).resolve().parents[1]
    print("Création de l'image d'exemple", flush=True)
    generer_image()
    print("Construction de l'outil OCR Docker", flush=True)
    subprocess.run(["docker", "build", "-t", "pipeline-data:local", "."], cwd=racine, check=True)
    services = ["postgres", "seaweedfs"] + ([] if sans_modele else ["ollama"])
    subprocess.run(["docker", "compose", "--profile", "niveau3", "up", "-d", "--wait", *services],
                   cwd=racine, check=True)
    if not sans_modele:
        attendre_ollama()
        print(f"Téléchargement unique du modèle {MODELE}", flush=True)
        subprocess.run(["docker", "compose", "exec", "-T", "ollama", "ollama", "pull", MODELE],
                       cwd=racine, check=True)
    if sans_modele:
        print("OCR prêt. Relancer sans --sans-modele pour préparer aussi le SLM.", flush=True)
    else:
        print("Outils prêts. Lancer : python -m src.demo verifier", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sans-modele", action="store_true")
    preparer(parser.parse_args().sans_modele)
