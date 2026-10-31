import os
import pymupdf
import pytest

from perfectdf import adicionar_imagem, proteger_pdf


@pytest.fixture
def pdf_base(tmp_path):
    caminho = str(tmp_path / "base.pdf")
    doc = pymupdf.open()
    doc.new_page(width=500, height=700)
    doc.new_page(width=500, height=700)
    doc.save(caminho)
    doc.close()
    return caminho


@pytest.fixture
def imagem_png(tmp_path):
    caminho = str(tmp_path / "icone.png")
    pix = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 80, 60), 0)
    pix.clear_with(200)
    pix.save(caminho)
    return caminho


def test_adicionar_imagem_basico(tmp_path, pdf_base, imagem_png):
    saida = str(tmp_path / "com_imagem.pdf")
    resultado = adicionar_imagem(
        pdf=pdf_base,
        pagina=1,
        imagem=imagem_png,
        posicao=(50, 100),
        tamanho=(120, 90),
        saida=saida,
    )
    assert resultado == saida
    assert os.path.isfile(saida)

    doc = pymupdf.open(saida)
    assert len(doc[0].get_images()) == 1
    assert len(doc[1].get_images()) == 0
    doc.close()


def test_adicionar_imagem_mesmo_arquivo(tmp_path, pdf_base, imagem_png):
    copia = str(tmp_path / "copia.pdf")
    doc = pymupdf.open(pdf_base)
    doc.save(copia)
    doc.close()

    resultado = adicionar_imagem(
        pdf=copia,
        pagina=2,
        imagem=imagem_png,
        posicao=(100, 150),
        tamanho=100.0,  # Proporcional
    )
    assert resultado == copia
    doc_editado = pymupdf.open(copia)
    assert len(doc_editado[1].get_images()) == 1
    doc_editado.close()


def test_adicionar_imagem_tamanho_none(tmp_path, pdf_base, imagem_png):
    saida = str(tmp_path / "tam_original.pdf")
    adicionar_imagem(
        pdf=pdf_base,
        pagina=1,
        imagem=imagem_png,
        posicao=(20, 20),
        tamanho=None,
        saida=saida,
    )
    doc = pymupdf.open(saida)
    assert len(doc[0].get_images()) == 1
    doc.close()


def test_adicionar_imagem_pagina_rotacionada(tmp_path, imagem_png):
    caminho = str(tmp_path / "rotacionado.pdf")
    doc = pymupdf.open()
    page = doc.new_page(width=400, height=600)
    page.set_rotation(90)
    doc.save(caminho)
    doc.close()

    saida = str(tmp_path / "rot_imagem.pdf")
    adicionar_imagem(
        pdf=caminho,
        pagina=1,
        imagem=imagem_png,
        posicao=(50, 50),
        tamanho=(80, 60),
        saida=saida,
    )
    doc2 = pymupdf.open(saida)
    assert len(doc2[0].get_images()) == 1
    doc2.close()


def test_adicionar_imagem_validacoes(tmp_path, pdf_base, imagem_png):
    # Arquivo PDF não existe
    with pytest.raises(ValueError, match="não foi encontrado"):
        adicionar_imagem("inexistente.pdf", 1, imagem_png, (50, 50), (100, 100))

    # Imagem não existe
    with pytest.raises(ValueError, match="não foi encontrado"):
        adicionar_imagem(pdf_base, 1, "inexistente.png", (50, 50), (100, 100))

    # Arquivo não é imagem válida
    falso = str(tmp_path / "falso.png")
    with open(falso, "w") as f:
        f.write("não é imagem")
    with pytest.raises(ValueError, match="não é uma imagem válida"):
        adicionar_imagem(pdf_base, 1, falso, (50, 50), (100, 100))

    # Página inválida
    with pytest.raises(ValueError, match="Página inválida"):
        adicionar_imagem(pdf_base, 99, imagem_png, (50, 50), (100, 100))
    with pytest.raises(ValueError, match="maior ou igual a 1"):
        adicionar_imagem(pdf_base, 0, imagem_png, (50, 50), (100, 100))

    # Posição negativa ou fora dos limites
    with pytest.raises(ValueError, match="não podem ser negativas"):
        adicionar_imagem(pdf_base, 1, imagem_png, (-10, 50), (100, 100))
    with pytest.raises(ValueError, match="fora dos limites"):
        adicionar_imagem(pdf_base, 1, imagem_png, (1000, 1000), (100, 100))

    # Tamanho inválido
    with pytest.raises(ValueError, match="maiores que zero"):
        adicionar_imagem(pdf_base, 1, imagem_png, (50, 50), (-10, 50))
    with pytest.raises(ValueError, match="maior que zero"):
        adicionar_imagem(pdf_base, 1, imagem_png, (50, 50), 0)


def test_adicionar_imagem_pdf_protegido(tmp_path, pdf_base, imagem_png):
    protegido = str(tmp_path / "protegido.pdf")
    proteger_pdf(pdf_base, protegido, "senha123")

    with pytest.raises(ValueError, match="protegido por senha"):
        adicionar_imagem(protegido, 1, imagem_png, (50, 50), (100, 100))
