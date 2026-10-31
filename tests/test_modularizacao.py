import perfectdf
from perfectdf import (
    abrir_pdf,
    achatar_formulario,
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
    listar_campos,
    numerar_paginas,
    parsear_ordem,
    parsear_paginas,
    pdf_para_imagens,
    preencher_formulario,
    proteger_pdf,
    remover_senha,
    reordenar_paginas,
)
from perfectdf.anotacoes import (
    adicionar_marca_dagua as a_marca,
)
from perfectdf.anotacoes import (
    adicionar_nota as a_nota,
)
from perfectdf.anotacoes import (
    destacar_texto as a_destacar,
)
from perfectdf.anotacoes import (
    numerar_paginas as a_numerar,
)
from perfectdf.compressao import comprimir_pdf as c_comprimir
from perfectdf.comum import (
    abrir_pdf as c_abrir,
)
from perfectdf.comum import (
    parsear_ordem as c_ordem,
)
from perfectdf.comum import (
    parsear_paginas as c_paginas,
)
from perfectdf.conversao import (
    adicionar_imagem as c_imagem,
)
from perfectdf.conversao import (
    imagens_para_pdf as c_img2pdf,
)
from perfectdf.conversao import (
    pdf_para_imagens as c_pdf2img,
)
from perfectdf.formularios import (
    achatar_formulario as f_achatar,
)
from perfectdf.formularios import (
    listar_campos as f_listar,
)
from perfectdf.formularios import (
    preencher_formulario as f_preencher,
)
from perfectdf.metadados import (
    editar_metadados as m_editar,
)
from perfectdf.metadados import (
    ler_metadados as m_ler,
)
from perfectdf.paginas import (
    excluir_paginas as p_excluir,
)
from perfectdf.paginas import (
    extrair_paginas as p_extrair,
)
from perfectdf.paginas import (
    girar_paginas as p_girar,
)
from perfectdf.paginas import (
    juntar_pdfs as p_juntar,
)
from perfectdf.paginas import (
    reordenar_paginas as p_reordenar,
)
from perfectdf.seguranca import (
    proteger_pdf as s_proteger,
)
from perfectdf.seguranca import (
    remover_senha as s_remover,
)
from perfectdf.texto import (
    adicionar_texto as t_texto,
)
from perfectdf.texto import (
    extrair_texto as t_extrair,
)


def test_import_raiz():
    """Garante que todas as funções públicas estão acessíveis a partir da raiz do pacote."""
    assert callable(abrir_pdf)
    assert callable(achatar_formulario)
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
    assert callable(listar_campos)
    assert callable(preencher_formulario)
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
    assert f_listar is listar_campos
    assert f_preencher is preencher_formulario
    assert f_achatar is achatar_formulario


def test_all_definido():
    """Garante que __all__ expõe todas as funções públicas."""
    assert len(perfectdf.__all__) == 25
    for nome in perfectdf.__all__:
        assert hasattr(perfectdf, nome)
