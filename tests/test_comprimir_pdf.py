import os
import pymupdf
import pytest

from perfectdf.core import abrir_pdf, comprimir_pdf


def test_comprimir_pdf_nivel_baixo(tmp_path):
    origem = tmp_path / "origem.pdf"
    saida = tmp_path / "saida_baixo.pdf"

    # Cria documento com conteúdo repetitivo e sem compressão inicial
    doc = pymupdf.open()
    for i in range(1, 10):
        p = doc.new_page()
        p.insert_text((50, 50), f"Página de teste número {i} com texto repetido " * 5)
    # Salva sem deflate para permitir compressão posterior
    doc.save(str(origem), deflate=False)
    doc.close()

    res = comprimir_pdf(str(origem), str(saida), nivel="baixo")
    assert "tamanho_original" in res
    assert "tamanho_final" in res
    assert "economia_percentual" in res
    assert res["tamanho_original"] == os.path.getsize(str(origem))
    assert res["tamanho_final"] == os.path.getsize(str(saida))
    assert res["tamanho_final"] < res["tamanho_original"]
    assert res["economia_percentual"] > 0

    # Verifica se PDF comprimido é válido e legível
    doc_comprimido = abrir_pdf(str(saida))
    assert doc_comprimido.page_count == 9
    assert "Página de teste número 1" in doc_comprimido[0].get_text()
    doc_comprimido.close()


def test_comprimir_pdf_nivel_medio(tmp_path):
    origem = tmp_path / "origem.pdf"
    saida = tmp_path / "saida_medio.pdf"

    doc = pymupdf.open()
    for i in range(1, 15):
        p = doc.new_page()
        p.insert_text((50, 50), f"Conteúdo da página {i} " * 20)
    doc.save(str(origem), deflate=False)
    doc.close()

    res = comprimir_pdf(str(origem), str(saida), nivel="medio")
    assert res["tamanho_final"] < res["tamanho_original"]
    assert res["economia_percentual"] > 0

    doc_comprimido = abrir_pdf(str(saida))
    assert doc_comprimido.page_count == 14
    doc_comprimido.close()


def test_comprimir_pdf_nivel_alto_com_imagem(tmp_path):
    origem = tmp_path / "origem_img.pdf"
    saida = tmp_path / "saida_img.pdf"

    # Cria documento com imagem RGB sem compressão
    doc = pymupdf.open()
    page = doc.new_page(width=400, height=400)
    pix = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 300, 300), 0)
    page.insert_image(page.rect, pixmap=pix)
    doc.save(str(origem), deflate=False)
    doc.close()

    res = comprimir_pdf(str(origem), str(saida), nivel="alto")
    assert res["tamanho_final"] < res["tamanho_original"]
    assert res["economia_percentual"] > 50  # Recompressão em JPEG deve economizar muito

    # PDF de saída continua íntegro
    doc_comprimido = abrir_pdf(str(saida))
    assert doc_comprimido.page_count == 1
    assert len(doc_comprimido[0].get_images()) >= 1
    doc_comprimido.close()


def test_comprimir_pdf_sinaliza_quando_arquivo_aumenta(tmp_path):
    origem = tmp_path / "origem_minima.pdf"
    saida = tmp_path / "saida_minima.pdf"

    # PDF mínimo já altamente enxuto
    doc = pymupdf.open()
    doc.new_page()
    doc.save(str(origem), garbage=4, deflate=True)
    doc.close()

    # Nível baixo em PDF minúsculo tende a gerar overhead de estrutura
    res = comprimir_pdf(str(origem), str(saida), nivel="baixo")
    if res["tamanho_final"] > res["tamanho_original"]:
        assert res.get("aumentou") is True
        assert res["economia_percentual"] < 0
    else:
        assert "aumentou" not in res


def test_comprimir_pdf_validacoes(tmp_path):
    origem = tmp_path / "origem.pdf"
    saida = tmp_path / "saida.pdf"

    doc = pymupdf.open()
    doc.new_page()
    doc.save(str(origem))
    doc.close()

    # Saída igual à origem
    with pytest.raises(ValueError, match="igual ao arquivo de origem"):
        comprimir_pdf(str(origem), str(origem))

    # Arquivo não encontrado
    with pytest.raises(ValueError, match="não foi encontrado"):
        comprimir_pdf(str(tmp_path / "inexistente.pdf"), str(saida))

    # Caminho e saída vazios
    with pytest.raises(ValueError, match="string não vazia"):
        comprimir_pdf("", str(saida))
    with pytest.raises(ValueError, match="string não vazia"):
        comprimir_pdf(str(origem), "")

    # Nível inválido
    with pytest.raises(ValueError, match="Nível de compressão inválido"):
        comprimir_pdf(str(origem), str(saida), nivel="ultra")
    with pytest.raises(ValueError, match="Nível de compressão inválido"):
        comprimir_pdf(str(origem), str(saida), nivel=123)
    with pytest.raises(ValueError, match="Nível de compressão inválido"):
        comprimir_pdf(str(origem), str(saida), nivel=True)
