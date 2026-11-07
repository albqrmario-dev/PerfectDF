"""Testes para o backend web do PerfectDF."""

from fastapi.testclient import TestClient

from perfectdf.web.app import app

client = TestClient(app)


def test_ping() -> None:
    """Verifica a rota de healthcheck /api/ping."""
    response = client.get("/api/ping")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "pong"}


def test_index() -> None:
    """Verifica se a rota raiz entrega o index.html."""
    response = client.get("/")
    assert response.status_code == 200
    assert "PerfectDF" in response.text
    assert "text/html" in response.headers.get("content-type", "")


def test_static_files() -> None:
    """Verifica se os arquivos estáticos são servidos em /static."""
    response_css = client.get("/static/style.css")
    assert response_css.status_code == 200
    assert "--primary" in response_css.text

    response_js = client.get("/static/app.js")
    assert response_js.status_code == 200
    assert "/api/ping" in response_js.text
