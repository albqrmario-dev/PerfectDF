import os

from perfectdf.comum import abrir_pdf


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
