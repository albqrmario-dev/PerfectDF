"""Testes para o backend web do PerfectDF."""

import io
import sys
from typing import Any
from fastapi.testclient import TestClient
import pymupdf
import pytest

from perfectdf.web.app import app

client = TestClient(app)


def _criar_pdf_exemplo(total_paginas: int = 2) -> bytes:
    doc = pymupdf.open()
    for i in range(total_paginas):
        page = doc.new_page(width=595, height=842)
        page.insert_text((50, 50), f"Página de teste {i + 1}")
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_ping() -> None:
    response = client.get("/api/ping")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "pong"}


def test_index() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "PerfectDF" in response.text
    assert "text/html" in response.headers.get("content-type", "")
    assert "viewer-section" in response.text
    assert "/static/vendor/pdfjs/pdf.min.js" in response.text


def test_static_files() -> None:
    response_css = client.get("/static/style.css")
    assert response_css.status_code == 200
    assert ":root" in response_css.text

    response_js = client.get("/static/app.js")
    assert response_js.status_code == 200
    assert "/api/ping" in response_js.text


def test_pdfjs_vendor_files() -> None:
    res_lib = client.get("/static/vendor/pdfjs/pdf.min.js")
    assert res_lib.status_code == 200
    assert "pdfjsLib" in res_lib.text

    res_worker = client.get("/static/vendor/pdfjs/pdf.worker.min.js")
    assert res_worker.status_code == 200
    assert len(res_worker.content) > 100_000


