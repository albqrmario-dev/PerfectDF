import os
import warnings

import pymupdf


def abrir_pdf(caminho):
    return pymupdf.open(caminho)


def juntar_pdfs(caminhos, saida):
    """Junta dois ou mais PDF's e os retorna."""

    doc = pymupdf.open()

    for caminho in caminhos:
        doc.insert_pdf(abrir_pdf(caminho))

    doc.save(saida)
    return saida


def parsear_paginas(texto: str) -> list[int]:
    """
    Converte uma string de páginas (ex: '1-3,5,7-9') em uma lista ordenada e sem duplicatas (base 1).
    Trata números avulsos, intervalos normais e invertidos, desconsiderando espaços
    extras e eliminando repetições.
    """

    if not isinstance(texto, str):
        raise ValueError("A especificação de páginas deve ser uma string.")  # noqa: TRY004

    texto_limpo = texto.strip()
    if not texto_limpo:
        raise ValueError("A especificação de páginas não pode estar vazia.")

    paginas = set()
    partes = texto_limpo.split(",")

    for parte in partes:
        item = parte.strip()
        if not item:
            raise ValueError(
                f"Trecho vazio encontrado na especificação de páginas: '{texto}'."
            )

        if "-" in item:
            subpartes = item.split("-")
            if len(subpartes) != 2:
                raise ValueError(
                    f"Intervalo malformado: '{item}'. Formato esperado: 'início-fim'."
                )

            inicio_str = subpartes[0].strip()
            fim_str = subpartes[1].strip()

            if not inicio_str or not fim_str:
                raise ValueError(
                    f"Intervalo incompleto: '{item}'. Formato esperado: 'início-fim'."
                )

            try:
                inicio = int(inicio_str)
                fim = int(fim_str)
            except ValueError:
                raise ValueError(f"Intervalo contém valores não numéricos: '{item}'.")

            if inicio < 1 or fim < 1:
                raise ValueError(
                    f"Os números de página no intervalo devem ser maiores ou iguais a 1: '{item}'."
                )

            if inicio <= fim:
                paginas.update(range(inicio, fim + 1))
            else:
                paginas.update(range(fim, inicio + 1))
        else:
            try:
                num = int(item)
            except ValueError:
                raise ValueError(
                    f"Página inválida (não é um número inteiro): '{item}'."
                )

            if num < 1:
                raise ValueError(
                    f"O número da página deve ser maior ou igual a 1 (recebido: {num})."
                )

            paginas.add(num)

    return sorted(paginas)


def extrair_paginas(caminho: str, paginas: list[int], saida: str) -> str:
    """Extrai páginas selecionadas de um PDF de origem e as salva em um novo arquivo na ordem informada.

    Valida se as páginas existem no documento, monta o novo PDF permitindo repetições intencionais
    e fecha todos os documentos abertos ao finalizar.
    """
    if not paginas:
        raise ValueError("A lista de páginas a serem extraídas não pode estar vazia.")

    doc_origem = abrir_pdf(caminho)
    try:
        doc_saida = pymupdf.open()
        try:
            total_paginas = doc_origem.page_count
            for pagina in paginas:
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

            for pagina in paginas:
                doc_saida.insert_pdf(
                    doc_origem, from_page=pagina - 1, to_page=pagina - 1
                )

            doc_saida.save(saida)
            return saida
        finally:
            doc_saida.close()
    finally:
        doc_origem.close()


