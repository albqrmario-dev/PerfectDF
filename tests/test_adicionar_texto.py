import os

import pymupdf
import pytest

from perfectdf import adicionar_texto, proteger_pdf


@pytest.fixture
def pdf_teste(tmp_path):
    caminho = str(tmp_path / "base.pdf")
    doc = pymupdf.open()
    page1 = doc.new_page(width=400, height=600)
    page1.insert_text((50, 50), "Texto original", fontsize=12)
    doc.new_page(width=400, height=600)
    doc.save(caminho)
    doc.close()
    return caminho


def test_adicionar_texto_basico(tmp_path, pdf_teste):
    saida = str(tmp_path / "texto_adicionado.pdf")
    resultado = adicionar_texto(
        pdf=pdf_teste,
        pagina=1,
        texto="Novo texto adicionado",
        posicao=(50, 150),
        fonte="helv",
        tamanho=14,
        cor="azul",
        saida=saida,
    )
    assert resultado == saida
    assert os.path.isfile(saida)

    doc = pymupdf.open(saida)
    assert "Novo texto adicionado" in doc[0].get_text()
    doc.close()


def test_adicionar_texto_mesmo_arquivo(tmp_path, pdf_teste):
    copia = str(tmp_path / "copia.pdf")
    doc = pymupdf.open(pdf_teste)
    doc.save(copia)
    doc.close()

    resultado = adicionar_texto(
        pdf=copia,
        pagina=2,
        texto="Texto na pagina 2",
        posicao=(60, 60),
    )
    assert resultado == copia
    doc_editado = pymupdf.open(copia)
    assert "Texto na pagina 2" in doc_editado[1].get_text()
    doc_editado.close()


def test_adicionar_texto_cores_diversas(tmp_path, pdf_teste):
    # Cores nomeadas e tuplas RGB (0-1 e 0-255)
    for i, cor in enumerate(["vermelho", (0.0, 1.0, 0.0), (0, 0, 255)]):
        saida = str(tmp_path / f"cor_{i}.pdf")
        adicionar_texto(
            pdf=pdf_teste,
            pagina=1,
            texto=f"Cor {i}",
            posicao=(50, 100 + i * 30),
            cor=cor,
            saida=saida,
        )
        assert os.path.isfile(saida)


def test_adicionar_texto_fontes(tmp_path, pdf_teste):
    for fonte in ["times", "courier", "helvetica"]:
        saida = str(tmp_path / f"fonte_{fonte}.pdf")
        adicionar_texto(
            pdf=pdf_teste,
            pagina=1,
            texto=f"Fonte {fonte}",
            posicao=(50, 100),
            fonte=fonte,
            saida=saida,
        )
        assert os.path.isfile(saida)


def test_adicionar_texto_pagina_rotacionada(tmp_path):
    caminho = str(tmp_path / "rotacionado.pdf")
    doc = pymupdf.open()
    page = doc.new_page(width=400, height=600)
    page.set_rotation(90)
    doc.save(caminho)
    doc.close()

    saida = str(tmp_path / "rotacionado_com_texto.pdf")
    adicionar_texto(
        pdf=caminho,
        pagina=1,
        texto="Texto em pagina rotacionada",
        posicao=(100, 100),
        saida=saida,
    )
    doc2 = pymupdf.open(saida)
    assert "Texto em pagina rotacionada" in doc2[0].get_text()
    doc2.close()


def test_adicionar_texto_validacoes(tmp_path, pdf_teste):
    # Arquivo não existe
    with pytest.raises(ValueError, match="não foi encontrado"):
        adicionar_texto("inexistente.pdf", 1, "Ola", (50, 50))

    # Página inválida
    with pytest.raises(ValueError, match="Página inválida"):
        adicionar_texto(pdf_teste, 99, "Ola", (50, 50))
    with pytest.raises(ValueError, match="maior ou igual a 1"):
        adicionar_texto(pdf_teste, 0, "Ola", (50, 50))

    # Texto vazio
    with pytest.raises(ValueError, match="não pode estar vazio"):
        adicionar_texto(pdf_teste, 1, "   ", (50, 50))

    # Posição negativa ou fora da página
    with pytest.raises(ValueError, match="não podem ser negativas"):
        adicionar_texto(pdf_teste, 1, "Ola", (-10, 50))
    with pytest.raises(ValueError, match="fora dos limites"):
        adicionar_texto(pdf_teste, 1, "Ola", (1000, 1000))

    # Tamanho de fonte inválido
    with pytest.raises(ValueError, match="maior que zero"):
        adicionar_texto(pdf_teste, 1, "Ola", (50, 50), tamanho=0)

    # Cor inválida
    with pytest.raises(ValueError, match="Cor inválida"):
        adicionar_texto(pdf_teste, 1, "Ola", (50, 50), cor="cor_inexistente")


def test_adicionar_texto_pdf_protegido(tmp_path, pdf_teste):
    protegido = str(tmp_path / "protegido.pdf")
    proteger_pdf(pdf_teste, protegido, "senha123")

    with pytest.raises(ValueError, match="protegido por senha"):
        adicionar_texto(protegido, 1, "Ola", (50, 50))
