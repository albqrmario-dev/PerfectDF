import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import * as mupdf from '../perfectdf/web/static/vendor/mupdf/mupdf.js';
import { processPdf, pages } from '../perfectdf/web/static/pdf-engine.js';

// Three pages of searchable text, one note, a text field and a checkbox.
const original = readFileSync(new URL('./fixtures/browser.pdf', import.meta.url));
const file = bytes => ({ bytes, name: 'exemplo.pdf' });
const run = (operation, fields = {}, bytes = original) => processPdf({ operation, fields, files: [file(bytes)] });
function simplePdf(label, pages) {
  const doc = new mupdf.PDFDocument(), font = new mupdf.Font('Helvetica');
  const pdfFont = doc.addSimpleFont(font, 'Latin'); font.destroy();
  for (const [index, bounds] of pages.entries()) {
    const [x0, y0, x1, y1] = bounds;
    const content = `BT /F1 16 Tf ${x0 + 24} ${y1 - 36} Td (${label} pagina ${index + 1}) Tj ET`;
    doc.insertPage(-1, doc.addPage(bounds, 0, { Font: { F1: pdfFont } }, content));
  }
  const buffer = doc.saveToBuffer({ compress: true });
  const bytes = buffer.asUint8Array().slice();
  buffer.destroy(); doc.destroy();
  return bytes;
}
function inspect(bytes, callback) {
  const doc = mupdf.Document.openDocument(bytes, 'application/pdf');
  try { return callback(doc); } finally { doc.destroy(); }
}
function text(bytes) { return run('texto/extrair', {}, bytes).json.texto; }