def girar_paginas(caminho: str, paginas: list[int], graus: int, saida: str) -> str:
    """Gira as páginas selecionadas de um documento PDF e salva o resultado em um novo arquivo.

    Soma o ângulo informado à rotação atual de cada página selecionada ((rotação + graus) % 360).
    As páginas não listadas permanecem inalteradas.

    Parâmetros:
        caminho: Caminho do arquivo PDF de origem.
        paginas: Lista de números de páginas (base 1) a serem rotacionadas.
        graus: Ângulo de rotação em graus (deve ser múltiplo de 90, ex: 90, 180, 270, -90).
        saida: Caminho do arquivo PDF resultante.

    Retorna:
        O caminho do arquivo salvo.

    Lança:
        ValueError: Se caminhos forem iguais/inválidos, graus não for múltiplo de 90,
                    ou qualquer página estiver fora dos limites do documento.
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

    if isinstance(graus, bool) or not isinstance(graus, int):
        raise ValueError("O valor de rotação (graus) deve ser um número inteiro.")
    if graus % 90 != 0:
        raise ValueError(
            f"O valor de rotação deve ser um múltiplo de 90 graus (recebido: {graus})."
        )

    if not isinstance(paginas, (list, tuple)) or not paginas:
        raise ValueError(
            "A lista de páginas a serem rotacionadas não pode estar vazia."
        )

    doc = abrir_pdf(caminho)
    try:
        total_paginas = doc.page_count
        for pagina in paginas:
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

        for pagina in set(paginas):
            page = doc[pagina - 1]
            page.set_rotation((page.rotation + graus) % 360)

        doc.save(saida)
        return saida
    finally:
        doc.close()


def excluir_paginas(caminho: str, paginas: list[int], saida: str) -> str:
    """Exclui páginas selecionadas de um documento PDF e salva o resultado em um novo arquivo.

    Remove as páginas informadas utilizando a base 1 do usuário. Lança exceção se qualquer página
    não existir no documento ou se a exclusão resultar em um documento com 0 páginas.

    Parâmetros:
        caminho: Caminho do arquivo PDF de origem.
        paginas: Lista de números de páginas (base 1) a serem excluídas.
        saida: Caminho do arquivo PDF resultante.

    Retorna:
        O caminho do arquivo salvo.

    Lança:
        ValueError: Se caminhos forem iguais/inválidos, se alguma página não existir,
                    se a lista de páginas for inválida ou se a exclusão deixar o PDF com 0 páginas.
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

    if not isinstance(paginas, (list, tuple)) or not paginas:
        raise ValueError("A lista de páginas a serem excluídas não pode estar vazia.")

    doc = abrir_pdf(caminho)
    try:
        total_paginas = doc.page_count
        for pagina in paginas:
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

        paginas_unicas = set(paginas)
        if len(paginas_unicas) >= total_paginas:
            raise ValueError(
                "A exclusão não pode ser realizada porque deixaria o PDF com 0 páginas."
            )

        indices_para_excluir = sorted(p - 1 for p in paginas_unicas)
        doc.delete_pages(indices_para_excluir)

        doc.save(saida)
        return saida
    finally:
        doc.close()


def parsear_ordem(texto: str) -> list[int]:
    """Converte uma string de páginas/intervalos em uma lista de páginas preservando a ordem especificada.

    Diferente de parsear_paginas, esta função não ordena nem remove repetições intencionais.
    Suporta páginas avulsas (ex: '3, 1, 2') e intervalos normais ou decrescentes (ex: '1-3' -> [1, 2, 3] ou '3-1' -> [3, 2, 1]).

    Parâmetros:
        texto: String contendo a sequência desejada de páginas.

    Retorna:
        Lista de inteiros (base 1) na ordem especificada.

    Lança:
        ValueError: Se a especificação for inválida, vazia ou contiver valores menores que 1.
    """
    if not isinstance(texto, str):
        raise ValueError("A especificação de ordem deve ser uma string.")

    texto_limpo = texto.strip()
    if not texto_limpo:
        raise ValueError("A especificação de ordem não pode estar vazia.")

    paginas: list[int] = []
    partes = texto_limpo.split(",")

    for parte in partes:
        item = parte.strip()
        if not item:
            raise ValueError(
                f"Trecho vazio encontrado na especificação de ordem: '{texto}'."
            )

        if "-" in item:
            subpartes = item.split("-")
            if len(subpartes) != 2:
                raise ValueError(
                    f"Intervalo malformado: '{item}'. Formato esperado: 'início-fim'."
                )

            inicio_str = subpartes[0].strip()
            fim_str = subpartes[1].strip()

            if not inicio_str or not fim_str:
                raise ValueError(
                    f"Intervalo incompleto: '{item}'. Formato esperado: 'início-fim'."
                )

            try:
                inicio = int(inicio_str)
                fim = int(fim_str)
            except ValueError:
                raise ValueError(f"Intervalo contém valores não numéricos: '{item}'.")

            if inicio < 1 or fim < 1:
                raise ValueError(
                    f"Os números de página no intervalo devem ser maiores ou iguais a 1: '{item}'."
                )

            if inicio <= fim:
                paginas.extend(range(inicio, fim + 1))
            else:
                paginas.extend(range(inicio, fim - 1, -1))
        else:
            try:
                num = int(item)
            except ValueError:
                raise ValueError(
                    f"Página inválida (não é um número inteiro): '{item}'."
                )

            if num < 1:
                raise ValueError(
                    f"O número da página deve ser maior ou igual a 1 (recebido: {num})."
                )

            paginas.append(num)

    return paginas


