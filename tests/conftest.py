"""Fixtures communes : seules les ressources réservées aux tests sont nettoyées."""

from uuid import uuid4

import pytest

from src.database import connecter
from src.s3_storage import creer_client_s3


@pytest.fixture
def base_test():
    nettoyage = """
        TRUNCATE TABLE transactions, totaux_iban_origine,
        totaux_banque_source, totaux_iban_destinataire, processed_files
        RESTART IDENTITY;
    """
    with connecter("transactions_test") as connexion:
        connexion.execute(nettoyage)
    try:
        yield "transactions_test"
    finally:
        with connecter("transactions_test") as connexion:
            connexion.execute(nettoyage)


@pytest.fixture
def bucket_s3_test():
    client = creer_client_s3()
    nom = "test-niveau3-" + uuid4().hex
    client.create_bucket(Bucket=nom)
    try:
        yield client, nom
    finally:
        for page in client.get_paginator("list_objects_v2").paginate(Bucket=nom):
            for objet in page.get("Contents", []):
                client.delete_object(Bucket=nom, Key=objet["Key"])
        client.delete_bucket(Bucket=nom)
