// Runs once inside a disposable worker. Terminating the worker releases WASM memory.
import * as mupdf from './vendor/mupdf/mupdf.js';

export function pages(spec, total, all = false) {
  if (!String(spec || '').trim()) {
    if (all) return Array.from({ length: total }, (_, i) => i);
    throw new Error('Informe as páginas.');
  }
  const result = [];
  for (const part of String(spec).split(',')) {
    const match = part.trim().match(/^(\d+)(?:\s*-\s*(\d+))?$/);
    if (!match) throw new Error('Páginas inválidas. Use, por exemplo, 1, 3-5.');
    const first = Number(match[1]), last = Number(match[2] || match[1]);
    if (first < 1 || last < first || last > total) throw new Error(`As páginas devem estar entre 1 e ${total}.`);
    for (let n = first; n <= last; n++) result.push(n - 1);
  }
  return result;
}

function required(value, label = 'Texto') {
  if (!String(value || '').trim()) throw new Error(`${label} não pode ficar vazio.`);
  return String(value);
}

function open(file, password) {
  const doc = mupdf.Document.openDocument(file.bytes, 'application/pdf').asPDF();
  if (!doc) throw new Error('O arquivo não é um PDF válido.');
  if (doc.needsPassword() && !doc.authenticatePassword(password || '')) {
    doc.destroy();
    throw new Error(password ? 'Senha incorreta.' : 'PDF protegido. Informe a senha na ferramenta Remover Senha.');
  }
  if (!doc.countPages()) { doc.destroy(); throw new Error('O PDF não contém páginas.'); }
  return doc;
}

// Copy inherited resources before extending them; other pages may share the original.
function copyDict(doc, original) {
  const copy = doc.newDictionary();
  original.forEach((value, key) => copy.put(key, value));
  return copy;
}
function textHex(text) {
  const extra = '€\u0081‚ƒ„…†‡ˆ‰Š‹Œ\u008dŽ\u008f\u0090‘’“”•–—˜™š›œ\u009džŸ';
  return [...text].map(char => {
    let n = char.codePointAt(0);
    if (n > 255) n = extra.includes(char) ? 128 + extra.indexOf(char) : -1;
    if (n < 0) throw new Error('Este texto contém caracteres não suportados pela fonte. Use caracteres latinos.');
    return n.toString(16).padStart(2, '0');
  }).join('');
}
function drawText(doc, page, text, x, y, size = 12, color = [0, 0, 0], opacity = 1, angle = 0, fontFamily = 'Helvetica') {
  const hex = textHex(text);
  const object = page.getObject();
  const resources = copyDict(doc, object.getInheritable('Resources'));
  const fonts = copyDict(doc, resources.get('Font'));
  const font = new mupdf.Font(fontFamily);
  let resourceIndex = 0;
  while (!fonts.get(`PerfectDFFont${resourceIndex}`).isNull()) resourceIndex++;
  const fontName = `PerfectDFFont${resourceIndex}`;
  const opacityName = `PerfectDFOpacity${resourceIndex}`;
  fonts.put(fontName, doc.addSimpleFont(font, 'Latin'));
  font.destroy();
  resources.put('Font', fonts);
  const states = copyDict(doc, resources.get('ExtGState'));
  states.put(opacityName, { Type: 'ExtGState', ca: opacity, CA: opacity });
  resources.put('ExtGState', states);
  object.put('Resources', resources);
  const matrix = mupdf.Matrix.invert(page.getTransform());
  const pdfNumber = value => Number(value.toFixed(6)).toString();
  const rad = angle * Math.PI / 180, c = pdfNumber(Math.cos(rad)), s = pdfNumber(Math.sin(rad));
  const content = `q ${matrix.map(pdfNumber).join(' ')} cm /${opacityName} gs BT /${fontName} ${pdfNumber(size)} Tf ${color.map(pdfNumber).join(' ')} rg ${c} ${s} ${s} ${-Number(c)} ${pdfNumber(x)} ${pdfNumber(y)} Tm <${hex}> Tj ET Q`;
  const existing = object.get('Contents');
  const contents = doc.newArray();
  // Isolate the original graphics state before appending new content.
  contents.push(doc.addStream('q', {}));
  if (existing.isArray()) existing.forEach(value => contents.push(value));
  else if (!existing.isNull()) contents.push(existing);
  contents.push(doc.addStream(`Q\n${content}`, {}));
  object.put('Contents', contents);
}

