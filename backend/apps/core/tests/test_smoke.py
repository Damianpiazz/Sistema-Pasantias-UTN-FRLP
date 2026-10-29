import pytest

pytestmark = pytest.mark.integration


def test_health_responde_ok(client):
    response = client.get("/health/")

    assert response.status_code == 200
    assert response.content == b"ok"


def test_home_renderiza(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"SGPC" in response.content
