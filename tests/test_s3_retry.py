from io import BytesIO
from unittest.mock import Mock, patch

import pytest
from botocore.exceptions import ClientError, EndpointConnectionError

from src.s3_storage import recuperer_csv


def test_reprise_apres_panne_temporaire():
    client = Mock()
    flux = BytesIO(b"contenu CSV de test")

    client.get_object.side_effect = [
        EndpointConnectionError(
            endpoint_url="http://127.0.0.1:8333"
        ),
        {"Body": flux},
    ]

    with patch("src.s3_storage.time.sleep") as attente:
        contenu = recuperer_csv(
            "exemple.csv",
            client,
            max_tentatives=3,
            delai=2,
        )

    assert contenu == b"contenu CSV de test"
    assert client.get_object.call_count == 2
    assert flux.closed
    attente.assert_called_once_with(2)


def test_arret_apres_limite():
    client = Mock()
    client.get_object.side_effect = EndpointConnectionError(
        endpoint_url="http://127.0.0.1:8333"
    )

    with patch("src.s3_storage.time.sleep") as attente:
        with pytest.raises(EndpointConnectionError):
            recuperer_csv(
                "exemple.csv",
                client,
                max_tentatives=3,
                delai=2,
            )

    assert client.get_object.call_count == 3
    assert attente.call_count == 2


def test_acces_refuse_sans_retry():
    client = Mock()
    client.get_object.side_effect = ClientError(
        {
            "Error": {
                "Code": "AccessDenied",
                "Message": "Accès refusé",
            },
            "ResponseMetadata": {
                "HTTPStatusCode": 403,
            },
        },
        "GetObject",
    )

    with patch("src.s3_storage.time.sleep") as attente:
        with pytest.raises(ClientError):
            recuperer_csv("exemple.csv", client)

    assert client.get_object.call_count == 1
    attente.assert_not_called()