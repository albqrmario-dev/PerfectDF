import os
import shutil
import tempfile

import pymupdf

from perfectdf.comum import abrir_pdf, parsear_paginas


def pdf_para_imagens(
    caminho: str,
    pasta_saida: str,
    paginas: list[int] | str | None = None,
    dpi: int = 150,
    formato: str = "png",
) -> list[str]:
    """Converte páginas de um documento PDF em arquivos de imagem.

    Renderiza as páginas selecionadas (ou todas) e as salva com nomes padronizados
    (ex: 'pagina_001.png', 'pagina_002.png') no diretório de destino, criando a pasta
    caso ela não exista.

    Parâmetros:
        caminho: Caminho do arquivo PDF de origem.
        pasta_saida: Diretório onde as imagens serão salvas (criado automaticamente se inexistente).
        paginas: None para converter todas as páginas, string de páginas/intervalos (ex: '1-3, 5')
                 ou lista de inteiros (base 1).
        dpi: Resolução de renderização em pontos por polegada (entre 36 e 600, padrão 150).
        formato: Formato da imagem ('png' ou 'jpg', padrão 'png').

    Retorna:
        Lista ordenada de caminhos dos arquivos de imagem gerados.

    Lança:
        ValueError: Se caminhos forem inválidos, se o arquivo não existir, se pasta_saida
                    for um arquivo existente, se DPI estiver fora dos limites [36, 600],
                    se formato não for 'png' ou 'jpg', ou se alguma página for inválida.
    """
    if not isinstance(caminho, str) or not caminho.strip():
        raise ValueError(
            "O caminho do arquivo de origem deve ser uma string não vazia."
        )
    if not os.path.isfile(caminho):
        raise ValueError(f"O arquivo de origem não foi encontrado: '{caminho}'.")

    if not isinstance(pasta_saida, str) or not pasta_saida.strip():
        raise ValueError("O caminho da pasta de saída deve ser uma string não vazia.")
    if os.path.abspath(caminho) == os.path.abspath(pasta_saida):
        raise ValueError("A pasta de saída não pode ser igual ao arquivo de origem.")
    if os.path.isfile(pasta_saida):
        raise ValueError(
            f"O caminho de saída especificado é um arquivo existente, não uma pasta: '{pasta_saida}'."
        )

    if isinstance(dpi, bool) or not isinstance(dpi, int) or not (36 <= dpi <= 600):
        raise ValueError(
            f"O valor de DPI deve ser um número inteiro entre 36 e 600 (recebido: {dpi})."
        )

    if not isinstance(formato, str) or not formato.strip():
        raise ValueError("O formato de imagem deve ser uma string não vazia.")

    formato_limpo = formato.lower().strip()
    if formato_limpo == "png":
        extensao = "png"
    elif formato_limpo in ("jpg", "jpeg"):
        extensao = "jpg"
    else:
        raise ValueError(
            f"Formato de imagem inválido: '{formato}'. Formatos aceitos: 'png', 'jpg'."
        )

    os.makedirs(pasta_saida, exist_ok=True)

    doc = abrir_pdf(caminho)
    try:
        total_paginas = doc.page_count
        if total_paginas == 0:
            raise ValueError("O documento não possui páginas para conversão em imagem.")

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
            raise ValueError("A lista de páginas para conversão não pode estar vazia.")

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

        paginas_ordenadas = sorted(set(paginas_alvo))
        caminhos_gerados: list[str] = []

        for pagina in paginas_ordenadas:
            page = doc[pagina - 1]
            pix = page.get_pixmap(dpi=dpi)
            nome_arquivo = f"pagina_{pagina:03d}.{extensao}"
            caminho_imagem = os.path.join(pasta_saida, nome_arquivo)
            pix.save(caminho_imagem)
            caminhos_gerados.append(caminho_imagem)

        return caminhos_gerados
    finally:
        doc.close()


def imagens_para_pdf(imagens: list[str], saida: str) -> str:
    """Cria um documento PDF a partir de uma lista ordenada de arquivos de imagem.

    Cada imagem é inserida em uma página individual na ordem fornecida, mantendo as
    dimensões originais da imagem como o tamanho da respectiva página no PDF.

    Parâmetros:
        imagens: Lista de caminhos para os arquivos de imagem a serem incluídos.
        saida: Caminho do arquivo PDF resultante.

    Retorna:
        O caminho do arquivo PDF salvo.

    Lança:
        ValueError: Se a lista de imagens for vazia, se caminhos forem inválidos ou
                    coincidirem com a saída, se algum arquivo não existir ou não for uma
                    imagem válida e legível.
    """
    if not isinstance(saida, str) or not saida.strip():
        raise ValueError("O caminho do arquivo de saída deve ser uma string não vazia.")

    if not isinstance(imagens, (list, tuple)):
        raise ValueError(  # noqa: TRY004
            "A coleção de imagens deve ser fornecida em uma lista ou tupla."
        )
    if len(imagens) == 0:
        raise ValueError("A lista de imagens não pode estar vazia.")

    dimensoes: list[tuple[float, float]] = []
    for img in imagens:
        if not isinstance(img, str) or not img.strip():
            raise ValueError("O caminho da imagem deve ser uma string não vazia.")
        if not os.path.isfile(img):
            raise ValueError(f"O arquivo de imagem não foi encontrado: '{img}'.")
        if os.path.abspath(img) == os.path.abspath(saida):
            raise ValueError(
                "O arquivo de saída não pode ser igual a um dos arquivos de imagem de origem."
            )
        try:
            pix = pymupdf.Pixmap(img)
            dimensoes.append((float(pix.width), float(pix.height)))
            del pix
        except Exception as e:
            raise ValueError(
                f"O arquivo '{img}' não é uma imagem válida ou legível."
            ) from e

    doc = pymupdf.open()
    try:
        for img, (largura, altura) in zip(imagens, dimensoes):
            page = doc.new_page(width=largura, height=altura)
            rect = pymupdf.Rect(0, 0, largura, altura)
            page.insert_image(rect, filename=img)

        doc.save(saida)
        return saida
    finally:
        doc.close()


