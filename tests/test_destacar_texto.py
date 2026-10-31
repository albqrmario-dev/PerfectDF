# pyright: reportArgumentType=false, reportAttributeAccessIssue=false, reportOptionalSubscript=false
import os

import pymupdf
import pytest

from perfectdf.core import destacar_texto

# Constantes de tipo de anotação do PyMuPDF
_HIGHLIGHT = pymupdf.PDF_ANNOT_HIGHLIGHT  # 8
_UNDERLINE = pymupdf.PDF_ANNOT_UNDERLINE  # 9
_STRIKEOUT = pymupdf.PDF_ANNOT_STRIKE_OUT  # 11


# ---------------------------------------------------------------------------
# Fixture: PDF com texto em 3 páginas
# ---------------------------------------------------------------------------


@pytest.fixture()
def pdf_com_texto(tmp_path):
    """Cria PDF de 3 páginas com textos variados para busca."""
    caminho = str(tmp_path / "origem.pdf")
    doc = pymupdf.open()
    textos = [
        "Python é uma linguagem de programação.",  # pág 1: "Python" 1x
        "python e PYTHON são a mesma palavra.",  # pág 2: "python"/"PYTHON" 2x (case-insensitive)
        "Aqui não tem a palavra procurada.",  # pág 3: nada
    ]
    for texto in textos:
        page = doc.new_page()
        page.insert_text((50, 72), texto, fontsize=14)
    doc.save(caminho)
    doc.close()
    return caminho


@pytest.fixture()
def pdf_escaneado(tmp_path):
    """Cria PDF de 1 página sem nenhum texto selecionável (simula scan)."""
    caminho = str(tmp_path / "scan.pdf")
    doc = pymupdf.open()
    doc.new_page()  # página em branco — sem camada de texto
    doc.save(caminho)
    doc.close()
    return caminho


@pytest.fixture()
def pdf_protegido(tmp_path):
    """Cria PDF protegido por senha."""
    caminho = str(tmp_path / "protegido.pdf")
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((50, 72), "texto secreto", fontsize=14)
    doc.save(caminho, encryption=pymupdf.PDF_ENCRYPT_AES_256, user_pw="senha123")
    doc.close()
    return caminho


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _abrir_e_coletar_annots(caminho):
    """Retorna lista de todas as anotações do PDF: (pagina_base1, tipo_num, tipo_str)."""
    doc = pymupdf.open(caminho)
    resultado = []
    for i, page in enumerate(doc):
        for a in page.annots():
            resultado.append((i + 1, a.type[0], a.type[1]))
    doc.close()
    return resultado


def _contar_annots_por_tipo(caminho, tipo_num):
    return sum(1 for _, t, _ in _abrir_e_coletar_annots(caminho) if t == tipo_num)


# ---------------------------------------------------------------------------
# Testes de comportamento principal
# ---------------------------------------------------------------------------


class TestDestacarTextoDestaque:
    def test_destaque_basico_cria_anotacoes_corretas(self, pdf_com_texto, tmp_path):
        saida = str(tmp_path / "saida.pdf")
        res = destacar_texto(pdf_com_texto, saida, "Python")

        # Retorno: 3 ocorrências totais (1 na pág 1 + 2 na pág 2, case-insensitive)
        assert res["total_ocorrencias"] == 3
        assert res["ocorrencias_por_pagina"] == {1: 1, 2: 2}

        # Arquivo de saída criado
        assert os.path.isfile(saida)

        # Verificar tipos de anotação no PDF de saída
        annots = _abrir_e_coletar_annots(saida)
        tipos = [t for _, t, _ in annots]
        assert len(tipos) == 3
        assert all(t == _HIGHLIGHT for t in tipos)

    def test_destaque_pagina_3_sem_ocorrencias_nao_aparece(
        self, pdf_com_texto, tmp_path
    ):
        saida = str(tmp_path / "saida.pdf")
        res = destacar_texto(pdf_com_texto, saida, "Python")

        # Página 3 não deve aparecer no dict
        assert 3 not in res["ocorrencias_por_pagina"]

    def test_original_nao_alterado(self, pdf_com_texto, tmp_path):
        saida = str(tmp_path / "saida.pdf")
        destacar_texto(pdf_com_texto, saida, "Python")

        # PDF original não deve ter anotações
        assert _contar_annots_por_tipo(pdf_com_texto, _HIGHLIGHT) == 0


