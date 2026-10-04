import pymupdf
import pytest

from perfectdf.core import abrir_pdf, extrair_paginas, juntar_pdfs, parsear_paginas


def test_parsear_paginas():
    assert parsear_paginas("1-3, 5, 9-7") == [1, 2, 3, 5, 7, 8, 9]
    assert parsear_paginas("4") == [4]
    assert parsear_paginas("  10 - 8 , 2  ") == [2, 8, 9, 10]

    with pytest.raises(ValueError):
        parsear_paginas("")
    with pytest.raises(ValueError):
        parsear_paginas(123)
    with pytest.raises(ValueError):
        parsear_paginas("1-abc")
    with pytest.raises(ValueError):
        parsear_paginas("1-2-3")
    with pytest.raises(ValueError):
        parsear_paginas("0")


def test_extrair_paginas(tmp_path):
    origem = tmp_path / "origem.pdf"
    saida = tmp_path / "saida.pdf"

    doc = pymupdf.open()
    for i in range(1, 6):
        page = doc.new_page()
        page.insert_text((50, 50), f"Pagina {i}")
    doc.save(str(origem))
    doc.close()

    resultado = extrair_paginas(str(origem), [2, 4], str(saida))
    assert resultado == str(saida)

    doc_extraido = abrir_pdf(resultado)
    assert doc_extraido.page_count == 2
    assert "Pagina 2" in doc_extraido[0].get_text()
    assert "Pagina 4" in doc_extraido[1].get_text()
    doc_extraido.close()

    with pytest.raises(ValueError):
        extrair_paginas(str(origem), [], str(saida))
    with pytest.raises(ValueError):
        extrair_paginas(str(origem), [99], str(saida))
    with pytest.raises(ValueError):
        extrair_paginas(str(origem), [True], str(saida))


def test_juntar_pdfs(tmp_path):
    p1 = tmp_path / "doc1.pdf"
    p2 = tmp_path / "doc2.pdf"
    saida = tmp_path / "junto.pdf"

    for p, txt in [(p1, "Doc 1"), (p2, "Doc 2")]:
        doc = pymupdf.open()
        page = doc.new_page()
        page.insert_text((50, 50), txt)
        doc.save(str(p))
        doc.close()

    resultado = juntar_pdfs([str(p1), str(p2)], str(saida))
    assert resultado == str(saida)

    doc_junto = abrir_pdf(resultado)
    assert doc_junto.page_count == 2
    assert "Doc 1" in doc_junto[0].get_text()
    assert "Doc 2" in doc_junto[1].get_text()
    doc_junto.close()
