import os
import pymupdf
import pytest

from perfectdf.cli import main


@pytest.fixture
def pdf_simples(tmp_path):
    """Cria um PDF de 3 páginas para testes da CLI."""
    doc = pymupdf.open()
    for i in range(1, 4):
        page = doc.new_page(width=300, height=300)
        page.insert_text((50, 50), f"Texto da Pagina {i}", fontsize=14)
    caminho = str(tmp_path / "simples.pdf")
    doc.save(caminho)
    doc.close()
    return caminho


def test_cli_help(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(["--help"])
    assert excinfo.value.code == 0
    captured = capsys.readouterr()
    assert "PerfectDF" in captured.out
    assert "juntar" in captured.out
    assert "extrair" in captured.out


def test_cli_sem_subcomando(capsys):
    codigo = main([])
    assert codigo == 2
    captured = capsys.readouterr()
    assert "Erro: Nenhum subcomando informado" in captured.err


def test_cli_juntar(tmp_path, pdf_simples, capsys):
    saida = str(tmp_path / "juntado.pdf")
    codigo = main(["juntar", pdf_simples, pdf_simples, "-o", saida])
    assert codigo == 0
    doc = pymupdf.open(saida)
    assert doc.page_count == 6
    doc.close()
    captured = capsys.readouterr()
    assert "Sucesso" in captured.out


def test_cli_extrair(tmp_path, pdf_simples, capsys):
    saida = str(tmp_path / "extraido.pdf")
    codigo = main(["extrair", pdf_simples, "-p", "1,3", "-o", saida])
    assert codigo == 0
    doc = pymupdf.open(saida)
    assert doc.page_count == 2
    doc.close()
    captured = capsys.readouterr()
    assert "Sucesso" in captured.out


def test_cli_girar(tmp_path, pdf_simples, capsys):
    saida = str(tmp_path / "girado.pdf")
    codigo = main(["girar", pdf_simples, "-p", "1", "-g", "90", "-o", saida])
    assert codigo == 0
    doc = pymupdf.open(saida)
    assert doc[0].rotation == 90
    assert doc[1].rotation == 0
    doc.close()


def test_cli_excluir(tmp_path, pdf_simples, capsys):
    saida = str(tmp_path / "excluido.pdf")
    codigo = main(["excluir", pdf_simples, "-p", "2", "-o", saida])
    assert codigo == 0
    doc = pymupdf.open(saida)
    assert doc.page_count == 2
    doc.close()


def test_cli_reordenar(tmp_path, pdf_simples, capsys):
    saida = str(tmp_path / "reordenado.pdf")
    codigo = main(["reordenar", pdf_simples, "--ordem", "3, 2, 1", "-o", saida])
    assert codigo == 0
    doc = pymupdf.open(saida)
    assert doc.page_count == 3
    assert "Pagina 3" in doc[0].get_text()
    doc.close()


def test_cli_metadados_leitura_e_edicao(tmp_path, pdf_simples, capsys):
    # Leitura inicial
    codigo = main(["metadados", pdf_simples])
    assert codigo == 0
    out = capsys.readouterr().out
    assert "Título:" in out
    assert "Autor:" in out

    # Edição
    saida = str(tmp_path / "meta_editado.pdf")
    codigo = main([
        "metadados",
        pdf_simples,
        "--titulo", "Novo Titulo",
        "--autor", "Autor Teste",
        "-o", saida
    ])
    assert codigo == 0

    doc = pymupdf.open(saida)
    assert doc.metadata["title"] == "Novo Titulo"
    assert doc.metadata["author"] == "Autor Teste"
    doc.close()


def test_cli_texto(tmp_path, pdf_simples, capsys):
    # Saída padrão
    codigo = main(["texto", pdf_simples, "-p", "1"])
    assert codigo == 0
    out = capsys.readouterr().out
    assert "Texto da Pagina 1" in out

    # Saída para arquivo
    txt_saida = str(tmp_path / "extraido.txt")
    codigo = main(["texto", pdf_simples, "-p", "1", "-o", txt_saida])
    assert codigo == 0
    assert os.path.isfile(txt_saida)
    with open(txt_saida, encoding="utf-8") as f:
        assert "Texto da Pagina 1" in f.read()


def test_cli_marca_dagua(tmp_path, pdf_simples, capsys):
    saida = str(tmp_path / "marca.pdf")
    codigo = main(["marca-dagua", pdf_simples, "RASCUNHO", "-o", saida])
    assert codigo == 0
    assert os.path.isfile(saida)


def test_cli_adicionar_nota(tmp_path, pdf_simples, capsys):
    saida = str(tmp_path / "com_nota.pdf")
    codigo = main([
        "adicionar-nota", pdf_simples, "-p", "2", "-t", "Revisar este trecho",
        "--posicao", "80,90", "-o", saida,
    ])
    assert codigo == 0
    assert os.path.isfile(saida)
    assert "Nota adicionada" in capsys.readouterr().out

    doc = pymupdf.open(saida)
    assert list(doc[1].annots())
    assert not list(doc[0].annots())
    doc.close()


def test_cli_adicionar_nota_alias(tmp_path, pdf_simples, capsys):
    saida = str(tmp_path / "com_nota_alias.pdf")
    codigo = main([
        "adicionar_nota", pdf_simples, "-p", "1", "-t", "Nota via alias", "-o", saida,
    ])
    assert codigo == 0
    assert os.path.isfile(saida)


def test_cli_numerar(tmp_path, pdf_simples, capsys):
    saida = str(tmp_path / "numerado.pdf")
    codigo = main(["numerar", pdf_simples, "-o", saida, "--posicao", "rodape-direita"])
    assert codigo == 0
    assert os.path.isfile(saida)


def test_cli_comprimir(tmp_path, pdf_simples, capsys):
    saida = str(tmp_path / "comprimido.pdf")
    codigo = main(["comprimir", pdf_simples, "-o", saida, "--nivel", "baixo"])
    assert codigo == 0
    assert os.path.isfile(saida)
    out = capsys.readouterr().out
    assert "Economia:" in out


def test_cli_proteger_e_remover_senha(tmp_path, pdf_simples, capsys):
    protegido = str(tmp_path / "protegido.pdf")
    codigo_prot = main(["proteger", pdf_simples, "-s", "segredo123", "-o", protegido])
    assert codigo_prot == 0

    desprotegido = str(tmp_path / "desprotegido.pdf")
    codigo_rem = main(["remover-senha", protegido, "-s", "segredo123", "-o", desprotegido])
    assert codigo_rem == 0

    doc = pymupdf.open(desprotegido)
    assert not doc.needs_pass
    doc.close()


def test_cli_pdf_para_imagens_e_imagens_para_pdf(tmp_path, pdf_simples, capsys):
    pasta_img = str(tmp_path / "imgs")
    codigo = main(["pdf-para-imagens", pdf_simples, "-o", pasta_img, "--dpi", "72"])
    assert codigo == 0
    imagens = sorted([os.path.join(pasta_img, f) for f in os.listdir(pasta_img)])
    assert len(imagens) == 3

    pdf_reconstruido = str(tmp_path / "de_imagens.pdf")
    codigo_img2pdf = main(["imagens-para-pdf", *imagens, "-o", pdf_reconstruido])
    assert codigo_img2pdf == 0
    doc = pymupdf.open(pdf_reconstruido)
    assert doc.page_count == 3
    doc.close()


def test_cli_erros_sem_stack_trace(tmp_path, pdf_simples, capsys):
    # Arquivo não encontrado
    codigo = main(["extrair", "arquivo_que_nao_existe.pdf", "-p", "1", "-o", str(tmp_path / "out.pdf")])
    assert codigo == 1
    captured = capsys.readouterr()
    assert "Erro: " in captured.err
    assert "Traceback" not in captured.err

    # Senha incorreta
    protegido = str(tmp_path / "prot.pdf")
    main(["proteger", pdf_simples, "-s", "correta", "-o", protegido])
    codigo_senha = main(["remover-senha", protegido, "-s", "errada", "-o", str(tmp_path / "unlocked.pdf")])
    assert codigo_senha == 1
    captured_senha = capsys.readouterr()
    assert "Erro: A senha informada está incorreta." in captured_senha.err
    assert "Traceback" not in captured_senha.err


def test_cli_adicionar_texto(tmp_path, pdf_simples, capsys):
    saida = str(tmp_path / "com_texto.pdf")
    codigo = main([
        "adicionar-texto",
        pdf_simples,
        "-p", "1",
        "-t", "Texto via CLI",
        "-o", saida,
        "--posicao", "60,80",
        "--cor", "vermelho",
    ])
    assert codigo == 0
    doc = pymupdf.open(saida)
    assert "Texto via CLI" in doc[0].get_text()
    doc.close()


def test_cli_adicionar_imagem(tmp_path, pdf_simples, capsys):
    img_path = str(tmp_path / "icone.png")
    pix = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 50, 50), 0)
    pix.clear_with(255)
    pix.save(img_path)

    saida = str(tmp_path / "com_imagem_cli.pdf")
    codigo = main([
        "adicionar-imagem",
        pdf_simples,
        "-p", "1",
        "-i", img_path,
        "-o", saida,
        "--posicao", "40,40",
        "--tamanho", "60,60",
    ])
    assert codigo == 0
    doc = pymupdf.open(saida)
    assert len(doc[0].get_images()) == 1
    doc.close()