test('inspection and text extraction stay local', () => {
  assert.equal(run('inspecionar').json.total_paginas, 3);
  assert.match(text(original), /Pagina 1/);
});
test('page ranges reject invalid, descending and out of bounds selections', () => {
  assert.deepEqual(pages('3, 1-2', 3), [2, 0, 1]);
  for (const invalid of ['0', '4', '3-1', 'a', '1,,2']) assert.throws(() => pages(invalid, 3));
  assert.throws(() => run('paginas/excluir', { paginas: '1-3' }));
});
test('extract, reorder and delete preserve selected content and annotations', () => {
  const extracted = run('paginas/extrair', { paginas: '3,1' }).bytes;
  assert.ok(text(extracted).indexOf('Pagina 3') < text(extracted).indexOf('Pagina 1'));
  inspect(extracted, doc => {
    assert.equal(doc.countPages(), 2);
    const page = doc.loadPage(1);
    assert.equal(page.getAnnotations()[0].getContents(), 'Nota original'); page.destroy();
  });
  const reordered = run('paginas/reordenar', { ordem: '3,2,1' }).bytes;
  assert.ok(text(reordered).indexOf('Pagina 3') < text(reordered).indexOf('Pagina 1'));
  const deleted = run('paginas/excluir', { paginas: '2' }).bytes;
  assert.doesNotMatch(text(deleted), /Pagina 2/);
});
test('rotation adds to existing rotation', () => {
  let bytes = run('paginas/girar', { graus: 90, paginas: '2' }).bytes;
  bytes = run('paginas/girar', { graus: 90, paginas: '2' }, bytes).bytes;
  inspect(bytes, doc => {
    assert.equal(doc.findPage(1).getInheritable('Rotate').asNumber(), 180);
    assert.equal(doc.findPage(0).getInheritable('Rotate').asNumber(), 0);
  });
});
test('insert text, watermark and numbering remain searchable and preserve notes', () => {
  let bytes = run('texto/adicionar', { texto: 'Olá ação', pagina: '1', cor: 'azul' }).bytes;
  assert.match(text(bytes), /Olá ação/);
  bytes = run('anotacoes/marca-dagua', { texto: 'CONFIDENCIAL', opacidade: '.3' }, bytes).bytes;
  bytes = run('anotacoes/numerar', { formato: 'Página {n} de {total}', posicao: 'rodape-centro' }, bytes).bytes;
  assert.match(text(bytes), /Página 3 de 3/);
  assert.match(text(bytes), /CONFIDENCIAL/);
  inspect(bytes, doc => { const p = doc.loadPage(0); assert.equal(p.getAnnotations()[0].getContents(), 'Nota original'); p.destroy(); });
});
test('notes and text highlights produce actual PDF annotations', () => {
  const bytes = run('anotacoes/nota', { texto: 'Revisar', pagina: 2 }).bytes;
  inspect(bytes, doc => { const p = doc.loadPage(1); assert.equal(p.getAnnotations()[0].getContents(), 'Revisar'); p.destroy(); });
  for (const tipo of ['destaque', 'sublinhado', 'riscado']) {
    const highlighted = run('anotacoes/destacar', { termo: 'teste', tipo }).bytes;
    inspect(highlighted, doc => { const p = doc.loadPage(1); assert.equal(p.getAnnotations().length, 1); p.destroy(); });
  }
});
test('form listing, filling and flattening preserve visible values', () => {
  assert.equal(run('formularios/listar').json.total, 2);
  const bytes = run('formularios/preencher', { dados_json: '{"nome":"João","aceito":true}' }).bytes;
  assert.deepEqual(run('formularios/listar', {}, bytes).json.campos.map(c => c.valor), ['João', 'Yes']);
  const flat = run('formularios/achatar', {}, bytes).bytes;
  assert.equal(run('formularios/listar', {}, flat).json.total, 0);
  assert.match(text(flat), /João/);
  assert.throws(() => run('formularios/preencher', { dados_json: '[]' }));
  assert.throws(() => run('formularios/preencher', { dados_json: '{"inexistente":"x"}' }));
});
test('joining keeps notes and independently editable forms from each input', () => {
  const { bytes } = processPdf({ operation: 'paginas/juntar', files: [file(original), file(original)] });
  inspect(bytes, doc => {
    assert.equal(doc.countPages(), 6);
    for (const i of [0, 3]) { const p = doc.loadPage(i); assert.equal(p.getAnnotations().length, 1); assert.equal(p.getWidgets().length, 2); p.destroy(); }
  });
  const filled = run('formularios/preencher', { dados_json: '{"arquivo1_nome":"Maria","arquivo2_nome":"João"}' }, bytes).bytes;
  assert.deepEqual(run('formularios/listar', {}, filled).json.campos.filter(c => c.tipo === 'text').map(c => c.valor), ['Maria', 'João']);
});
test('joining simple PDFs without AcroForm preserves order, page geometry, and all pages', () => {
  const portrait = simplePdf('Primeiro', [[0, 0, 595, 842], [0, 0, 595, 842]]);
  const landscape = simplePdf('Segundo', [[0, 0, 842, 595]]);
  const third = simplePdf('Terceiro', [[0, 0, 420, 595], [0, 0, 595, 420]]);
  const files = [portrait, landscape, third].map((bytes, index) => ({ name: `simples-${index + 1}.pdf`, bytes }));
  const { bytes } = processPdf({ operation: 'paginas/juntar', files });
  inspect(bytes, doc => {
    assert.equal(doc.countPages(), 5);
    assert.equal(doc.getTrailer().get('Root', 'AcroForm').isNull(), true);
    const labels = [];
    const sizes = [];
    for (let index = 0; index < doc.countPages(); index++) {
      const page = doc.loadPage(index);
      const text = page.toStructuredText();
      try { labels.push(text.asText().trim()); } finally { text.destroy(); }
      sizes.push(page.getBounds().slice(2));
      page.destroy();
    }
    assert.deepEqual(labels, [
      'Primeiro pagina 1', 'Primeiro pagina 2', 'Segundo pagina 1',
      'Terceiro pagina 1', 'Terceiro pagina 2',
    ]);
    assert.deepEqual(sizes, [[595, 842], [595, 842], [842, 595], [420, 595], [595, 420]]);
  });
  assert.match(text(bytes), /Terceiro pagina 2/);
});
test('joining mixed PDFs retains annotations and form widgets around simple PDFs', () => {
  const plain = simplePdf('Sem formulario', [[0, 0, 595, 842]]);
  const { bytes } = processPdf({ operation: 'paginas/juntar', files: [
    { name: 'simples.pdf', bytes: plain },
    { name: 'formulario.pdf', bytes: original },
    { name: 'outro-simples.pdf', bytes: plain },
  ] });
  inspect(bytes, doc => {
    assert.equal(doc.countPages(), 5);
    const formPage = doc.loadPage(1);
    assert.equal(formPage.getAnnotations().length, 1);
    assert.equal(formPage.getAnnotations()[0].getContents(), 'Nota original');
    assert.equal(formPage.getWidgets().length, 2);
    formPage.destroy();
  });
  assert.match(text(bytes), /Sem formulario pagina 1/);
  assert.match(text(bytes), /Pagina 3/);
});
test('joining reports the name of an invalid source PDF', () => {
  const valid = simplePdf('Valido', [[0, 0, 595, 842]]);
  for (const [name, bytes] of [
    ['invalido.pdf', new TextEncoder().encode('não é um PDF')],
    ['corrompido.pdf', valid.slice(0, 50)],
  ]) {
    assert.throws(() => processPdf({ operation: 'paginas/juntar', files: [
      { name: 'valido.pdf', bytes: valid }, { name, bytes },
    ] }), new RegExp(`${name.replace('.', '\\.')}.*inválido ou está corrompido`));
  }
});
test('metadata editing', () => {
  const bytes = run('metadados/editar', { titulo: 'Relatório', autor: 'Maria' }).bytes;
  inspect(bytes, doc => { assert.equal(doc.getMetaData('info:Title'), 'Relatório'); assert.equal(doc.getMetaData('info:Author'), 'Maria'); });
});
test('AES-256 requires the exact password and removal produces a readable PDF', () => {
  const password = 'ação,test=123';
  const bytes = run('seguranca/proteger', { senha_usuario: password }).bytes;
  inspect(bytes, doc => {
    assert.ok(doc.needsPassword());
    assert.equal(doc.authenticatePassword('incorreta'), 0);
    assert.ok(doc.authenticatePassword(password));
    assert.match(doc.getMetaData('encryption'), /256-bit AES/);
  });
  assert.throws(() => run('seguranca/remover-senha', { senha: 'errada' }, bytes), /Senha incorreta/);
  const unlocked = run('seguranca/remover-senha', { senha: password }, bytes).bytes;
  inspect(unlocked, doc => assert.equal(doc.needsPassword(), false));
  assert.match(text(unlocked), /Pagina 1/);
});
test('all compression levels keep text and never enlarge the document', () => {
  for (const nivel of ['baixo', 'medio', 'alto']) {
    const bytes = run('compressao/comprimir', { nivel }).bytes;
    assert.ok(bytes.length <= original.length);
    assert.match(text(bytes), /Pagina 3/);
  }
});
test('documents larger than the former 50 MB API limit can be inspected', () => {
  const doc = new mupdf.PDFDocument();
  const content = '%' + ' '.repeat(51 * 1024 * 1024) + '\n';
  doc.insertPage(-1, doc.addPage([0, 0, 595, 842], 0, {}, content));
  const buffer = doc.saveToBuffer({ compress: false });
  const bytes = buffer.asUint8Array().slice(); buffer.destroy(); doc.destroy();
  assert.ok(bytes.length > 50 * 1024 * 1024);
  assert.equal(run('inspecionar', {}, bytes).json.total_paginas, 1);
});

