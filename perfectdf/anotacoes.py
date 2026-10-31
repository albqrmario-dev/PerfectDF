import os
import string

import pymupdf

from perfectdf.comum import abrir_pdf, parsear_paginas


def adicionar_marca_dagua(
    caminho: str,
    saida: str,
    texto: str,
    paginas: list[int] | str | None = None,
    opacidade: float = 0.3,
    angulo: float = 45,
    tamanho_fonte: float = 48,
) -> str:
    """Adiciona uma marca d'água de texto diagonal, centralizada e translúcida às páginas de um PDF.

    Parâmetros:
        caminho: Caminho do arquivo PDF de origem.
        saida: Caminho do arquivo PDF resultante.
        texto: Texto da marca d'água a ser inserido.
        paginas: None para todas as páginas, string de páginas/intervalos (ex: '1-3, 5')
                 ou lista de inteiros (base 1).
        opacidade: Opacidade do texto entre 0.0 (invisível) e 1.0 (opaco). Padrão é 0.3.
        angulo: Ângulo da marca d'água em graus no sentido anti-horário (padrão 45).
        tamanho_fonte: Tamanho da fonte em pontos tipográficos (deve ser > 0, padrão 48).

    Retorna:
        O caminho do arquivo salvo.

    Lança:
        ValueError: Se caminhos forem inválidos ou iguais, texto vazio, opacidade, ângulo ou
                    tamanho_fonte fora dos limites permitidos, ou se alguma página for inválida.
    """
    if not isinstance(caminho, str) or not caminho.strip():
        raise ValueError(
            "O caminho do arquivo de origem deve ser uma string não vazia."
        )
    if not isinstance(saida, str) or not saida.strip():
        raise ValueError("O caminho do arquivo de saída deve ser uma string não vazia.")
    if os.path.abspath(caminho) == os.path.abspath(saida):
        raise ValueError(
            "O arquivo de saída não pode ser igual ao arquivo de origem para evitar sobrescrever o documento original."
        )
    if not os.path.isfile(caminho):
        raise ValueError(f"O arquivo de origem não foi encontrado: '{caminho}'.")

    if not isinstance(texto, str) or not texto.strip():
        raise ValueError("O texto da marca d'água deve ser uma string não vazia.")

    if (
        isinstance(opacidade, bool)
        or not isinstance(opacidade, (int, float))
        or not (0.0 <= opacidade <= 1.0)
    ):
        raise ValueError(
            f"A opacidade deve ser um número entre 0 e 1 (recebido: {opacidade})."
        )

    if (
        isinstance(tamanho_fonte, bool)
        or not isinstance(tamanho_fonte, (int, float))
        or tamanho_fonte <= 0
    ):
        raise ValueError(
            f"O tamanho da fonte deve ser um número maior que zero (recebido: {tamanho_fonte})."
        )

    if isinstance(angulo, bool) or not isinstance(angulo, (int, float)):
        raise ValueError(f"O valor do ângulo deve ser um número (recebido: {angulo}).")

    doc = abrir_pdf(caminho)
    try:
        total_paginas = doc.page_count
        if total_paginas == 0:
            raise ValueError(
                "O documento não possui páginas para adicionar marca d'água."
            )

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
                "A lista de páginas para aplicação da marca d'água não pode estar vazia."
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

        largura_texto = pymupdf.get_text_length(
            texto, fontname="helv", fontsize=tamanho_fonte
        )

        for pagina in set(paginas_alvo):
            page = doc[pagina - 1]
            vis_centro = pymupdf.Point(page.rect.width / 2, page.rect.height / 2)
            phys_centro = vis_centro * page.derotation_matrix

            angulo_mupdf = page.rotation - angulo
            ponto_base = pymupdf.Point(
                phys_centro.x - largura_texto / 2,
                phys_centro.y + tamanho_fonte * 0.35,
            )

            page.insert_text(
                ponto_base,
                texto,
                fontsize=tamanho_fonte,
                fontname="helv",
                morph=(phys_centro, pymupdf.Matrix(angulo_mupdf)),
                fill_opacity=opacidade,
            )

        doc.save(saida)
        return saida
    finally:
        doc.close()


