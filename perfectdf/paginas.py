import os

import pymupdf

from perfectdf.comum import abrir_pdf, parsear_ordem


def juntar_pdfs(caminhos, saida):
    """Junta dois ou mais PDF's e os retorna."""

    doc = pymupdf.open()

    for caminho in caminhos:
        doc.insert_pdf(abrir_pdf(caminho))

    doc.save(saida)
    return saida


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
