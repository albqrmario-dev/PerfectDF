import os
import pymupdf
import pytest

from perfectdf.core import abrir_pdf, imagens_para_pdf, pdf_para_imagens


def test_pdf_para_imagens_todas_as_paginas_png(tmp_path):
    origem = tmp_path / "origem.pdf"
    pasta_saida = tmp_path / "imagens_geradas"  # Pasta ainda não existe

    # Cria documento com 3 páginas
    doc = pymupdf.open()
    for i in range(1, 4):
        p = doc.new_page(width=300, height=400)
        p.insert_text((50, 50), f"Página {i}")
    doc.save(str(origem))
    doc.close()

    caminhos = pdf_para_imagens(str(origem), str(pasta_saida), dpi=150, formato="png")

    assert os.path.isdir(str(pasta_saida))
    assert len(caminhos) == 3
    assert caminhos[0].endswith("pagina_001.png")
    assert caminhos[1].endswith("pagina_002.png")
    assert caminhos[2].endswith("pagina_003.png")

    for c in caminhos:
        assert os.path.isfile(c)
        pix = pymupdf.Pixmap(c)
        assert pix.width > 0
        assert pix.height > 0


def test_pdf_para_imagens_jpg_e_paginas_selecionadas(tmp_path):
    origem = tmp_path / "origem.pdf"
    pasta_saida = tmp_path / "saida_jpg"

    doc = pymupdf.open()
    for i in range(1, 6):
        doc.new_page()
    doc.save(str(origem))
    doc.close()

    caminhos = pdf_para_imagens(
        str(origem), str(pasta_saida), paginas=[2, 4], dpi=200, formato="jpg"
    )

    assert len(caminhos) == 2
    assert caminhos[0].endswith("pagina_002.jpg")
    assert caminhos[1].endswith("pagina_004.jpg")
    assert not os.path.exists(os.path.join(str(pasta_saida), "pagina_001.jpg"))


def test_imagens_para_pdf_sucesso(tmp_path):
    img1 = tmp_path / "img1.png"
    img2 = tmp_path / "img2.jpg"
    saida = tmp_path / "documento_imagens.pdf"

    # Cria duas imagens com dimensões conhecidas
    p1 = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 250, 350), 0)
    p1.save(str(img1))
    p2 = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 500, 200), 0)
    p2.save(str(img2))

    res = imagens_para_pdf([str(img1), str(img2)], str(saida))
    assert res == str(saida)

    doc = abrir_pdf(str(saida))
    assert doc.page_count == 2
    # Confere que a página foi gerada exatamente no tamanho da imagem
    assert doc[0].rect.width == 250
    assert doc[0].rect.height == 350
    assert len(doc[0].get_images()) == 1

    assert doc[1].rect.width == 500
    assert doc[1].rect.height == 200
    assert len(doc[1].get_images()) == 1
    doc.close()


def test_roundtrip_pdf_imagens_pdf(tmp_path):
    origem = tmp_path / "original.pdf"
    pasta_imgs = tmp_path / "imgs_roundtrip"
    reconstruido = tmp_path / "reconstruido.pdf"

    doc = pymupdf.open()
    p = doc.new_page(width=300, height=400)
    p.insert_text((50, 50), "Teste Roundtrip")
    doc.save(str(origem))
    doc.close()

    imgs = pdf_para_imagens(str(origem), str(pasta_imgs), dpi=72, formato="png")
    imagens_para_pdf(imgs, str(reconstruido))

    doc_rec = abrir_pdf(str(reconstruido))
    assert doc_rec.page_count == 1
    assert len(doc_rec[0].get_images()) == 1
    doc_rec.close()


def test_pdf_para_imagens_validacoes(tmp_path):
    origem = tmp_path / "origem.pdf"
    pasta = tmp_path / "pasta"

    doc = pymupdf.open()
    doc.new_page()
    doc.save(str(origem))
    doc.close()

    # Origem inexistente
    with pytest.raises(ValueError, match="não foi encontrado"):
        pdf_para_imagens(str(tmp_path / "inexistente.pdf"), str(pasta))

    # Caminho e pasta vazios
    with pytest.raises(ValueError, match="string não vazia"):
        pdf_para_imagens("", str(pasta))
    with pytest.raises(ValueError, match="string não vazia"):
        pdf_para_imagens(str(origem), "")

    # Pasta de saída igual ao arquivo de origem
    with pytest.raises(ValueError, match="não pode ser igual"):
        pdf_para_imagens(str(origem), str(origem))

    # Pasta de saída sendo arquivo existente
    arquivo_bloqueio = tmp_path / "arquivo_existente.txt"
    arquivo_bloqueio.write_text("bloqueio")
    with pytest.raises(ValueError, match="é um arquivo existente"):
        pdf_para_imagens(str(origem), str(arquivo_bloqueio))

    # DPI fora dos limites ou booleano
    with pytest.raises(ValueError, match="entre 36 e 600"):
        pdf_para_imagens(str(origem), str(pasta), dpi=20)
    with pytest.raises(ValueError, match="entre 36 e 600"):
        pdf_para_imagens(str(origem), str(pasta), dpi=700)
    with pytest.raises(ValueError, match="entre 36 e 600"):
        pdf_para_imagens(str(origem), str(pasta), dpi=True)

    # Formato inválido
    with pytest.raises(ValueError, match="Formato de imagem inválido"):
        pdf_para_imagens(str(origem), str(pasta), formato="gif")

    # Páginas inválidas
    with pytest.raises(ValueError, match="não pode estar vazia"):
        pdf_para_imagens(str(origem), str(pasta), paginas=[])
    with pytest.raises(ValueError, match="Página inválida"):
        pdf_para_imagens(str(origem), str(pasta), paginas=[2])


def test_imagens_para_pdf_validacoes(tmp_path):
    saida = tmp_path / "saida.pdf"
    img_valida = tmp_path / "valida.png"
    p = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 50, 50), 0)
    p.save(str(img_valida))

    # Lista vazia
    with pytest.raises(ValueError, match="não pode estar vazia"):
        imagens_para_pdf([], str(saida))

    # Não lista/tupla
    with pytest.raises(ValueError, match="lista ou tupla"):
        imagens_para_pdf("uma_imagem.png", str(saida))

    # Saída vazia
    with pytest.raises(ValueError, match="string não vazia"):
        imagens_para_pdf([str(img_valida)], "")

    # Imagem inexistente
    with pytest.raises(ValueError, match="não foi encontrado"):
        imagens_para_pdf([str(tmp_path / "inexistente.png")], str(saida))

    # Imagem corrompida / não imagem
    arquivo_corrompido = tmp_path / "falsa_imagem.png"
    arquivo_corrompido.write_text("este texto não é uma imagem")
    with pytest.raises(ValueError, match="não é uma imagem válida"):
        imagens_para_pdf([str(arquivo_corrompido)], str(saida))

    # Saída igual a uma das imagens
    with pytest.raises(ValueError, match="não pode ser igual"):
        imagens_para_pdf([str(img_valida)], str(img_valida))
