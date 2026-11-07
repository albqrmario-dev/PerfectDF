"""Aplicação backend FastAPI para a interface web do PerfectDF."""

import json
import logging
from pathlib import Path
import tempfile
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.requests import Request

from perfectdf.anotacoes import (
    adicionar_marca_dagua,
    adicionar_nota,
    destacar_texto,
    numerar_paginas,
)
from perfectdf.compressao import comprimir_pdf
from perfectdf.comum import abrir_pdf, parsear_paginas
from perfectdf.formularios import (
    achatar_formulario,
    listar_campos,
    preencher_formulario,
)
from perfectdf.metadados import editar_metadados, ler_metadados
from perfectdf.paginas import (
    excluir_paginas,
    extrair_paginas,
    girar_paginas,
    juntar_pdfs,
    reordenar_paginas,
)
from perfectdf.seguranca import proteger_pdf, remover_senha
from perfectdf.texto import adicionar_texto, extrair_texto

# Limite máximo de upload: 50 MB
MAX_UPLOAD_SIZE = 50 * 1024 * 1024

logger = logging.getLogger("perfectdf.web")

# Diretório base dos arquivos estáticos
STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(
    title="PerfectDF Web",
    description="Interface web para manipulação e edição de PDFs com PerfectDF",
    version="0.1.0",
)