function editingFixture({ hidden = false, opacity = false, rotated = false, scan = false, logo = false, blank = false } = {}) {
  const doc = new mupdf.PDFDocument(), font = new mupdf.Font('Helvetica');
  const resources = { Font: { F1: doc.addSimpleFont(font, 'Latin') }, ExtGState: { Invisible: { ca: 0 } } };
  let content = 'q .9 .95 .97 rg 0 0 595 842 re f Q\n';
  if (scan || logo) {
    const pixmap = new mupdf.Pixmap(mupdf.ColorSpace.DeviceRGB, [0, 0, 2, 2], false);
    pixmap.clear(255);
    const image = new mupdf.Image(pixmap.asPNG()); pixmap.destroy();
    resources.XObject = { Scan: doc.addImage(image) }; image.destroy();
    content += scan ? 'q 595 0 0 842 0 0 cm /Scan Do Q\n' : 'q 24 0 0 24 500 750 cm /Scan Do Q\n';
  }
  if (!blank) content += `BT /F1 12 Tf ${hidden ? '3 Tr' : ''} ${opacity ? '/Invisible gs' : ''} 50 790 Td (Repeat text) Tj 0 -14 Td (Keep this line) Tj 0 -14 Td (Repeat text) Tj ET`;
  doc.insertPage(-1, doc.addPage([0, 0, 595, 842], rotated ? 90 : 0, resources, content));
  const buffer = doc.saveToBuffer({});
  try { return buffer.asUint8Array().slice(); } finally { buffer.destroy(); font.destroy(); doc.destroy(); }
}
const edit = (bytes, changes) => run('texto/editar', { edicoes: JSON.stringify(changes) }, bytes).bytes;