def numerar_paginas(
    caminho: str,
    saida: str,
    formato: str = "Página {n} de {total}",
    posicao: str = "rodape-centro",
    inicio: int = 1,
    paginas: list[int] | str | None = None,
    tamanho_fonte: float = 10,
) -> str:
    """Adiciona numeração às páginas de um documento PDF.

    Parâmetros:
        caminho: Caminho do arquivo PDF de origem.
        saida: Caminho do arquivo PDF resultante.
        formato: Padrão textual da numeração contendo os marcadores '{n}' (número da página atual)
                 e/ou '{total}'. Quando 'paginas' for informado, '{total}' representa a quantidade
                 total de páginas selecionadas para numeração, e não o total absoluto de páginas
                 do documento. Se 'paginas' for None, '{total}' corresponde ao total de páginas do PDF.
        posicao: Alinhamento da numeração na página. Opções aceitas: 'rodape-centro',
                 'rodape-direita', 'rodape-esquerda', 'topo-centro', 'topo-direita', 'topo-esquerda'.
        inicio: Valor inicial para a contagem {n} (padrão é 1).
        paginas: None para numerar todas as páginas, string de páginas/intervalos (ex: '1-3, 5')
                 ou lista de inteiros (base 1). As páginas selecionadas são numeradas
                 sequencialmente a partir de 'inicio'.
        tamanho_fonte: Tamanho da fonte em pontos tipográficos (> 0, padrão 10).

    Retorna:
        O caminho do arquivo salvo.

    Lança:
        ValueError: Se caminhos forem inválidos ou iguais, se o formato contiver placeholders
                    desconhecidos ou for malformado, se a posição for desconhecida,
                    se inicio não for int, se tamanho_fonte <= 0, ou se alguma página for inválida.
    """
    if not isinstance(caminho, str) or not caminho.strip():
        raise ValueError(
            "O caminho do arquivo de origem deve ser uma string não vazia."
        )
    if not isinstance(saida, str) or not saida.strip():
        raise ValueError("O caminho do arquivo de saída deve ser uma string não vazia.")
    if os.path.abspath(caminho) == os.path.abspath(saida):
        raise ValueError(
            "O arquivo de saída não pode ser igual ao arquivo de origem para evitar sobrescrever o documento original."
        )
    if not os.path.isfile(caminho):
        raise ValueError(f"O arquivo de origem não foi encontrado: '{caminho}'.")

    if not isinstance(formato, str) or not formato.strip():
        raise ValueError("O formato de numeração deve ser uma string não vazia.")

    try:
        parsed_format = list(string.Formatter().parse(formato))
    except ValueError as e:
        raise ValueError(f"Formato de numeração malformado: '{formato}'.") from e

    campos = [field for _, field, _, _ in parsed_format if field is not None]
    for campo in campos:
        nome_campo = campo.split(":")[0].split(".")[0]
        if nome_campo not in ("n", "total"):
            raise ValueError(
                f"Placeholder desconhecido no formato: '{campo}'. "
                "Os placeholders permitidos são '{n}' e '{total}'."
            )

    posicoes_validas = {
        "rodape-centro",
        "rodape-direita",
        "rodape-esquerda",
        "topo-centro",
        "topo-direita",
        "topo-esquerda",
    }
    if not isinstance(posicao, str) or posicao not in posicoes_validas:
        raise ValueError(
            f"Posição inválida: '{posicao}'. As posições aceitas são: {sorted(posicoes_validas)}."
        )

    if isinstance(inicio, bool) or not isinstance(inicio, int):
        raise ValueError("O valor de início da numeração deve ser um número inteiro.")

    if (
        isinstance(tamanho_fonte, bool)
        or not isinstance(tamanho_fonte, (int, float))
        or tamanho_fonte <= 0
    ):
        raise ValueError(
            f"O tamanho da fonte deve ser um número maior que zero (recebido: {tamanho_fonte})."
        )

    doc = abrir_pdf(caminho)
    try:
        total_paginas = doc.page_count
        if total_paginas == 0:
            raise ValueError("O documento não possui páginas para numeração.")

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
            raise ValueError("A lista de páginas para numeração não pode estar vazia.")

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
        total_selecionadas = len(paginas_ordenadas)

        margem_x = 36.0
        margem_y = 36.0

        for i, num_pagina in enumerate(paginas_ordenadas):
            n = inicio + i
            texto_formatado = formato.format(n=n, total=total_selecionadas)
            largura_texto = pymupdf.get_text_length(
                texto_formatado, fontname="helv", fontsize=tamanho_fonte
            )

            page = doc[num_pagina - 1]
            largura_pagina = page.rect.width
            altura_pagina = page.rect.height

            if "esquerda" in posicao:
                x_vis = margem_x
            elif "direita" in posicao:
                x_vis = largura_pagina - margem_x - largura_texto
            else:  # centro
                x_vis = (largura_pagina - largura_texto) / 2.0

            if "topo" in posicao:
                y_vis = margem_y + tamanho_fonte
            else:  # rodape
                y_vis = altura_pagina - margem_y

            ponto_vis = pymupdf.Point(x_vis, y_vis)
            ponto_phys = ponto_vis * page.derotation_matrix

            page.insert_text(
                ponto_phys,
                texto_formatado,
                fontsize=tamanho_fonte,
                fontname="helv",
                morph=(ponto_phys, pymupdf.Matrix(page.rotation)),
            )

        doc.save(saida)
        return saida
    finally:
        doc.close()