def adicionar_imagem(
    pdf: str,
    pagina: int,
    imagem: str,
    posicao: tuple[float, float] = (50, 50),
    tamanho: tuple[float, float] | float | None = None,
    saida: str | None = None,
) -> str:
    """Insere uma imagem em uma página específica de um documento PDF.

    Parâmetros:
        pdf: Caminho do arquivo PDF de origem.
        pagina: Número da página onde a imagem será inserida (base 1).
        imagem: Caminho do arquivo de imagem (PNG, JPG, etc.).
        posicao: Coordenadas (x, y) no espaço visual da página (canto superior esquerdo como origem).
        tamanho: Tupla (largura, altura) em pontos tipográficos, ou número float indicando a largura
                 (com altura calculada proporcionalmente ao aspecto original), ou None para usar as
                 dimensões originais da imagem.
        saida: Caminho do arquivo PDF salvo. Se None, modifica o próprio arquivo original.

    Retorna:
        Caminho do arquivo PDF salvo.

    Lança:
        ValueError: Se caminhos forem inválidos, se arquivos não existirem, se a imagem for inválida,
                    se a página estiver fora dos limites, se posição for negativa ou fora dos limites,
                    se tamanho for menor ou igual a zero, ou se o PDF estiver protegido por senha.
    """
    if not isinstance(pdf, str) or not pdf.strip():
        raise ValueError(
            "O caminho do arquivo de origem deve ser uma string não vazia."
        )
    if not os.path.isfile(pdf):
        raise ValueError(f"O arquivo de origem não foi encontrado: '{pdf}'.")

    if not isinstance(imagem, str) or not imagem.strip():
        raise ValueError("O caminho da imagem deve ser uma string não vazia.")
    if not os.path.isfile(imagem):
        raise ValueError(f"O arquivo de imagem não foi encontrado: '{imagem}'.")

    if saida is not None and (not isinstance(saida, str) or not saida.strip()):
        raise ValueError("O caminho do arquivo de saída deve ser uma string não vazia.")

    if isinstance(pagina, bool) or not isinstance(pagina, int):
        raise ValueError("O número da página deve ser um número inteiro.")  # noqa: TRY004
    if pagina < 1:
        raise ValueError(
            f"O número da página deve ser maior ou igual a 1 (recebido: {pagina})."
        )

    if not isinstance(posicao, (tuple, list)) or len(posicao) != 2:
        raise ValueError(
            "A posição deve ser uma tupla ou lista com exatamente 2 coordenadas (x, y)."
        )

    for coord in posicao:
        if isinstance(coord, bool) or not isinstance(coord, (int, float)):
            raise ValueError(  # noqa: TRY004
                f"Cada coordenada da posição deve ser um número (recebido: {coord!r})."
            )
        if coord < 0:
            raise ValueError(
                f"As coordenadas da posição não podem ser negativas (recebido: {coord!r})."
            )

    # Validar e abrir a imagem para extrair dimensões
    try:
        pix = pymupdf.Pixmap(imagem)
        img_largura_orig = float(pix.width)
        img_altura_orig = float(pix.height)
        del pix
    except Exception as e:
        raise ValueError(
            f"O arquivo '{imagem}' não é uma imagem válida ou legível."
        ) from e

    # Resolução de dimensões da imagem a ser inserida
    if tamanho is None:
        largura, altura = img_largura_orig, img_altura_orig
    elif isinstance(tamanho, (tuple, list)):
        if len(tamanho) != 2:
            raise ValueError(
                "O tamanho deve conter exatamente 2 valores (largura, altura)."
            )
        for val in tamanho:
            if isinstance(val, bool) or not isinstance(val, (int, float)) or val <= 0:
                raise ValueError(
                    f"As dimensões de tamanho devem ser números maiores que zero (recebido: {val!r})."
                )
        largura, altura = float(tamanho[0]), float(tamanho[1])
    elif isinstance(tamanho, (int, float)) and not isinstance(tamanho, bool):
        if tamanho <= 0:
            raise ValueError(
                f"A largura informada deve ser maior que zero (recebido: {tamanho})."
            )
        largura = float(tamanho)
        proporcao = img_altura_orig / img_largura_orig
        altura = largura * proporcao
    else:
        raise ValueError(
            "O tamanho deve ser uma tupla (largura, altura) ou um número positivo."
        )

    doc = abrir_pdf(pdf)
    try:
        if doc.needs_pass:
            raise ValueError(
                "O documento está protegido por senha. Remova a senha antes de adicionar imagens."
            )

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

        p1 = pymupdf.Point(x, y) * page.derotation_matrix
        p2 = pymupdf.Point(x + largura, y + altura) * page.derotation_matrix
        rect_phys = pymupdf.Rect(p1, p2).normalize()

        page.insert_image(rect_phys, filename=imagem, rotate=page.rotation)

        caminho_final = saida if saida is not None else pdf
        if saida is not None and os.path.abspath(saida) != os.path.abspath(pdf):
            doc.save(saida)
        else:
            dir_temp = os.path.dirname(os.path.abspath(pdf))
            with tempfile.NamedTemporaryFile(
                dir=dir_temp, delete=False, suffix=".pdf"
            ) as tmp:
                temp_name = tmp.name
            doc.save(temp_name)
            doc.close()
            shutil.move(temp_name, pdf)
            return pdf

        return caminho_final
    finally:
        if not doc.is_closed:
            doc.close()