test('editing removes only the selected occurrence and preserves nearby lines and background', () => {
  const bytes = editingFixture({ logo: true });
  const info = run('texto/listar-editaveis', { pagina: 1 }, bytes).json;
  assert.equal(info.disponivel, true); assert.equal(info.linhas.length, 3);
  const edited = edit(bytes, [{ pagina: 1, linha: 0, original: 'Repeat text', novo: 'Novo texto' }]);
  const extracted = text(edited);
  assert.equal(extracted.match(/Repeat text/g).length, 1);
  assert.match(extracted, /Keep this line/); assert.match(extracted, /Novo texto/);
  inspect(edited, doc => {
    const p = doc.loadPage(0), pix = p.toPixmap(mupdf.Matrix.identity, mupdf.ColorSpace.DeviceRGB, false);
    try { assert.deepEqual(Array.from(pix.getPixels().slice((40 * 595 + 50) * 3, (40 * 595 + 50) * 3 + 3)), [229, 242, 247]); }
    finally { pix.destroy(); p.destroy(); }
  });
});

test('multiple replacements use the original line IDs and retain annotations and forms', () => {
  const edited = edit(original, [
    { pagina: 1, linha: 0, original: 'Pagina 1 Ola teste', novo: 'Página corrigida' },
    { pagina: 2, linha: 0, original: 'Pagina 2 Ola teste', novo: 'Outro texto' },
  ]);
  assert.doesNotMatch(text(edited), /Pagina [12] Ola teste/);
  assert.match(text(edited), /Página corrigida/); assert.match(text(edited), /Outro texto/);
  assert.match(text(edited), /Pagina 3/);
  assert.equal(run('formularios/listar', {}, edited).json.total, 2);
  inspect(edited, doc => { const p = doc.loadPage(0); assert.equal(p.getAnnotations()[0].getContents(), 'Nota original'); p.destroy(); });
});

test('OCR, invisible text, large scans and pages without text cannot be edited', () => {
  for (const options of [{ hidden: true, scan: true }, { hidden: true }, { opacity: true }, { scan: true }, { blank: true }]) {
    const bytes = editingFixture(options);
    const info = run('texto/listar-editaveis', { pagina: 1 }, bytes).json;
    assert.equal(info.disponivel, false);
    assert.ok(info.motivo);
    assert.throws(() => edit(bytes, [{ pagina: 1, linha: 0, original: 'Repeat text', novo: 'Changed' }]));
  }
});

