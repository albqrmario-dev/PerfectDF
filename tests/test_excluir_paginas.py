import pymupdf
import pytest

from perfectdf.core import abrir_pdf, excluir_paginas


def test_excluir_paginas_sucesso(tmp_path):
    origem = tmp_path / "origem.pdf"
    saida = tmp_path / "saida.pdf"

    # Cria documento com 4 páginas
    doc = pymupdf.open()
    for i in range(1, 5):
        page = doc.new_page()
        page.insert_text((50, 50), f"Página {i}")
    doc.save(str(origem))
    doc.close()

    # Exclui páginas 1 e 3 (restam 2 e 4)
    res = excluir_paginas(str(origem), [1, 3], str(saida))
    assert res == str(saida)

    # Documento original permanece intacto
    doc_orig = abrir_pdf(str(origem))
    assert doc_orig.page_count == 4
    doc_orig.close()

    # Documento de saída possui 2 páginas com os textos esperados
    doc_saida = abrir_pdf(str(saida))
    assert doc_saida.page_count == 2
    assert "Página 2" in doc_saida[0].get_text()
    assert "Página 4" in doc_saida[1].get_text()
    doc_saida.close()


def test_excluir_paginas_validacoes(tmp_path):
    origem = tmp_path / "origem.pdf"
    saida = tmp_path / "saida.pdf"

    doc = pymupdf.open()
    for i in range(3):
        doc.new_page()
    doc.save(str(origem))
    doc.close()

    # Saída igual à origem
    with pytest.raises(ValueError, match="igual ao arquivo de origem"):
        excluir_paginas(str(origem), [1], str(origem))

    # Origem inexistente
    with pytest.raises(ValueError, match="não foi encontrado"):
        excluir_paginas(str(tmp_path / "inexistente.pdf"), [1], str(saida))

    # Lista vazia
    with pytest.raises(ValueError, match="não pode estar vazia"):
        excluir_paginas(str(origem), [], str(saida))

    # Página inválida (zero, booleano, ou maior que total)
    with pytest.raises(ValueError, match="Página inválida"):
        excluir_paginas(str(origem), [0], str(saida))
    with pytest.raises(ValueError, match="Página inválida"):
        excluir_paginas(str(origem), [4], str(saida))
    with pytest.raises(ValueError, match="Página inválida"):
        excluir_paginas(str(origem), [True], str(saida))

    # Exclusão de todas as páginas (deixando PDF com 0 páginas)
    with pytest.raises(ValueError, match="0 páginas"):
        excluir_paginas(str(origem), [1, 2, 3], str(saida))

    # Exclusão com duplicatas que somam todas as páginas
    with pytest.raises(ValueError, match="0 páginas"):
        excluir_paginas(str(origem), [1, 2, 2, 3], str(saida))