function compatibleFont(font) {
  if (font.isMono()) return 'Courier' + (font.isBold() ? '-Bold' : '') + (font.isItalic() ? (font.isBold() ? 'Oblique' : '-Oblique') : '');
  if (font.isSerif()) return font.isBold() ? (font.isItalic() ? 'Times-BoldItalic' : 'Times-Bold') : (font.isItalic() ? 'Times-Italic' : 'Times-Roman');
  return 'Helvetica' + (font.isBold() ? '-Bold' : '') + (font.isItalic() ? (font.isBold() ? 'Oblique' : '-Oblique') : '');
}

function editablePage(page) {
  const bounds = page.getBounds();
  const area = (bounds[2] - bounds[0]) * (bounds[3] - bounds[1]);
  let hidden = false, imageArea = 0, clipped = false;
  const trace = new mupdf.Device({
    ignoreText() { hidden = true; },
    fillText(_text, _matrix, _space, _color, alpha) { if (alpha < .01) hidden = true; },
    strokeText() { clipped = true; },
    clipText() { clipped = true; },
    clipStrokeText() { clipped = true; },
    fillImage(_image, matrix, alpha) {
      if (alpha < .01) return;
      const rect = mupdf.Rect.transform([0, 0, 1, 1], matrix);
      imageArea += Math.max(0, Math.min(bounds[2], rect[2]) - Math.max(bounds[0], rect[0]))
        * Math.max(0, Math.min(bounds[3], rect[3]) - Math.max(bounds[1], rect[1]));
    },
  });
  try { page.runPageContents(trace, mupdf.Matrix.identity); trace.close(); }
  finally { trace.destroy(); }
  const blocked = message => ({ bounds, linhas: [], disponivel: false, motivo: message });
  if (hidden || imageArea > area * .6) return blocked('Esta página parece digitalizada ou contém texto invisível de OCR. A edição aceita apenas texto visível de PDFs de texto.');
  if (clipped) return blocked('Esta página usa texto com contornos ou máscaras que ainda não podem ser editados.');
  if (page.getAnnotations().some(annotation => annotation.getType() === 'Redact')) return blocked('Esta página contém marcações de remoção de conteúdo. Resolva essas marcações antes de editar o texto.');
  // Read only page content: form widgets and comments are separate tools.
  const display = new mupdf.DisplayList(bounds);
  const device = new mupdf.DisplayListDevice(display);
  let structured;
  const lines = [];
  try {
    page.runPageContents(device, mupdf.Matrix.identity); device.close();
    structured = display.toStructuredText('preserve-whitespace');
    let line;
    structured.walk({
      beginLine(rect, mode, direction) { line = { texto: '', rect, direction, chars: [], supported: mode === 0 && Math.min(Math.abs(direction[0]), Math.abs(direction[1])) < .001 }; },
      onChar(char, origin, font, size, quad, color) {
        const style = { fonte: compatibleFont(font), tamanho: size, cor: color };
        if (!line.chars.length) Object.assign(line, style, { origem: origin, fonteOriginal: font.getName() });
        else if (line.fonte !== style.fonte || Math.abs(line.tamanho - size) > .1 || String(line.cor) !== String(color)) line.supported = false;
        line.texto += char;
        line.chars.push(quad);
      },
      endLine() {
        if (!line.texto.trim()) return;
        try { textHex(line.texto); } catch { line.supported = false; }
        line.id = lines.length;
        const projections = line.chars.flatMap(q => [0, 2, 4, 6].map(i => q[i] * line.direction[0] + q[i + 1] * line.direction[1]));
        line.largura = projections.reduce((max, n) => Math.max(max, n), -Infinity) - projections.reduce((min, n) => Math.min(min, n), Infinity);
        lines.push(line);
      },
    });
  } finally { structured?.destroy(); device.destroy(); display.destroy(); }
  if (!lines.length) return blocked('Esta página não contém texto editável. Imagens, digitalizações e letras convertidas em desenho não podem ser editadas.');
  return { bounds, disponivel: lines.some(line => line.supported), linhas: lines, motivo: lines.some(line => line.supported) ? '' : 'O texto desta página usa estilos, caracteres ou direções ainda não suportados.' };
}