test('editing validates the original content, page, duplicate changes and available space', () => {
  const bytes = editingFixture();
  for (const changes of [
    [{ pagina: 1, linha: 0, original: 'wrong', novo: 'New' }],
    [{ pagina: 2, linha: 0, original: 'Repeat text', novo: 'New' }],
    [{ pagina: 1, linha: 0, original: 'Repeat text', novo: 'Too long '.repeat(50) }],
    [{ pagina: 1, linha: 0, original: 'Repeat text', novo: 'Two\nlines' }],
    [{ pagina: 1, linha: 0, original: 'Repeat text', novo: '💡' }],
    [{ pagina: 1, linha: 0, original: 'Repeat text', novo: '' }],
    [0, 0].map(() => ({ pagina: 1, linha: 0, original: 'Repeat text', novo: 'New' })),
  ]) assert.throws(() => edit(bytes, changes));
});

test('editing works on rotated pages without changing other lines', () => {
  const bytes = editingFixture({ rotated: true });
  const result = run('texto/listar-editaveis', { pagina: 1 }, bytes).json;
  assert.equal(result.disponivel, true);
  const edited = edit(bytes, [{ pagina: 1, linha: 0, original: 'Repeat text', novo: 'New' }]);
  assert.match(text(edited), /New/); assert.match(text(edited), /Keep this line/);
  inspect(edited, doc => assert.equal(doc.findPage(0).getInheritable('Rotate').asNumber(), 90));
});

test('signature vectors appear at native PDF coordinates and preserve other pages', () => {
  const signature = { page: 2, matrix: [100, 0, 0, -100, 70, 600], aspect: .4, pen: .03, strokes: [[[.05, .05], [.5, .3], [.95, .05]]] };
  const output = run('assinatura/adicionar', { assinatura: JSON.stringify(signature) }).bytes;
  assert.equal(run('inspecionar', {}, output).json.total_paginas, 3);
  assert.equal(text(output), text(original));
  const pixels = (bytes, n) => inspect(bytes, doc => { const p = doc.loadPage(n), pix = p.toPixmap(mupdf.Matrix.identity, mupdf.ColorSpace.DeviceRGB, false); try { return pix.getPixels().slice(); } finally { pix.destroy(); p.destroy(); } });
  assert.deepEqual(pixels(output, 0), pixels(original, 0));
  assert.deepEqual(pixels(output, 2), pixels(original, 2));
  const before = pixels(original, 1), after = pixels(output, 1);
  let changed = 0;
  for (let i = 0; i < before.length; i += 3) if (before[i] !== after[i] || before[i + 1] !== after[i + 1] || before[i + 2] !== after[i + 2]) {
    const pixel = i / 3, x = pixel % 595, y = Math.floor(pixel / 595);
    assert.ok(x >= 69 && x <= 171 && y >= 241 && y <= 284, `${x},${y}`); changed++;
  }
  assert.ok(changed > 50);
});

test('signature rejects empty strokes, invalid matrices, wrong pages and off-page placement', () => {
  const base = { page: 1, matrix: [100, 0, 0, -100, 50, 500], aspect: .5, pen: .01, strokes: [[[.1, .1], [.8, .4]]] };
  for (const patch of [{page: 0}, {page: 4}, {matrix: [0, 0, 0, 0, 0, 0]}, {matrix: [100, 0, 0, -100, -500, 0]}, {strokes: []}, {strokes: [[[2, .1], [.8, .4]]]}, {aspect: -1}]) {
    assert.throws(() => run('assinatura/adicionar', { assinatura: JSON.stringify({...base, ...patch}) }));
  }
});