def destacar_texto(
    caminho: str,
    saida: str,
    termo: str,
    paginas: list[int] | str | None = None,
    tipo: str = "destaque",
    cor: str | tuple = "amarelo",
    ignorar_maiusculas: bool = True,
) -> dict:
    """Busca um termo de texto em um documento PDF e adiciona anotações de destaque nas ocorrências encontradas.

    Limitação conhecida: termos quebrados entre duas linhas (com hifenização ou sem)
    podem não ser encontrados, pois a busca opera sobre os blocos de texto extraídos
    página a página pelo PyMuPDF.

    Parâmetros:
        caminho: Caminho do arquivo PDF de origem.
        saida: Caminho do arquivo PDF resultante. Gerado apenas quando há ocorrências.
        termo: Texto a ser buscado e destacado.
        paginas: None para buscar em todas as páginas, string de páginas/intervalos
                 (ex: '1-3, 5') ou lista de inteiros (base 1).
        tipo: Tipo da anotação — 'destaque' (marca-texto), 'sublinhado' ou 'riscado'.
        cor: Nome da cor ('amarelo', 'verde', 'azul', 'rosa', 'laranja', 'vermelho') ou
             tupla RGB com três valores entre 0.0 e 1.0 (ex: (1.0, 0.5, 0.0)).
        ignorar_maiusculas: Se True (padrão), a busca é insensível a maiúsculas/minúsculas.
                            Se False, somente ocorrências com grafia exata são destacadas.

    Retorna:
        Dicionário com as chaves:
        - 'total_ocorrencias': número total de ocorrências encontradas e anotadas.
        - 'ocorrencias_por_pagina': dicionário {numero_pagina: contagem} em base 1.
        - 'aviso' (opcional): mensagem de alerta quando nenhuma ocorrência é encontrada
          por ausência de camada de texto (PDF possivelmente escaneado), com sugestão de OCR.
        O arquivo de saída só é gerado quando total_ocorrencias > 0.

    Lança:
        ValueError: Se caminhos forem inválidos ou iguais, se o arquivo não existir,
                    se o termo for vazio, se o tipo ou cor forem inválidos,
                    se alguma página for inválida ou se o PDF estiver protegido por senha.
    """
    _CORES = {
        "amarelo":  (1.0, 1.0, 0.0),
        "verde":    (0.0, 0.8, 0.0),
        "azul":     (0.0, 0.5, 1.0),
        "rosa":     (1.0, 0.4, 0.7),
        "laranja":  (1.0, 0.5, 0.0),
        "vermelho": (1.0, 0.0, 0.0),
    }
    _TIPOS_VALIDOS = {"destaque", "sublinhado", "riscado"}

    if not isinstance(caminho, str) or not caminho.strip():
        raise ValueError(
            "O caminho do arquivo de origem deve ser uma string não vazia."
        )
    if not isinstance(saida, str) or not saida.strip():
        raise ValueError("O caminho do arquivo de saída deve ser uma string não vazia.")
    if os.path.abspath(caminho) == os.path.abspath(saida):
        raise ValueError(
            "O arquivo de saída não pode ser igual ao arquivo de origem para evitar sobrescrever o documento original."
        )
    if not os.path.isfile(caminho):
        raise ValueError(f"O arquivo de origem não foi encontrado: '{caminho}'.")

    if not isinstance(termo, str) or not termo.strip():
        raise ValueError("O termo de busca deve ser uma string não vazia.")

    if not isinstance(tipo, str) or tipo not in _TIPOS_VALIDOS:
        raise ValueError(
            f"Tipo de anotação inválido: '{tipo}'. Tipos aceitos: {sorted(_TIPOS_VALIDOS)}."
        )

    cor_rgb: tuple[float, float, float]
    if isinstance(cor, str):
        if cor not in _CORES:
            raise ValueError(
                f"Cor inválida: '{cor}'. Cores aceitas: {sorted(_CORES)}."
            )
        cor_rgb = _CORES[cor]
    elif isinstance(cor, tuple):
        if len(cor) != 3:
            raise ValueError(
                "A cor em tupla RGB deve ter exatamente 3 componentes (R, G, B)."
            )
        for i, componente in enumerate(cor):
            if (
                isinstance(componente, bool)
                or not isinstance(componente, (int, float))
                or not (0.0 <= componente <= 1.0)
            ):
                raise ValueError(
                    f"Cada componente da cor deve ser um número entre 0.0 e 1.0 "
                    f"(componente {i} inválido: {componente!r})."
                )
        cor_rgb = (float(cor[0]), float(cor[1]), float(cor[2]))
    else:
        raise ValueError(
            "A cor deve ser um nome em string ou uma tupla RGB com valores entre 0.0 e 1.0."
        )

    doc = abrir_pdf(caminho)
    try:
        if doc.needs_pass:
            raise ValueError(
                "O documento está protegido por senha. Remova a senha antes de destacar texto."
            )

        total_paginas = doc.page_count

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
                "A lista de páginas para busca e destaque não pode estar vazia."
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

        total_ocorrencias = 0
        ocorrencias_por_pagina: dict[int, int] = {}
        paginas_unicas = sorted(set(paginas_alvo))

        total_caracteres_examinados = 0

        for pagina in paginas_unicas:
            page = doc[pagina - 1]
            total_caracteres_examinados += len(page.get_text().strip())

            retangulos_raw = page.search_for(termo)
            if not ignorar_maiusculas:
                retangulos = [
                    rect
                    for rect in retangulos_raw
                    if page.get_text("text", clip=rect).strip() == termo
                ]
            else:
                retangulos = retangulos_raw

            qtd = len(retangulos)
            if qtd > 0:
                ocorrencias_por_pagina[pagina] = qtd
                total_ocorrencias += qtd

                for rect in retangulos:
                    if tipo == "destaque":
                        annot = page.add_highlight_annot(rect)
                    elif tipo == "sublinhado":
                        annot = page.add_underline_annot(rect)
                    else:  # riscado
                        annot = page.add_strikeout_annot(rect)

                    annot.set_colors(stroke=cor_rgb)
                    annot.update()

        resultado: dict = {
            "total_ocorrencias": total_ocorrencias,
            "ocorrencias_por_pagina": ocorrencias_por_pagina,
        }

        if total_ocorrencias == 0 and total_caracteres_examinados == 0:
            resultado["aviso"] = (
                "Nenhum texto detectável foi encontrado nas páginas pesquisadas. "
                "O documento pode ser um PDF escaneado (sem texto selecionável). "
                "Considere utilizar OCR antes de buscar texto."
            )

        if total_ocorrencias > 0:
            doc.save(saida)

        return resultado
    finally:
        doc.close()


