# PerfectDF

O **PerfectDF** é uma biblioteca Python gratuita e open source projetada para facilitar a manipulação, edição e otimização de documentos PDF. Construída sobre o motor [PyMuPDF](https://pymupdf.readthedocs.io/), oferece uma API simples, direta e robusta em português para as tarefas mais comuns do dia a dia com arquivos PDF.

---

## 🚀 Instalação

Recomenda-se o uso de um ambiente virtual (`venv`):

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/perfectdf.git
cd perfectdf

# Crie e ative o ambiente virtual
python3 -m venv venv
source venv/bin/activate  # No Linux/macOS
# ou: venv\Scripts\activate  # No Windows

# Instale as dependências
pip install -r requirements.txt
```

---

## 💡 Exemplos de Uso

Todas as funções principais podem ser importadas diretamente do pacote `perfectdf`:

```python
from perfectdf import (
    juntar_pdfs,
    extrair_paginas,
    girar_paginas,
    excluir_paginas,
    reordenar_paginas,
    ler_metadados,
    editar_metadados,
    extrair_texto,
    adicionar_texto,
    adicionar_marca_dagua,
    numerar_paginas,
    adicionar_nota,
    destacar_texto,
    comprimir_pdf,
    proteger_pdf,
    remover_senha,
    pdf_para_imagens,
    imagens_para_pdf,
    adicionar_imagem,
    listar_campos,
    preencher_formulario,
    achatar_formulario,
)
```

### 1. Manipulação de Páginas

#### Juntar PDFs
Une múltiplos arquivos PDF em um único documento resultante.
```python
juntar_pdfs(["capa.pdf", "capitulo1.pdf", "anexos.pdf"], saida="documento_completo.pdf")
```

#### Extrair Páginas
Extrai páginas específicas (base 1) para um novo arquivo na ordem indicada.
```python
extrair_paginas("documento.pdf", paginas=[1, 3, 5], saida="paginas_selecionadas.pdf")
```

#### Girar Páginas
Aplica rotação (múltiplos de 90 graus: 90, 180, 270, -90) em páginas específicas.
```python
girar_paginas("documento.pdf", paginas=[2], graus=90, saida="documento_girado.pdf")
```

#### Excluir Páginas
Remove páginas específicas (base 1) e salva o PDF resultante.
```python
excluir_paginas("documento.pdf", paginas=[2, 4], saida="documento_sem_paginas.pdf")
```

#### Reordenar Páginas
Reorganiza a sequência de páginas aceitando listas de inteiros ou strings formatadas (ex: `"3, 1-2"`).
```python
reordenar_paginas("documento.pdf", ordem="3, 1-2", saida="documento_reordenado.pdf")
```

---

### 2. Metadados e Texto

#### Ler Metadados
Obtém o dicionário de metadados do documento.
```python
metadados = ler_metadados("documento.pdf")
print(metadados.get("title"), metadados.get("author"))
```

#### Editar Metadados
Modifica campos padrão (`title`, `author`, `subject`, `keywords`).
```python
novos = {
    "title": "Relatório Anual 2026",
    "author": "Equipe PerfectDF",
    "subject": "Financeiro",
    "keywords": "relatório, pdf, 2026",
}
editar_metadados("documento.pdf", novos=novos, saida="documento_atualizado.pdf")
```

#### Extrair Texto
Extrai o texto legível de páginas específicas ou de todo o PDF.
```python
# Todas as páginas
texto = extrair_texto("documento.pdf")

# Páginas selecionadas (string ou lista)
texto_parcial = extrair_texto("documento.pdf", paginas="1-3, 5")
print(texto)
```

#### Adicionar Texto
Insere texto com fonte, tamanho, cor e posição visual configuráveis.
```python
adicionar_texto(
    pdf="documento.pdf",
    pagina=1,
    texto="Aprovado pela Diretoria",
    posicao=(50, 100),
    fonte="helv",
    tamanho=14,
    cor="azul",  # ou tupla RGB: (0.0, 0.5, 1.0)
    saida="documento_aprovado.pdf",  # Opcional: se omitido, modifica o próprio arquivo
)
```

---

### 3. Anotações e Marcações

#### Adicionar Marca d'Água
Insere uma marca d'água diagonal, centralizada e translúcida.
```python
adicionar_marca_dagua(
    caminho="documento.pdf",
    saida="documento_confidencial.pdf",
    texto="CONFIDENCIAL",
    opacidade=0.25,
    angulo=45,
    tamanho_fonte=48,
)
```

#### Numerar Páginas
Adiciona rodapé ou cabeçalho de numeração configurável.
```python
numerar_paginas(
    caminho="documento.pdf",
    saida="documento_numerado.pdf",
    formato="Página {n} de {total}",
    posicao="rodape-centro",  # ou: 'rodape-direita', 'topo-centro', etc.
    inicio=1,
)
```

#### Adicionar Nota (Post-it)
Adiciona uma anotação pop-up em coordenadas visuais específicas.
```python
adicionar_nota(
    caminho="documento.pdf",
    saida="documento_com_nota.pdf",
    pagina=1,
    texto="Revisar estes números antes do envio.",
    posicao=(50, 100),
)
```

#### Destacar Texto
Localiza termos e aplica anotações de realce (`destaque`, `sublinhado` ou `riscado`).
```python
resultado = destacar_texto(
    caminho="documento.pdf",
    saida="documento_destacado.pdf",
    termo="importante",
    tipo="destaque",
    cor="amarelo",
    ignorar_maiusculas=True,
)
print(f"Total de ocorrências destacadas: {resultado['total_ocorrencias']}")
```

---

### 4. Formulários PDF (AcroForm)

#### Listar Campos de Formulário
Retorna todos os campos do formulário com seus tipos, valores e páginas.
```python
campos = listar_campos("formulario.pdf")
for campo in campos:
    print(
        f"Nome: {campo['nome']} | Tipo: {campo['tipo']} | Valor: {campo['valor']} | Pág: {campo['pagina']}"
    )
```

#### Preencher Formulário
Preenche campos de texto, checkboxes e outros widgets pelo nome.
```python
valores = {
    "nome_completo": "João Silva",
    "email": "joao@exemplo.com",
    "aceito_termos": True,
}
preencher_formulario(
    "formulario.pdf", valores=valores, saida="formulario_preenchido.pdf"
)
```

#### Achatar Formulário (Flatten)
Converte os campos editáveis em conteúdo fixo permanente (não editável).
```python
achatar_formulario("formulario_preenchido.pdf", saida="formulario_final.pdf")
```

---

### 5. Segurança e Otimização

#### Proteger com Senha
Criptografa o PDF com AES-256 definindo senha de usuário e opcionalmente de proprietário.
```python
proteger_pdf(
    caminho="documento.pdf",
    saida="documento_protegido.pdf",
    senha_usuario="senha123",
    senha_dono="admin456",
)
```

#### Remover Senha
Descriptografa um documento PDF protegido.
```python
remover_senha(
    caminho="documento_protegido.pdf", senha="senha123", saida="documento_aberto.pdf"
)
```

#### Comprimir PDF
Reduz o tamanho do arquivo utilizando diferentes níveis (`baixo`, `medio`, `alto`).
```python
estatisticas = comprimir_pdf(
    "documento.pdf", saida="documento_comprimido.pdf", nivel="medio"
)
print(f"Economia de espaço: {estatisticas['economia_percentual']}%")
```

---

### 6. Conversão PDF ↔ Imagens

#### PDF para Imagens
Renderiza páginas do PDF como arquivos de imagem (PNG ou JPG).
```python
imagens = pdf_para_imagens(
    caminho="documento.pdf", pasta_saida="imagens_extraidas", dpi=150, formato="png"
)
print("Imagens geradas:", imagens)
```

#### Imagens para PDF
Cria um PDF a partir de uma sequência ordenada de imagens.
```python
imagens_para_pdf(
    imagens=["pagina_001.png", "pagina_002.png"], saida="documento_compilado.pdf"
)
```

#### Adicionar Imagem a uma Página
Insere uma imagem em uma posição específica, com controle de tamanho ou escala proporcional.
```python
adicionar_imagem(
    pdf="documento.pdf",
    pagina=1,
    imagem="logo.png",
    posicao=(50, 50),
    tamanho=(
        150,
        80,
    ),  # Ou apenas 150 para largura proporcional, ou None para tamanho original
    saida="documento_com_logo.pdf",  # Opcional: se omitido, modifica o próprio arquivo
)
```

---

## 🖥️ Uso via Linha de Comando (CLI)

O **PerfectDF** disponibiliza uma interface CLI completa executável via módulo Python:

```bash
python -m perfectdf --help
```

### Comandos da CLI

- **Juntar PDFs:**
  ```bash
  python -m perfectdf juntar doc1.pdf doc2.pdf -o unificado.pdf
  ```

- **Extrair Páginas:**
  ```bash
  python -m perfectdf extrair documento.pdf -p "1,3,5" -o extraido.pdf
  ```

- **Girar Páginas:**
  ```bash
  python -m perfectdf girar documento.pdf -p "1-3" -g 90 -o girado.pdf
  ```

- **Excluir Páginas:**
  ```bash
  python -m perfectdf excluir documento.pdf -p "2,4" -o sem_paginas.pdf
  ```

- **Reordenar Páginas:**
  ```bash
  python -m perfectdf reordenar documento.pdf --ordem "3, 1-2" -o reordenado.pdf
  ```

- **Metadados (Ler ou Editar):**
  ```bash
  # Visualizar metadados
  python -m perfectdf metadados documento.pdf

  # Editar metadados
  python -m perfectdf metadados documento.pdf --titulo "Novo Titulo" --autor "Equipe" -o atualizado.pdf
  ```

- **Extrair Texto:**
  ```bash
  # Imprimir no terminal
  python -m perfectdf texto documento.pdf -p "1-3"

  # Salvar em arquivo
  python -m perfectdf texto documento.pdf -o conteudo.txt
  ```

- **Adicionar Texto:**
  ```bash
  python -m perfectdf adicionar-texto documento.pdf -p 1 -t "Aprovado" --posicao "100,200" --cor "azul" -o aprovado.pdf
  ```

- **Adicionar Imagem:**
  ```bash
  python -m perfectdf adicionar-imagem documento.pdf -p 1 -i logo.png --posicao "50,50" --tamanho "150,80" -o saida.pdf
  ```

- **Marca d'Água:**
  ```bash
  python -m perfectdf marca-dagua documento.pdf "CONFIDENCIAL" -o protegido.pdf --opacidade 0.2
  ```

- **Adicionar Nota:**
  ```bash
  python -m perfectdf adicionar-nota documento.pdf -p 1 -t "Revisar este trecho" --posicao "50,100" -o documento_com_nota.pdf
  ```

- **Numerar Páginas:**
  ```bash
  python -m perfectdf numerar documento.pdf -o numerado.pdf --posicao rodape-direita --formato "Pág. {n}/{total}"
  ```

- **Listar Campos de Formulário:**
  ```bash
  python -m perfectdf listar-campos formulario.pdf
  ```

- **Preencher Formulário:**
  ```bash
  python -m perfectdf preencher formulario.pdf --campo "nome=João Silva" --campo "cidade=São Paulo" -o preenchido.pdf
  ```

- **Achatar Formulário:**
  ```bash
  python -m perfectdf achatar formulario.pdf -o fixo.pdf
  ```

- **Comprimir PDF:**
  ```bash
  python -m perfectdf comprimir documento.pdf -o comprimido.pdf --nivel alto
  ```

- **Proteger e Remover Senha:**
  ```bash
  # Proteger
  python -m perfectdf proteger documento.pdf -s "senha123" -o protegido.pdf

  # Remover senha
  python -m perfectdf remover-senha protegido.pdf -s "senha123" -o desbloqueado.pdf
  ```

- **Conversão PDF ↔ Imagens:**
  ```bash
  # PDF para Imagens
  python -m perfectdf pdf-para-imagens documento.pdf -o pasta_imagens/ --dpi 200 --formato png

  # Imagens para PDF
  python -m perfectdf imagens-para-pdf img1.png img2.png -o saida.pdf
  ```

---

## 🌐 Interface Web

A interface web permite visualizar e editar PDFs no navegador. Com o ambiente virtual ativado e as dependências instaladas, inicie o servidor na raiz do projeto:

```bash
uvicorn perfectdf.web.app:app --reload
```

Acesse [http://127.0.0.1:8000](http://127.0.0.1:8000).

---

## 🧪 Como Rodar os Testes

Para executar a suíte de testes com o [pytest](https://pytest.org/):

```bash
# Ative o ambiente virtual
source venv/bin/activate

# Instale as dependências de desenvolvimento
pip install -r requirements-dev.txt

# Execute todos os testes
pytest

# Ou com saída detalhada
pytest -v
```

---

## 📄 Licença

Este projeto é distribuído sob os termos da licença **GNU Affero General Public License v3.0 (AGPL-3.0)** em conformidade com as dependências do [PyMuPDF](https://pymupdf.readthedocs.io/). Consulte o arquivo [LICENSE](LICENSE) para mais detalhes.
