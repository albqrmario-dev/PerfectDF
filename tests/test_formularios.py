# pyright: reportArgumentType=false, reportAttributeAccessIssue=false, reportOptionalSubscript=false
"""Testes para o módulo perfectdf.formularios (AcroForm)."""

import os

import pymupdf
import pytest

from perfectdf.formularios import (
    achatar_formulario,
    listar_campos,
    preencher_formulario,
)


@pytest.fixture
def pdf_com_formulario(tmp_path):
    """Cria um PDF com vários tipos de campos de formulário usando widgets do PyMuPDF."""
    doc = pymupdf.open()
    page = doc.new_page(width=400, height=400)

    # Campo de texto
    widget_texto = pymupdf.Widget()
    widget_texto.field_name = "nome_completo"
    widget_texto.field_type = pymupdf.PDF_WIDGET_TYPE_TEXT
    widget_texto.field_value = ""
    widget_texto.rect = pymupdf.Rect(50, 50, 250, 70)
    page.add_widget(widget_texto)

    # Checkbox
    widget_check = pymupdf.Widget()
    widget_check.field_name = "aceito_termos"
    widget_check.field_type = pymupdf.PDF_WIDGET_TYPE_CHECKBOX
    widget_check.field_value = "Off"
    widget_check.rect = pymupdf.Rect(50, 90, 70, 110)
    page.add_widget(widget_check)

    # Outro campo de texto
    widget_email = pymupdf.Widget()
    widget_email.field_name = "email"
    widget_email.field_type = pymupdf.PDF_WIDGET_TYPE_TEXT
    widget_email.field_value = ""
    widget_email.rect = pymupdf.Rect(50, 130, 250, 150)
    page.add_widget(widget_email)

    caminho = str(tmp_path / "formulario.pdf")
    doc.save(caminho)
    doc.close()
    return caminho


@pytest.fixture
def pdf_sem_formulario(tmp_path):
    """Cria um PDF simples sem nenhum campo de formulário."""
    doc = pymupdf.open()
    page = doc.new_page(width=300, height=300)
    page.insert_text((50, 50), "Sem formulário", fontsize=14)
    caminho = str(tmp_path / "sem_formulario.pdf")
    doc.save(caminho)
    doc.close()
    return caminho


@pytest.fixture
def pdf_formulario_multipaginas(tmp_path):
    """Cria um PDF com campos de formulário em 2 páginas diferentes."""
    doc = pymupdf.open()

    # Página 1
    page1 = doc.new_page(width=400, height=400)
    w1 = pymupdf.Widget()
    w1.field_name = "campo_pag1"
    w1.field_type = pymupdf.PDF_WIDGET_TYPE_TEXT
    w1.field_value = "valor_inicial"
    w1.rect = pymupdf.Rect(50, 50, 250, 70)
    page1.add_widget(w1)

    # Página 2
    page2 = doc.new_page(width=400, height=400)
    w2 = pymupdf.Widget()
    w2.field_name = "campo_pag2"
    w2.field_type = pymupdf.PDF_WIDGET_TYPE_TEXT
    w2.field_value = ""
    w2.rect = pymupdf.Rect(50, 50, 250, 70)
    page2.add_widget(w2)

    caminho = str(tmp_path / "multi_paginas.pdf")
    doc.save(caminho)
    doc.close()
    return caminho


# ─────────────────────────────────────────────────────────────────────────────
# listar_campos
# ─────────────────────────────────────────────────────────────────────────────


