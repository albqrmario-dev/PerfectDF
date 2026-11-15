# PerfectDF

O **PerfectDF** é uma biblioteca Python gratuita e open source projetada para facilitar a manipulação, edição e otimização de documentos PDF. Construída sobre o motor [PyMuPDF](https://pymupdf.readthedocs.io/), oferece uma API simples, direta e robusta em português para as tarefas mais comuns do dia a dia com arquivos PDF.

---

## 🚀 Instalação

Recomenda-se o uso de um ambiente virtual (`venv`):

```bash
# Clone o repositório
git clone https://github.com/albqrmario-dev/PerfectDF.git
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

## 🌐 Interface Web — processamento no navegador

A interface usa **MuPDF.js/WebAssembly em Web Workers** para editar PDFs no próprio dispositivo. Os arquivos não são enviados à API nem armazenados no servidor. O PDF.js 6.5.438, com versão fixa no lockfile, é responsável pela visualização. Ao trocar arquivos ou prévias, o visualizador anterior é destruído. Operações em andamento são invalidadas ao trocar de arquivo ou ferramenta. As bibliotecas, fontes e o WASM são servidos pelo próprio site, sem dependência de CDNs em tempo de execução.

### Executar o site estático

Requisitos: Node.js 22.13 ou superior, `tar` e Python 3 (apenas para o servidor estático de desenvolvimento).

```bash
npm ci
npm run build
npm start
```

Abra http://localhost:8000. O build gera `dist/`, incluindo o motor WASM. Não abra o HTML diretamente via `file://`: os módulos e workers precisam de HTTP/HTTPS.

### Aparência clara e escura

Na primeira visita, a interface acompanha a preferência de aparência do sistema, inclusive se ela mudar com o site aberto. O botão de aparência no cabeçalho (lua para ativar o tema escuro, sol para voltar ao claro) alterna a aparência e salva a escolha neste navegador; essa escolha passa a ter prioridade sobre o sistema. O mesmo controle está disponível na página de licenças. Se o armazenamento local estiver bloqueado, a alternância continua funcionando durante a visita.

O tema muda apenas a interface. As páginas do PDF, o desenho da assinatura e o conteúdo exportado mantêm as cores originais.

### Publicar na Vercel

Importe este repositório na Vercel. O `vercel.json` já define:

- Framework: Other (sem framework).
- Build: `npm run build`.
- Diretório de saída: `dist`.

O build inclui a página de licenças, um arquivo dos fontes desta publicação e os fontes completos do MuPDF. Na primeira execução, baixa aproximadamente 69 MB do arquivo oficial do MuPDF e verifica seu SHA-256; as próximas execuções locais usam `.cache/perfectdf/`. Esses fontes são downloads separados e não são carregados ao abrir o editor. O build precisa de acesso à rede caso o cache ainda não exista.

Não configure uma função Python para o site. A Vercel entrega apenas arquivos estáticos; uploads e downloads de PDFs são operações locais do navegador. A biblioteca Python, a CLI e a API continuam disponíveis para quem quiser executá-las localmente.

### Recursos e limites

A interface mantém operações de páginas, junção, anotações, texto, metadados, formulários, compressão e proteção AES-256. Não há o limite de upload de 50 MB da API no processamento local. O tamanho viável depende da memória e capacidade do dispositivo; PDFs grandes podem exigir um computador. Cada operação tem um prazo de cinco minutos e seu worker é encerrado ao concluir ou falhar para liberar memória.

- A compressão é estrutural e sem rasterizar páginas: o nível médio usa object streams e o alto também otimiza fontes. Não recomprime imagens como o backend Python. Se não houver redução, conserva o arquivo original.
- Inserção de texto, numeração e marca d'água usam Helvetica com caracteres latinos (incluindo português); caracteres não suportados retornam uma mensagem de erro.
- Na junção, os campos de cada formulário recebem prefixos como `arquivo1_nome`, para que campos de documentos diferentes continuem independentes. Use “Listar Campos” para consultar os nomes finais.
- PDFs que exigem senha podem ser abertos pela ferramenta “Remover Senha”, fornecendo a senha correta, e então editados. A extração de texto não faz OCR de páginas digitalizadas.
- Não há service worker para instalar o site offline. Após os recursos serem carregados, a edição é local; isso não garante recarregar o site sem conexão.

### Adicionar assinatura desenhada

Em **Anotações → Adicionar assinatura**, clique em **Desenhar assinatura** e use mouse, toque ou caneta. **Apagar desenho** limpa a área para refazer; **Cancelar** preserva a assinatura já posicionada. Confirme com **Usar assinatura**.

Arraste a assinatura sobre o documento e use o controle do canto para redimensioná-la. O campo **Página da assinatura** permite transferi-la para outra página. **Remover assinatura** elimina o desenho ainda não aplicado. Também é possível focar a assinatura e usar as setas para mover, Shift para passos maiores, `+`/`-` para redimensionar e Delete para remover.

Use **Gerar prévia**, confira o PDF e clique em **Baixar PDF**. Para ajustar novamente, volte a **Original**. Uma prévia desatualizada da assinatura não pode ser baixada: gere outra após o ajuste. A ferramenta mantém uma assinatura por vez, antes de aplicar; o arquivo original não é sobrescrito.

O desenho é exportado como traços vetoriais nas coordenadas nativas do PDF, com conversão pelo viewport do PDF.js. Zoom, rolagem, rotação e densidade de pixels da tela não são usados como coordenadas do arquivo. O PDF e o desenho permanecem locais; não há dependências novas nem armazenamento da assinatura entre sessões. Trata-se de uma assinatura visual desenhada, **sem certificado digital ou assinatura criptográfica**.

### Editar texto existente

Em **Texto → Editar texto existente**, escolha a página e clique numa linha do PDF (ou escolha a linha pela lista nos ajustes). Digite a substituição em **Novo texto**. Você pode alterar outras linhas e páginas antes de gerar a prévia e baixar uma cópia.

A substituição remove o conteúdo textual selecionado e insere o novo no mesmo lugar; não cobre o original com uma caixa. A posição, a cor e uma família de fonte compatível são usadas na substituição. Fontes personalizadas não têm garantia de aparência idêntica. O texto pode diminuir para caber na largura original; substituições muito longas são recusadas. Não há reorganização de parágrafos ou suporte a quebras de linha nesta ferramenta.

A verificação é por página e conservadora: texto invisível, imagens ocupando a maior parte da página e alguns estilos complexos bloqueiam a edição. Isso evita editar camadas de OCR de digitalizações comuns. PDF não possui um indicador universal de origem/OCR; reconstruções que já tenham virado texto visível nativo podem não ser distinguíveis. Linhas com estilos mistos, caracteres fora do conjunto latino ou texto inclinado podem não ser editáveis. Formulários têm sua própria ferramenta.

### API Python opcional

Após `npm ci && npm run build` (para preparar os arquivos do motor local), também é possível servir a interface pelo FastAPI:

```bash
uvicorn perfectdf.web.app:app --reload
```

Os clientes da API Python continuam usando as rotas existentes. A interface usa exclusivamente o motor local.

### Verificar o motor e a interface

```bash
npm test
npx playwright install chromium
npm run test:browser
```

Os testes do motor verificam PDFs gerados (páginas, texto, anotações, formulários, compressão e senhas), incluindo leitura de um documento maior que 50 MB. Os testes de navegador usam um servidor puramente estático e verificam prévia/download e ausência de uploads ou chamadas à API.

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

Este projeto é distribuído sob os termos da licença **GNU Affero General Public License v3.0 (AGPL-3.0)** em conformidade com as dependências do [PyMuPDF](https://pymupdf.readthedocs.io/). Consulte [LICENSE](LICENSE), [THIRD_PARTY.md](THIRD_PARTY.md) e [as instruções de fontes e reconstrução](licenses/README.md) para mais detalhes. A página “Licenças e fontes” do site oferece as licenças e os fontes da versão publicada.
