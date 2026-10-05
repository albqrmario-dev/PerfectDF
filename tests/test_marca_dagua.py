import pymupdf
import pytest

from perfectdf.core import abrir_pdf, adicionar_marca_dagua


def test_adicionar_marca_dagua_todas_as_paginas(tmp_path):
    origem = tmp_path / "origem.pdf"
    saida = tmp_path / "saida.pdf"

    # Cria documento com 3 páginas e texto inicial
    doc = pymupdf.open()
    for i in range(1, 4):
        p = doc.new_page()
        p.insert_text((50, 50), f"Conteúdo da página {i}")
    doc.save(str(origem))
    doc.close()

    res = adicionar_marca_dagua(str(origem), str(saida), "CONFIDENCIAL")
    assert res == str(saida)

    # Verifica se documento original permaneceu intacto
    doc_orig = abrir_pdf(str(origem))
    for p in doc_orig:
        assert "CONFIDENCIAL" not in p.get_text()
    doc_orig.close()

    # Verifica se a marca d'água e o texto original aparecem em todas as páginas do PDF resultante
    doc_saida = abrir_pdf(str(saida))
    assert doc_saida.page_count == 3
    for idx, p in enumerate(doc_saida, start=1):
        txt = p.get_text()
        assert f"Conteúdo da página {idx}" in txt
        assert "CONFIDENCIAL" in txt
    doc_saida.close()


def test_adicionar_marca_dagua_com_acentos(tmp_path):
    origem = tmp_path / "origem.pdf"
    saida = tmp_path / "saida.pdf"

    doc = pymupdf.open()
    p = doc.new_page()
    p.insert_text((50, 50), "Documento Oficial")
    doc.save(str(origem))
    doc.close()

    texto_marca = "Cópia Não Autorizada - Versão 1"
    adicionar_marca_dagua(str(origem), str(saida), texto_marca)

    doc_saida = abrir_pdf(str(saida))
    texto_extraido = doc_saida[0].get_text()
    assert "Cópia Não Autorizada - Versão 1" in texto_extraido
    doc_saida.close()


def test_adicionar_marca_dagua_paginas_selecionadas(tmp_path):
    origem = tmp_path / "origem.pdf"
    saida_lista = tmp_path / "saida_lista.pdf"
    saida_str = tmp_path / "saida_str.pdf"

    doc = pymupdf.open()
    for i in range(1, 5):
        p = doc.new_page()
        p.insert_text((50, 50), f"Página {i}")
    doc.save(str(origem))
    doc.close()

    # Apenas páginas 2 e 3 via lista
    adicionar_marca_dagua(str(origem), str(saida_lista), "RESTRITO", paginas=[2, 3])
    doc_lista = abrir_pdf(str(saida_lista))
    assert "RESTRITO" not in doc_lista[0].get_text()
    assert "RESTRITO" in doc_lista[1].get_text()
    assert "RESTRITO" in doc_lista[2].get_text()
    assert "RESTRITO" not in doc_lista[3].get_text()
    doc_lista.close()

    # Apenas páginas 1 e 4 via string parsear_paginas
    adicionar_marca_dagua(str(origem), str(saida_str), "EXTERNO", paginas="1, 4")
    doc_str = abrir_pdf(str(saida_str))
    assert "EXTERNO" in doc_str[0].get_text()
    assert "EXTERNO" not in doc_str[1].get_text()
    assert "EXTERNO" not in doc_str[2].get_text()
    assert "EXTERNO" in doc_str[3].get_text()
    doc_str.close()


def test_adicionar_marca_dagua_pagina_rotacionada(tmp_path):
    origem = tmp_path / "origem.pdf"
    saida = tmp_path / "saida.pdf"

    doc = pymupdf.open()
    p = doc.new_page(width=400, height=600)
    p.set_rotation(90)
    p.insert_text((50, 50), "Texto Girado")
    doc.save(str(origem))
    doc.close()

    adicionar_marca_dagua(str(origem), str(saida), "DIAGONAL", angulo=45)

    doc_saida = abrir_pdf(str(saida))
    assert doc_saida[0].rotation == 90
    txt = doc_saida[0].get_text()
    assert "Texto Girado" in txt
    assert "DIAGONAL" in txt
    doc_saida.close()


