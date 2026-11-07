"""Aplicação backend FastAPI para a interface web do PerfectDF."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

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