class TestDestacarTextoTipos:
    def test_sublinhado(self, pdf_com_texto, tmp_path):
        saida = str(tmp_path / "saida.pdf")
        res = destacar_texto(pdf_com_texto, saida, "Python", tipo="sublinhado")

        assert res["total_ocorrencias"] == 3
        assert _contar_annots_por_tipo(saida, _UNDERLINE) == 3
        assert _contar_annots_por_tipo(saida, _HIGHLIGHT) == 0

    def test_riscado(self, pdf_com_texto, tmp_path):
        saida = str(tmp_path / "saida.pdf")
        res = destacar_texto(pdf_com_texto, saida, "Python", tipo="riscado")

        assert res["total_ocorrencias"] == 3
        assert _contar_annots_por_tipo(saida, _STRIKEOUT) == 3
        assert _contar_annots_por_tipo(saida, _HIGHLIGHT) == 0


class TestDestacarTextoCores:
    def test_cor_string_valida(self, pdf_com_texto, tmp_path):
        # Deve funcionar sem erros — todas as cores nomeadas
        for nome_cor in ("amarelo", "verde", "azul", "rosa", "laranja", "vermelho"):
            saida = str(tmp_path / f"saida_{nome_cor}.pdf")
            res = destacar_texto(pdf_com_texto, saida, "Python", cor=nome_cor)
            assert res["total_ocorrencias"] == 3
            assert os.path.isfile(saida)

    def test_cor_tupla_valida(self, pdf_com_texto, tmp_path):
        saida = str(tmp_path / "saida.pdf")
        res = destacar_texto(pdf_com_texto, saida, "Python", cor=(0.2, 0.8, 0.4))
        assert res["total_ocorrencias"] == 3
        assert os.path.isfile(saida)

    def test_cor_tupla_com_int_valido(self, pdf_com_texto, tmp_path):
        saida = str(tmp_path / "saida.pdf")
        # Inteiros 0 e 1 são válidos como float
        res = destacar_texto(pdf_com_texto, saida, "Python", cor=(1, 1, 0))
        assert res["total_ocorrencias"] == 3


class TestDestacarTextoSelecaoPaginas:
    def test_paginas_como_lista(self, pdf_com_texto, tmp_path):
        saida = str(tmp_path / "saida.pdf")
        res = destacar_texto(pdf_com_texto, saida, "Python", paginas=[1])

        # Apenas página 1: 1 ocorrência
        assert res["total_ocorrencias"] == 1
        assert res["ocorrencias_por_pagina"] == {1: 1}
        assert _contar_annots_por_tipo(saida, _HIGHLIGHT) == 1

    def test_paginas_como_string(self, pdf_com_texto, tmp_path):
        saida = str(tmp_path / "saida.pdf")
        res = destacar_texto(pdf_com_texto, saida, "Python", paginas="1-2")

        assert res["total_ocorrencias"] == 3
        assert set(res["ocorrencias_por_pagina"].keys()) == {1, 2}

    def test_pagina_sem_ocorrencia_nao_gera_saida_vazia(self, pdf_com_texto, tmp_path):
        saida = str(tmp_path / "saida.pdf")
        res = destacar_texto(pdf_com_texto, saida, "Python", paginas=[3])

        # Página 3 não tem "Python" → zero ocorrências → sem arquivo
        assert res["total_ocorrencias"] == 0
        assert not os.path.isfile(saida)


