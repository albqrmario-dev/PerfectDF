"""Aplicação backend FastAPI para a interface web do PerfectDF."""

import json
from pathlib import Path
import tempfile
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

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

# Diretório base dos arquivos estáticos
STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(
    title="PerfectDF Web",
    description="Interface web para manipulação e edição de PDFs com PerfectDF",
    version="0.1.0",
)

# Monta o diretório de arquivos estáticos
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def _validar_extensao_pdf(nome_arquivo: str | None) -> None:
    """Valida se o arquivo informado possui extensão .pdf."""
    if not nome_arquivo or not nome_arquivo.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="O arquivo enviado deve ter a extensão .pdf",
        )


async def _salvar_upload(arquivo: UploadFile, destino: Path) -> int:
    """Salva um UploadFile em disco em blocos seguros."""
    tamanho = 0
    with open(destino, "wb") as f:
        while chunk := await arquivo.read(1024 * 1024):
            f.write(chunk)
            tamanho += len(chunk)
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
    _validar_extensao_pdf(arquivo.filename)

    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path = Path(tmpdir) / "upload.pdf"
        tamanho = await _salvar_upload(arquivo, temp_path)

        try:
            doc = abrir_pdf(str(temp_path))
            total_paginas = len(doc)
            doc.close()
            metadados = ler_metadados(str(temp_path))
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Não foi possível ler o arquivo PDF: {e}",
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
    _validar_extensao_pdf(arquivo.filename)

    with tempfile.TemporaryDirectory() as tmpdir:
        inp = Path(tmpdir) / "input.pdf"
        out = Path(tmpdir) / "output.pdf"
        await _salvar_upload(arquivo, inp)

        doc = abrir_pdf(str(inp))
        total = len(doc)
        doc.close()

        lista_paginas = (
            parsear_paginas(paginas) if paginas.strip() else list(range(1, total + 1))
        )
        girar_paginas(str(inp), paginas=lista_paginas, graus=graus, saida=str(out))
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
    _validar_extensao_pdf(arquivo.filename)

    with tempfile.TemporaryDirectory() as tmpdir:
        inp = Path(tmpdir) / "input.pdf"
        out = Path(tmpdir) / "output.pdf"
        await _salvar_upload(arquivo, inp)

        lista_paginas = parsear_paginas(paginas)
        if not lista_paginas:
            raise HTTPException(
                status_code=400, detail="Nenhuma página válida especificada."
            )

        extrair_paginas(str(inp), paginas=lista_paginas, saida=str(out))
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
    _validar_extensao_pdf(arquivo.filename)

    with tempfile.TemporaryDirectory() as tmpdir:
        inp = Path(tmpdir) / "input.pdf"
        out = Path(tmpdir) / "output.pdf"
        await _salvar_upload(arquivo, inp)

        lista_paginas = parsear_paginas(paginas)
        if not lista_paginas:
            raise HTTPException(
                status_code=400,
                detail="Nenhuma página especificada para exclusão.",
            )

        excluir_paginas(str(inp), paginas=lista_paginas, saida=str(out))
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
    _validar_extensao_pdf(arquivo.filename)

    with tempfile.TemporaryDirectory() as tmpdir:
        inp = Path(tmpdir) / "input.pdf"
        out = Path(tmpdir) / "output.pdf"
        await _salvar_upload(arquivo, inp)

        reordenar_paginas(str(inp), ordem=ordem, saida=str(out))
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
            _validar_extensao_pdf(arq.filename)
            p = Path(tmpdir) / f"doc_{i}.pdf"
            await _salvar_upload(arq, p)
            caminhos.append(str(p))

        out = Path(tmpdir) / "unificado.pdf"
        juntar_pdfs(caminhos=caminhos, saida=str(out))
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
    _validar_extensao_pdf(arquivo.filename)

    with tempfile.TemporaryDirectory() as tmpdir:
        inp = Path(tmpdir) / "input.pdf"
        out = Path(tmpdir) / "output.pdf"
        await _salvar_upload(arquivo, inp)

        pags = parsear_paginas(paginas) if paginas.strip() else None
        adicionar_marca_dagua(
            caminho=str(inp),
            saida=str(out),
            texto=texto,
            paginas=pags,
            opacidade=opacidade,
            angulo=angulo,
            tamanho_fonte=tamanho_fonte,
        )
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
    _validar_extensao_pdf(arquivo.filename)

    with tempfile.TemporaryDirectory() as tmpdir:
        inp = Path(tmpdir) / "input.pdf"
        out = Path(tmpdir) / "output.pdf"
        await _salvar_upload(arquivo, inp)

        pags = parsear_paginas(paginas) if paginas.strip() else None
        numerar_paginas(
            caminho=str(inp),
            saida=str(out),
            formato=formato,
            posicao=posicao,
            inicio=inicio,
            paginas=pags,
            tamanho_fonte=tamanho_fonte,
        )
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
    _validar_extensao_pdf(arquivo.filename)

    with tempfile.TemporaryDirectory() as tmpdir:
        inp = Path(tmpdir) / "input.pdf"
        out = Path(tmpdir) / "output.pdf"
        await _salvar_upload(arquivo, inp)

        adicionar_nota(
            caminho=str(inp),
            saida=str(out),
            pagina=pagina,
            texto=texto,
            posicao=(pos_x, pos_y),
        )
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
    _validar_extensao_pdf(arquivo.filename)

    with tempfile.TemporaryDirectory() as tmpdir:
        inp = Path(tmpdir) / "input.pdf"
        out = Path(tmpdir) / "output.pdf"
        await _salvar_upload(arquivo, inp)

        pags = parsear_paginas(paginas) if paginas.strip() else None
        destacar_texto(
            caminho=str(inp),
            saida=str(out),
            termo=termo,
            paginas=pags,
            tipo=tipo,
            cor=cor,
            ignorar_maiusculas=ignorar_maiusculas,
        )
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
    _validar_extensao_pdf(arquivo.filename)

    with tempfile.TemporaryDirectory() as tmpdir:
        inp = Path(tmpdir) / "input.pdf"
        await _salvar_upload(arquivo, inp)
        campos = listar_campos(str(inp))

    return {"total": len(campos), "campos": campos}


