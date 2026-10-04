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
        raise ValueError("O caminho do arquivo de origem deve ser uma string não vazia.")
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
        raise ValueError("A lista de páginas a serem rotacionadas não pode estar vazia.")

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
        raise ValueError("O caminho do arquivo de origem deve ser uma string não vazia.")
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
        raise ValueError("O caminho do arquivo de origem deve ser uma string não vazia.")
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
        raise ValueError("A especificação de ordem deve ser uma string ou lista de inteiros.")

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
        raise ValueError("O caminho do arquivo de origem deve ser uma string não vazia.")
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


def extrair_texto(
    caminho: str, paginas: list[int] | str | None = None
) -> str:
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
            raise ValueError("A lista de páginas para extração de texto não pode estar vazia.")

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


if __name__ == "__main__":
    import os
    import tempfile

    print("=== Demonstração do PerfectDF: parsear_paginas e extrair_paginas ===\n")

    # 1. Demonstração de parsing de string no estilo caixa de impressão
    exemplo_texto = "1-3, 5, 9-7"
    print(f"1. Parseando a string de páginas: '{exemplo_texto}'")
    paginas_extrair = parsear_paginas(exemplo_texto)
    print(f"   Resultado (ordenado, sem duplicatas, base 1): {paginas_extrair}\n")

    # 2. Criação de um PDF de teste e extração real das páginas
    with tempfile.TemporaryDirectory() as pasta_temp:
        caminho_origem = os.path.join(pasta_temp, "documento_original.pdf")
        caminho_saida = os.path.join(pasta_temp, "documento_extraido.pdf")
        caminho_repetidas = os.path.join(pasta_temp, "documento_repetidas.pdf")

        # Gerando PDF de origem com 10 páginas para teste
        doc_origem_teste = pymupdf.open()
        for i in range(1, 11):
            pagina = doc_origem_teste.new_page()
            pagina.insert_text(
                (50, 72),
                f"Página {i} de 10 - Documento de Origem",
                fontsize=18,
            )
        doc_origem_teste.save(caminho_origem)
        doc_origem_teste.close()
        print(f"2. PDF de teste gerado com 10 páginas em: {caminho_origem}")

        # Extraindo páginas selecionadas
        print(f"\n3. Extraindo páginas {paginas_extrair} para: {caminho_saida}")
        resultado = extrair_paginas(caminho_origem, paginas_extrair, caminho_saida)
        print(f"   Arquivo gerado com sucesso: {resultado}")

        # Verificando o conteúdo do PDF gerado
        doc_verificacao = abrir_pdf(resultado)
        print(f"   Total de páginas no PDF extraído: {doc_verificacao.page_count}")
        for idx, pagina in enumerate(doc_verificacao, start=1):
            texto_pagina = pagina.get_text().strip()
            print(f"   - Página {idx} contém: '{texto_pagina}'")
        doc_verificacao.close()

        # Demonstração de repetições intencionais e ordem personalizada
        ordem_personalizada = [3, 1, 1]
        print(
            f"\n4. Testando extração com repetições e ordem personalizada: {ordem_personalizada}"
        )
        extrair_paginas(caminho_origem, ordem_personalizada, caminho_repetidas)
        doc_rep = abrir_pdf(caminho_repetidas)
        print(f"   Total de páginas no PDF com repetições: {doc_rep.page_count}")
        for idx, pagina in enumerate(doc_rep, start=1):
            print(f"   - Página {idx} contém: '{pagina.get_text().strip()}'")
        doc_rep.close()

        # Demonstração do tratamento de erros
        print("\n5. Demonstração de tratamento de erros:")
        casos_invalidos = ["", "1-abc", "1-2-3"]
        for caso in casos_invalidos:
            try:
                parsear_paginas(caso)
            except ValueError as e:
                print(f"   [parsear_paginas] Entrada '{caso}' -> Erro capturado: {e}")

        try:
            extrair_paginas(caminho_origem, [99], os.path.join(pasta_temp, "erro.pdf"))
        except ValueError as e:
            print(f"   [extrair_paginas] Página fora do limite -> Erro capturado: {e}")

    print("\n=== Todos os testes manuais foram executados com sucesso! ===")
