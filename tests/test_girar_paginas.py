import pymupdf
import pytest

from perfectdf.core import abrir_pdf, girar_paginas


def test_girar_paginas_sucesso(tmp_path):
    origem = tmp_path / "origem.pdf"
    saida = tmp_path / "saida.pdf"

    # Cria PDF com 3 páginas
    doc = pymupdf.open()
    for i in range(1, 4):
        page = doc.new_page()
        page.insert_text((50, 50), f"Página {i}")
    doc.save(str(origem))
    doc.close()

    # Gira página 2 em 90 graus
    res = girar_paginas(str(origem), [2], 90, str(saida))
    assert res == str(saida)

    # Verifica se documento original não foi alterado
    doc_orig = abrir_pdf(str(origem))
    for p in doc_orig:
        assert p.rotation == 0
    doc_orig.close()

    # Verifica se documento de saída tem a página 2 girada e as outras não
    doc_saida = abrir_pdf(str(saida))
    assert doc_saida[0].rotation == 0
    assert doc_saida[1].rotation == 90
    assert doc_saida[2].rotation == 0
    doc_saida.close()


def test_girar_paginas_acumulada_e_negativa(tmp_path):
    origem = tmp_path / "origem.pdf"
    saida1 = tmp_path / "saida1.pdf"
    saida2 = tmp_path / "saida2.pdf"

    doc = pymupdf.open()
    page = doc.new_page()
    page.set_rotation(90)
    doc.save(str(origem))
    doc.close()

    # Página já tinha 90, somando 180 vira 270
    girar_paginas(str(origem), [1], 180, str(saida1))
    doc1 = abrir_pdf(str(saida1))
    assert doc1[0].rotation == 270
    doc1.close()

    # Página já tinha 90, somando -90 vira 0
    girar_paginas(str(origem), [1], -90, str(saida2))
    doc2 = abrir_pdf(str(saida2))
    assert doc2[0].rotation == 0
    doc2.close()


def test_girar_paginas_validacoes(tmp_path):
    origem = tmp_path / "origem.pdf"
    saida = tmp_path / "saida.pdf"

    doc = pymupdf.open()
    doc.new_page()
    doc.save(str(origem))
    doc.close()

    # Saída igual à origem
    with pytest.raises(ValueError, match="igual ao arquivo de origem"):
        girar_paginas(str(origem), [1], 90, str(origem))

    # Origem inexistente
    with pytest.raises(ValueError, match="não foi encontrado"):
        girar_paginas(str(tmp_path / "inexistente.pdf"), [1], 90, str(saida))

    # Graus não inteiro ou booleano
    with pytest.raises(ValueError, match="número inteiro"):
        girar_paginas(str(origem), [1], True, str(saida))
    with pytest.raises(ValueError, match="número inteiro"):
        girar_paginas(str(origem), [1], "90", str(saida))

    # Graus não múltiplo de 90
    with pytest.raises(ValueError, match="múltiplo de 90 graus"):
        girar_paginas(str(origem), [1], 45, str(saida))

    # Lista de páginas vazia
    with pytest.raises(ValueError, match="não pode estar vazia"):
        girar_paginas(str(origem), [], 90, str(saida))

    # Página inválida (fora do limite ou booleano)
    with pytest.raises(ValueError, match="Página inválida"):
        girar_paginas(str(origem), [0], 90, str(saida))
    with pytest.raises(ValueError, match="Página inválida"):
        girar_paginas(str(origem), [2], 90, str(saida))
    with pytest.raises(ValueError, match="Página inválida"):
        girar_paginas(str(origem), [True], 90, str(saida))
