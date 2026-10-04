import pymupdf
import pytest

from perfectdf.core import editar_metadados, ler_metadados


def test_ler_e_editar_metadados_sucesso(tmp_path):
    origem = tmp_path / "origem.pdf"
    saida = tmp_path / "saida.pdf"

    # Cria PDF inicial com metadados
    doc = pymupdf.open()
    doc.new_page()
    doc.set_metadata(
        {
            "title": "Título Original",
            "author": "Autor Original",
            "subject": "Assunto Original",
            "keywords": "original, pdf",
        }
    )
    doc.save(str(origem))
    doc.close()

    # Leitura dos metadados
    meta_inicial = ler_metadados(str(origem))
    assert meta_inicial["title"] == "Título Original"
    assert meta_inicial["author"] == "Autor Original"
    assert meta_inicial["subject"] == "Assunto Original"
    assert meta_inicial["keywords"] == "original, pdf"

    # Edição parcial dos metadados
    novos = {"title": "Novo Título", "keywords": "atualizado, teste"}
    res = editar_metadados(str(origem), novos, str(saida))
    assert res == str(saida)

    # Verifica se o arquivo original permaneceu intacto
    meta_orig_depois = ler_metadados(str(origem))
    assert meta_orig_depois["title"] == "Título Original"

    # Verifica se os metadados no arquivo de saída foram atualizados e os não alterados foram preservados
    meta_saida = ler_metadados(str(saida))
    assert meta_saida["title"] == "Novo Título"
    assert meta_saida["author"] == "Autor Original"
    assert meta_saida["keywords"] == "atualizado, teste"


def test_editar_metadados_rejeicao_chaves_desconhecidas(tmp_path):
    origem = tmp_path / "origem.pdf"
    saida = tmp_path / "saida.pdf"

    doc = pymupdf.open()
    doc.new_page()
    doc.save(str(origem))
    doc.close()

    # Chave desconhecida / erro de digitação
    with pytest.raises(ValueError, match="não permitida"):
        editar_metadados(str(origem), {"autor": "Mario"}, str(saida))

    # Chave de sistema (ex: creator, producer) que não está na lista permitida
    with pytest.raises(ValueError, match="não permitida"):
        editar_metadados(str(origem), {"creator": "MeuApp"}, str(saida))


def test_editar_metadados_validacoes(tmp_path):
    origem = tmp_path / "origem.pdf"
    saida = tmp_path / "saida.pdf"

    doc = pymupdf.open()
    doc.new_page()
    doc.save(str(origem))
    doc.close()

    # Saída igual à origem
    with pytest.raises(ValueError, match="igual ao arquivo de origem"):
        editar_metadados(str(origem), {"title": "Novo"}, str(origem))

    # Origem inexistente
    with pytest.raises(ValueError, match="não foi encontrado"):
        editar_metadados(
            str(tmp_path / "inexistente.pdf"), {"title": "Novo"}, str(saida)
        )

    # novos não é dicionário
    with pytest.raises(ValueError, match="devem ser fornecidos em um dicionário"):
        editar_metadados(str(origem), "title=Novo", str(saida))

    # Valor do metadado não é string
    with pytest.raises(ValueError, match="deve ser uma string"):
        editar_metadados(str(origem), {"title": 123}, str(saida))
    with pytest.raises(ValueError, match="deve ser uma string"):
        editar_metadados(str(origem), {"title": True}, str(saida))


def test_ler_metadados_validacoes(tmp_path):
    with pytest.raises(ValueError, match="string não vazia"):
        ler_metadados("")
    with pytest.raises(ValueError, match="não foi encontrado"):
        ler_metadados(str(tmp_path / "inexistente.pdf"))
