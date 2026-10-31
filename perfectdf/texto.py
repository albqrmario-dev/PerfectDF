import os
import shutil
import tempfile
import warnings

import pymupdf

from perfectdf.comum import abrir_pdf, parsear_paginas

_CORES_TEXTO = {
    "preto": (0.0, 0.0, 0.0),
    "branco": (1.0, 1.0, 1.0),
    "vermelho": (1.0, 0.0, 0.0),
    "verde": (0.0, 0.8, 0.0),
    "azul": (0.0, 0.5, 1.0),
    "amarelo": (1.0, 1.0, 0.0),
    "cinza": (0.5, 0.5, 0.5),
    "laranja": (1.0, 0.5, 0.0),
    "rosa": (1.0, 0.4, 0.7),
}

_FONTES_MAP = {
    "helv": "helv",
    "helvetica": "helv",
    "times": "tiro",
    "times-roman": "tiro",
    "tiro": "tiro",
    "courier": "cour",
    "cour": "cour",
}


def extrair_texto(caminho: str, paginas: list[int] | str | None = None) -> str:
    """Extrai o texto de páginas selecionadas (ou de todas) de um documento PDF.

    Se paginas for None, extrai de todas as páginas. Também aceita string formatada
    (ex: '1-3, 5') reaproveitando parsear_paginas, ou lista de inteiros (base 1).
    Retorna o texto concatenado com separação clara entre cada página.
    Caso o documento ou as páginas selecionadas não contenham texto extraível
    (característico de PDFs escaneados sem OCR), emite um aviso amigável (UserWarning)
    sem interromper a execução.

    Parâmetros:
        caminho: Caminho do arquivo PDF.
        paginas: None para todas as páginas, string de páginas ou lista de inteiros (base 1).

    Retorna:
        String com o texto extraído formatado por página.

    Lança:
        ValueError: Se o caminho for inválido, o arquivo não for encontrado ou
                    se alguma página informada for inválida.
    """
    if not isinstance(caminho, str) or not caminho.strip():
        raise ValueError("O caminho do arquivo deve ser uma string não vazia.")
    if not os.path.isfile(caminho):
        raise ValueError(f"O arquivo não foi encontrado: '{caminho}'.")

    doc = abrir_pdf(caminho)
    try:
        total_paginas = doc.page_count
        if total_paginas == 0:
            raise ValueError("O documento não possui páginas para extração de texto.")

        if paginas is None:
            paginas_alvo = list(range(1, total_paginas + 1))
        elif isinstance(paginas, str):
            paginas_alvo = parsear_paginas(paginas)
        elif isinstance(paginas, (list, tuple)):
            paginas_alvo = list(paginas)
        else:
            raise ValueError(
                "A especificação de páginas deve ser None, uma string (ex: '1-3') ou uma lista de inteiros."
            )

        if not paginas_alvo:
            raise ValueError(
                "A lista de páginas para extração de texto não pode estar vazia."
            )

        for pagina in paginas_alvo:
            if (
                isinstance(pagina, bool)
                or not isinstance(pagina, int)
                or pagina < 1
                or pagina > total_paginas
            ):
                raise ValueError(
                    f"Página inválida: {pagina}. O documento possui {total_paginas} página(s) "
                    f"(páginas permitidas: 1 a {total_paginas})."
                )

        partes = []
        tem_texto = False
        for pagina in paginas_alvo:
            texto_pagina = doc[pagina - 1].get_text()
            if texto_pagina.strip():
                tem_texto = True
            partes.append(f"--- Página {pagina} ---\n{texto_pagina.strip()}")

        if not tem_texto:
            warnings.warn(
                f"O arquivo '{caminho}' parece ser escaneado ou não contém texto selecionável nas páginas consultadas.",
                UserWarning,
                stacklevel=2,
            )

        return "\n\n".join(partes)
    finally:
        doc.close()


