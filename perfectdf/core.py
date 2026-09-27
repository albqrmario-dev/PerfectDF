import pymupdf


def abrir_pdf(caminho):
    return pymupdf.open(caminho)


def juntar_pdfs(caminhos, saida):

    doc = pymupdf.open()

    for caminho in caminhos:
        doc.insert_pdf(abrir_pdf(caminho))

    doc.save(saida)
    return saida


def parsear_paginas(texto: str) -> list[int]:
    """Converte uma string de páginas (ex: '1-3,5,7-9') em uma lista ordenada e sem duplicatas (base 1).

    Trata números avulsos, intervalos normais e invertidos, desconsiderando espaços
    extras e eliminando repetições.
    """
    if not isinstance(texto, str):
        raise ValueError("A especificação de páginas deve ser uma string.")

    texto_limpo = texto.strip()
    if not texto_limpo:
        raise ValueError("A especificação de páginas não pode estar vazia.")

    paginas = set()
    partes = texto_limpo.split(",")

    for parte in partes:
        item = parte.strip()
        if not item:
            raise ValueError(f"Trecho vazio encontrado na especificação de páginas: '{texto}'.")

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
                raise ValueError(
                    f"Intervalo contém valores não numéricos: '{item}'."
                )

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
                raise ValueError(f"Página inválida (não é um número inteiro): '{item}'.")

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
                if isinstance(pagina, bool) or not isinstance(pagina, int) or pagina < 1 or pagina > total_paginas:
                    raise ValueError(
                        f"Página inválida: {pagina}. O documento possui {total_paginas} página(s) "
                        f"(páginas permitidas: 1 a {total_paginas})."
                    )

            for pagina in paginas:
                doc_saida.insert_pdf(doc_origem, from_page=pagina - 1, to_page=pagina - 1)

            doc_saida.save(saida)
            return saida
        finally:
            doc_saida.close()
    finally:
        doc_origem.close()


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
        print(f"\n4. Testando extração com repetições e ordem personalizada: {ordem_personalizada}")
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