def test_adicionar_marca_dagua_validacoes(tmp_path):
    origem = tmp_path / "origem.pdf"
    saida = tmp_path / "saida.pdf"

    doc = pymupdf.open()
    doc.new_page()
    doc.save(str(origem))
    doc.close()

    # Saída igual à origem
    with pytest.raises(ValueError, match="igual ao arquivo de origem"):
        adicionar_marca_dagua(str(origem), str(origem), "TESTE")

    # Arquivo de origem inexistente
    with pytest.raises(ValueError, match="não foi encontrado"):
        adicionar_marca_dagua(str(tmp_path / "inexistente.pdf"), str(saida), "TESTE")

    # Caminho e saída vazios ou não strings
    with pytest.raises(ValueError, match="string não vazia"):
        adicionar_marca_dagua("", str(saida), "TESTE")
    with pytest.raises(ValueError, match="string não vazia"):
        adicionar_marca_dagua(str(origem), "", "TESTE")

    # Texto vazio
    with pytest.raises(ValueError, match="string não vazia"):
        adicionar_marca_dagua(str(origem), str(saida), "")
    with pytest.raises(ValueError, match="string não vazia"):
        adicionar_marca_dagua(str(origem), str(saida), "   ")

    # Opacidade inválida
    with pytest.raises(ValueError, match="número entre 0 e 1"):
        adicionar_marca_dagua(str(origem), str(saida), "TESTE", opacidade=-0.1)
    with pytest.raises(ValueError, match="número entre 0 e 1"):
        adicionar_marca_dagua(str(origem), str(saida), "TESTE", opacidade=1.1)
    with pytest.raises(ValueError, match="número entre 0 e 1"):
        adicionar_marca_dagua(str(origem), str(saida), "TESTE", opacidade=True)

    # Tamanho de fonte inválido
    with pytest.raises(ValueError, match="maior que zero"):
        adicionar_marca_dagua(str(origem), str(saida), "TESTE", tamanho_fonte=0)
    with pytest.raises(ValueError, match="maior que zero"):
        adicionar_marca_dagua(str(origem), str(saida), "TESTE", tamanho_fonte=-10)
    with pytest.raises(ValueError, match="maior que zero"):
        adicionar_marca_dagua(str(origem), str(saida), "TESTE", tamanho_fonte=True)

    # Ângulo inválido
    with pytest.raises(ValueError, match="deve ser um número"):
        adicionar_marca_dagua(str(origem), str(saida), "TESTE", angulo="45")
    with pytest.raises(ValueError, match="deve ser um número"):
        adicionar_marca_dagua(str(origem), str(saida), "TESTE", angulo=True)

    # Especificação de páginas inválida
    with pytest.raises(ValueError, match="deve ser None, uma string"):
        adicionar_marca_dagua(str(origem), str(saida), "TESTE", paginas=123)

    # Lista de páginas vazia
    with pytest.raises(ValueError, match="não pode estar vazia"):
        adicionar_marca_dagua(str(origem), str(saida), "TESTE", paginas=[])

    # Página inválida (fora do limite ou booleano)
    with pytest.raises(ValueError, match="Página inválida"):
        adicionar_marca_dagua(str(origem), str(saida), "TESTE", paginas=[0])
    with pytest.raises(ValueError, match="Página inválida"):
        adicionar_marca_dagua(str(origem), str(saida), "TESTE", paginas=[2])
    with pytest.raises(ValueError, match="Página inválida"):
        adicionar_marca_dagua(str(origem), str(saida), "TESTE", paginas=[True])
