# pyright: reportArgumentType=false, reportAttributeAccessIssue=false, reportOptionalSubscript=false
import os

import pymupdf
import pytest

from perfectdf.core import adicionar_nota

_ANNOT_TEXT = pymupdf.PDF_ANNOT_TEXT  # 0


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def pdf_simples(tmp_path):
    """PDF com 3 páginas sem rotação."""
    caminho = str(tmp_path / "origem.pdf")
    doc = pymupdf.open()
    for i in range(3):
        page = doc.new_page()
        page.insert_text((50, 72), f"Página {i + 1}", fontsize=14)
    doc.save(caminho)
    doc.close()
    return caminho


@pytest.fixture()
def pdf_rotacionado(tmp_path):
    """PDF com 1 página girada 90°."""
    caminho = str(tmp_path / "rotacionado.pdf")
    doc = pymupdf.open()
    page = doc.new_page()
    page.set_rotation(90)
    page.insert_text((50, 72), "página girada", fontsize=14)
    doc.save(caminho)
    doc.close()
    return caminho


@pytest.fixture()
def pdf_protegido(tmp_path):
    caminho = str(tmp_path / "protegido.pdf")
    doc = pymupdf.open()
    doc.new_page()
    doc.save(caminho, encryption=pymupdf.PDF_ENCRYPT_AES_256, user_pw="x")
    doc.close()
    return caminho


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _coletar_notas(caminho):
    """Retorna lista de (pagina_base1, tipo_num, content) de todas as anotações."""
    doc = pymupdf.open(caminho)
    resultado = []
    for i, page in enumerate(doc):
        for a in page.annots():
            resultado.append((i + 1, a.type[0], a.info.get("content", "")))
    doc.close()
    return resultado


# ---------------------------------------------------------------------------
# Comportamento principal
# ---------------------------------------------------------------------------

class TestAdicionarNotaBasico:
    def test_cria_nota_e_retorna_caminho(self, pdf_simples, tmp_path):
        saida = str(tmp_path / "saida.pdf")
        resultado = adicionar_nota(pdf_simples, saida, 1, "Minha nota aqui")
        assert resultado == saida
        assert os.path.isfile(saida)

    def test_tipo_de_anotacao_e_texto(self, pdf_simples, tmp_path):
        saida = str(tmp_path / "saida.pdf")
        adicionar_nota(pdf_simples, saida, 1, "Conteúdo da nota")

        notas = _coletar_notas(saida)
        assert len(notas) == 1
        pagina, tipo, content = notas[0]
        assert tipo == _ANNOT_TEXT        # sticky note
        assert pagina == 1
        assert "Conteúdo da nota" in content

    def test_nota_na_pagina_correta(self, pdf_simples, tmp_path):
        saida = str(tmp_path / "saida.pdf")
        adicionar_nota(pdf_simples, saida, 2, "Nota na página 2")

        notas = _coletar_notas(saida)
        assert len(notas) == 1
        assert notas[0][0] == 2   # página base 1

    def test_original_nao_alterado(self, pdf_simples, tmp_path):
        saida = str(tmp_path / "saida.pdf")
        adicionar_nota(pdf_simples, saida, 1, "nota")

        # Original não deve ter anotações
        assert _coletar_notas(pdf_simples) == []

    def test_notas_em_paginas_diferentes_via_chamadas_separadas(self, pdf_simples, tmp_path):
        # Adicionar nota na pág 1 e depois na pág 3 (passando o output como input)
        intermediario = str(tmp_path / "inter.pdf")
        saida = str(tmp_path / "saida.pdf")
        adicionar_nota(pdf_simples, intermediario, 1, "Nota pág 1")
        adicionar_nota(intermediario, saida, 3, "Nota pág 3")

        notas = _coletar_notas(saida)
        assert len(notas) == 2
        paginas = {n[0] for n in notas}
        assert paginas == {1, 3}

    def test_posicao_padrao(self, pdf_simples, tmp_path):
        """Deve funcionar com posição padrão sem erro."""
        saida = str(tmp_path / "saida.pdf")
        adicionar_nota(pdf_simples, saida, 1, "nota padrão")
        assert os.path.isfile(saida)

    def test_posicao_personalizada(self, pdf_simples, tmp_path):
        saida = str(tmp_path / "saida.pdf")
        adicionar_nota(pdf_simples, saida, 1, "nota", posicao=(100.5, 200.0))
        notas = _coletar_notas(saida)
        assert len(notas) == 1

    def test_posicao_na_borda_da_pagina(self, pdf_simples, tmp_path):
        """Coordenadas exatamente no limite da página devem ser aceitas."""
        doc = pymupdf.open(pdf_simples)
        page = doc[0]
        largura = page.rect.width
        altura = page.rect.height
        doc.close()

        saida = str(tmp_path / "saida.pdf")
        adicionar_nota(pdf_simples, saida, 1, "borda", posicao=(largura, altura))
        assert os.path.isfile(saida)