class TestListarCampos:
    def test_listar_campos_basico(self, pdf_com_formulario):
        campos = listar_campos(pdf_com_formulario)
        assert isinstance(campos, list)
        assert len(campos) == 3

        nomes = [c["nome"] for c in campos]
        assert "nome_completo" in nomes
        assert "aceito_termos" in nomes
        assert "email" in nomes

    def test_listar_campos_tipos(self, pdf_com_formulario):
        campos = listar_campos(pdf_com_formulario)
        por_nome = {c["nome"]: c for c in campos}

        assert por_nome["nome_completo"]["tipo"] == "texto"
        assert por_nome["aceito_termos"]["tipo"] == "checkbox"
        assert por_nome["email"]["tipo"] == "texto"

    def test_listar_campos_pagina(self, pdf_com_formulario):
        campos = listar_campos(pdf_com_formulario)
        for campo in campos:
            assert campo["pagina"] == 1

    def test_listar_campos_multipaginas(self, pdf_formulario_multipaginas):
        campos = listar_campos(pdf_formulario_multipaginas)
        por_nome = {c["nome"]: c for c in campos}

        assert por_nome["campo_pag1"]["pagina"] == 1
        assert por_nome["campo_pag2"]["pagina"] == 2

    def test_listar_campos_valor_atual(self, pdf_formulario_multipaginas):
        campos = listar_campos(pdf_formulario_multipaginas)
        por_nome = {c["nome"]: c for c in campos}
        assert por_nome["campo_pag1"]["valor"] == "valor_inicial"

    def test_listar_campos_pdf_sem_formulario(self, pdf_sem_formulario):
        with pytest.raises(ValueError, match="não contém formulário"):
            listar_campos(pdf_sem_formulario)

    def test_listar_campos_arquivo_nao_encontrado(self):
        with pytest.raises(ValueError, match="não foi encontrado"):
            listar_campos("/caminho/inexistente.pdf")

    def test_listar_campos_caminho_vazio(self):
        with pytest.raises(ValueError, match="string não vazia"):
            listar_campos("")


# ─────────────────────────────────────────────────────────────────────────────
# preencher_formulario
# ─────────────────────────────────────────────────────────────────────────────


class TestPreencherFormulario:
    def test_preencher_texto(self, tmp_path, pdf_com_formulario):
        saida = str(tmp_path / "preenchido.pdf")
        preencher_formulario(
            pdf_com_formulario,
            {"nome_completo": "João Silva", "email": "joao@email.com"},
            saida,
        )
        assert os.path.isfile(saida)

        # Verificar que os campos foram preenchidos
        campos = listar_campos(saida)
        por_nome = {c["nome"]: c for c in campos}
        assert por_nome["nome_completo"]["valor"] == "João Silva"
        assert por_nome["email"]["valor"] == "joao@email.com"

    def test_preencher_checkbox_bool(self, tmp_path, pdf_com_formulario):
        saida = str(tmp_path / "preenchido_check.pdf")
        preencher_formulario(
            pdf_com_formulario,
            {"aceito_termos": True},
            saida,
        )
        campos = listar_campos(saida)
        por_nome = {c["nome"]: c for c in campos}
        assert por_nome["aceito_termos"]["valor"] == "Yes"

    def test_preencher_checkbox_false(self, tmp_path, pdf_com_formulario):
        saida = str(tmp_path / "preenchido_uncheck.pdf")
        preencher_formulario(
            pdf_com_formulario,
            {"aceito_termos": False},
            saida,
        )
        campos = listar_campos(saida)
        por_nome = {c["nome"]: c for c in campos}
        assert por_nome["aceito_termos"]["valor"] == "Off"

    def test_preencher_campo_inexistente(self, tmp_path, pdf_com_formulario):
        saida = str(tmp_path / "saida.pdf")
        with pytest.raises(ValueError, match="Campo.*não encontrado"):
            preencher_formulario(
                pdf_com_formulario,
                {"campo_que_nao_existe": "valor"},
                saida,
            )

    def test_preencher_pdf_sem_formulario(self, tmp_path, pdf_sem_formulario):
        saida = str(tmp_path / "saida.pdf")
        with pytest.raises(ValueError, match="não contém formulário"):
            preencher_formulario(
                pdf_sem_formulario,
                {"qualquer": "valor"},
                saida,
            )

    def test_preencher_valores_vazio(self, tmp_path, pdf_com_formulario):
        saida = str(tmp_path / "saida.pdf")
        with pytest.raises(ValueError, match="dicionário não vazio"):
            preencher_formulario(pdf_com_formulario, {}, saida)

    def test_preencher_retorna_caminho(self, tmp_path, pdf_com_formulario):
        saida = str(tmp_path / "preenchido.pdf")
        resultado = preencher_formulario(
            pdf_com_formulario,
            {"nome_completo": "Teste"},
            saida,
        )
        assert resultado == saida

    def test_preencher_saida_igual_origem(self, pdf_com_formulario):
        with pytest.raises(ValueError, match="não pode ser igual"):
            preencher_formulario(
                pdf_com_formulario,
                {"nome_completo": "Teste"},
                pdf_com_formulario,
            )

    def test_preencher_arquivo_nao_encontrado(self, tmp_path):
        saida = str(tmp_path / "saida.pdf")
        with pytest.raises(ValueError, match="não foi encontrado"):
            preencher_formulario(
                "/caminho/inexistente.pdf",
                {"campo": "valor"},
                saida,
            )

    def test_preencher_multipaginas(self, tmp_path, pdf_formulario_multipaginas):
        saida = str(tmp_path / "preenchido_multi.pdf")
        preencher_formulario(
            pdf_formulario_multipaginas,
            {"campo_pag1": "Novo valor 1", "campo_pag2": "Novo valor 2"},
            saida,
        )
        campos = listar_campos(saida)
        por_nome = {c["nome"]: c for c in campos}
        assert por_nome["campo_pag1"]["valor"] == "Novo valor 1"
        assert por_nome["campo_pag2"]["valor"] == "Novo valor 2"