def adicionar_nota(
    caminho: str,
    saida: str,
    pagina: int,
    texto: str,
    posicao: tuple[float, float] = (50, 50),
) -> str:
    """Adiciona uma anotação pop-up do tipo 'nota' (post-it) a uma página específica de um PDF.

    A anotação é inserida na coordenada visual especificada e seu ícone é exibido
    corretamente independentemente da rotação da página.

    Parâmetros:
        caminho: Caminho do arquivo PDF de origem.
        saida: Caminho do arquivo PDF resultante.
        pagina: Número da página onde a nota será inserida (base 1).
        texto: Conteúdo textual da anotação.
        posicao: Tupla (x, y) em pontos tipográficos no espaço visual da página,
                 com origem no canto superior esquerdo. Padrão: (50, 50).

    Retorna:
        O caminho do arquivo salvo.

    Lança:
        ValueError: Se caminhos forem inválidos ou iguais, se o arquivo não existir,
                    se a página for inválida, se o texto for vazio, se a posição
                    contiver valores inválidos ou estiver fora dos limites da página,
                    ou se o PDF estiver protegido por senha.
    """
    if not isinstance(caminho, str) or not caminho.strip():
        raise ValueError(
            "O caminho do arquivo de origem deve ser uma string não vazia."
        )
    if not isinstance(saida, str) or not saida.strip():
        raise ValueError("O caminho do arquivo de saída deve ser uma string não vazia.")
    if os.path.abspath(caminho) == os.path.abspath(saida):
        raise ValueError(
            "O arquivo de saída não pode ser igual ao arquivo de origem para evitar sobrescrever o documento original."
        )
    if not os.path.isfile(caminho):
        raise ValueError(f"O arquivo de origem não foi encontrado: '{caminho}'.")

    if isinstance(pagina, bool) or not isinstance(pagina, int):
        raise ValueError("O número da página deve ser um número inteiro.")
    if pagina < 1:
        raise ValueError(
            f"O número da página deve ser maior ou igual a 1 (recebido: {pagina})."
        )

    if not isinstance(texto, str) or not texto.strip():
        raise ValueError("O texto da nota deve ser uma string não vazia.")

    if not isinstance(posicao, tuple) or len(posicao) != 2:
        raise ValueError(
            "A posição deve ser uma tupla com exatamente 2 valores (x, y)."
        )
    for coord in posicao:
        if isinstance(coord, bool) or not isinstance(coord, (int, float)):
            raise ValueError(
                f"Cada coordenada da posição deve ser um número (recebido: {coord!r})."
            )
        if coord < 0:
            raise ValueError(
                f"As coordenadas de posição não podem ser negativas (recebido: {coord!r})."
            )

    doc = abrir_pdf(caminho)
    try:
        if doc.needs_pass:
            raise ValueError(
                "O documento está protegido por senha. Remova a senha antes de adicionar notas."
            )

        total_paginas = doc.page_count
        if pagina > total_paginas:
            raise ValueError(
                f"Página inválida: {pagina}. O documento possui {total_paginas} página(s) "
                f"(páginas permitidas: 1 a {total_paginas})."
            )

        page = doc[pagina - 1]

        # Dimensões visuais da página levando em conta a rotação
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

        # Converter coordenadas visuais para espaço físico do PDF
        ponto_vis = pymupdf.Point(x, y)
        ponto_phys = ponto_vis * page.derotation_matrix

        annot = page.add_text_annot(ponto_phys, texto)
        annot.update()

        doc.save(saida)
        return saida
    finally:
        doc.close()