# Monta o diretório de arquivos estáticos
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# =========================================================================
# Exception Handlers Globais (JSON seguro sem stack trace e sem vazamento)
# =========================================================================


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Retorna respostas HTTP padronizadas com a chave 'erro'."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"erro": str(exc.detail)},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Captura erros de validação da requisição (422) retornando mensagem clara em português."""
    return JSONResponse(
        status_code=422,
        content={"erro": "Dados da requisição inválidos ou incompletos."},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Captura exceções inesperadas registrando apenas o tipo da exceção e a rota no log."""
    logger.error("Erro interno %s na rota %s", type(exc).__name__, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"erro": "Ocorreu um erro interno ao processar a operação solicitada."},
    )


# =========================================================================
# Helpers de Validação e Gravação Segura
# =========================================================================


def _validar_extensao_pdf(nome_arquivo: str | None) -> None:
    """Valida se o arquivo informado possui extensão .pdf."""
    if not nome_arquivo or not nome_arquivo.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="O arquivo enviado deve ter a extensão .pdf",
        )


async def _salvar_e_validar_upload_pdf(arquivo: UploadFile, destino: Path) -> int:
    """Salva o UploadFile em disco com limite de 50MB e valida a integridade do PDF.

    Garante fechamento imediato com doc.close() em bloco try/finally.
    """
    _validar_extensao_pdf(arquivo.filename)

    tamanho = 0
    cabecalho = b""
    with open(destino, "wb") as f:
        while chunk := await arquivo.read(1024 * 1024):
            tamanho += len(chunk)
            if tamanho > MAX_UPLOAD_SIZE:
                raise HTTPException(
                    status_code=413,
                    detail="O arquivo excede o limite máximo permitido de 50 MB.",
                )
            if len(cabecalho) < 5:
                cabecalho += chunk[: 5 - len(cabecalho)]
            f.write(chunk)

    if not cabecalho.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=400,
            detail="O arquivo enviado não é um documento PDF válido.",
        )

    try:
        doc = abrir_pdf(str(destino))
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="O arquivo enviado não é um documento PDF válido.",
        )
    else:
        try:
            _ = len(doc)
        finally:
            doc.close()

    return tamanho


@app.get("/api/ping")
def ping() -> dict[str, str]:
    """Rota de verificação de integridade da API."""
    return {"status": "ok", "message": "pong"}


@app.get("/")
def index() -> FileResponse:
    """Serve a página principal da interface web."""
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/api/inspecionar")
async def inspecionar_pdf(arquivo: UploadFile = File(...)) -> dict[str, Any]:
    """Inspeciona um arquivo PDF enviado e retorna metadados e contagem de páginas."""
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path = Path(tmpdir) / "upload.pdf"
        tamanho = await _salvar_e_validar_upload_pdf(arquivo, temp_path)

        try:
            doc = abrir_pdf(str(temp_path))
            try:
                total_paginas = len(doc)
            finally:
                doc.close()
            metadados = ler_metadados(str(temp_path))
        except Exception:
            raise HTTPException(
                status_code=400,
                detail="Não foi possível ler as informações do documento PDF.",
            )

    return {
        "nome": arquivo.filename,
        "tamanho": tamanho,
        "total_paginas": total_paginas,
        "metadados": metadados,
    }


# =========================================================================
# 1. PÁGINAS (Girar, Extrair, Excluir, Reordenar, Juntar)
# =========================================================================


@app.post("/api/paginas/girar")
async def rota_girar_paginas(
    arquivo: UploadFile = File(...),
    graus: int = Form(90),
    paginas: str = Form(""),
) -> Response:
    """Gira páginas selecionadas do PDF."""
    with tempfile.TemporaryDirectory() as tmpdir:
        inp = Path(tmpdir) / "input.pdf"
        out = Path(tmpdir) / "output.pdf"
        await _salvar_e_validar_upload_pdf(arquivo, inp)

        doc = abrir_pdf(str(inp))
        try:
            total = len(doc)
        finally:
            doc.close()

        lista_paginas = (
            parsear_paginas(paginas) if paginas.strip() else list(range(1, total + 1))
        )
        try:
            girar_paginas(str(inp), paginas=lista_paginas, graus=graus, saida=str(out))
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        conteudo = out.read_bytes()

    return Response(
        content=conteudo,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="girado_{arquivo.filename}"'
        },
    )


@app.post("/api/paginas/extrair")
async def rota_extrair_paginas(
    arquivo: UploadFile = File(...),
    paginas: str = Form(...),
) -> Response:
    """Extrai páginas selecionadas para um novo PDF."""
    with tempfile.TemporaryDirectory() as tmpdir:
        inp = Path(tmpdir) / "input.pdf"
        out = Path(tmpdir) / "output.pdf"
        await _salvar_e_validar_upload_pdf(arquivo, inp)

        lista_paginas = parsear_paginas(paginas)
        if not lista_paginas:
            raise HTTPException(
                status_code=400, detail="Nenhuma página válida especificada."
            )

        try:
            extrair_paginas(str(inp), paginas=lista_paginas, saida=str(out))
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        conteudo = out.read_bytes()

    return Response(
        content=conteudo,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="extraido_{arquivo.filename}"'
        },
    )


@app.post("/api/paginas/excluir")
async def rota_excluir_paginas(
    arquivo: UploadFile = File(...),
    paginas: str = Form(...),
) -> Response:
    """Exclui páginas selecionadas de um PDF."""
    with tempfile.TemporaryDirectory() as tmpdir:
        inp = Path(tmpdir) / "input.pdf"
        out = Path(tmpdir) / "output.pdf"
        await _salvar_e_validar_upload_pdf(arquivo, inp)

        lista_paginas = parsear_paginas(paginas)
        if not lista_paginas:
            raise HTTPException(
                status_code=400,
                detail="Nenhuma página especificada para exclusão.",
            )

        try:
            excluir_paginas(str(inp), paginas=lista_paginas, saida=str(out))
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        conteudo = out.read_bytes()

    return Response(
        content=conteudo,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="excluido_{arquivo.filename}"'
        },
    )


@app.post("/api/paginas/reordenar")
async def rota_reordenar_paginas(
    arquivo: UploadFile = File(...),
    ordem: str = Form(...),
) -> Response:
    """Reordena páginas de um PDF."""
    with tempfile.TemporaryDirectory() as tmpdir:
        inp = Path(tmpdir) / "input.pdf"
        out = Path(tmpdir) / "output.pdf"
        await _salvar_e_validar_upload_pdf(arquivo, inp)

        try:
            reordenar_paginas(str(inp), ordem=ordem, saida=str(out))
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        conteudo = out.read_bytes()

    return Response(
        content=conteudo,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="reordenado_{arquivo.filename}"'
        },
    )


@app.post("/api/paginas/juntar")
async def rota_juntar_pdfs(
    arquivos: list[UploadFile] = File(...),
) -> Response:
    """Une dois ou mais arquivos PDF em um único documento."""
    if len(arquivos) < 2:
        raise HTTPException(
            status_code=400,
            detail="Envie pelo menos 2 arquivos PDF para juntar.",
        )

    with tempfile.TemporaryDirectory() as tmpdir:
        caminhos: list[str] = []
        for i, arq in enumerate(arquivos):
            p = Path(tmpdir) / f"doc_{i}.pdf"
            await _salvar_e_validar_upload_pdf(arq, p)
            caminhos.append(str(p))

        out = Path(tmpdir) / "unificado.pdf"
        try:
            juntar_pdfs(caminhos=caminhos, saida=str(out))
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        conteudo = out.read_bytes()

    return Response(
        content=conteudo,
        media_type="application/pdf",
        headers={
            "Content-Disposition": 'attachment; filename="documento_juntado.pdf"'
        },
    )


# =========================================================================
# 2. ANOTAÇÕES (Marca d'água, Numeração, Nota, Destacar)
# =========================================================================


@app.post("/api/anotacoes/marca-dagua")
async def rota_marca_dagua(
    arquivo: UploadFile = File(...),
    texto: str = Form(...),
    paginas: str = Form(""),
    opacidade: float = Form(0.3),
    angulo: float = Form(45.0),
    tamanho_fonte: float = Form(48.0),
) -> Response:
    """Aplica marca d'água de texto nas páginas do PDF."""
    with tempfile.TemporaryDirectory() as tmpdir:
        inp = Path(tmpdir) / "input.pdf"
        out = Path(tmpdir) / "output.pdf"
        await _salvar_e_validar_upload_pdf(arquivo, inp)

        pags = parsear_paginas(paginas) if paginas.strip() else None
        try:
            adicionar_marca_dagua(
                caminho=str(inp),
                saida=str(out),
                texto=texto,
                paginas=pags,
                opacidade=opacidade,
                angulo=angulo,
                tamanho_fonte=tamanho_fonte,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        conteudo = out.read_bytes()

    return Response(
        content=conteudo,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="marcadagua_{arquivo.filename}"'
        },
    )


@app.post("/api/anotacoes/numerar")
async def rota_numerar_paginas(
    arquivo: UploadFile = File(...),
    formato: str = Form("Página {n} de {total}"),
    posicao: str = Form("rodape-centro"),
    inicio: int = Form(1),
    paginas: str = Form(""),
    tamanho_fonte: float = Form(10.0),
) -> Response:
    """Adiciona numeração às páginas de um PDF."""
    with tempfile.TemporaryDirectory() as tmpdir:
        inp = Path(tmpdir) / "input.pdf"
        out = Path(tmpdir) / "output.pdf"
        await _salvar_e_validar_upload_pdf(arquivo, inp)

        pags = parsear_paginas(paginas) if paginas.strip() else None
        try:
            numerar_paginas(
                caminho=str(inp),
                saida=str(out),
                formato=formato,
                posicao=posicao,
                inicio=inicio,
                paginas=pags,
                tamanho_fonte=tamanho_fonte,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        conteudo = out.read_bytes()

    return Response(
        content=conteudo,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="numerado_{arquivo.filename}"'
        },
    )


@app.post("/api/anotacoes/nota")
async def rota_adicionar_nota(
    arquivo: UploadFile = File(...),
    pagina: int = Form(1),
    texto: str = Form(...),
    pos_x: float = Form(50.0),
    pos_y: float = Form(50.0),
) -> Response:
    """Adiciona uma nota (post-it) a uma página específica."""
    with tempfile.TemporaryDirectory() as tmpdir:
        inp = Path(tmpdir) / "input.pdf"
        out = Path(tmpdir) / "output.pdf"
        await _salvar_e_validar_upload_pdf(arquivo, inp)

        try:
            adicionar_nota(
                caminho=str(inp),
                saida=str(out),
                pagina=pagina,
                texto=texto,
                posicao=(pos_x, pos_y),
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        conteudo = out.read_bytes()

    return Response(
        content=conteudo,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="com_nota_{arquivo.filename}"'
        },
    )


@app.post("/api/anotacoes/destacar")
async def rota_destacar_texto(
    arquivo: UploadFile = File(...),
    termo: str = Form(...),
    paginas: str = Form(""),
    tipo: str = Form("destaque"),
    cor: str = Form("amarelo"),
    ignorar_maiusculas: bool = Form(True),
) -> Response:
    """Destaca termos de texto no PDF."""
    with tempfile.TemporaryDirectory() as tmpdir:
        inp = Path(tmpdir) / "input.pdf"
        out = Path(tmpdir) / "output.pdf"
        await _salvar_e_validar_upload_pdf(arquivo, inp)

        pags = parsear_paginas(paginas) if paginas.strip() else None
        try:
            destacar_texto(
                caminho=str(inp),
                saida=str(out),
                termo=termo,
                paginas=pags,
                tipo=tipo,
                cor=cor,
                ignorar_maiusculas=ignorar_maiusculas,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        conteudo = out.read_bytes()

    return Response(
        content=conteudo,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="destacado_{arquivo.filename}"'
        },
    )


# =========================================================================
# 3. FORMULÁRIOS (Listar campos, Preencher, Achatar)
# =========================================================================


@app.post("/api/formularios/listar")
async def rota_listar_campos(
    arquivo: UploadFile = File(...),
) -> dict[str, Any]:
    """Lista todos os campos de formulário presentes no PDF."""
    with tempfile.TemporaryDirectory() as tmpdir:
        inp = Path(tmpdir) / "input.pdf"
        await _salvar_e_validar_upload_pdf(arquivo, inp)
        try:
            campos = listar_campos(str(inp))
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    return {"total": len(campos), "campos": campos}


@app.post("/api/formularios/preencher")
async def rota_preencher_formulario(
    arquivo: UploadFile = File(...),
    dados_json: str = Form(...),
) -> Response:
    """Preenche campos de formulário a partir de um JSON."""
    try:
        valores = json.loads(dados_json)
        if not isinstance(valores, dict):
            raise ValueError()
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Formato de dados JSON inválido. Certifique-se de enviar um objeto chave-valor válido.",
        )

    with tempfile.TemporaryDirectory() as tmpdir:
        inp = Path(tmpdir) / "input.pdf"
        out = Path(tmpdir) / "output.pdf"
        await _salvar_e_validar_upload_pdf(arquivo, inp)

        try:
            preencher_formulario(str(inp), valores=valores, saida=str(out))
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        conteudo = out.read_bytes()

    return Response(
        content=conteudo,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="preenchido_{arquivo.filename}"'
        },
    )