# ─────────────────────────────────────────────────────────────────────────────
# achatar_formulario
# ─────────────────────────────────────────────────────────────────────────────


class TestAchatarFormulario:
    def test_achatar_remove_widgets(self, tmp_path, pdf_com_formulario):
        saida = str(tmp_path / "achatado.pdf")
        achatar_formulario(pdf_com_formulario, saida)
        assert os.path.isfile(saida)

        # Após achatar, não deve mais haver widgets
        doc = pymupdf.open(saida)
        total_widgets = 0
        for page in doc:
            for _ in page.widgets():
                total_widgets += 1
        doc.close()
        assert total_widgets == 0

    def test_achatar_preserva_conteudo_preenchido(self, tmp_path, pdf_com_formulario):
        # Primeiro preencher, depois achatar
        preenchido = str(tmp_path / "preenchido.pdf")
        preencher_formulario(
            pdf_com_formulario,
            {"nome_completo": "Maria Santos"},
            preenchido,
        )

        achatado = str(tmp_path / "achatado.pdf")
        achatar_formulario(preenchido, achatado)

        # O arquivo deve existir e não ter widgets
        doc = pymupdf.open(achatado)
        total_widgets = 0
        for page in doc:
            for _ in page.widgets():
                total_widgets += 1
        doc.close()
        assert total_widgets == 0

    def test_achatar_pdf_sem_formulario(self, tmp_path, pdf_sem_formulario):
        saida = str(tmp_path / "saida.pdf")
        with pytest.raises(ValueError, match="não contém formulário"):
            achatar_formulario(pdf_sem_formulario, saida)

    def test_achatar_retorna_caminho(self, tmp_path, pdf_com_formulario):
        saida = str(tmp_path / "achatado.pdf")
        resultado = achatar_formulario(pdf_com_formulario, saida)
        assert resultado == saida

    def test_achatar_saida_igual_origem(self, pdf_com_formulario):
        with pytest.raises(ValueError, match="não pode ser igual"):
            achatar_formulario(pdf_com_formulario, pdf_com_formulario)

    def test_achatar_arquivo_nao_encontrado(self, tmp_path):
        saida = str(tmp_path / "saida.pdf")
        with pytest.raises(ValueError, match="não foi encontrado"):
            achatar_formulario("/caminho/inexistente.pdf", saida)
