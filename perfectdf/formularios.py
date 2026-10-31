"""Módulo de formulários PDF (AcroForm) do PerfectDF.

Permite listar campos, preencher valores e achatar formulários
utilizando os widgets nativos do PyMuPDF, sem dependências extras.
"""

import os

import pymupdf

from perfectdf.comum import abrir_pdf

# Mapeamento dos tipos de widget do PyMuPDF para nomes amigáveis em português.
_TIPO_WIDGET: dict[int, str] = {
    pymupdf.PDF_WIDGET_TYPE_TEXT: "texto",  # pyright: ignore[reportAttributeAccessIssue]  # PyMuPDF exports this runtime constant without declaring it.
    pymupdf.PDF_WIDGET_TYPE_CHECKBOX: "checkbox",  # pyright: ignore[reportAttributeAccessIssue]  # PyMuPDF exports this runtime constant without declaring it.
    pymupdf.PDF_WIDGET_TYPE_RADIOBUTTON: "radio",  # pyright: ignore[reportAttributeAccessIssue]  # PyMuPDF exports this runtime constant without declaring it.
    pymupdf.PDF_WIDGET_TYPE_LISTBOX: "lista",  # pyright: ignore[reportAttributeAccessIssue]  # PyMuPDF exports this runtime constant without declaring it.
    pymupdf.PDF_WIDGET_TYPE_COMBOBOX: "lista",  # pyright: ignore[reportAttributeAccessIssue]  # PyMuPDF exports this runtime constant without declaring it.
    pymupdf.PDF_WIDGET_TYPE_BUTTON: "botão",  # pyright: ignore[reportAttributeAccessIssue]  # PyMuPDF exports this runtime constant without declaring it.
    pymupdf.PDF_WIDGET_TYPE_SIGNATURE: "assinatura",  # pyright: ignore[reportAttributeAccessIssue]  # PyMuPDF exports this runtime constant without declaring it.
}


def _tipo_amigavel(field_type: int) -> str:
    """Retorna o nome amigável em português do tipo de widget."""
    return _TIPO_WIDGET.get(field_type, "desconhecido")


def _validar_caminho_origem(caminho: str) -> None:
    """Validações comuns para o caminho de origem."""
    if not isinstance(caminho, str) or not caminho.strip():
        raise ValueError(
            "O caminho do arquivo de origem deve ser uma string não vazia."
        )
    if not os.path.isfile(caminho):
        raise ValueError(f"O arquivo de origem não foi encontrado: '{caminho}'.")


def _validar_saida(caminho: str, saida: str) -> None:
    """Validações comuns para o caminho de saída."""
    if not isinstance(saida, str) or not saida.strip():
        raise ValueError("O caminho do arquivo de saída deve ser uma string não vazia.")
    if os.path.abspath(caminho) == os.path.abspath(saida):
        raise ValueError(
            "O arquivo de saída não pode ser igual ao arquivo de origem "
            "para evitar sobrescrever o documento original."
        )


def listar_campos(
    caminho: str,
) -> list[dict[str, str | int | bool | None]]:
    """Lista todos os campos de formulário (widgets) presentes em um PDF.

    Parâmetros:
        caminho: Caminho do arquivo PDF.

    Retorna:
        Lista de dicionários, cada um contendo:
        - 'nome': nome do campo (field_name).
        - 'tipo': tipo amigável em português ('texto', 'checkbox', 'radio',
                   'lista', 'botão', 'assinatura' ou 'desconhecido').
        - 'valor': valor atual do campo (string ou None).
        - 'pagina': número da página (base 1) onde o campo está.

    Lança:
        ValueError: Se o caminho for inválido, o arquivo não existir ou o
                    PDF não contiver formulário.
    """
    _validar_caminho_origem(caminho)

    doc = abrir_pdf(caminho)
    try:
        campos: list[dict[str, str | int | bool | None]] = []
        for num_pagina in range(doc.page_count):
            page = doc[num_pagina]
            for item in page.widgets():
                if not isinstance(item, pymupdf.Widget):
                    continue
                widget = item
                campos.append(
                    {
                        "nome": widget.field_name,
                        "tipo": _tipo_amigavel(widget.field_type),
                        "valor": widget.field_value,
                        "pagina": num_pagina + 1,
                    }
                )

        if not campos:
            raise ValueError(
                "O PDF não contém formulário (nenhum campo AcroForm encontrado)."
            )

        return campos
    finally:
        doc.close()