class TestDestacarTextoIgnorarMaiusculas:
    def test_ignorar_maiusculas_true_encontra_todas(self, pdf_com_texto, tmp_path):
        saida = str(tmp_path / "saida.pdf")
        # "python" minúsculo deve achar "Python" e "PYTHON" também
        res = destacar_texto(pdf_com_texto, saida, "python", ignorar_maiusculas=True)
        assert res["total_ocorrencias"] == 3

    def test_ignorar_maiusculas_false_case_exato(self, pdf_com_texto, tmp_path):
        saida = str(tmp_path / "saida.pdf")
        # "python" minúsculo exato: só a ocorrência "python" na pág 2
        res = destacar_texto(pdf_com_texto, saida, "python", ignorar_maiusculas=False)
        assert res["total_ocorrencias"] == 1
        assert res["ocorrencias_por_pagina"] == {2: 1}

    def test_ignorar_maiusculas_false_maiusculo_exato(self, pdf_com_texto, tmp_path):
        saida = str(tmp_path / "saida.pdf")
        # "PYTHON" maiúsculo exato: só a ocorrência "PYTHON" na pág 2
        res = destacar_texto(pdf_com_texto, saida, "PYTHON", ignorar_maiusculas=False)
        assert res["total_ocorrencias"] == 1
        assert res["ocorrencias_por_pagina"] == {2: 1}

    def test_ignorar_maiusculas_false_sem_match(self, pdf_com_texto, tmp_path):
        saida = str(tmp_path / "saida.pdf")
        # "PyThOn" não existe com essa grafia → zero resultados, sem arquivo
        res = destacar_texto(pdf_com_texto, saida, "PyThOn", ignorar_maiusculas=False)
        assert res["total_ocorrencias"] == 0
        assert not os.path.isfile(saida)


class TestDestacarTextoZeroOcorrencias:
    def test_zero_ocorrencias_nao_gera_arquivo(self, pdf_com_texto, tmp_path):
        saida = str(tmp_path / "saida.pdf")
        res = destacar_texto(pdf_com_texto, saida, "termoquenonexiste")

        assert res["total_ocorrencias"] == 0
        assert res["ocorrencias_por_pagina"] == {}
        assert not os.path.isfile(saida)
        assert "aviso" not in res  # há texto no PDF, não é scan

    def test_pdf_escaneado_inclui_aviso_no_retorno(self, pdf_escaneado, tmp_path):
        saida = str(tmp_path / "saida.pdf")
        res = destacar_texto(pdf_escaneado, saida, "qualquer coisa")

        assert res["total_ocorrencias"] == 0
        assert not os.path.isfile(saida)
        assert "aviso" in res
        assert "OCR" in res["aviso"]
        assert (
            "escaneado" in res["aviso"].lower() or "texto selecionável" in res["aviso"]
        )


# ---------------------------------------------------------------------------
# Testes de validação de entradas
# ---------------------------------------------------------------------------


