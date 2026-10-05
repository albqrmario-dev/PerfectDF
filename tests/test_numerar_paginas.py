import pymupdf
import pytest

from perfectdf.core import abrir_pdf, numerar_paginas


def test_numerar_paginas_padrao(tmp_path):
    origem = tmp_path / "origem.pdf"
    saida = tmp_path / "saida.pdf"

    # Cria documento com 3 páginas
    doc = pymupdf.open()
    for i in range(1, 4):
        p = doc.new_page()
        p.insert_text((50, 50), f"Texto base {i}")
    doc.save(str(origem))
    doc.close()

    res = numerar_paginas(str(origem), str(saida))
    assert res == str(saida)

    # Documento de origem intacto
    doc_orig = abrir_pdf(str(origem))
    for p in doc_orig:
        assert "Página" not in p.get_text()
    doc_orig.close()

    # Documento de saída possui numeração sequencial correta
    doc_saida = abrir_pdf(str(saida))
    assert doc_saida.page_count == 3
    assert "Página 1 de 3" in doc_saida[0].get_text()
    assert "Página 2 de 3" in doc_saida[1].get_text()
    assert "Página 3 de 3" in doc_saida[2].get_text()
    doc_saida.close()


def test_numerar_paginas_formato_e_inicio_customizados(tmp_path):
    origem = tmp_path / "origem.pdf"
    saida = tmp_path / "saida.pdf"

    doc = pymupdf.open()
    for _ in range(2):
        doc.new_page()
    doc.save(str(origem))
    doc.close()

    numerar_paginas(
        str(origem),
        str(saida),
        formato="{n}/{total}",
        inicio=10,
    )

    doc_saida = abrir_pdf(str(saida))
    assert "10/2" in doc_saida[0].get_text()
    assert "11/2" in doc_saida[1].get_text()
    doc_saida.close()


def test_numerar_paginas_selecionadas(tmp_path):
    origem = tmp_path / "origem.pdf"
    saida_lista = tmp_path / "saida_lista.pdf"
    saida_str = tmp_path / "saida_str.pdf"

    # Documento com 5 páginas
    doc = pymupdf.open()
    for i in range(1, 6):
        p = doc.new_page()
        p.insert_text((50, 50), f"Página original {i}")
    doc.save(str(origem))
    doc.close()

    # Numerando páginas 2 e 4 (total selecionadas = 2) via lista
    numerar_paginas(str(origem), str(saida_lista), paginas=[2, 4])
    doc_l = abrir_pdf(str(saida_lista))
    assert "Página 1 de 2" not in doc_l[0].get_text()  # Pág 1 sem numeração
    assert "Página 1 de 2" in doc_l[1].get_text()      # Pág 2 tem 1 de 2
    assert "de 2" not in doc_l[2].get_text()           # Pág 3 sem numeração
    assert "Página 2 de 2" in doc_l[3].get_text()      # Pág 4 tem 2 de 2
    assert "de 2" not in doc_l[4].get_text()           # Pág 5 sem numeração
    doc_l.close()

    # Numerando páginas 1, 3 e 5 via string (total selecionadas = 3)
    numerar_paginas(str(origem), str(saida_str), paginas="1, 3, 5")
    doc_s = abrir_pdf(str(saida_str))
    assert "Página 1 de 3" in doc_s[0].get_text()
    assert "de 3" not in doc_s[1].get_text()
    assert "Página 2 de 3" in doc_s[2].get_text()
    assert "de 3" not in doc_s[3].get_text()
    assert "Página 3 de 3" in doc_s[4].get_text()
    doc_s.close()


def test_numerar_paginas_todas_as_posicoes(tmp_path):
    origem = tmp_path / "origem.pdf"

    doc = pymupdf.open()
    doc.new_page()
    doc.save(str(origem))
    doc.close()

    posicoes = [
        "rodape-centro",
        "rodape-direita",
        "rodape-esquerda",
        "topo-centro",
        "topo-direita",
        "topo-esquerda",
    ]

    for pos in posicoes:
        saida = tmp_path / f"saida_{pos}.pdf"
        numerar_paginas(str(origem), str(saida), posicao=pos)
        doc_s = abrir_pdf(str(saida))
        assert "Página 1 de 1" in doc_s[0].get_text()
        doc_s.close()