def test_cli_destacar_texto_com_ocorrencias(tmp_path, pdf_simples, capsys):
    saida = str(tmp_path / "destacado.pdf")
    codigo = main([
        "destacar-texto",
        pdf_simples,
        "Pagina",
        "-o", saida,
    ])
    assert codigo == 0
    out = capsys.readouterr().out
    assert "ocorrência(s)" in out
    assert os.path.isfile(saida)

    doc = pymupdf.open(saida)
    annots = list(doc[0].annots())
    assert len(annots) > 0
    doc.close()


def test_cli_destacar_texto_sem_ocorrencias(tmp_path, pdf_simples, capsys):
    saida = str(tmp_path / "sem_destaque.pdf")
    codigo = main([
        "destacar-texto",
        pdf_simples,
        "INEXISTENTE_XYZ_12345",
        "-o", saida,
    ])
    assert codigo == 0
    out = capsys.readouterr().out
    assert "Nenhuma ocorrência" in out


def test_cli_destacar_texto_sublinhado_e_paginas(tmp_path, pdf_simples, capsys):
    saida = str(tmp_path / "sublinhado.pdf")
    codigo = main([
        "destacar-texto",
        pdf_simples,
        "Texto",
        "-o", saida,
        "-p", "1-2",
        "--tipo", "sublinhado",
        "--cor", "azul",
    ])
    assert codigo == 0
    out = capsys.readouterr().out
    assert "ocorrência(s)" in out
