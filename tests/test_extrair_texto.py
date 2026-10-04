import pymupdf
import pytest

from perfectdf.core import extrair_texto


def test_extrair_texto_todas_as_paginas(tmp_path):
    caminho = tmp_path / "documento.pdf"

    doc = pymupdf.open()
    for i in range(1, 4):
        p = doc.new_page()
        p.insert_text((50, 50), f"Texto da página {i}")
    doc.save(str(caminho))
    doc.close()

    # Extrai todas as páginas (paginas=None)
    resultado = extrair_texto(str(caminho))
    assert "--- Página 1 ---" in resultado
    assert "Texto da página 1" in resultado
    assert "--- Página 2 ---" in resultado
    assert "Texto da página 2" in resultado
    assert "--- Página 3 ---" in resultado
    assert "Texto da página 3" in resultado


def test_extrair_texto_paginas_selecionadas(tmp_path):
    caminho = tmp_path / "documento.pdf"

    doc = pymupdf.open()
    for i in range(1, 5):
        p = doc.new_page()
        p.insert_text((50, 50), f"Conteúdo {i}")
    doc.save(str(caminho))
    doc.close()

    # Com lista de páginas
    resultado_lista = extrair_texto(str(caminho), [2, 4])
    assert "--- Página 2 ---" in resultado_lista
    assert "Conteúdo 2" in resultado_lista
    assert "--- Página 4 ---" in resultado_lista
    assert "Conteúdo 4" in resultado_lista
    assert "--- Página 1 ---" not in resultado_lista

    # Com string no formato parsear_paginas
    resultado_str = extrair_texto(str(caminho), "1, 3")
    assert "--- Página 1 ---" in resultado_str
    assert "Conteúdo 1" in resultado_str
    assert "--- Página 3 ---" in resultado_str
    assert "Conteúdo 3" in resultado_str
    assert "--- Página 2 ---" not in resultado_str


def test_extrair_texto_aviso_escaneado(tmp_path):
    caminho = tmp_path / "escaneado.pdf"

    # Cria PDF sem texto selecionável (página em branco, como scan)
    doc = pymupdf.open()
    doc.new_page()
    doc.save(str(caminho))
    doc.close()

    # Deve disparar UserWarning sem quebrar/lançar exceção
    with pytest.warns(UserWarning, match="parece ser escaneado"):
        texto = extrair_texto(str(caminho))
    assert "--- Página 1 ---" in texto


def test_extrair_texto_validacoes(tmp_path):
    caminho = tmp_path / "doc.pdf"

    doc = pymupdf.open()
    doc.new_page()
    doc.save(str(caminho))
    doc.close()

    with pytest.raises(ValueError, match="não foi encontrado"):
        extrair_texto(str(tmp_path / "inexistente.pdf"))

    with pytest.raises(ValueError, match="string não vazia"):
        extrair_texto("")

    with pytest.raises(ValueError, match="deve ser None, uma string"):
        extrair_texto(str(caminho), paginas=123)

    with pytest.raises(ValueError, match="Página inválida"):
        extrair_texto(str(caminho), [99])

    with pytest.raises(ValueError, match="Página inválida"):
        extrair_texto(str(caminho), [True])
