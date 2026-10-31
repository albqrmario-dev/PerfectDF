"""Módulo central do PerfectDF mantido para retrocompatibilidade.

Todas as funções foram modularizadas em submódulos específicos em português
(paginas, anotacoes, seguranca, conversao, texto, metadados, compressao, comum),
mas continuam disponíveis aqui.
"""

from perfectdf.anotacoes import (
    adicionar_marca_dagua,
    adicionar_nota,
    destacar_texto,
    numerar_paginas,
)
from perfectdf.compressao import (
    comprimir_pdf,
)
from perfectdf.comum import (
    abrir_pdf,
    parsear_ordem,
    parsear_paginas,
)
from perfectdf.conversao import (
    adicionar_imagem,
    imagens_para_pdf,
    pdf_para_imagens,
)
from perfectdf.metadados import (
    editar_metadados,
    ler_metadados,
)
from perfectdf.paginas import (
    excluir_paginas,
    extrair_paginas,
    girar_paginas,
    juntar_pdfs,
    reordenar_paginas,
)
from perfectdf.seguranca import (
    proteger_pdf,
    remover_senha,
)
from perfectdf.texto import (
    adicionar_texto,
    extrair_texto,
)

__all__ = [
    "abrir_pdf",
    "adicionar_imagem",
    "adicionar_marca_dagua",
    "adicionar_nota",
    "adicionar_texto",
    "comprimir_pdf",
    "destacar_texto",
    "editar_metadados",
    "excluir_paginas",
    "extrair_paginas",
    "extrair_texto",
    "girar_paginas",
    "imagens_para_pdf",
    "juntar_pdfs",
    "ler_metadados",
    "numerar_paginas",
    "parsear_ordem",
    "parsear_paginas",
    "pdf_para_imagens",
    "proteger_pdf",
    "remover_senha",
    "reordenar_paginas",
]
