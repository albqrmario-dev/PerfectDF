import pymupdf


def abrir_pdf(caminho):
    return pymupdf.open(caminho)