class TestDestacarTextoValidacoes:
    def test_caminho_vazio(self, tmp_path):
        with pytest.raises(ValueError, match="origem"):
            destacar_texto("", str(tmp_path / "s.pdf"), "termo")

    def test_caminho_nao_string(self, tmp_path):
        with pytest.raises(ValueError, match="origem"):
            destacar_texto(123, str(tmp_path / "s.pdf"), "termo")

    def test_saida_vazia(self, pdf_com_texto, tmp_path):
        with pytest.raises(ValueError, match="saída"):
            destacar_texto(pdf_com_texto, "", "termo")

    def test_saida_igual_origem(self, pdf_com_texto):
        with pytest.raises(ValueError, match="igual"):
            destacar_texto(pdf_com_texto, pdf_com_texto, "termo")

    def test_arquivo_nao_encontrado(self, tmp_path):
        with pytest.raises(ValueError, match="não foi encontrado"):
            destacar_texto(
                str(tmp_path / "inexistente.pdf"), str(tmp_path / "s.pdf"), "termo"
            )

    def test_termo_vazio(self, pdf_com_texto, tmp_path):
        with pytest.raises(ValueError, match="termo"):
            destacar_texto(pdf_com_texto, str(tmp_path / "s.pdf"), "")

    def test_termo_so_espacos(self, pdf_com_texto, tmp_path):
        with pytest.raises(ValueError, match="termo"):
            destacar_texto(pdf_com_texto, str(tmp_path / "s.pdf"), "   ")

    def test_tipo_invalido(self, pdf_com_texto, tmp_path):
        with pytest.raises(ValueError, match="Tipo de anotação inválido"):
            destacar_texto(
                pdf_com_texto, str(tmp_path / "s.pdf"), "Python", tipo="negrito"
            )

    def test_cor_string_invalida(self, pdf_com_texto, tmp_path):
        with pytest.raises(ValueError, match="Cor inválida"):
            destacar_texto(pdf_com_texto, str(tmp_path / "s.pdf"), "Python", cor="roxo")

    def test_cor_tupla_tamanho_errado(self, pdf_com_texto, tmp_path):
        with pytest.raises(ValueError, match="3 componentes"):
            destacar_texto(
                pdf_com_texto, str(tmp_path / "s.pdf"), "Python", cor=(1.0, 0.5)
            )

    def test_cor_tupla_valor_fora_do_intervalo(self, pdf_com_texto, tmp_path):
        with pytest.raises(ValueError, match="0.0 e 1.0"):
            destacar_texto(
                pdf_com_texto, str(tmp_path / "s.pdf"), "Python", cor=(1.5, 0.0, 0.0)
            )

    def test_cor_tupla_componente_booleano(self, pdf_com_texto, tmp_path):
        with pytest.raises(ValueError, match="0.0 e 1.0"):
            destacar_texto(
                pdf_com_texto, str(tmp_path / "s.pdf"), "Python", cor=(True, 0.0, 0.0)
            )

    def test_cor_tipo_invalido(self, pdf_com_texto, tmp_path):
        with pytest.raises(ValueError, match="nome em string ou uma tupla"):
            destacar_texto(pdf_com_texto, str(tmp_path / "s.pdf"), "Python", cor=42)

    def test_pagina_invalida_zero(self, pdf_com_texto, tmp_path):
        with pytest.raises(ValueError, match="Página inválida"):
            destacar_texto(
                pdf_com_texto, str(tmp_path / "s.pdf"), "Python", paginas=[0]
            )

    def test_pagina_invalida_booleano(self, pdf_com_texto, tmp_path):
        with pytest.raises(ValueError, match="Página inválida"):
            destacar_texto(
                pdf_com_texto, str(tmp_path / "s.pdf"), "Python", paginas=[True]
            )

    def test_pagina_invalida_fora_do_limite(self, pdf_com_texto, tmp_path):
        with pytest.raises(ValueError, match="Página inválida"):
            destacar_texto(
                pdf_com_texto, str(tmp_path / "s.pdf"), "Python", paginas=[99]
            )

    def test_paginas_lista_vazia(self, pdf_com_texto, tmp_path):
        with pytest.raises(ValueError, match="vazia"):
            destacar_texto(pdf_com_texto, str(tmp_path / "s.pdf"), "Python", paginas=[])

    def test_paginas_tipo_invalido(self, pdf_com_texto, tmp_path):
        with pytest.raises(ValueError, match="especificação de páginas"):
            destacar_texto(pdf_com_texto, str(tmp_path / "s.pdf"), "Python", paginas=42)

    def test_pdf_protegido_lanca_erro(self, pdf_protegido, tmp_path):
        with pytest.raises(ValueError, match="protegido por senha"):
            destacar_texto(pdf_protegido, str(tmp_path / "s.pdf"), "texto")