def adicionar_texto(
    pdf: str,
    pagina: int,
    texto: str,
    posicao: tuple[float, float] = (50, 50),
    fonte: str = "helv",
    tamanho: float = 12.0,
    cor: str | tuple[float, float, float] = "preto",
    saida: str | None = None,
) -> str:
    """Adiciona texto formatado em uma página específica de um documento PDF.

    Parâmetros:
        pdf: Caminho do arquivo PDF de origem.
        pagina: Número da página onde o texto será inserido (base 1).
        texto: Texto a ser inserido.
        posicao: Coordenadas (x, y) no espaço visual da página (canto superior esquerdo como origem).
        fonte: Nome da fonte (padrão 'helv', opções: 'helvetica', 'times', 'courier', etc.).
        tamanho: Tamanho da fonte em pontos (padrão 12.0).
        cor: Nome da cor ('preto', 'vermelho', 'azul', 'verde', etc.) ou tupla RGB (r, g, b).
        saida: Caminho do arquivo salvo. Se None, modifica o próprio arquivo original.

    Retorna:
        Caminho do arquivo PDF salvo.

    Lança:
        ValueError: Se o caminho for inválido, o arquivo não existir, página fora dos limites,
                    texto vazio, posição negativa ou fora da página, tamanho <= 0 ou cor inválida.
    """
    if not isinstance(pdf, str) or not pdf.strip():
        raise ValueError("O caminho do arquivo de origem deve ser uma string não vazia.")
    if not os.path.isfile(pdf):
        raise ValueError(f"O arquivo de origem não foi encontrado: '{pdf}'.")

    if saida is not None and (not isinstance(saida, str) or not saida.strip()):
        raise ValueError("O caminho do arquivo de saída deve ser uma string não vazia.")

    if isinstance(pagina, bool) or not isinstance(pagina, int):
        raise ValueError("O número da página deve ser um número inteiro.")
    if pagina < 1:
        raise ValueError(f"O número da página deve ser maior ou igual a 1 (recebido: {pagina}).")

    if not isinstance(texto, str) or not texto.strip():
        raise ValueError("O texto a ser inserido não pode estar vazio.")

    if not isinstance(posicao, (tuple, list)) or len(posicao) != 2:
        raise ValueError("A posição deve ser uma tupla ou lista com exatamente 2 coordenadas (x, y).")

    for coord in posicao:
        if isinstance(coord, bool) or not isinstance(coord, (int, float)):
            raise ValueError(f"Cada coordenada da posição deve ser um número (recebido: {coord!r}).")
        if coord < 0:
            raise ValueError(f"As coordenadas da posição não podem ser negativas (recebido: {coord!r}).")

    if isinstance(tamanho, bool) or not isinstance(tamanho, (int, float)) or tamanho <= 0:
        raise ValueError(f"O tamanho da fonte deve ser maior que zero (recebido: {tamanho}).")

    # Resolução da cor
    cor_rgb: tuple[float, float, float]
    if isinstance(cor, str):
        cor_limpa = cor.lower().strip()
        if cor_limpa not in _CORES_TEXTO:
            raise ValueError(
                f"Cor inválida: '{cor}'. Cores aceitas: {sorted(_CORES_TEXTO.keys())}."
            )
        cor_rgb = _CORES_TEXTO[cor_limpa]
    elif isinstance(cor, (tuple, list)):
        if len(cor) != 3:
            raise ValueError("A tupla de cor RGB deve conter exatamente 3 valores (R, G, B).")
        valores = []
        for val in cor:
            if isinstance(val, bool) or not isinstance(val, (int, float)):
                raise ValueError(f"Componente de cor inválido: {val!r}.")
            if val < 0:
                raise ValueError(f"Componente de cor não pode ser negativo: {val}.")
            valores.append(float(val))
        # Normalização se estiver na escala 0-255
        if any(v > 1.0 for v in valores):
            if any(v > 255.0 for v in valores):
                raise ValueError("Os valores de cor RGB devem estar entre 0.0-1.0 ou 0-255.")
            cor_rgb = (valores[0] / 255.0, valores[1] / 255.0, valores[2] / 255.0)
        else:
            cor_rgb = (valores[0], valores[1], valores[2])
    else:
        raise ValueError("A cor deve ser uma string ou uma tupla RGB com 3 componentes.")

    # Resolução da fonte
    fonte_mupdf = _FONTES_MAP.get(fonte.lower().strip(), fonte)

    doc = abrir_pdf(pdf)
    try:
        if doc.needs_pass:
            raise ValueError("O documento está protegido por senha. Remova a senha antes de adicionar texto.")

        total_paginas = doc.page_count
        if total_paginas == 0:
            raise ValueError("O documento não possui páginas.")
        if pagina > total_paginas:
            raise ValueError(
                f"Página inválida: {pagina}. O documento possui {total_paginas} página(s) "
                f"(páginas permitidas: 1 a {total_paginas})."
            )

        page = doc[pagina - 1]

        if page.rotation % 180 == 90:
            largura_visual = page.rect.height
            altura_visual = page.rect.width
        else:
            largura_visual = page.rect.width
            altura_visual = page.rect.height

        x, y = posicao
        if x > largura_visual or y > altura_visual:
            raise ValueError(
                f"Posição ({x}, {y}) está fora dos limites visuais da página "
                f"(largura: {largura_visual}, altura: {altura_visual})."
            )

        ponto_vis = pymupdf.Point(x, y)
        ponto_phys = ponto_vis * page.derotation_matrix

        page.insert_text(
            ponto_phys,
            texto,
            fontsize=tamanho,
            fontname=fonte_mupdf,
            color=cor_rgb,
            morph=(ponto_phys, pymupdf.Matrix(page.rotation)),
        )

        caminho_final = saida if saida is not None else pdf
        if saida is not None and os.path.abspath(saida) != os.path.abspath(pdf):
            doc.save(saida)
        else:
            # Salvar no mesmo arquivo com segurança atômica
            dir_temp = os.path.dirname(os.path.abspath(pdf))
            with tempfile.NamedTemporaryFile(dir=dir_temp, delete=False, suffix=".pdf") as tmp:
                temp_name = tmp.name
            doc.save(temp_name)
            doc.close()
            shutil.move(temp_name, pdf)
            return pdf

        return caminho_final
    finally:
        if not doc.is_closed:
            doc.close()