function replaceText(doc, edits) {
  if (!Array.isArray(edits) || !edits.length || edits.length > 500) throw new Error('Selecione uma linha e escreva a substituição.');
  const byPage = new Map(), seen = new Set();
  for (const edit of edits) {
    if (!Number.isInteger(edit.pagina) || edit.pagina < 1 || edit.pagina > doc.countPages()) throw new Error('Página inválida.');
    const key = `${edit.pagina}:${edit.linha}`;
    if (seen.has(key)) throw new Error('A mesma linha foi selecionada mais de uma vez.');
    seen.add(key);
    if (!byPage.has(edit.pagina)) byPage.set(edit.pagina, []);
    byPage.get(edit.pagina).push(edit);
  }
  // Validate all edits before modifying any page. Coordinates always come from the PDF.
  const plans = [];
  for (const [pageNumber, changes] of byPage) {
    const page = doc.loadPage(pageNumber - 1);
    try {
      const info = editablePage(page);
      if (!info.disponivel) throw new Error(info.motivo);
      const replacements = [];
      for (const change of changes) {
        const line = info.linhas.find(item => item.id === change.linha);
        if (!line?.supported || line.texto !== change.original) throw new Error('O trecho não está disponível para edição. Selecione novamente.');
        const text = required(change.novo, 'Novo texto');
        if (/[\r\n]/.test(text)) throw new Error('Edite uma linha por vez, sem quebras de linha.');
        textHex(text);
        const font = new mupdf.Font(line.fonte);
        let units = 0;
        try { for (const char of text) units += font.advanceGlyph(font.encodeCharacter(char)); }
        finally { font.destroy(); }
        const size = Math.min(line.tamanho, line.largura / Math.max(units, .001));
        if (size < Math.min(line.tamanho, Math.max(5, line.tamanho * .6))) throw new Error('O novo texto é longo demais para este espaço. Encurte a substituição.');
        replacements.push({ line, text, size });
      }
      plans.push({ pageNumber, replacements });
    } finally { page.destroy(); }
  }
  for (const { pageNumber, replacements } of plans) {
    const page = doc.loadPage(pageNumber - 1);
    try {
      for (const { line } of replacements) {
        const redaction = page.createAnnotation('Redact');
        // A narrow band through each glyph removes its text without touching nearby lines.
        const quads = line.chars.map(q => {
          const lerp = (top, bottom, t) => top + (bottom - top) * t;
          return [lerp(q[0], q[4], .3), lerp(q[1], q[5], .3), lerp(q[2], q[6], .3), lerp(q[3], q[7], .3),
            lerp(q[0], q[4], .7), lerp(q[1], q[5], .7), lerp(q[2], q[6], .7), lerp(q[3], q[7], .7)];
        });
        redaction.setQuadPoints(quads); redaction.getObject().delete('IC'); redaction.update();
      }
      page.applyRedactions(false, 0, 0, 0);
      for (const { line, text, size } of replacements) {
        const angle = Math.atan2(line.direction[1], line.direction[0]) * 180 / Math.PI;
        drawText(doc, page, text, line.origem[0], line.origem[1], size, line.cor, 1, angle, line.fonte);
      }
      page.update();
    } finally { page.destroy(); }
  }
}

