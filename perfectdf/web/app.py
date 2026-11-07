"""Aplicação backend FastAPI para a interface web do PerfectDF."""

from pathlib import Path
import tempfile

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from perfectdf.comum import abrir_pdf, parsear_paginas
from perfectdf.compressao import comprimir_pdf
from perfectdf.metadados import ler_metadados
from perfectdf.paginas import girar_paginas

# Diretório base dos arquivos estáticos
STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(
    title="PerfectDF Web",
    description="Interface web para manipulação e edição de PDFs com PerfectDF",
    version="0.1.0",
)

# Monta o diretório de arquivos estáticos
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/api/ping")
def ping() -> dict[str, str]:
    """Rota de verificação de integridade da API."""
    return {"status": "ok", "message": "pong"}


@app.get("/")
def index() -> FileResponse:
    """Serve a página principal da interface web."""
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/api/inspecionar")
async def inspecionar_pdf(arquivo: UploadFile = File(...)) -> dict[str, object]:
    """Inspeciona um arquivo PDF enviado e retorna informações básicas de forma segura."""
    if not arquivo.filename or not arquivo.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="O arquivo enviado deve ter a extensão .pdf",
        )

    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path = Path(tmpdir) / "upload.pdf"
        tamanho = 0
        with open(temp_path, "wb") as f:
            while chunk := await arquivo.read(1024 * 1024):
                f.write(chunk)
                tamanho += len(chunk)

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


@app.post("/api/processar")
async def processar_pdf(
    arquivo: UploadFile = File(...),
    operacao: str = Form("comprimir"),
    nivel: str = Form("medio"),
    graus: int = Form(90),
    paginas: str = Form(""),
) -> Response:
    """Recebe um PDF, executa a operação solicitada via módulos do PerfectDF e devolve o PDF processado.

    Utiliza diretório temporário seguro (tempfile) com limpeza garantida ao término.
    """
    if not arquivo.filename or not arquivo.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="O arquivo enviado deve ter a extensão .pdf",
        )

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "origem.pdf"
        output_path = Path(tmpdir) / "saida.pdf"

        # Gravação em blocos para evitar consumo excessivo de memória
        with open(input_path, "wb") as f:
            while chunk := await arquivo.read(1024 * 1024):
                f.write(chunk)

        # Validação estrutural do PDF com abrir_pdf
        try:
            doc = abrir_pdf(str(input_path))
            total_paginas = len(doc)
            doc.close()
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Arquivo PDF inválido ou corrompido: {e}",
            )

        # Execução da operação utilizando os módulos existentes
        try:
            if operacao == "comprimir":
                comprimir_pdf(str(input_path), str(output_path), nivel=nivel)
            elif operacao == "girar":
                lista_paginas = (
                    parsear_paginas(paginas)
                    if paginas.strip()
                    else list(range(1, total_paginas + 1))
                )
                girar_paginas(
                    caminho=str(input_path),
                    paginas=lista_paginas,
                    graus=graus,
                    saida=str(output_path),
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Operação '{operacao}' não suportada.",
                )

            if not output_path.exists():
                raise HTTPException(
                    status_code=500,
                    detail="Falha ao gerar o arquivo PDF processado.",
                )

            conteudo_final = output_path.read_bytes()
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Erro durante o processamento do PDF: {e}",
            )

    nome_saida = f"processado_{arquivo.filename}"
    return Response(
        content=conteudo_final,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{nome_saida}"',
        },
    )
