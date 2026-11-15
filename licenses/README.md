# Origem dos avisos e fontes

Os textos em `mupdf-1.28.6/` foram copiados sem alterações do arquivo oficial `mupdf-1.28.6-source.tar.gz`, identificado pelo SHA-256 em `sources.json`. Incluem a licença principal e avisos das bibliotecas presentes no tarball; alguns desses componentes são desativados na configuração padrão de WASM. Os textos adicionais no arquivo-fonte completo também são preservados na distribuição.

O build publica o arquivo-fonte completo de MuPDF, incluindo as dependências de `thirdparty` e os scripts de `platform/wasm`, em `/sources/mupdf-1.28.6-source.tar.gz`. O download upstream é verificado por SHA-256. O cache fica em `.cache/perfectdf/` e não faz parte do Git. O arquivo completo tem aproximadamente 69 MB e só é transferido ao visitante quando ele escolhe baixá-lo; não é carregado pelo editor.

O PDF.js é obtido da versão fixa de `pdfjs-dist` no lockfile. Sua licença Apache-2.0 e as licenças dos recursos distribuídos (cmaps, fontes padrão, WASM e perfis ICC) são copiadas junto aos respectivos arquivos. O manifesto publicado informa as versões, os commits upstream e os hashes dos arquivos principais.

As fontes de interface preservam suas licenças OFL em `perfectdf/web/static/vendor/fonts/`.

## Reconstruir o motor MuPDF/WASM

1. Obtenha o arquivo completo de fontes pelo site ou pelo URL em `sources.json` e confira o SHA-256.
2. Extraia o tarball e entre em `mupdf-1.28.6-source/platform/wasm/`.
3. Disponibilize Node.js/npm, Make, um compilador C e uma instalação do Emscripten SDK (`emsdk`).
4. Execute `EMSDK=/caminho/para/emsdk make`. O script upstream `tools/build.sh` instala/ativa Emscripten 4.0.8. Consulte o próprio script para as opções e defaults da versão.
5. A saída é gerada em `platform/wasm/dist`. O PerfectDF usa os binários oficiais não modificados do pacote npm `mupdf@1.28.6`; o lockfile registra a integridade desse pacote. Não prometemos hashes idênticos entre recompilações com ferramentas auxiliares diferentes.

Também é possível obter o repositório no commit indicado em `sources.json` e inicializar os submódulos com `git submodule update --init --recursive`. Ao contrário de um simples snapshot Git sem submódulos, o tarball distribuído no site já inclui as fontes de terceiros necessárias.

## Reconstruir o PerfectDF publicado

O build produz `/sources/perfectdf-source.tar.gz` a partir de uma lista explícita de arquivos do projeto, incluindo código, lockfile, configuração, documentação e testes. Não inclui `.git`, ambientes locais, caches ou arquivos pessoais. Depois de extrair, execute `npm ci` e `npm run build`. O motor e o visualizador são obtidos das versões fixas do lockfile.
