import pymupdf


def abrir_pdf(caminho):
    return pymupdf.open(caminho)


def juntar_pdfs(caminhos, saida):

    doc = pymupdf.open()

    for caminho in caminhos:
        doc.insert_pdf(abrir_pdf(caminho))

    doc.save(saida)
    return saida