@app.post("/api/formularios/achatar")
async def rota_achatar_formulario(
    arquivo: UploadFile = File(...),
) -> Response:
    """Achata campos de formulário tornando o conteúdo estático."""
    with tempfile.TemporaryDirectory() as tmpdir:
        inp = Path(tmpdir) / "input.pdf"
        out = Path(tmpdir) / "output.pdf"
        await _salvar_e_validar_upload_pdf(arquivo, inp)

        try:
            achatar_formulario(str(inp), saida=str(out))
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        conteudo = out.read_bytes()

    return Response(
        content=conteudo,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="achatado_{arquivo.filename}"'
        },
    )


# =========================================================================
# 4. TEXTO & METADADOS (Extrair texto, Adicionar texto, Editar metadados)
# =========================================================================


@app.post("/api/texto/extrair")
async def rota_extrair_texto(
    arquivo: UploadFile = File(...),
    paginas: str = Form(""),
) -> dict[str, str]:
    """Extrai texto legível das páginas do PDF."""
    with tempfile.TemporaryDirectory() as tmpdir:
        inp = Path(tmpdir) / "input.pdf"
        await _salvar_e_validar_upload_pdf(arquivo, inp)

        pags = parsear_paginas(paginas) if paginas.strip() else None
        try:
            texto = extrair_texto(str(inp), paginas=pags)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    return {"texto": texto}


