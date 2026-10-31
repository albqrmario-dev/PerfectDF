import os

import pymupdf


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
            encryption=pymupdf.PDF_ENCRYPT_AES_256,  # type: ignore[attr-defined]
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

        doc.save(saida, encryption=pymupdf.PDF_ENCRYPT_NONE)  # type: ignore[attr-defined]
        return saida
    finally:
        doc.close()
