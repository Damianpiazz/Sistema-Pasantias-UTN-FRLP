import pytest

pytestmark = pytest.mark.integration


def test_pagina_login_renderiza(client):
    response = client.get("/cuentas/login/")

    assert response.status_code == 200
    assert b"Iniciar sesi" in response.content