@app.post("/api/texto/adicionar")
async def rota_adicionar_texto(
    arquivo: UploadFile = File(...),
    pagina: int = Form(1),
    texto: str = Form(...),
    pos_x: float = Form(50.0),
    pos_y: float = Form(50.0),
    fonte: str = Form("helv"),
    tamanho: float = Form(12.0),
    cor: str = Form("preto"),
) -> Response:
    """Adiciona texto em posição específica de uma página."""
    with tempfile.TemporaryDirectory() as tmpdir:
        inp = Path(tmpdir) / "input.pdf"
        out = Path(tmpdir) / "output.pdf"
        await _salvar_e_validar_upload_pdf(arquivo, inp)

        try:
            adicionar_texto(
                pdf=str(inp),
                pagina=pagina,
                texto=texto,
                posicao=(pos_x, pos_y),
                fonte=fonte,
                tamanho=tamanho,
                cor=cor,
                saida=str(out),
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        conteudo = out.read_bytes()

    return Response(
        content=conteudo,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="texto_inserido_{arquivo.filename}"'
        },
    )


@app.post("/api/metadados/editar")
async def rota_editar_metadados(
    arquivo: UploadFile = File(...),
    titulo: str = Form(""),
    autor: str = Form(""),
    assunto: str = Form(""),
    palavras_chave: str = Form(""),
) -> Response:
    """Atualiza metadados do documento PDF."""
    novos_meta: dict[str, str] = {}
    if titulo:
        novos_meta["title"] = titulo
    if autor:
        novos_meta["author"] = autor
    if assunto:
        novos_meta["subject"] = assunto
    if palavras_chave:
        novos_meta["keywords"] = palavras_chave

    with tempfile.TemporaryDirectory() as tmpdir:
        inp = Path(tmpdir) / "input.pdf"
        out = Path(tmpdir) / "output.pdf"
        await _salvar_e_validar_upload_pdf(arquivo, inp)

        try:
            editar_metadados(str(inp), novos=novos_meta, saida=str(out))
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        conteudo = out.read_bytes()

    return Response(
        content=conteudo,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="metadados_{arquivo.filename}"'
        },
    )


