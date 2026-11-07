"""Testes para o backend web do PerfectDF."""

import io
from fastapi.testclient import TestClient
import pymupdf

from perfectdf.web.app import app

client = TestClient(app)


def _criar_pdf_exemplo(total_paginas: int = 2) -> bytes:
    """Cria um PDF simples em memória para uso nos testes."""
    doc = pymupdf.open()
    for i in range(total_paginas):
        page = doc.new_page(width=595, height=842)
        page.insert_text((50, 50), f"Página de teste {i + 1}")
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_ping() -> None:
    """Verifica a rota de healthcheck /api/ping."""
    response = client.get("/api/ping")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "pong"}


def test_index() -> None:
    """Verifica se a rota raiz entrega o index.html com os elementos do visualizador."""
    response = client.get("/")
    assert response.status_code == 200
    assert "PerfectDF" in response.text
    assert "text/html" in response.headers.get("content-type", "")
    assert "viewer-section" in response.text
    assert "/static/vendor/pdfjs/pdf.min.js" in response.text


def test_static_files() -> None:
    """Verifica se os arquivos estáticos são servidos em /static."""
    response_css = client.get("/static/style.css")
    assert response_css.status_code == 200
    assert "--primary" in response_css.text

    response_js = client.get("/static/app.js")
    assert response_js.status_code == 200
    assert "/api/ping" in response_js.text


def test_pdfjs_vendor_files() -> None:
    """Verifica se os arquivos da biblioteca pdf.js estão presentes e são servidos localmente sem CDN."""
    res_lib = client.get("/static/vendor/pdfjs/pdf.min.js")
    assert res_lib.status_code == 200
    assert "pdfjsLib" in res_lib.text

    res_worker = client.get("/static/vendor/pdfjs/pdf.worker.min.js")
    assert res_worker.status_code == 200
    assert len(res_worker.content) > 100_000


def test_inspecionar_pdf_valido() -> None:
    """Testa a rota /api/inspecionar com PDF válido."""
    pdf_bytes = _criar_pdf_exemplo(total_paginas=3)
    files = {"arquivo": ("exemplo.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    response = client.post("/api/inspecionar", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["nome"] == "exemplo.pdf"
    assert data["total_paginas"] == 3
    assert data["tamanho"] == len(pdf_bytes)


def test_inspecionar_arquivo_invalido() -> None:
    """Testa a rota /api/inspecionar com arquivo sem extensão .pdf ou corrompido."""
    files_ext = {"arquivo": ("teste.txt", io.BytesIO(b"conteudo"), "text/plain")}
    response_ext = client.post("/api/inspecionar", files=files_ext)
    assert response_ext.status_code == 400

    files_bad = {"arquivo": ("corrompido.pdf", io.BytesIO(b"invalido"), "application/pdf")}
    response_bad = client.post("/api/inspecionar", files=files_bad)
    assert response_bad.status_code == 400


def test_processar_comprimir() -> None:
    """Testa a rota /api/processar na operação de compressão."""
    pdf_bytes = _criar_pdf_exemplo(total_paginas=2)
    files = {"arquivo": ("doc.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    data = {"operacao": "comprimir", "nivel": "medio"}
    response = client.post("/api/processar", files=files, data=data)

    assert response.status_code == 200
    assert response.headers.get("content-type") == "application/pdf"
    assert "attachment; filename=\"processado_doc.pdf\"" in response.headers.get("content-disposition", "")

    # Valida que o PDF resultante é válido
    result_doc = pymupdf.open(stream=response.content, filetype="pdf")
    assert len(result_doc) == 2
    result_doc.close()


def test_processar_girar() -> None:
    """Testa a rota /api/processar na operação de giro de páginas."""
    pdf_bytes = _criar_pdf_exemplo(total_paginas=1)
    files = {"arquivo": ("girar.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    data = {"operacao": "girar", "graus": "90"}
    response = client.post("/api/processar", files=files, data=data)

    assert response.status_code == 200
    assert response.headers.get("content-type") == "application/pdf"

    result_doc = pymupdf.open(stream=response.content, filetype="pdf")
    assert result_doc[0].rotation == 90
    result_doc.close()
