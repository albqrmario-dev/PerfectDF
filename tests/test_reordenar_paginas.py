import pymupdf
import pytest

from perfectdf.core import abrir_pdf, parsear_ordem, reordenar_paginas


def test_parsear_ordem():
    # Ordem preservada
    assert parsear_ordem("3,1,2") == [3, 1, 2]
    assert parsear_ordem("3, 1-2") == [3, 1, 2]
    assert parsear_ordem("3-1") == [3, 2, 1]
    assert parsear_ordem("1, 2, 1") == [1, 2, 1]

    # Validações de erro
    with pytest.raises(ValueError, match="deve ser uma string"):
        parsear_ordem(123)
    with pytest.raises(ValueError, match="não pode estar vazia"):
        parsear_ordem("")
    with pytest.raises(ValueError, match="Trecho vazio"):
        parsear_ordem("1,,2")
    with pytest.raises(ValueError, match="Intervalo malformado"):
        parsear_ordem("1-2-3")
    with pytest.raises(ValueError, match="valores não numéricos"):
        parsear_ordem("1-abc")
    with pytest.raises(ValueError, match="maiores ou iguais a 1"):
        parsear_ordem("0-2")
    with pytest.raises(ValueError, match="maior ou igual a 1"):
        parsear_ordem("0")


def test_reordenar_paginas_sucesso(tmp_path):
    origem = tmp_path / "origem.pdf"
    saida1 = tmp_path / "reordenado1.pdf"
    saida2 = tmp_path / "reordenado2.pdf"
    saida3 = tmp_path / "reordenado3.pdf"

    # Cria documento com 4 páginas
    doc = pymupdf.open()
    for i in range(1, 5):
        page = doc.new_page()
        page.insert_text((50, 50), f"Página {i}")
    doc.save(str(origem))
    doc.close()

    # Reordena com string "3, 1, 2"
    res1 = reordenar_paginas(str(origem), "3, 1, 2", str(saida1))
    assert res1 == str(saida1)

    doc1 = abrir_pdf(str(saida1))
    assert doc1.page_count == 3
    assert "Página 3" in doc1[0].get_text()
    assert "Página 1" in doc1[1].get_text()
    assert "Página 2" in doc1[2].get_text()
    doc1.close()

    # Reordena com intervalo "3-1"
    reordenar_paginas(str(origem), "3-1", str(saida2))
    doc2 = abrir_pdf(str(saida2))
    assert doc2.page_count == 3
    assert "Página 3" in doc2[0].get_text()
    assert "Página 2" in doc2[1].get_text()
    assert "Página 1" in doc2[2].get_text()
    doc2.close()

    # Reordena passando lista de inteiros diretamente
    reordenar_paginas(str(origem), [4, 1], str(saida3))
    doc3 = abrir_pdf(str(saida3))
    assert doc3.page_count == 2
    assert "Página 4" in doc3[0].get_text()
    assert "Página 1" in doc3[1].get_text()
    doc3.close()

    # Original permanece intacto
    doc_orig = abrir_pdf(str(origem))
    assert doc_orig.page_count == 4
    doc_orig.close()


def test_reordenar_paginas_validacoes(tmp_path):
    origem = tmp_path / "origem.pdf"
    saida = tmp_path / "saida.pdf"

    doc = pymupdf.open()
    for i in range(3):
        doc.new_page()
    doc.save(str(origem))
    doc.close()

    # Saída igual à origem
    with pytest.raises(ValueError, match="igual ao arquivo de origem"):
        reordenar_paginas(str(origem), "2, 1", str(origem))

    # Origem inexistente
    with pytest.raises(ValueError, match="não foi encontrado"):
        reordenar_paginas(str(tmp_path / "inexistente.pdf"), "2, 1", str(saida))

    # Tipo de ordem inválido
    with pytest.raises(ValueError, match="deve ser uma string ou lista"):
        reordenar_paginas(str(origem), 123, str(saida))

    # Ordem vazia
    with pytest.raises(ValueError, match="não pode estar vazia"):
        reordenar_paginas(str(origem), "", str(saida))
    with pytest.raises(ValueError, match="não pode estar vazia"):
        reordenar_paginas(str(origem), [], str(saida))

    # Página inexistente ou booleano
    with pytest.raises(ValueError, match="Página inválida"):
        reordenar_paginas(str(origem), "99", str(saida))
    with pytest.raises(ValueError, match="Página inválida"):
        reordenar_paginas(str(origem), [True], str(saida))