# =========================================================================
# 5. COMPRESSÃO & SEGURANÇA (Comprimir, Proteger, Remover Senha)
# =========================================================================


@app.post("/api/compressao/comprimir")
async def rota_comprimir_pdf(
    arquivo: UploadFile = File(...),
    nivel: str = Form("medio"),
) -> Response:
    """Comprime o documento PDF reduzindo seu tamanho."""
    with tempfile.TemporaryDirectory() as tmpdir:
        inp = Path(tmpdir) / "input.pdf"
        out = Path(tmpdir) / "output.pdf"
        await _salvar_e_validar_upload_pdf(arquivo, inp)

        try:
            comprimir_pdf(str(inp), saida=str(out), nivel=nivel)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        conteudo = out.read_bytes()

    return Response(
        content=conteudo,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="comprimido_{arquivo.filename}"'
        },
    )


@app.post("/api/seguranca/proteger")
async def rota_proteger_pdf(
    arquivo: UploadFile = File(...),
    senha_usuario: str = Form(...),
    senha_dono: str = Form(""),
) -> Response:
    """Protege um PDF com senha de usuário."""
    with tempfile.TemporaryDirectory() as tmpdir:
        inp = Path(tmpdir) / "input.pdf"
        out = Path(tmpdir) / "output.pdf"
        await _salvar_e_validar_upload_pdf(arquivo, inp)

        dono = senha_dono if senha_dono.strip() else None
        try:
            proteger_pdf(
                str(inp),
                saida=str(out),
                senha_usuario=senha_usuario,
                senha_dono=dono,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        conteudo = out.read_bytes()

    return Response(
        content=conteudo,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="protegido_{arquivo.filename}"'
        },
    )


@app.post("/api/seguranca/remover-senha")
async def rota_remover_senha(
    arquivo: UploadFile = File(...),
    senha: str = Form(...),
) -> Response:
    """Remove a senha de um PDF protegido."""
    with tempfile.TemporaryDirectory() as tmpdir:
        inp = Path(tmpdir) / "input.pdf"
        out = Path(tmpdir) / "output.pdf"
        await _salvar_e_validar_upload_pdf(arquivo, inp)

        try:
            remover_senha(str(inp), senha=senha, saida=str(out))
        except ValueError as e:
            # Nunca expõe a senha digitada no erro
            msg = str(e)
            if (
                "senha informada está incorreta" in msg.lower()
                or "não possui proteção" in msg.lower()
            ):
                raise HTTPException(status_code=400, detail=msg)
            raise HTTPException(
                status_code=400, detail="Senha incorreta ou inválida para o documento."
            )

        conteudo = out.read_bytes()

    return Response(
        content=conteudo,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="desbloqueado_{arquivo.filename}"'
        },
    )


# Rota retrocompatível de processamento geral
@app.post("/api/processar")
async def processar_pdf(
    arquivo: UploadFile = File(...),
    operacao: str = Form("comprimir"),
    nivel: str = Form("medio"),
    graus: int = Form(90),
    paginas: str = Form(""),
) -> Response:
    """Despachante geral para compatibilidade com versões iniciais."""
    if operacao == "comprimir":
        return await rota_comprimir_pdf(arquivo=arquivo, nivel=nivel)
    elif operacao == "girar":
        return await rota_girar_paginas(arquivo=arquivo, graus=graus, paginas=paginas)
    raise HTTPException(
        status_code=400, detail=f"Operação '{operacao}' não reconhecida."
    )