def preencher_formulario(
    caminho: str,
    valores: dict[str, str | bool],
    saida: str,
) -> str:
    """Preenche campos de um formulário PDF pelos seus nomes.

    Parâmetros:
        caminho: Caminho do arquivo PDF de origem.
        valores: Dicionário {nome_do_campo: novo_valor}. Para campos de texto,
                 o valor deve ser uma string. Para checkboxes, pode ser bool
                 (True/False) ou string ("Yes"/"Off").
        saida: Caminho do arquivo PDF resultante.

    Retorna:
        O caminho do arquivo salvo.

    Lança:
        ValueError: Se caminhos forem inválidos, se o arquivo não existir,
                    se o PDF não tiver formulário, ou se algum campo informado
                    não existir no documento.
    """
    _validar_caminho_origem(caminho)
    _validar_saida(caminho, saida)

    if not isinstance(valores, dict) or not valores:
        raise ValueError(
            "O parâmetro 'valores' deve ser um dicionário não vazio "
            "com os campos a preencher."
        )

    doc = abrir_pdf(caminho)
    try:
        # Mapear todos os widgets disponíveis por nome
        widgets_por_nome: dict[
            str | None, list[tuple[pymupdf.Page, pymupdf.Widget]]
        ] = {}
        for num_pagina in range(doc.page_count):
            page = doc[num_pagina]
            for item in page.widgets():
                if not isinstance(item, pymupdf.Widget):
                    continue
                widget = item
                nome = widget.field_name
                if nome is None:
                    widgets_por_nome.setdefault(None, []).append((page, widget))
                    continue
                widgets_por_nome.setdefault(nome, []).append((page, widget))

        if not widgets_por_nome:
            raise ValueError(
                "O PDF não contém formulário (nenhum campo AcroForm encontrado)."
            )

        # Verificar se todos os campos solicitados existem
        campos_inexistentes = [nome for nome in valores if nome not in widgets_por_nome]
        if campos_inexistentes:
            disponiveis = sorted(
                widgets_por_nome.keys(), key=lambda nome: (nome is None, nome or "")
            )
            raise ValueError(
                f"Campo(s) não encontrado(s) no formulário: "
                f"{campos_inexistentes}. "
                f"Campos disponíveis: {disponiveis}."
            )

        # Preencher cada campo
        for nome, valor in valores.items():
            for page, widget in widgets_por_nome[nome]:
                if widget.field_type == pymupdf.PDF_WIDGET_TYPE_CHECKBOX:  # pyright: ignore[reportAttributeAccessIssue]  # PyMuPDF omits this runtime constant from its declarations.
                    if isinstance(valor, bool):
                        widget.field_value = "Yes" if valor else "Off"  # pyright: ignore[reportAttributeAccessIssue]  # PyMuPDF's Widget fields are dynamic and missing from its declarations.
                    else:
                        widget.field_value = str(valor)  # pyright: ignore[reportAttributeAccessIssue]  # PyMuPDF's Widget fields are dynamic and missing from its declarations.
                else:
                    widget.field_value = str(valor)  # pyright: ignore[reportAttributeAccessIssue]  # PyMuPDF's Widget fields are dynamic and missing from its declarations.
                widget.update()

        doc.save(saida)
        return saida
    finally:
        doc.close()


def achatar_formulario(caminho: str, saida: str) -> str:
    """Converte os campos de formulário em conteúdo fixo (não editável).

    Após o achatamento, os valores preenchidos permanecem visíveis no PDF,
    mas não podem mais ser modificados por leitores de PDF.

    Parâmetros:
        caminho: Caminho do arquivo PDF de origem.
        saida: Caminho do arquivo PDF resultante.

    Retorna:
        O caminho do arquivo salvo.

    Lança:
        ValueError: Se caminhos forem inválidos, se o arquivo não existir
                    ou se o PDF não contiver formulário para achatar.
    """
    _validar_caminho_origem(caminho)
    _validar_saida(caminho, saida)

    doc = abrir_pdf(caminho)
    try:
        tem_widgets = False
        for num_pagina in range(doc.page_count):
            page = doc[num_pagina]
            # Verificar se tem ao menos um widget
            for _ in page.widgets():
                tem_widgets = True
                break
            if tem_widgets:
                break

        if not tem_widgets:
            raise ValueError(
                "O PDF não contém formulário (nenhum campo AcroForm encontrado) "
                "para achatar."
            )

        # Achatar usando o método nativo do PyMuPDF
        # Precisamos re-abrir para usar need_appearances antes de achatar
        for num_pagina in range(doc.page_count):
            page = doc[num_pagina]
            # Apagar cada widget e inserir sua aparência como conteúdo fixo
            annot = page.first_widget
            while annot is not None:
                next_annot = annot.next
                if isinstance(annot, pymupdf.Widget):
                    page.delete_widget(annot)
                annot = next_annot

        doc.save(saida)
        return saida
    finally:
        doc.close()