def test_inspecionar_pdf_valido() -> None:
    pdf_bytes = _criar_pdf_exemplo(total_paginas=3)
    files = {"arquivo": ("exemplo.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    response = client.post("/api/inspecionar", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["nome"] == "exemplo.pdf"
    assert data["total_paginas"] == 3
    assert data["tamanho"] == len(pdf_bytes)


def test_inspecionar_arquivo_invalido() -> None:
    files_ext = {"arquivo": ("teste.txt", io.BytesIO(b"conteudo"), "text/plain")}
    response_ext = client.post("/api/inspecionar", files=files_ext)
    assert response_ext.status_code == 400
    assert "erro" in response_ext.json()

    files_bad = {"arquivo": ("corrompido.pdf", io.BytesIO(b"invalido"), "application/pdf")}
    response_bad = client.post("/api/inspecionar", files=files_bad)
    assert response_bad.status_code == 400
    assert "erro" in response_bad.json()


def test_upload_arquivo_maior_que_50mb() -> None:
    conteudo_pesado = io.BytesIO(b"%PDF-" + (b"A" * (50 * 1024 * 1024 + 1024)))
    files = {"arquivo": ("pesado.pdf", conteudo_pesado, "application/pdf")}
    response = client.post("/api/inspecionar", files=files)
    assert response.status_code == 413
    assert response.json() == {
        "erro": "O arquivo excede o limite máximo permitido de 50 MB."
    }


def test_arquivo_falso_renomeado_pdf() -> None:
    falso_pdf = io.BytesIO(b"Este texto claramente nao e um documento pdf valido")
    files = {"arquivo": ("falso.pdf", falso_pdf, "application/pdf")}
    response = client.post("/api/inspecionar", files=files)
    assert response.status_code == 400
    assert response.json() == {
        "erro": "O arquivo enviado não é um documento PDF válido."
    }


def test_senha_incorreta_sem_vazar_senha() -> None:
    pdf_base = _criar_pdf_exemplo(total_paginas=1)
    files = {"arquivo": ("doc.pdf", io.BytesIO(pdf_base), "application/pdf")}
    res_prot = client.post(
        "/api/seguranca/proteger",
        files=files,
        data={"senha_usuario": "senhaSuperSecreta123"},
    )
    assert res_prot.status_code == 200

    senha_tentada = "senhaErradaTentativa999"
    files_prot = {"arquivo": ("protegido.pdf", io.BytesIO(res_prot.content), "application/pdf")}
    res_err = client.post(
        "/api/seguranca/remover-senha",
        files=files_prot,
        data={"senha": senha_tentada},
    )
    assert res_err.status_code == 400
    data = res_err.json()
    assert "erro" in data
    assert senha_tentada not in res_err.text
    assert "A senha informada está incorreta." in data["erro"]


def test_pagina_inexistente_retorna_400() -> None:
    pdf_base = _criar_pdf_exemplo(total_paginas=2)
    files = {"arquivo": ("doc.pdf", io.BytesIO(pdf_base), "application/pdf")}
    response = client.post("/api/paginas/extrair", files=files, data={"paginas": "99"})
    assert response.status_code == 400
    data = response.json()
    assert "erro" in data
    assert "Página inválida: 99" in data["erro"]


def test_erro_inesperado_retorna_500_generico(monkeypatch: pytest.MonkeyPatch) -> None:
    app_module = sys.modules["perfectdf.web.app"]
    client_safe = TestClient(app, raise_server_exceptions=False)

    pdf_base = _criar_pdf_exemplo(total_paginas=1)
    files = {"arquivo": ("doc.pdf", io.BytesIO(pdf_base), "application/pdf")}

    def _falha_forcada(*args: Any, **kwargs: Any) -> None:
        raise RuntimeError("Erro interno forçado para teste")

    monkeypatch.setattr(app_module, "girar_paginas", _falha_forcada)

    response = client_safe.post("/api/paginas/girar", files=files, data={"graus": "90"})
    assert response.status_code == 500
    assert response.json() == {
        "erro": "Ocorreu um erro interno ao processar a operação solicitada."
    }
    assert "Traceback" not in response.text
    assert "Erro interno forçado" not in response.text


def test_request_validation_error_422() -> None:
    response = client.post("/api/paginas/girar")
    assert response.status_code == 422
    assert response.json() == {
        "erro": "Dados da requisição inválidos ou incompletos."
    }


def test_rota_paginas_extrair_e_excluir() -> None:
    pdf_bytes = _criar_pdf_exemplo(total_paginas=4)

    files = {"arquivo": ("doc.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    res_ext = client.post("/api/paginas/extrair", files=files, data={"paginas": "1,3"})
    assert res_ext.status_code == 200
    doc_ext = pymupdf.open(stream=res_ext.content, filetype="pdf")
    assert len(doc_ext) == 2
    doc_ext.close()

    files = {"arquivo": ("doc.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    res_del = client.post("/api/paginas/excluir", files=files, data={"paginas": "1"})
    assert res_del.status_code == 200
    doc_del = pymupdf.open(stream=res_del.content, filetype="pdf")
    assert len(doc_del) == 3
    doc_del.close()


def test_rota_paginas_juntar() -> None:
    pdf1 = _criar_pdf_exemplo(total_paginas=1)
    pdf2 = _criar_pdf_exemplo(total_paginas=2)

    files = [
        ("arquivos", ("doc1.pdf", io.BytesIO(pdf1), "application/pdf")),
        ("arquivos", ("doc2.pdf", io.BytesIO(pdf2), "application/pdf")),
    ]
    response = client.post("/api/paginas/juntar", files=files)
    assert response.status_code == 200
    doc_juntado = pymupdf.open(stream=response.content, filetype="pdf")
    assert len(doc_juntado) == 3
    doc_juntado.close()


def test_rota_anotacoes() -> None:
    pdf_bytes = _criar_pdf_exemplo(total_paginas=2)

    files = {"arquivo": ("doc.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    res_marca = client.post("/api/anotacoes/marca-dagua", files=files, data={"texto": "CONFIDENCIAL"})
    assert res_marca.status_code == 200

    files = {"arquivo": ("doc.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    res_num = client.post("/api/anotacoes/numerar", files=files, data={"formato": "Pág {n}"})
    assert res_num.status_code == 200

    files = {"arquivo": ("doc.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    res_nota = client.post("/api/anotacoes/nota", files=files, data={"pagina": "1", "texto": "Nota teste"})
    assert res_nota.status_code == 200


def test_rota_texto_e_metadados() -> None:
    pdf_bytes = _criar_pdf_exemplo(total_paginas=1)

    files = {"arquivo": ("doc.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    res_txt = client.post("/api/texto/extrair", files=files)
    assert res_txt.status_code == 200
    assert "Página de teste 1" in res_txt.json()["texto"]

    files = {"arquivo": ("doc.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    res_add = client.post(
        "/api/texto/adicionar",
        files=files,
        data={"pagina": "1", "texto": "Novo Texto Inserido", "pos_x": "50", "pos_y": "100"},
    )
    assert res_add.status_code == 200
    doc_add = pymupdf.open(stream=res_add.content, filetype="pdf")
    assert "Novo Texto Inserido" in doc_add[0].get_text()
    doc_add.close()

    files = {"arquivo": ("doc.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    res_meta = client.post(
        "/api/metadados/editar",
        files=files,
        data={"titulo": "Titulo Teste", "autor": "Autor Teste"},
    )
    assert res_meta.status_code == 200
    doc_meta = pymupdf.open(stream=res_meta.content, filetype="pdf")
    assert doc_meta.metadata.get("title") == "Titulo Teste"
    assert doc_meta.metadata.get("author") == "Autor Teste"
    doc_meta.close()


def test_rota_seguranca_proteger_e_desproteger() -> None:
    pdf_bytes = _criar_pdf_exemplo(total_paginas=1)

    files = {"arquivo": ("doc.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    res_prot = client.post(
        "/api/seguranca/proteger",
        files=files,
        data={"senha_usuario": "senha123"},
    )
    assert res_prot.status_code == 200

    # Confirma a criptografia antes de testar a remoção da senha.
    doc_enc = pymupdf.open(stream=res_prot.content, filetype="pdf")
    assert doc_enc.is_encrypted
    assert not doc_enc.authenticate("errada")
    assert doc_enc.authenticate("senha123")
    doc_enc.close()

    files_rem = {"arquivo": ("prot.pdf", io.BytesIO(res_prot.content), "application/pdf")}
    res_rem = client.post(
        "/api/seguranca/remover-senha",
        files=files_rem,
        data={"senha": "senha123"},
    )
    assert res_rem.status_code == 200
    doc_dec = pymupdf.open(stream=res_rem.content, filetype="pdf")
    assert not doc_dec.is_encrypted
    doc_dec.close()
