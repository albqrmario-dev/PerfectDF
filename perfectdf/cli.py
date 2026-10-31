"""Interface de Linha de Comando (CLI) para o PerfectDF."""

import argparse
import sys
from collections.abc import Sequence

from perfectdf import (
    achatar_formulario,
    adicionar_imagem,
    adicionar_marca_dagua,
    adicionar_nota,
    adicionar_texto,
    comprimir_pdf,
    destacar_texto,
    editar_metadados,
    excluir_paginas,
    extrair_paginas,
    extrair_texto,
    girar_paginas,
    imagens_para_pdf,
    juntar_pdfs,
    ler_metadados,
    listar_campos,
    numerar_paginas,
    parsear_ordem,
    parsear_paginas,
    pdf_para_imagens,
    preencher_formulario,
    proteger_pdf,
    remover_senha,
    reordenar_paginas,
)


class PerfectDFArgumentParser(argparse.ArgumentParser):
    """Parser customizado para exibir erros claros em português sem stack trace."""

    def error(self, message: str):
        sys.stderr.write(f"Erro: {message}\n")
        sys.stderr.write("Use '--help' para instruções de uso detalhadas.\n")
        sys.exit(2)


def criar_parser() -> argparse.ArgumentParser:
    """Cria e configura o parser principal de argumentos da CLI."""
    parser = PerfectDFArgumentParser(
        prog="perfectdf",
        description="PerfectDF — Ferramenta de linha de comando para manipulação e edição de PDFs.",
    )
    subparsers = parser.add_subparsers(
        dest="comando",
        title="Subcomandos disponíveis",
        description="Escolha uma das ações abaixo para executar:",
        metavar="<comando>",
    )

    # 1. juntar
    p_juntar = subparsers.add_parser(
        "juntar", help="Junta múltiplos arquivos PDF em um único arquivo."
    )
    p_juntar.add_argument(
        "arquivos", nargs="+", help="Arquivos PDF a serem combinados."
    )
    p_juntar.add_argument(
        "-o", "--saida", required=True, help="Caminho do arquivo PDF resultante."
    )

    # 2. extrair
    p_extrair = subparsers.add_parser(
        "extrair", help="Extrai páginas específicas de um PDF para um novo arquivo."
    )
    p_extrair.add_argument("pdf", help="Arquivo PDF de origem.")
    p_extrair.add_argument(
        "-p",
        "--paginas",
        required=True,
        help="Páginas a serem extraídas (ex: '1,3,5' ou '1-3').",
    )
    p_extrair.add_argument(
        "-o", "--saida", required=True, help="Caminho do arquivo PDF resultante."
    )

    # 3. girar
    p_girar = subparsers.add_parser(
        "girar", help="Gira páginas selecionadas de um PDF em ângulos múltiplos de 90°."
    )
    p_girar.add_argument("pdf", help="Arquivo PDF de origem.")
    p_girar.add_argument(
        "-p",
        "--paginas",
        required=True,
        help="Páginas a serem giradas (ex: '1,2' ou '1-5').",
    )
    p_girar.add_argument(
        "-g",
        "--graus",
        type=int,
        required=True,
        help="Ângulo de rotação em graus (ex: 90, 180, 270, -90).",
    )
    p_girar.add_argument(
        "-o", "--saida", required=True, help="Caminho do arquivo PDF resultante."
    )

    # 4. excluir
    p_excluir = subparsers.add_parser(
        "excluir", help="Remove páginas selecionadas de um PDF."
    )
    p_excluir.add_argument("pdf", help="Arquivo PDF de origem.")
    p_excluir.add_argument(
        "-p",
        "--paginas",
        required=True,
        help="Páginas a serem removidas (ex: '2' ou '2,4').",
    )
    p_excluir.add_argument(
        "-o", "--saida", required=True, help="Caminho do arquivo PDF resultante."
    )

    # 5. reordenar
    p_reordenar = subparsers.add_parser(
        "reordenar", help="Reorganiza a ordem das páginas de um PDF."
    )
    p_reordenar.add_argument("pdf", help="Arquivo PDF de origem.")
    p_reordenar.add_argument(
        "--ordem",
        required=True,
        help="Sequência desejada de páginas (ex: '3, 1-2').",
    )
    p_reordenar.add_argument(
        "-o", "--saida", required=True, help="Caminho do arquivo PDF resultante."
    )

    # 6. metadados
    p_meta = subparsers.add_parser(
        "metadados",
        help="Visualiza ou atualiza os metadados (título, autor, etc.) de um PDF.",
    )
    p_meta.add_argument("pdf", help="Arquivo PDF.")
    p_meta.add_argument("--titulo", help="Novo título do documento.")
    p_meta.add_argument("--autor", help="Novo autor do documento.")
    p_meta.add_argument("--assunto", help="Novo assunto do documento.")
    p_meta.add_argument("--palavras-chave", help="Novas palavras-chave do documento.")
    p_meta.add_argument(
        "-o",
        "--saida",
        help="Caminho do arquivo PDF resultante (obrigatório para edição).",
    )

    # 7. texto
    p_texto = subparsers.add_parser(
        "texto", help="Extrai o conteúdo textual de páginas de um PDF."
    )
    p_texto.add_argument("pdf", help="Arquivo PDF.")
    p_texto.add_argument(
        "-p",
        "--paginas",
        help="Páginas específicas para extrair (ex: '1-3, 5'). Padrão: todas.",
    )
    p_texto.add_argument(
        "-o",
        "--saida",
        help="Arquivo de texto (.txt) de saída (opcional, padrão: imprime na tela).",
    )

    # 8. marca-dagua
    p_marca = subparsers.add_parser(
        "marca-dagua",
        aliases=["marca_dagua"],
        help="Adiciona uma marca d'água diagonal translúcida às páginas.",
    )
    p_marca.add_argument("pdf", help="Arquivo PDF de origem.")
    p_marca.add_argument("texto", help="Texto da marca d'água.")
    p_marca.add_argument(
        "-o", "--saida", required=True, help="Caminho do arquivo PDF resultante."
    )
    p_marca.add_argument(
        "-p", "--paginas", help="Páginas alvo (ex: '1-3'). Padrão: todas."
    )
    p_marca.add_argument(
        "--opacidade",
        type=float,
        default=0.3,
        help="Opacidade de 0.0 a 1.0 (padrão: 0.3).",
    )
    p_marca.add_argument(
        "--angulo",
        type=float,
        default=45.0,
        help="Ângulo de rotação em graus (padrão: 45).",
    )
    p_marca.add_argument(
        "--tamanho-fonte",
        type=float,
        default=48.0,
        help="Tamanho da fonte em pontos (padrão: 48).",
    )

    # 9. adicionar-nota
    p_nota = subparsers.add_parser(
        "adicionar-nota",
        aliases=["adicionar_nota"],
        help="Adiciona uma anotação pop-up a uma página do PDF.",
    )
    p_nota.add_argument("pdf", help="Arquivo PDF de origem.")
    p_nota.add_argument(
        "-p", "--pagina", type=int, required=True, help="Número da página (base 1)."
    )
    p_nota.add_argument("-t", "--texto", required=True, help="Texto da anotação.")
    p_nota.add_argument(
        "-o", "--saida", required=True, help="Caminho do arquivo PDF resultante."
    )
    p_nota.add_argument(
        "--posicao",
        default="50,50",
        help="Coordenadas visuais x,y na página (padrão: '50,50').",
    )

    # 10. numerar
    p_numerar = subparsers.add_parser(
        "numerar", help="Adiciona numeração sequencial às páginas do PDF."
    )
    p_numerar.add_argument("pdf", help="Arquivo PDF de origem.")
    p_numerar.add_argument(
        "-o", "--saida", required=True, help="Caminho do arquivo PDF resultante."
    )
    p_numerar.add_argument(
        "--formato",
        default="Página {n} de {total}",
        help="Formato do texto de numeração (padrão: 'Página {n} de {total}').",
    )
    p_numerar.add_argument(
        "--posicao",
        default="rodape-centro",
        choices=[
            "rodape-centro",
            "rodape-direita",
            "rodape-esquerda",
            "topo-centro",
            "topo-direita",
            "topo-esquerda",
        ],
        help="Posição do número na página (padrão: 'rodape-centro').",
    )
    p_numerar.add_argument(
        "--inicio",
        type=int,
        default=1,
        help="Número inicial da contagem (padrão: 1).",
    )
    p_numerar.add_argument(
        "-p", "--paginas", help="Páginas a serem numeradas (ex: '1-5'). Padrão: todas."
    )
    p_numerar.add_argument(
        "--tamanho-fonte",
        type=float,
        default=10.0,
        help="Tamanho da fonte em pontos (padrão: 10).",
    )

    # 10. comprimir
    p_comp = subparsers.add_parser(
        "comprimir", help="Otimiza e reduz o tamanho do arquivo PDF."
    )
    p_comp.add_argument("pdf", help="Arquivo PDF de origem.")
    p_comp.add_argument(
        "-o", "--saida", required=True, help="Caminho do arquivo PDF resultante."
    )
    p_comp.add_argument(
        "--nivel",
        default="medio",
        choices=["baixo", "medio", "alto"],
        help="Nível de compressão desejado (padrão: medio).",
    )

    # 11. proteger
    p_prot = subparsers.add_parser(
        "proteger", help="Criptografa o PDF com proteção por senha (AES-256)."
    )
    p_prot.add_argument("pdf", help="Arquivo PDF de origem.")
    p_prot.add_argument(
        "-s",
        "--senha",
        dest="senha_usuario",
        required=True,
        help="Senha para visualização do documento.",
    )
    p_prot.add_argument(
        "-d",
        "--senha-dono",
        help="Senha administrativa do proprietário (opcional).",
    )
    p_prot.add_argument(
        "-o", "--saida", required=True, help="Caminho do arquivo PDF resultante."
    )

    # 12. remover-senha
    p_rem = subparsers.add_parser(
        "remover-senha",
        aliases=["remover_senha"],
        help="Remove a proteção por senha de um PDF criptografado.",
    )
    p_rem.add_argument("pdf", help="Arquivo PDF protegido.")
    p_rem.add_argument(
        "-s", "--senha", required=True, help="Senha para descriptografar o documento."
    )
    p_rem.add_argument(
        "-o", "--saida", required=True, help="Caminho do arquivo PDF descriptografado."
    )

    # 13. pdf-para-imagens
    p_p2i = subparsers.add_parser(
        "pdf-para-imagens",
        aliases=["pdf_para_imagens"],
        help="Converte as páginas do PDF em arquivos de imagem.",
    )
    p_p2i.add_argument("pdf", help="Arquivo PDF de origem.")
    p_p2i.add_argument(
        "-o",
        "--pasta-saida",
        required=True,
        help="Diretório onde as imagens serão salvas.",
    )
    p_p2i.add_argument(
        "-p", "--paginas", help="Páginas a converter (ex: '1-3'). Padrão: todas."
    )
    p_p2i.add_argument(
        "--dpi",
        type=int,
        default=150,
        help="Resolução em DPI (entre 36 e 600, padrão: 150).",
    )
    p_p2i.add_argument(
        "--formato",
        default="png",
        choices=["png", "jpg"],
        help="Formato das imagens (padrão: png).",
    )

    # 14. imagens-para-pdf
    p_i2p = subparsers.add_parser(
        "imagens-para-pdf",
        aliases=["imagens_para_pdf"],
        help="Cria um PDF a partir de imagens.",
    )
    p_i2p.add_argument(
        "imagens", nargs="+", help="Arquivos de imagem na ordem em que devem aparecer."
    )
    p_i2p.add_argument(
        "-o", "--saida", required=True, help="Caminho do arquivo PDF resultante."
    )

    # 15. adicionar-texto
    p_add_txt = subparsers.add_parser(
        "adicionar-texto",
        aliases=["adicionar_texto"],
        help="Adiciona texto formatado a uma página de um PDF.",
    )
    p_add_txt.add_argument("pdf", help="Arquivo PDF de origem.")
    p_add_txt.add_argument(
        "-p", "--pagina", type=int, required=True, help="Número da página (base 1)."
    )
    p_add_txt.add_argument(
        "-t", "--texto", required=True, help="Texto a ser adicionado."
    )
    p_add_txt.add_argument(
        "-o",
        "--saida",
        help="Arquivo PDF resultante (se omitido, altera o próprio PDF original).",
    )
    p_add_txt.add_argument(
        "--posicao",
        default="50,50",
        help="Coordenadas visuais x,y na página (ex: '100,200', padrão: '50,50').",
    )
    p_add_txt.add_argument(
        "--fonte",
        default="helv",
        help="Fonte do texto (ex: helv, times, courier; padrão: helv).",
    )
    p_add_txt.add_argument(
        "--tamanho",
        type=float,
        default=12.0,
        help="Tamanho da fonte em pontos (padrão: 12.0).",
    )
    p_add_txt.add_argument(
        "--cor",
        default="preto",
        help="Cor do texto ('preto', 'azul', 'vermelho' ou 'R,G,B'; padrão: preto).",
    )

    # 16. adicionar-imagem
    p_add_img = subparsers.add_parser(
        "adicionar-imagem",
        aliases=["adicionar_imagem"],
        help="Insere uma imagem em uma página de um PDF.",
    )
    p_add_img.add_argument("pdf", help="Arquivo PDF de origem.")
    p_add_img.add_argument(
        "-p", "--pagina", type=int, required=True, help="Número da página (base 1)."
    )
    p_add_img.add_argument(
        "-i", "--imagem", required=True, help="Caminho do arquivo de imagem."
    )
    p_add_img.add_argument(
        "-o",
        "--saida",
        help="Arquivo PDF resultante (se omitido, altera o próprio PDF original).",
    )
    p_add_img.add_argument(
        "--posicao",
        default="50,50",
        help="Coordenadas visuais x,y na página (ex: '100,200', padrão: '50,50').",
    )
    p_add_img.add_argument(
        "--tamanho",
        help="Dimensões da imagem: 'largura,altura' ou apenas 'largura' (ex: '150,100' ou '200').",
    )

    # 17. destacar-texto
    p_dest = subparsers.add_parser(
        "destacar-texto",
        aliases=["destacar_texto"],
        help="Busca e destaca (marca-texto, sublinhado ou riscado) ocorrências de um termo no PDF.",
    )
    p_dest.add_argument("pdf", help="Arquivo PDF de origem.")
    p_dest.add_argument("termo", help="Texto a ser buscado e destacado.")
    p_dest.add_argument(
        "-o", "--saida", required=True, help="Caminho do arquivo PDF resultante."
    )
    p_dest.add_argument(
        "-p", "--paginas", help="Páginas alvo (ex: '1-3'). Padrão: todas."
    )
    p_dest.add_argument(
        "--tipo",
        default="destaque",
        choices=["destaque", "sublinhado", "riscado"],
        help="Tipo de anotação (padrão: destaque).",
    )
    p_dest.add_argument(
        "--cor",
        default="amarelo",
        help="Cor da anotação ('amarelo', 'verde', 'azul', 'rosa', 'laranja', 'vermelho'; padrão: amarelo).",
    )
    p_dest.add_argument(
        "--case-sensitive",
        action="store_true",
        default=False,
        help="Se informado, busca diferenciando maiúsculas/minúsculas.",
    )

    # 18. listar-campos
    p_listar = subparsers.add_parser(
        "listar-campos",
        aliases=["listar_campos"],
        help="Lista os campos de formulário (AcroForm) presentes em um PDF.",
    )
    p_listar.add_argument("pdf", help="Arquivo PDF com formulário.")

    # 19. preencher
    p_preencher = subparsers.add_parser(
        "preencher",
        help="Preenche campos de um formulário PDF pelos seus nomes.",
    )
    p_preencher.add_argument("pdf", help="Arquivo PDF com formulário.")
    p_preencher.add_argument(
        "-o", "--saida", required=True, help="Caminho do arquivo PDF resultante."
    )
    p_preencher.add_argument(
        "--campo",
        action="append",
        required=True,
        metavar="nome=valor",
        help="Campo a preencher no formato 'nome=valor'. Pode ser repetido.",
    )

    # 20. achatar
    p_achatar = subparsers.add_parser(
        "achatar",
        help="Converte os campos de formulário em conteúdo fixo (não editável).",
    )
    p_achatar.add_argument("pdf", help="Arquivo PDF com formulário.")
    p_achatar.add_argument(
        "-o", "--saida", required=True, help="Caminho do arquivo PDF resultante."
    )

    return parser