test('signature placement supports rotated CropBoxes and UserUnit without shifting the image', () => {
  const bytes = editingFixture({rotated:true});
  const doc = mupdf.Document.openDocument(bytes,'application/pdf');
  doc.findPage(0).put('CropBox',[20,20,575,822]); doc.findPage(0).put('UserUnit',1.5);
  const buffer=doc.saveToBuffer({}), cropped=buffer.asUint8Array().slice();buffer.destroy();doc.destroy();
  const sig={page:1,matrix:[100,0,0,-100,100,600],aspect:.4,pen:.02,strokes:[[[.1,.1],[.8,.3]]]};
  const signed=run('assinatura/adicionar',{assinatura:JSON.stringify(sig)},cropped).bytes;
  const render=bytes=>inspect(bytes,d=>{const p=d.loadPage(0),pix=p.toPixmap(mupdf.Matrix.identity,mupdf.ColorSpace.DeviceRGB,false);try{return {width:pix.getWidth(),pixels:pix.getPixels().slice()};}finally{pix.destroy();p.destroy();}});
  const before=render(cropped),after=render(signed);let changes=0;
  // Native x=110..180, y=570..590; rotated + CropBox + UserUnit map to x=825..855, y=135..240.
  for(let i=0;i<before.pixels.length;i+=3) if(before.pixels[i]!==after.pixels[i]) {
    const x=(i/3)%after.width,y=Math.floor(i/3/after.width);
    assert.ok(x>=820&&x<=860&&y>=130&&y<=245,`${x},${y}`);changes++;
  }
  assert.ok(changes>20);
});

// Compare painted pixels, not text origins or font ascender rectangles. At 2x,
// 1.5 PDF points allows three raster pixels for hinting and antialiasing.
test('watermarks center the rotated ink on mixed page sizes, CropBoxes and rotations', () => {
  const doc = new mupdf.PDFDocument();
  for (const [box, rotation] of [
    [[0, 0, 595, 842], 0], [[0, 0, 842, 595], 0], [[0, 0, 320, 480], 0],
    [[20, 30, 620, 830], 90], [[0, 0, 595, 842], 180], [[0, 0, 595, 842], 270],
  ]) doc.insertPage(-1, doc.addPage(box, rotation, {}, ''));
  doc.findPage(3).put('CropBox', [40, 60, 600, 800]);
  const buffer = doc.saveToBuffer();
  const input = buffer.asUint8Array().slice(); buffer.destroy(); doc.destroy();
  for (const angle of [0, 45]) {
    const { bytes } = run('anotacoes/marca-dagua', { texto: 'CONFIDENCIAL', opacidade: '.3', angulo: angle }, input);
    inspect(bytes, output => {
      assert.equal(output.countPages(), 6);
      for (let i = 0; i < output.countPages(); i++) {
        const page = output.loadPage(i), pixmap = page.toPixmap(mupdf.Matrix.scale(2, 2), mupdf.ColorSpace.DeviceRGB, false);
        const pixels = pixmap.getPixels(), stride = pixmap.getStride(), components = pixmap.getNumberOfComponents();
        let left = Infinity, top = Infinity, right = -Infinity, bottom = -Infinity;
        for (let y = 0; y < pixmap.getHeight(); y++) for (let x = 0; x < pixmap.getWidth(); x++) {
          if (pixels[y * stride + x * components] < 245) {
            left = Math.min(left, x); right = Math.max(right, x + 1);
            top = Math.min(top, y); bottom = Math.max(bottom, y + 1);
          }
        }
        assert.ok(Number.isFinite(left), 'watermark must be visible');
        assert.ok(Math.abs((left + right - pixmap.getWidth()) / 4) <= 1.5, `page ${i}, angle ${angle}: horizontal ink center`);
        assert.ok(Math.abs((top + bottom - pixmap.getHeight()) / 4) <= 1.5, `page ${i}, angle ${angle}: vertical ink center`);
        pixmap.destroy(); page.destroy();
      }
    });
  }
});