function addSignature(doc, value) {
  if (!value || !Number.isInteger(value.page) || value.page < 1 || value.page > doc.countPages()) throw new Error('Escolha uma página válida para a assinatura.');
  const { matrix, strokes, aspect, pen } = value;
  if (!Array.isArray(matrix) || matrix.length !== 6 || matrix.some(n => !Number.isFinite(n) || Math.abs(n) > 1e7)
    || !Number.isFinite(aspect) || aspect <= 0 || aspect > 100 || !Number.isFinite(pen) || pen <= 0 || pen > .3
    || !Array.isArray(strokes) || !strokes.length || strokes.length > 1000) throw new Error('Os dados da assinatura são inválidos. Desenhe novamente.');
  const determinant = matrix[0] * matrix[3] - matrix[1] * matrix[2];
  if (Math.abs(determinant) < 1e-6) throw new Error('O tamanho da assinatura é inválido.');
  let count = 0;
  for (const stroke of strokes) {
    if (!Array.isArray(stroke) || stroke.length < 2) throw new Error('A assinatura está vazia ou incompleta.');
    for (const p of stroke) {
      if (!Array.isArray(p) || p.length !== 2 || !Number.isFinite(p[0]) || !Number.isFinite(p[1]) || p[0] < 0 || p[0] > 1 || p[1] < 0 || p[1] > aspect || ++count > 100000) throw new Error('O desenho da assinatura é inválido ou grande demais.');
    }
  }
  const page = doc.loadPage(value.page - 1);
  try {
    // PDF.js convertToPdfPoint gives native page coordinates; MuPDF content uses the same units.
    // Validate against the visible CropBox after applying MuPDF's page transform.
    const visible = page.getBounds(), transform = page.getTransform();
    for (const [x, y] of [[0, 0], [1, 0], [0, aspect], [1, aspect]]) {
      const px = matrix[0] * x + matrix[2] * y + matrix[4], py = matrix[1] * x + matrix[3] * y + matrix[5];
      const vx = transform[0] * px + transform[2] * py + transform[4], vy = transform[1] * px + transform[3] * py + transform[5];
      if (vx < visible[0] - .1 || vy < visible[1] - .1 || vx > visible[2] + .1 || vy > visible[3] + .1) throw new Error('Posicione a assinatura dentro da página antes de aplicar.');
    }
    const number = n => Number(n.toFixed(8)).toString();
    const commands = [`q ${matrix.map(number).join(' ')} cm 0.125 0.145 0.165 RG ${number(pen)} w 1 J 1 j`];
    for (const stroke of strokes) {
      commands.push(`${stroke[0].map(number).join(' ')} m`);
      for (const p of stroke.slice(1)) commands.push(`${p.map(number).join(' ')} l`);
      commands.push('S');
    }
    commands.push('Q');
    const object = page.getObject(), existing = object.get('Contents'), contents = doc.newArray();
    contents.push(doc.addStream('q', {}));
    if (existing.isArray()) existing.forEach(item => contents.push(item));
    else if (!existing.isNull()) contents.push(existing);
    contents.push(doc.addStream('Q\n' + commands.join('\n'), {}));
    object.put('Contents', contents);
  } finally { page.destroy(); }
}

