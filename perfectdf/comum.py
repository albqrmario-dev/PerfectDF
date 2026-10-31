import pymupdf


def abrir_pdf(caminho: str) -> pymupdf.Document:
    return pymupdf.open(caminho)


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

    paginas: set[int] = set()
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
        raise ValueError("A especificação de ordem deve ser uma string.")  # noqa: TRY004

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