def reordenar_paginas(caminho: str, ordem: str | list[int], saida: str) -> str:
    """Reordena as páginas de um documento PDF conforme a sequência informada e salva em um novo arquivo.

    A ordem pode ser fornecida como string (ex: '3, 1, 2' ou '3, 1-2') ou como lista de inteiros.
    Se a ordem informada não incluir todas as páginas do documento original, as páginas omitidas
    ficarão de fora do documento resultante. Reaproveita a função extrair_paginas para evitar
    duplicação da lógica de montagem do PDF.

    Parâmetros:
        caminho: Caminho do arquivo PDF de origem.
        ordem: String com a ordem/intervalos ou lista de inteiros (base 1).
        saida: Caminho do arquivo PDF resultante.

    Retorna:
        O caminho do arquivo salvo.

    Lança:
        ValueError: Se caminhos forem iguais/inválidos, se a ordem for inválida ou
                    contiver páginas inexistentes no documento de origem.
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

    if isinstance(ordem, str):
        paginas = parsear_ordem(ordem)
    elif isinstance(ordem, (list, tuple)):
        paginas = list(ordem)
    else:
        raise ValueError(
            "A especificação de ordem deve ser uma string ou lista de inteiros."
        )

    if not paginas:
        raise ValueError("A lista de páginas a serem reordenadas não pode estar vazia.")

    return extrair_paginas(caminho, paginas, saida)


def ler_metadados(caminho: str) -> dict:
    """Lê os metadados de um documento PDF.

    Parâmetros:
        caminho: Caminho do arquivo PDF.

    Retorna:
        Dicionário contendo os metadados do documento (ex: title, author, subject, keywords).

    Lança:
        ValueError: Se o caminho for inválido ou o arquivo não for encontrado.
    """
    if not isinstance(caminho, str) or not caminho.strip():
        raise ValueError("O caminho do arquivo deve ser uma string não vazia.")
    if not os.path.isfile(caminho):
        raise ValueError(f"O arquivo não foi encontrado: '{caminho}'.")

    doc = abrir_pdf(caminho)
    try:
        return dict(doc.metadata)
    finally:
        doc.close()


def editar_metadados(caminho: str, novos: dict[str, str], saida: str) -> str:
    """Edita os metadados de um documento PDF e salva o resultado em um novo arquivo.

    Permite a edição exclusiva dos campos conhecidos: 'title', 'author', 'subject' e 'keywords'.
    Chaves desconhecidas são rejeitadas com ValueError para prevenir erros de digitação.

    Parâmetros:
        caminho: Caminho do arquivo PDF de origem.
        novos: Dicionário com os novos metadados a serem aplicados.
        saida: Caminho do arquivo PDF resultante.

    Retorna:
        O caminho do arquivo salvo.

    Lança:
        ValueError: Se caminhos forem iguais/inválidos, se novos não for um dicionário,
                    se contiver chaves não permitidas ou valores que não sejam strings.
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

    if not isinstance(novos, dict):
        raise ValueError("Os novos metadados devem ser fornecidos em um dicionário.")

    chaves_permitidas = {"title", "author", "subject", "keywords"}
    chaves_invalidas = set(novos.keys()) - chaves_permitidas
    if chaves_invalidas:
        raise ValueError(
            f"Chave(s) de metadados não permitida(s): {sorted(chaves_invalidas)}. "
            f"Campos permitidos: {sorted(chaves_permitidas)}."
        )

    for chave, valor in novos.items():
        if not isinstance(valor, str):
            raise ValueError(
                f"O valor do metadado '{chave}' deve ser uma string (recebido: {type(valor).__name__})."
            )

    doc = abrir_pdf(caminho)
    try:
        doc.set_metadata(novos)
        doc.save(saida)
        return saida
    finally:
        doc.close()


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
    import string

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