@app.post("/api/formularios/preencher")
async def rota_preencher_formulario(
    arquivo: UploadFile = File(...),
    dados_json: str = Form(...),
) -> Response:
    """Preenche campos de formulário a partir de um JSON."""
    _validar_extensao_pdf(arquivo.filename)

    try:
        valores = json.loads(dados_json)
        if not isinstance(valores, dict):
            raise ValueError("O formato de dados_json deve ser um dicionário.")
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"JSON de dados inválido: {e}",
        )

    with tempfile.TemporaryDirectory() as tmpdir:
        inp = Path(tmpdir) / "input.pdf"
        out = Path(tmpdir) / "output.pdf"
        await _salvar_upload(arquivo, inp)

        preencher_formulario(str(inp), valores=valores, saida=str(out))
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
    _validar_extensao_pdf(arquivo.filename)

    with tempfile.TemporaryDirectory() as tmpdir:
        inp = Path(tmpdir) / "input.pdf"
        out = Path(tmpdir) / "output.pdf"
        await _salvar_upload(arquivo, inp)

        achatar_formulario(str(inp), saida=str(out))
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
    _validar_extensao_pdf(arquivo.filename)

    with tempfile.TemporaryDirectory() as tmpdir:
        inp = Path(tmpdir) / "input.pdf"
        await _salvar_upload(arquivo, inp)

        pags = parsear_paginas(paginas) if paginas.strip() else None
        texto = extrair_texto(str(inp), paginas=pags)

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
    _validar_extensao_pdf(arquivo.filename)

    with tempfile.TemporaryDirectory() as tmpdir:
        inp = Path(tmpdir) / "input.pdf"
        out = Path(tmpdir) / "output.pdf"
        await _salvar_upload(arquivo, inp)

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
    _validar_extensao_pdf(arquivo.filename)

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
        await _salvar_upload(arquivo, inp)

        editar_metadados(str(inp), novos=novos_meta, saida=str(out))
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
    _validar_extensao_pdf(arquivo.filename)

    with tempfile.TemporaryDirectory() as tmpdir:
        inp = Path(tmpdir) / "input.pdf"
        out = Path(tmpdir) / "output.pdf"
        await _salvar_upload(arquivo, inp)

        comprimir_pdf(str(inp), saida=str(out), nivel=nivel)
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
    _validar_extensao_pdf(arquivo.filename)

    with tempfile.TemporaryDirectory() as tmpdir:
        inp = Path(tmpdir) / "input.pdf"
        out = Path(tmpdir) / "output.pdf"
        await _salvar_upload(arquivo, inp)

        dono = senha_dono if senha_dono.strip() else None
        proteger_pdf(
            str(inp),
            saida=str(out),
            senha_usuario=senha_usuario,
            senha_dono=dono,
        )
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
    _validar_extensao_pdf(arquivo.filename)

    with tempfile.TemporaryDirectory() as tmpdir:
        inp = Path(tmpdir) / "input.pdf"
        out = Path(tmpdir) / "output.pdf"
        await _salvar_upload(arquivo, inp)

        remover_senha(str(inp), senha=senha, saida=str(out))
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
        return await rota_girar_paginas(
            arquivo=arquivo, graus=graus, paginas=paginas
        )
    raise HTTPException(
        status_code=400, detail=f"Operação '{operacao}' não reconhecida."
    )