class TestAdicionarNotaRotacao:
    def test_nota_em_pagina_rotacionada_aceita_coordenadas_visuais(
        self, pdf_rotacionado, tmp_path
    ):
        """Em página com rotation=90, as dimensões visuais se invertem.
        (50, 50) deve ser aceito e gerar uma nota válida."""
        saida = str(tmp_path / "saida.pdf")
        adicionar_nota(pdf_rotacionado, saida, 1, "nota em página girada", posicao=(50, 50))

        notas = _coletar_notas(saida)
        assert len(notas) == 1
        assert notas[0][1] == _ANNOT_TEXT

    def test_posicao_fora_dos_limites_visuais_em_rotacionada(
        self, pdf_rotacionado, tmp_path
    ):
        """Para rotation=90, largura_visual = altura_física e vice-versa.
        Uma posição válida no espaço físico pode ser inválida no visual."""
        doc = pymupdf.open(pdf_rotacionado)
        page = doc[0]
        # Página rotacionada 90°: dimensão física width × height → visual height × width
        largura_fisica = page.rect.width
        altura_fisica = page.rect.height
        doc.close()

        saida = str(tmp_path / "saida.pdf")
        # largura_visual = altura_fisica; pedir x > altura_fisica deve falhar
        with pytest.raises(ValueError, match="fora dos limites"):
            adicionar_nota(
                pdf_rotacionado, saida, 1, "nota",
                posicao=(altura_fisica + 1, 50),
            )

        # largura_fisica sozinha não ultrapassa a largura_visual (= altura_fisica),
        # mas ultrapassa a altura_visual (= largura_fisica)
        with pytest.raises(ValueError, match="fora dos limites"):
            adicionar_nota(
                pdf_rotacionado, saida, 1, "nota",
                posicao=(50, largura_fisica + 1),
            )


# ---------------------------------------------------------------------------
# Validações de entrada
# ---------------------------------------------------------------------------

class TestAdicionarNotaValidacoes:
    def test_caminho_vazio(self, tmp_path):
        with pytest.raises(ValueError, match="origem"):
            adicionar_nota("", str(tmp_path / "s.pdf"), 1, "nota")

    def test_caminho_nao_string(self, tmp_path):
        with pytest.raises(ValueError, match="origem"):
            adicionar_nota(None, str(tmp_path / "s.pdf"), 1, "nota")

    def test_saida_vazia(self, pdf_simples):
        with pytest.raises(ValueError, match="saída"):
            adicionar_nota(pdf_simples, "", 1, "nota")

    def test_saida_igual_origem(self, pdf_simples):
        with pytest.raises(ValueError, match="igual"):
            adicionar_nota(pdf_simples, pdf_simples, 1, "nota")

    def test_arquivo_nao_encontrado(self, tmp_path):
        with pytest.raises(ValueError, match="não foi encontrado"):
            adicionar_nota(str(tmp_path / "x.pdf"), str(tmp_path / "s.pdf"), 1, "nota")

    def test_pagina_booleano(self, pdf_simples, tmp_path):
        with pytest.raises(ValueError, match="inteiro"):
            adicionar_nota(pdf_simples, str(tmp_path / "s.pdf"), True, "nota")

    def test_pagina_float(self, pdf_simples, tmp_path):
        with pytest.raises(ValueError, match="inteiro"):
            adicionar_nota(pdf_simples, str(tmp_path / "s.pdf"), 1.5, "nota")

    def test_pagina_zero(self, pdf_simples, tmp_path):
        with pytest.raises(ValueError, match="maior ou igual a 1"):
            adicionar_nota(pdf_simples, str(tmp_path / "s.pdf"), 0, "nota")

    def test_pagina_negativa(self, pdf_simples, tmp_path):
        with pytest.raises(ValueError, match="maior ou igual a 1"):
            adicionar_nota(pdf_simples, str(tmp_path / "s.pdf"), -1, "nota")

    def test_pagina_fora_do_documento(self, pdf_simples, tmp_path):
        with pytest.raises(ValueError, match="Página inválida"):
            adicionar_nota(pdf_simples, str(tmp_path / "s.pdf"), 99, "nota")

    def test_texto_vazio(self, pdf_simples, tmp_path):
        with pytest.raises(ValueError, match="texto"):
            adicionar_nota(pdf_simples, str(tmp_path / "s.pdf"), 1, "")

    def test_texto_so_espacos(self, pdf_simples, tmp_path):
        with pytest.raises(ValueError, match="texto"):
            adicionar_nota(pdf_simples, str(tmp_path / "s.pdf"), 1, "   ")

    def test_posicao_nao_tuple(self, pdf_simples, tmp_path):
        with pytest.raises(ValueError, match="tupla"):
            adicionar_nota(pdf_simples, str(tmp_path / "s.pdf"), 1, "nota", posicao=[10, 10])

    def test_posicao_tamanho_errado(self, pdf_simples, tmp_path):
        with pytest.raises(ValueError, match="2 valores"):
            adicionar_nota(pdf_simples, str(tmp_path / "s.pdf"), 1, "nota", posicao=(10,))

    def test_posicao_coordenada_booleana(self, pdf_simples, tmp_path):
        with pytest.raises(ValueError, match="número"):
            adicionar_nota(pdf_simples, str(tmp_path / "s.pdf"), 1, "nota", posicao=(True, 50))

    def test_posicao_coordenada_negativa(self, pdf_simples, tmp_path):
        with pytest.raises(ValueError, match="negativas"):
            adicionar_nota(pdf_simples, str(tmp_path / "s.pdf"), 1, "nota", posicao=(-1, 50))

    def test_posicao_fora_dos_limites(self, pdf_simples, tmp_path):
        with pytest.raises(ValueError, match="fora dos limites"):
            adicionar_nota(pdf_simples, str(tmp_path / "s.pdf"), 1, "nota", posicao=(9999, 9999))

    def test_pdf_protegido(self, pdf_protegido, tmp_path):
        with pytest.raises(ValueError, match="protegido por senha"):
            adicionar_nota(pdf_protegido, str(tmp_path / "s.pdf"), 1, "nota")