def executar_comando(args: argparse.Namespace) -> int:
    """Executa a ação correspondente ao subcomando selecionado."""
    cmd = args.comando
    if not cmd:
        sys.stderr.write(
            "Erro: Nenhum subcomando informado. Use '--help' para ver os comandos disponíveis.\n"
        )
        return 2

    # Normalizar aliases
    cmd = cmd.replace("_", "-")

    if cmd == "juntar":
        juntar_pdfs(args.arquivos, args.saida)
        print(f"Sucesso: PDFs combinados salvos em '{args.saida}'.")

    elif cmd == "extrair":
        paginas = parsear_ordem(args.paginas)
        extrair_paginas(args.pdf, paginas, args.saida)
        print(f"Sucesso: Páginas extraídas salvas em '{args.saida}'.")

    elif cmd == "girar":
        paginas = parsear_paginas(args.paginas)
        girar_paginas(args.pdf, paginas, args.graus, args.saida)
        print(f"Sucesso: Páginas giradas salvas em '{args.saida}'.")

    elif cmd == "excluir":
        paginas = parsear_paginas(args.paginas)
        excluir_paginas(args.pdf, paginas, args.saida)
        print(f"Sucesso: Páginas excluídas. Arquivo salvo em '{args.saida}'.")

    elif cmd == "reordenar":
        reordenar_paginas(args.pdf, args.ordem, args.saida)
        print(f"Sucesso: PDF reordenado salvo em '{args.saida}'.")

    elif cmd == "metadados":
        tem_edicao = any(
            [
                args.titulo is not None,
                args.autor is not None,
                args.assunto is not None,
                args.palavras_chave is not None,
            ]
        )
        if tem_edicao:
            if not args.saida:
                raise ValueError(
                    "O parâmetro '--saida' / '-o' é obrigatório ao editar metadados."
                )
            novos = {}
            if args.titulo is not None:
                novos["title"] = args.titulo
            if args.autor is not None:
                novos["author"] = args.autor
            if args.assunto is not None:
                novos["subject"] = args.assunto
            if args.palavras_chave is not None:
                novos["keywords"] = args.palavras_chave

            editar_metadados(args.pdf, novos, args.saida)
            print(f"Sucesso: Metadados atualizados salvos em '{args.saida}'.")
        else:
            meta = ler_metadados(args.pdf)
            print(f"Título:         {meta.get('title') or ''}")
            print(f"Autor:          {meta.get('author') or ''}")
            print(f"Assunto:        {meta.get('subject') or ''}")
            print(f"Palavras-chave: {meta.get('keywords') or ''}")

    elif cmd == "texto":
        conteudo = extrair_texto(args.pdf, paginas=args.paginas)
        if args.saida:
            with open(args.saida, "w", encoding="utf-8") as f:
                f.write(conteudo)
            print(f"Sucesso: Texto extraído salvo em '{args.saida}'.")
        else:
            print(conteudo)

    elif cmd == "marca-dagua":
        adicionar_marca_dagua(
            caminho=args.pdf,
            saida=args.saida,
            texto=args.texto,
            paginas=args.paginas,
            opacidade=args.opacidade,
            angulo=args.angulo,
            tamanho_fonte=args.tamanho_fonte,
        )
        print(f"Sucesso: Marca d'água aplicada e salva em '{args.saida}'.")

    elif cmd == "adicionar-nota":
        partes_pos = [p.strip() for p in args.posicao.split(",")]
        if len(partes_pos) != 2:
            raise ValueError(
                f"Posição inválida: '{args.posicao}'. Formato esperado: 'X,Y'."
            )
        try:
            posicao = (float(partes_pos[0]), float(partes_pos[1]))
        except ValueError as e:
            raise ValueError(
                f"As coordenadas da posição devem ser numéricas: '{args.posicao}'."
            ) from e

        adicionar_nota(
            caminho=args.pdf,
            saida=args.saida,
            pagina=args.pagina,
            texto=args.texto,
            posicao=posicao,
        )
        print(f"Sucesso: Nota adicionada e salva em '{args.saida}'.")

    elif cmd == "numerar":
        numerar_paginas(
            caminho=args.pdf,
            saida=args.saida,
            formato=args.formato,
            posicao=args.posicao,
            inicio=args.inicio,
            paginas=args.paginas,
            tamanho_fonte=args.tamanho_fonte,
        )
        print(f"Sucesso: Numeração adicionada e salva em '{args.saida}'.")

    elif cmd == "comprimir":
        res = comprimir_pdf(args.pdf, args.saida, nivel=args.nivel)
        print(f"Sucesso: PDF comprimido salvo em '{args.saida}'.")
        print(f"  Tamanho original: {res['tamanho_original']} bytes")
        print(f"  Tamanho final:    {res['tamanho_final']} bytes")
        print(f"  Economia:         {res['economia_percentual']}%")
        if res.get("aumentou"):
            print("  Aviso: O arquivo gerado ficou maior do que o original.")

    elif cmd == "proteger":
        proteger_pdf(
            args.pdf,
            args.saida,
            senha_usuario=args.senha_usuario,
            senha_dono=args.senha_dono,
        )
        print(f"Sucesso: PDF protegido por senha salvo em '{args.saida}'.")

    elif cmd == "remover-senha":
        remover_senha(args.pdf, args.senha, args.saida)
        print(f"Sucesso: Senha removida. PDF salvo em '{args.saida}'.")

    elif cmd == "pdf-para-imagens":
        arquivos = pdf_para_imagens(
            caminho=args.pdf,
            pasta_saida=args.pasta_saida,
            paginas=args.paginas,
            dpi=args.dpi,
            formato=args.formato,
        )
        print(
            f"Sucesso: {len(arquivos)} página(s) convertida(s) em imagens na pasta '{args.pasta_saida}'."
        )

    elif cmd == "imagens-para-pdf":
        imagens_para_pdf(args.imagens, args.saida)
        print(f"Sucesso: PDF criado a partir das imagens em '{args.saida}'.")

    elif cmd == "adicionar-texto":
        # Parse posição
        partes_pos = [p.strip() for p in args.posicao.split(",")]
        if len(partes_pos) != 2:
            raise ValueError(
                f"Posição inválida: '{args.posicao}'. Formato esperado: 'X,Y'."
            )
        try:
            posicao = (float(partes_pos[0]), float(partes_pos[1]))
        except ValueError as e:
            raise ValueError(
                f"As coordenadas da posição devem ser numéricas: '{args.posicao}'."
            ) from e

        # Parse cor
        if "," in args.cor:
            partes_cor = [c.strip() for c in args.cor.split(",")]
            if len(partes_cor) != 3:
                raise ValueError(
                    f"Tupla de cor inválida: '{args.cor}'. Formato esperado: 'R,G,B'."
                )
            try:
                cor_parsed: str | tuple[float, float, float] = (
                    float(partes_cor[0]),
                    float(partes_cor[1]),
                    float(partes_cor[2]),
                )
            except ValueError as e:
                raise ValueError(
                    f"Os componentes de cor RGB devem ser numéricos: '{args.cor}'."
                ) from e
        else:
            cor_parsed = args.cor

        destino = adicionar_texto(
            pdf=args.pdf,
            pagina=args.pagina,
            texto=args.texto,
            posicao=posicao,
            fonte=args.fonte,
            tamanho=args.tamanho,
            cor=cor_parsed,
            saida=args.saida,
        )
        print(f"Sucesso: Texto adicionado e salvo em '{destino}'.")

    elif cmd == "adicionar-imagem":
        # Parse posição
        partes_pos = [p.strip() for p in args.posicao.split(",")]
        if len(partes_pos) != 2:
            raise ValueError(
                f"Posição inválida: '{args.posicao}'. Formato esperado: 'X,Y'."
            )
        try:
            posicao = (float(partes_pos[0]), float(partes_pos[1]))
        except ValueError as e:
            raise ValueError(
                f"As coordenadas da posição devem ser numéricas: '{args.posicao}'."
            ) from e

        # Parse tamanho
        tamanho_parsed: tuple[float, float] | float | None = None
        if args.tamanho:
            if "," in args.tamanho:
                partes_tam = [t.strip() for t in args.tamanho.split(",")]
                if len(partes_tam) != 2:
                    raise ValueError(
                        f"Tamanho inválido: '{args.tamanho}'. Formato esperado: 'largura,altura'."
                    )
                try:
                    tamanho_parsed = (float(partes_tam[0]), float(partes_tam[1]))
                except ValueError as e:
                    raise ValueError(
                        f"As dimensões de tamanho devem ser numéricas: '{args.tamanho}'."
                    ) from e
            else:
                try:
                    tamanho_parsed = float(args.tamanho)
                except ValueError as e:
                    raise ValueError(
                        f"A dimensão de largura deve ser numérica: '{args.tamanho}'."
                    ) from e

        destino = adicionar_imagem(
            pdf=args.pdf,
            pagina=args.pagina,
            imagem=args.imagem,
            posicao=posicao,
            tamanho=tamanho_parsed,
            saida=args.saida,
        )
        print(f"Sucesso: Imagem adicionada e salva em '{destino}'.")

    elif cmd == "destacar-texto":
        resultado = destacar_texto(
            caminho=args.pdf,
            saida=args.saida,
            termo=args.termo,
            paginas=args.paginas,
            tipo=args.tipo,
            cor=args.cor,
            ignorar_maiusculas=not args.case_sensitive,
        )
        total = resultado["total_ocorrencias"]
        if total > 0:
            print(
                f"Sucesso: {total} ocorrência(s) de '{args.termo}' destacada(s) e salva(s) em '{args.saida}'."
            )
            for pag, qtd in sorted(resultado["ocorrencias_por_pagina"].items()):
                print(f"  Página {pag}: {qtd} ocorrência(s)")
        else:
            print(f"Nenhuma ocorrência de '{args.termo}' foi encontrada.")
            if "aviso" in resultado:
                print(f"  Aviso: {resultado['aviso']}")

    elif cmd == "listar-campos":
        campos = listar_campos(args.pdf)
        for campo in campos:
            print(
                f"  Campo: '{campo['nome']}' | Tipo: {campo['tipo']} "
                f"| Valor: '{campo['valor']}' | Página: {campo['pagina']}"
            )
        print(f"Total: {len(campos)} campo(s) encontrado(s).")

    elif cmd == "preencher":
        valores: dict[str, str | bool] = {}
        for item in args.campo:
            if "=" not in item:
                raise ValueError(
                    f"Formato inválido para --campo: '{item}'. "
                    "Use o formato 'nome=valor'."
                )
            nome, valor = item.split("=", 1)
            nome = nome.strip()
            valor = valor.strip()
            if not nome:
                raise ValueError(
                    f"Nome de campo vazio em '--campo {item}'. "
                    "Use o formato 'nome=valor'."
                )
            valores[nome] = valor
        preencher_formulario(args.pdf, valores, args.saida)
        print(f"Sucesso: Formulário preenchido e salvo em '{args.saida}'.")

    elif cmd == "achatar":
        achatar_formulario(args.pdf, args.saida)
        print(f"Sucesso: Formulário achatado e salvo em '{args.saida}'.")

    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Ponto de entrada principal da CLI."""
    parser = criar_parser()
    args = parser.parse_args(argv)

    try:
        return executar_comando(args)
    except (ValueError, FileNotFoundError, PermissionError) as e:
        sys.stderr.write(f"Erro: {e}\n")
        return 1
    except Exception as e:  # noqa: BLE001
        sys.stderr.write(f"Erro: {e}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