def test_numerar_paginas_pagina_rotacionada(tmp_path):
    origem = tmp_path / "origem.pdf"
    saida = tmp_path / "saida.pdf"

    doc = pymupdf.open()
    p = doc.new_page(width=400, height=600)
    p.set_rotation(90)
    p.insert_text((50, 50), "Texto Rotacionado")
    doc.save(str(origem))
    doc.close()

    numerar_paginas(str(origem), str(saida))

    doc_saida = abrir_pdf(str(saida))
    assert doc_saida[0].rotation == 90
    txt = doc_saida[0].get_text()
    assert "Texto Rotacionado" in txt
    assert "Página 1 de 1" in txt
    doc_saida.close()


def test_numerar_paginas_validacoes(tmp_path):
    origem = tmp_path / "origem.pdf"
    saida = tmp_path / "saida.pdf"

    doc = pymupdf.open()
    doc.new_page()
    doc.save(str(origem))
    doc.close()

    # Saída igual à origem
    with pytest.raises(ValueError, match="igual ao arquivo de origem"):
        numerar_paginas(str(origem), str(origem))

    # Arquivo não encontrado
    with pytest.raises(ValueError, match="não foi encontrado"):
        numerar_paginas(str(tmp_path / "inexistente.pdf"), str(saida))

    # Caminho e saída vazios
    with pytest.raises(ValueError, match="string não vazia"):
        numerar_paginas("", str(saida))
    with pytest.raises(ValueError, match="string não vazia"):
        numerar_paginas(str(origem), "")

    # Placeholders desconhecidos no formato (deve lançar ValueError, não KeyError)
    with pytest.raises(ValueError, match="Placeholder desconhecido"):
        numerar_paginas(str(origem), str(saida), formato="Página {pagina}")
    with pytest.raises(ValueError, match="Placeholder desconhecido"):
        numerar_paginas(str(origem), str(saida), formato="{n} de {x}")

    # Formato malformado
    with pytest.raises(ValueError, match="malformado"):
        numerar_paginas(str(origem), str(saida), formato="Página {n")

    # Formato vazio
    with pytest.raises(ValueError, match="string não vazia"):
        numerar_paginas(str(origem), str(saida), formato="")

    # Posição inválida
    with pytest.raises(ValueError, match="Posição inválida"):
        numerar_paginas(str(origem), str(saida), posicao="centro")
    with pytest.raises(ValueError, match="Posição inválida"):
        numerar_paginas(str(origem), str(saida), posicao="inferior")

    # Início inválido (não inteiro ou booleano)
    with pytest.raises(ValueError, match="número inteiro"):
        numerar_paginas(str(origem), str(saida), inicio=True)
    with pytest.raises(ValueError, match="número inteiro"):
        numerar_paginas(str(origem), str(saida), inicio="1")

    # Tamanho de fonte inválido
    with pytest.raises(ValueError, match="maior que zero"):
        numerar_paginas(str(origem), str(saida), tamanho_fonte=0)
    with pytest.raises(ValueError, match="maior que zero"):
        numerar_paginas(str(origem), str(saida), tamanho_fonte=-5)
    with pytest.raises(ValueError, match="maior que zero"):
        numerar_paginas(str(origem), str(saida), tamanho_fonte=True)

    # Páginas inválidas
    with pytest.raises(ValueError, match="não pode estar vazia"):
        numerar_paginas(str(origem), str(saida), paginas=[])
    with pytest.raises(ValueError, match="Página inválida"):
        numerar_paginas(str(origem), str(saida), paginas=[0])
    with pytest.raises(ValueError, match="Página inválida"):
        numerar_paginas(str(origem), str(saida), paginas=[2])
    with pytest.raises(ValueError, match="Página inválida"):
        numerar_paginas(str(origem), str(saida), paginas=[True])
