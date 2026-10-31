import perfectdf
from perfectdf import (
    abrir_pdf,
    adicionar_imagem,
    adicionar_marca_dagua,
    adicionar_nota,
    adicionar_texto,
    comprimir_pdf,
    destacar_texto,
    editar_metadados,
    excluir_paginas,
    extrair_paginas,
    extrair_texto,
    girar_paginas,
    imagens_para_pdf,
    juntar_pdfs,
    ler_metadados,
    numerar_paginas,
    parsear_ordem,
    parsear_paginas,
    pdf_para_imagens,
    proteger_pdf,
    remover_senha,
    reordenar_paginas,
)
from perfectdf.anotacoes import (
    adicionar_marca_dagua as a_marca,
    adicionar_nota as a_nota,
    destacar_texto as a_destacar,
    numerar_paginas as a_numerar,
)
from perfectdf.compressao import comprimir_pdf as c_comprimir
from perfectdf.comum import (
    abrir_pdf as c_abrir,
    parsear_ordem as c_ordem,
    parsear_paginas as c_paginas,
)
from perfectdf.conversao import (
    adicionar_imagem as c_imagem,
    imagens_para_pdf as c_img2pdf,
    pdf_para_imagens as c_pdf2img,
)
from perfectdf.metadados import (
    editar_metadados as m_editar,
    ler_metadados as m_ler,
)
from perfectdf.paginas import (
    excluir_paginas as p_excluir,
    extrair_paginas as p_extrair,
    girar_paginas as p_girar,
    juntar_pdfs as p_juntar,
    reordenar_paginas as p_reordenar,
)
from perfectdf.seguranca import (
    proteger_pdf as s_proteger,
    remover_senha as s_remover,
)
from perfectdf.texto import (
    adicionar_texto as t_texto,
    extrair_texto as t_extrair,
)


def test_import_raiz():
    """Garante que todas as funções públicas estão acessíveis a partir da raiz do pacote."""
    assert callable(abrir_pdf)
    assert callable(adicionar_imagem)
    assert callable(juntar_pdfs)
    assert callable(extrair_paginas)
    assert callable(girar_paginas)
    assert callable(excluir_paginas)
    assert callable(reordenar_paginas)
    assert callable(parsear_paginas)
    assert callable(parsear_ordem)
    assert callable(ler_metadados)
    assert callable(editar_metadados)
    assert callable(extrair_texto)
    assert callable(adicionar_marca_dagua)
    assert callable(numerar_paginas)
    assert callable(destacar_texto)
    assert callable(adicionar_nota)
    assert callable(adicionar_texto)
    assert callable(comprimir_pdf)
    assert callable(proteger_pdf)
    assert callable(remover_senha)
    assert callable(pdf_para_imagens)
    assert callable(imagens_para_pdf)


def test_import_submodulos():
    """Garante que as funções nos submódulos em português correspondem às funções exportadas."""
    assert c_abrir is abrir_pdf
    assert c_paginas is parsear_paginas
    assert c_ordem is parsear_ordem
    assert p_juntar is juntar_pdfs
    assert p_extrair is extrair_paginas
    assert p_girar is girar_paginas
    assert p_excluir is excluir_paginas
    assert p_reordenar is reordenar_paginas
    assert m_ler is ler_metadados
    assert m_editar is editar_metadados
    assert t_extrair is extrair_texto
    assert t_texto is adicionar_texto
    assert a_marca is adicionar_marca_dagua
    assert a_numerar is numerar_paginas
    assert a_destacar is destacar_texto
    assert a_nota is adicionar_nota
    assert c_comprimir is comprimir_pdf
    assert s_proteger is proteger_pdf
    assert s_remover is remover_senha
    assert c_pdf2img is pdf_para_imagens
    assert c_img2pdf is imagens_para_pdf
    assert c_imagem is adicionar_imagem


def test_all_definido():
    """Garante que __all__ expõe todas as funções públicas."""
    assert len(perfectdf.__all__) == 22
    for nome in perfectdf.__all__:
        assert hasattr(perfectdf, nome)