def comprimir_pdf(caminho: str, saida: str, nivel: str = "medio") -> dict:
    """Comprime um documento PDF reduzindo o tamanho do arquivo final.

    Aplica diferentes estratégias de compressão conforme o nível selecionado:
    - 'baixo': limpeza estrutural de objetos não utilizados e deflação de streams (garbage=4, deflate=True, clean=True).
    - 'medio': limpeza estrutural somada à geração de Object Streams e compressão de fontes/imagens.
    - 'alto': aplica todas as otimizações do nível médio e recomprime as imagens do documento com rewrite_images().

    Parâmetros:
        caminho: Caminho do arquivo PDF de origem.
        saida: Caminho do arquivo PDF resultante.
        nivel: Nível de compressão desejado ('baixo', 'medio', 'alto'). Padrão é 'medio'.

    Retorna:
        Dicionário com estatísticas da operação:
        - 'tamanho_original': Tamanho em bytes do arquivo inicial.
        - 'tamanho_final': Tamanho em bytes do arquivo gerado.
        - 'economia_percentual': Porcentagem de redução de tamanho obtida.
        - 'aumentou': Presente e igual a True caso o arquivo final tenha ficado maior que o original.

    Lança:
        ValueError: Se caminhos forem inválidos ou iguais, se o arquivo de origem não existir,
                    ou se o nível for diferente de 'baixo', 'medio' ou 'alto'.
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

    niveis_validos = {"baixo", "medio", "alto"}
    if not isinstance(nivel, str) or nivel not in niveis_validos:
        raise ValueError(
            f"Nível de compressão inválido: '{nivel}'. Níveis permitidos: {sorted(niveis_validos)}."
        )

    tamanho_original = os.path.getsize(caminho)

    doc = abrir_pdf(caminho)
    try:
        if nivel == "baixo":
            doc.save(saida, garbage=4, deflate=True, clean=True)
        elif nivel == "medio":
            doc.save(
                saida,
                garbage=4,
                deflate=True,
                clean=True,
                use_objstms=1,
                deflate_images=True,
                deflate_fonts=True,
            )
        else:  # alto
            if hasattr(doc, "rewrite_images"):
                doc.rewrite_images()
            doc.save(
                saida,
                garbage=4,
                deflate=True,
                clean=True,
                use_objstms=1,
                deflate_images=True,
                deflate_fonts=True,
            )
    finally:
        doc.close()

    tamanho_final = os.path.getsize(saida)
    if tamanho_original > 0:
        economia_percentual = round(
            ((tamanho_original - tamanho_final) / tamanho_original) * 100, 2
        )
    else:
        economia_percentual = 0.0

    resultado = {
        "tamanho_original": tamanho_original,
        "tamanho_final": tamanho_final,
        "economia_percentual": economia_percentual,
    }
    if tamanho_final > tamanho_original:
        resultado["aumentou"] = True

    return resultado


def proteger_pdf(
    caminho: str, saida: str, senha_usuario: str, senha_dono: str | None = None
) -> str:
    """Protege um documento PDF com senha utilizando criptografia AES-256.

    Parâmetros:
        caminho: Caminho do arquivo PDF de origem.
        saida: Caminho do arquivo PDF resultante.
        senha_usuario: Senha necessária para abrir e visualizar o documento.
        senha_dono: Senha de proprietário/administrador com permissões totais (opcional).

    Retorna:
        O caminho do arquivo salvo.

    Lança:
        ValueError: Se caminhos forem inválidos ou iguais, se o arquivo não existir,
                    se as senhas forem vazias ou de tipo inválido, ou se o PDF já estiver protegido.
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

    if not isinstance(senha_usuario, str) or not senha_usuario:
        raise ValueError("A senha de usuário deve ser uma string não vazia.")

    if senha_dono is not None and (not isinstance(senha_dono, str) or not senha_dono):
        raise ValueError(
            "A senha de dono deve ser uma string não vazia quando informada."
        )

    doc = pymupdf.open(caminho)
    try:
        if doc.needs_pass:
            raise ValueError("O documento de origem já está protegido por senha.")

        doc.save(
            saida,
            encryption=pymupdf.PDF_ENCRYPT_AES_256,
            user_pw=senha_usuario,
            owner_pw=senha_dono,
        )
        return saida
    finally:
        doc.close()


def remover_senha(caminho: str, senha: str, saida: str) -> str:
    """Remove a proteção por senha de um documento PDF e salva uma versão descriptografada.

    Parâmetros:
        caminho: Caminho do arquivo PDF protegido.
        senha: Senha de usuário ou de dono para descriptografar o documento.
        saida: Caminho do arquivo PDF resultante sem senha.

    Retorna:
        O caminho do arquivo salvo.

    Lança:
        ValueError: Se caminhos forem inválidos ou iguais, se o arquivo não existir,
                    se a senha for vazia ou de tipo inválido, se o PDF não possuir senha,
                    ou se a senha informada estiver incorreta.
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

    if not isinstance(senha, str) or not senha:
        raise ValueError("A senha informada deve ser uma string não vazia.")

    doc = pymupdf.open(caminho)
    try:
        if not doc.needs_pass and not doc.is_encrypted:
            raise ValueError("O arquivo PDF informado não possui proteção por senha.")

        auth_resultado = doc.authenticate(senha)
        if auth_resultado == 0:
            raise ValueError("A senha informada está incorreta.")

        doc.save(saida, encryption=pymupdf.PDF_ENCRYPT_NONE)
        return saida
    finally:
        doc.close()


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
        raise ValueError(
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
            pix = None
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
