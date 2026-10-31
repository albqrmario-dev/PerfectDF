import os
from typing import cast

from perfectdf.comum import abrir_pdf


def ler_metadados(caminho: str) -> dict[str, str | None]:
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
        # A rotina abre PDFs, cujo objeto sempre fornece um mapa de metadados.
        return dict(cast(dict[str, str | None], doc.metadata))
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
        raise ValueError("Os novos metadados devem ser fornecidos em um dicionário.")  # noqa: TRY004

    chaves_permitidas = {"title", "author", "subject", "keywords"}
    chaves_invalidas = set(novos.keys()) - chaves_permitidas
    if chaves_invalidas:
        raise ValueError(
            f"Chave(s) de metadados não permitida(s): {sorted(chaves_invalidas)}. "
            f"Campos permitidos: {sorted(chaves_permitidas)}."
        )

    for chave, valor in novos.items():
        if not isinstance(valor, str):
            raise ValueError(  # noqa: TRY004
                f"O valor do metadado '{chave}' deve ser uma string (recebido: {type(valor).__name__})."
            )

    doc = abrir_pdf(caminho)
    try:
        doc.set_metadata(novos)
        doc.save(saida)
        return saida
    finally:
        doc.close()