export function processPdf({ operation, fields = {}, files }) {
  let doc;
  const loaded = [];
  try {
    const read = file => { const d = open(file, fields.senha); loaded.push(d); return d; };
    if (operation === 'paginas/juntar') {
      if (files.length < 2) throw new Error('Selecione pelo menos dois PDFs.');
      doc = new mupdf.PDFDocument(); loaded.push(doc);
      const destinationForm = doc.newDictionary();
      const destinationFields = doc.newArray();
      const destinationFonts = doc.newDictionary();
      destinationForm.put('Fields', destinationFields);
      destinationForm.put('DR', { Font: destinationFonts });
      doc.getTrailer().get('Root').put('AcroForm', destinationForm);
      for (const [fileIndex, file] of files.entries()) {
        const source = read(file);
        const map = doc.newGraftMap();
        try {
          const form = source.getTrailer().get('Root', 'AcroForm');
          const fontNames = new Map();
          form.get('DR', 'Font').forEach((font, name) => {
            const unique = `D${fileIndex}_${name}`;
            fontNames.set(name, unique);
            destinationFonts.put(unique, map.graftObject(font));
          });
          const rewriteDA = value => value.replace(/\/([^\s/]+)/g, (match, name) => fontNames.has(name) ? '/' + fontNames.get(name) : match);
          const updateField = (field, inheritedDA) => {
            const appearance = field.get('DA').asString() || inheritedDA;
            if (appearance) field.put('DA', source.newString(rewriteDA(appearance)));
            field.get('Kids').forEach(child => updateField(child, appearance));
          };
          form.get('Fields').forEach(field => {
            updateField(field, form.get('DA').asString());
            // Namespace independent forms so identically named fields stay independent.
            field.put('T', source.newString(`arquivo${fileIndex + 1}_${field.get('T').asString()}`));
            destinationFields.push(map.graftObject(field));
          });
          for (let i = 0; i < source.countPages(); i++) {
            const page = source.findPage(i);
            for (const key of ['Resources', 'MediaBox', 'CropBox', 'Rotate']) {
              const value = page.getInheritable(key);
              if (!value.isNull()) page.put(key, value);
            }
            // Copy the complete page, retaining annotations, links and widget objects.
            doc.insertPage(-1, map.graftObject(page));
          }
        } finally { map.destroy(); }
      }
    } else doc = read(files[0]);
    const total = doc.countPages();
    if (operation === 'inspecionar') return { json: { tamanho: files[0].bytes.byteLength, total_paginas: total } };
    let options = { garbage: 4, compress: true, 'compress-fonts': true, 'compress-images': true };
    const pageIndex = () => pages(String(fields.pagina || 1), total)[0];
    if (operation === 'texto/listar-editaveis') {
      const page = doc.loadPage(pageIndex());
      try { return { json: editablePage(page) }; } finally { page.destroy(); }
    }
    if (operation === 'assinatura/adicionar') {
      let signature;
      try { signature = JSON.parse(fields.assinatura); } catch { throw new Error('Crie uma assinatura válida antes de aplicar.'); }
      addSignature(doc, signature);
    } else if (operation === 'texto/editar') {
      let edits;
      try { edits = JSON.parse(fields.edicoes); } catch { throw new Error('Dados de edição inválidos.'); }
      replaceText(doc, edits);
    } else if (operation === 'paginas/girar') {
      const degrees = Number(fields.graus);
      if (![90, 180, 270].includes(degrees)) throw new Error('Rotação inválida.');
      for (const index of new Set(pages(fields.paginas, total, true))) {
        const obj = doc.findPage(index);
        obj.put('Rotate', (obj.getInheritable('Rotate').asNumber() + degrees) % 360);
      }
    } else if (['paginas/extrair', 'paginas/reordenar', 'paginas/excluir'].includes(operation)) {
      let selected = pages(fields.ordem || fields.paginas, total);
      if (operation === 'paginas/excluir') selected = Array.from({ length: total }, (_, i) => i).filter(i => !selected.includes(i));
      if (!selected.length) throw new Error('O documento precisa manter pelo menos uma página.');
      doc.rearrangePages(selected);
    } else if (operation === 'texto/extrair') {
      let text = '';
      for (let i = 0; i < total; i++) {
        const p = doc.loadPage(i), structured = p.toStructuredText();
        try { text += structured.asText() + '\n'; } finally { structured.destroy(); p.destroy(); }
      }
      return { json: { texto: text } };
    } else if (operation === 'metadados/editar') {
      doc.setMetaData('info:Title', String(fields.titulo || ''));
      doc.setMetaData('info:Author', String(fields.autor || ''));
    } else if (operation === 'seguranca/proteger') {
      const password = required(fields.senha_usuario, 'Senha');
      const random = new Uint8Array(24); crypto.getRandomValues(random);
      options = { ...options, encrypt: 'aes-256', 'user-password': password, 'owner-password': Array.from(random, n => n.toString(16).padStart(2, '0')).join('') };
    } else if (operation === 'seguranca/remover-senha') {
      required(fields.senha, 'Senha');
      options.encrypt = 'none';
    } else if (operation === 'compressao/comprimir') {
      if (!['baixo', 'medio', 'alto'].includes(fields.nivel)) throw new Error('Nível de compressão inválido.');
      if (fields.nivel !== 'baixo') options['objstms'] = true;
      if (fields.nivel === 'alto') doc.subsetFonts();
    } else if (operation === 'formularios/achatar') {
      doc.bake(false, true);
    } else if (['formularios/listar', 'formularios/preencher'].includes(operation)) {
      let values = {};
      if (operation.endsWith('preencher')) {
        try { values = JSON.parse(fields.dados_json); } catch { throw new Error('Informe um objeto JSON válido.'); }
        if (!values || Array.isArray(values) || typeof values !== 'object') throw new Error('Informe um objeto JSON válido.');
      }
      const result = [], found = new Set();
      for (let i = 0; i < total; i++) {
        const p = doc.loadPage(i);
        try {
          for (const widget of p.getWidgets()) {
            const name = widget.getName();
            result.push({ nome: name, tipo: widget.getFieldType(), valor: widget.getValue(), pagina: i + 1, opcoes: widget.isChoice() ? widget.getOptions() : [], somente_leitura: widget.isReadOnly() });
            if (Object.hasOwn(values, name)) {
              found.add(name);
              const value = values[name];
              if (widget.isCheckbox() || widget.isRadioButton()) {
                if (typeof value !== 'boolean') throw new Error(`O campo ${name} exige true ou false.`);
                if ((widget.getValue() !== 'Off') !== value && !widget.toggle()) throw new Error(`Não foi possível alterar ${name}.`);
              } else {
                const ok = widget.isChoice() ? widget.setChoiceValue(String(value)) : widget.isText() ? widget.setTextValue(String(value)) : 0;
                if (!ok) throw new Error(`Valor inválido ou tipo não suportado no campo ${name}.`);
              }
              widget.update();
            }
          }
          p.update();
        } finally { p.destroy(); }
      }
      if (operation.endsWith('listar')) return { json: { campos: result, total: result.length } };
      for (const name of Object.keys(values)) if (!found.has(name)) throw new Error(`Campo não encontrado: ${name}.`);
    } else if (operation.startsWith('anotacoes/') || operation === 'texto/adicionar') {
      const text = required(operation.endsWith('destacar') ? fields.termo : operation.endsWith('numerar') ? fields.formato : fields.texto);
      const selected = ['anotacoes/nota', 'texto/adicionar'].includes(operation) ? [pageIndex()] : Array.from({ length: total }, (_, i) => i);
      for (const i of selected) {
        const p = doc.loadPage(i);
        try {
          const [x0, y0, x1, y1] = p.getBounds();
          if (operation === 'anotacoes/nota') {
            const a = p.createAnnotation('Text'); a.setRect([x0 + 50, y0 + 50, x0 + 70, y0 + 70]); a.setContents(text); a.update();
          } else if (operation === 'anotacoes/destacar') {
            const type = { destaque: 'Highlight', sublinhado: 'Underline', riscado: 'StrikeOut' }[fields.tipo];
            if (!type) throw new Error('Estilo de destaque inválido.');
            for (const quads of p.search(text)) {
              const a = p.createAnnotation(type); a.setQuadPoints(quads); a.setColor([1, 1, 0]); a.update();
            }
          } else if (operation === 'anotacoes/marca-dagua') {
            const opacity = Number(fields.opacidade);
            if (!Number.isFinite(opacity) || opacity < 0 || opacity > 1) throw new Error('Opacidade inválida.');
            drawText(doc, p, text, x0 + (x1 - x0) * .15, y0 + (y1 - y0) * .65, Math.min(48, (x1 - x0) / Math.max(text.length * .65, 1)), [.5, .5, .5], opacity, -45);
          } else if (operation === 'anotacoes/numerar') {
            const label = text.replaceAll('{n}', String(i + 1)).replaceAll('{total}', String(total));
            const position = fields.posicao || 'rodape-centro';
            const width = label.length * 6;
            const x = position.endsWith('direita') ? x1 - 30 - width : position.endsWith('esquerda') ? x0 + 30 : (x0 + x1 - width) / 2;
            drawText(doc, p, label, x, position.startsWith('topo') ? y0 + 30 : y1 - 25);
          } else if (operation === 'texto/adicionar') {
            drawText(doc, p, text, x0 + 50, y0 + 100, 12, { preto: [0, 0, 0], azul: [0, 0, 1], vermelho: [1, 0, 0] }[fields.cor] || [0, 0, 0]);
          } else throw new Error('Operação desconhecida.');
          p.update();
        } finally { p.destroy(); }
      }
    } else if (operation !== 'paginas/juntar') throw new Error('Operação desconhecida.');
    const output = doc.saveToBuffer(options);
    let bytes;
    try { bytes = output.asUint8Array().slice(); } finally { output.destroy(); }
    // Never replace a file with a larger copy when compression cannot improve it.
    if (operation === 'compressao/comprimir' && bytes.byteLength >= files[0].bytes.byteLength) bytes = new Uint8Array(files[0].bytes).slice();
    return { bytes, filename: operation === 'paginas/juntar' ? 'documento_juntado.pdf' : `editado_${files[0].name}` };
  } finally {
    for (const d of loaded.reverse()) d.destroy();
  }
}
