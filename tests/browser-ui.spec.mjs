import { test, expect } from '@playwright/test';
import { readFile } from 'node:fs/promises';
import { processPdf } from '../perfectdf/web/static/pdf-engine.js';
const fixture = new URL('./fixtures/browser.pdf', import.meta.url).pathname;
const themeButton = page => page.getByRole('button', { name: /^Ativar tema (claro|escuro)$/ });
async function expectTheme(page, theme) {
  await expect(page.locator('html')).toHaveAttribute('data-theme', theme);
  await expect(page.locator('html')).toHaveCSS('color-scheme', theme);
  const action = theme === 'dark' ? 'Ativar tema claro' : 'Ativar tema escuro';
  await expect(themeButton(page)).toHaveAttribute('aria-label', action);
  await expect(themeButton(page)).toHaveAttribute('title', action);
  await expect(themeButton(page).locator(theme === 'dark' ? '.theme-sun' : '.theme-moon')).toBeVisible();
  await expect(themeButton(page).locator(theme === 'dark' ? '.theme-moon' : '.theme-sun')).toBeHidden();
}

for (const theme of ['light', 'dark']) {
  test(`first visit follows the ${theme} system appearance without saving a manual choice`, async ({ page }) => {
    await page.emulateMedia({ colorScheme: theme });
    await page.goto('/');
    await expectTheme(page, theme);
    expect(await page.evaluate(() => localStorage.getItem('perfectdf-theme'))).toBeNull();
    await page.reload();
    await expectTheme(page, theme);
  });
}

test('theme toggle supports keyboard, saves the choice and restores it on reopening', async ({ page, browser }) => {
  await page.emulateMedia({ colorScheme: 'light' });
  await page.goto('/');
  await page.keyboard.press('Tab');
  await expect(page.getByRole('link', { name: 'PerfectDF, início' })).toBeFocused();
  await page.keyboard.press('Tab');
  await expect(themeButton(page)).toBeFocused();
  await expect(themeButton(page)).toHaveCSS('outline-width', '2px');
  await page.keyboard.press('Space');
  await expectTheme(page, 'dark');
  expect(await page.evaluate(() => localStorage.getItem('perfectdf-theme'))).toBe('dark');
  await page.reload();
  await expectTheme(page, 'dark');
  const reopened = await browser.newContext({ storageState: await page.context().storageState(), colorScheme: 'light' });
  try {
    const next = await reopened.newPage();
    await next.goto(new URL('/', page.url()).href);
    await expectTheme(next, 'dark');
    await themeButton(next).focus();
    await next.keyboard.press('Enter');
    await expectTheme(next, 'light');
    await next.reload();
    await expectTheme(next, 'light');
  } finally { await reopened.close(); }
});

test('system appearance changes are followed until a manual theme is chosen', async ({ page }) => {
  await page.emulateMedia({ colorScheme: 'light' });
  await page.goto('/');
  await expectTheme(page, 'light');
  await page.emulateMedia({ colorScheme: 'dark' });
  await expectTheme(page, 'dark');
  await themeButton(page).click();
  await expectTheme(page, 'light');
  await page.emulateMedia({ colorScheme: 'light' });
  await page.emulateMedia({ colorScheme: 'dark' });
  await expectTheme(page, 'light');
  expect(await page.evaluate(() => localStorage.getItem('perfectdf-theme'))).toBe('light');
});

test('blocked storage does not break theme switching or opening a PDF', async ({ page }) => {
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.addInitScript(() => {
    for (const key of ['getItem', 'setItem']) Object.defineProperty(Storage.prototype, key, {
      value() { throw new DOMException('Storage blocked', 'SecurityError'); },
    });
  });
  await page.emulateMedia({ colorScheme: 'dark' });
  await page.goto('/');
  await expectTheme(page, 'dark');
  await themeButton(page).click();
  await expectTheme(page, 'light');
  await page.emulateMedia({ colorScheme: 'light' });
  await page.emulateMedia({ colorScheme: 'dark' });
  await expectTheme(page, 'light');
  await page.locator('#file-input').setInputFiles(fixture);
  await expect(page.locator('#span-page-count')).toHaveText('3');
  expect(errors).toEqual([]);
});

test('theme choice is shared with the license page and other tabs', async ({ page, context }) => {
  await page.emulateMedia({ colorScheme: 'dark' });
  await page.goto('/');
  const legal = await context.newPage();
  await legal.emulateMedia({ colorScheme: 'dark' });
  await legal.goto('/licenses.html');
  await expectTheme(legal, 'dark');
  await themeButton(page).click();
  await expectTheme(legal, 'light');
  await expect(legal.locator('meta[name="theme-color"]')).toHaveAttribute('content', '#f1f3f5');
  await themeButton(legal).click();
  await expectTheme(page, 'dark');
  await expect(page.locator('meta[name="theme-color"]')).toHaveAttribute('content', '#151e29');
  await legal.reload();
  await expectTheme(legal, 'dark');
  await legal.evaluate(() => localStorage.removeItem('perfectdf-theme'));
  await expectTheme(page, 'dark');
  await page.emulateMedia({ colorScheme: 'light' });
  await expectTheme(page, 'light');
});

test('theme control remains reachable by touch and keyboard on a small phone', async ({ browser, baseURL }) => {
  const context = await browser.newContext({ viewport: { width: 320, height: 740 }, hasTouch: true, isMobile: true, colorScheme: 'dark', reducedMotion: 'reduce' });
  try {
    const page = await context.newPage();
    await page.goto(baseURL);
    await expectTheme(page, 'dark');
    const button = await themeButton(page).boundingBox();
    expect(button.width).toBeGreaterThanOrEqual(44);
    expect(button.height).toBeGreaterThanOrEqual(44);
    await page.getByRole('link', { name: 'PerfectDF, início' }).focus();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await themeButton(page).tap();
    await expectTheme(page, 'light');
    await themeButton(page).focus();
    await page.keyboard.press('Space');
    await expectTheme(page, 'dark');
    await page.goto(new URL('/licenses.html', baseURL).href);
    await expectTheme(page, 'dark');
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  } finally { await context.close(); }
});

test('changing theme preserves white PDF pages, rendered pixels and the exported bytes', async ({ page }) => {
  await page.emulateMedia({ colorScheme: 'light' });
  await page.goto('/');
  await page.locator('#file-input').setInputFiles(fixture);
  await expect(page.locator('#span-page-count')).toHaveText('3');
  await page.locator('#btn-executar-acao').click();
  await expect(page.locator('#estado-visualizacao')).toHaveText('Mostrando prévia');
  const downloadBytes = async () => {
    const downloaded = page.waitForEvent('download');
    await page.locator('#btn-baixar-previa').click();
    return readFile(await (await downloaded).path());
  };
  const before = await downloadBytes();
  const pixels = await page.locator('#pdf-canvas').evaluate(canvas => canvas.toDataURL());
  for (const theme of ['dark', 'light']) {
    await themeButton(page).click();
    await expectTheme(page, theme);
    await expect(page.locator('#pdf-canvas')).toHaveCSS('background-color', 'rgb(255, 255, 255)');
    await expect(page.locator('.pdf-page-surface')).toHaveCSS('color-scheme', 'light');
    await expect(page.locator('#pdf-canvas')).toHaveCSS('filter', 'none');
    expect(await page.locator('#pdf-canvas').evaluate(canvas => canvas.toDataURL())).toBe(pixels);
    await expect(page.locator('#btn-baixar-previa')).toBeEnabled();
    expect(await downloadBytes()).toEqual(before);
  }
  expect(processPdf({ operation: 'inspecionar', files: [{ bytes: new Uint8Array(before), name: 'export.pdf' }] }).json.total_paginas).toBe(3);
});

test('dark panels, controls, dialog and errors have readable contrast while the signature pad stays light', async ({ page }) => {
  await page.emulateMedia({ colorScheme: 'dark' });
  await page.goto('/');
  await page.locator('#file-input').setInputFiles(fixture);
  await expect(page.locator('#span-page-count')).toHaveText('3');
  const contrast = selector => page.locator(selector).first().evaluate(element => {
    const rgb = color => color.match(/[\d.]+/g).map(Number);
    const luminance = color => rgb(color).slice(0, 3).map(c => c / 255).map(c => c <= .04045 ? c / 12.92 : ((c + .055) / 1.055) ** 2.4).reduce((sum, c, i) => sum + c * [.2126, .7152, .0722][i], 0);
    let surface = element;
    while (surface.parentElement && (rgb(getComputedStyle(surface).backgroundColor)[3] ?? 1) === 0) surface = surface.parentElement;
    const a = luminance(getComputedStyle(element).color), b = luminance(getComputedStyle(surface).backgroundColor);
    return (Math.max(a, b) + .05) / (Math.min(a, b) + .05);
  });
  for (const selector of ['.app-header', '.tool-sidebar', '.tool-area', '.operation-button.active', '#btn-executar-acao', '#input-paginas-lista', '.field-hint', '.app-footer']) {
    expect(await contrast(selector), selector).toBeGreaterThanOrEqual(4.5);
  }
  await page.locator('#input-paginas-lista').focus();
  await expect(page.locator('#input-paginas-lista')).toHaveCSS('outline-style', 'solid');
  await page.locator('[data-tab="tab-anotacoes"]').click();
  await page.getByRole('button', { name: 'Adicionar assinatura', exact: true }).click();
  await page.locator('#signature-create').click();
  await expect(page.locator('#signature-dialog')).toBeVisible();
  expect(await contrast('#signature-dialog')).toBeGreaterThanOrEqual(4.5);
  await expect(page.locator('#signature-pad')).toHaveCSS('background-color', 'rgb(250, 251, 252)');
  await page.locator('#signature-confirm').click();
  await expect(page.locator('#signature-draw-error')).toContainText('Desenhe');
  expect(await contrast('#signature-draw-error')).toBeGreaterThanOrEqual(4.5);
  await page.locator('#signature-cancel').click();
  await page.locator('#file-input').setInputFiles({ name: 'invalid.pdf', mimeType: 'application/pdf', buffer: Buffer.from('invalid') });
  await expect(page.locator('#feedback-message')).toHaveClass(/error/);
  expect(await contrast('#feedback-message')).toBeGreaterThanOrEqual(4.5);
});

test('static site opens, previews and downloads a PDF without API calls or uploads', async ({ page }) => {
  const requests = [], errors = [];
  page.on('request', request => requests.push({ method: request.method(), url: request.url() }));
  page.on('pageerror', error => errors.push(error.message));
  await page.goto('/');
  await expect(page.locator('#api-status-badge')).toHaveText('Processamento local');
  await page.locator('#file-input').setInputFiles(fixture);
  await expect(page.locator('#file-meta')).toContainText('Páginas: 3');
  await expect(page.locator('#span-page-count')).toHaveText('3');
  await page.locator('#input-paginas-lista').fill('1');
  await page.locator('#btn-executar-acao').click();
  await expect(page.locator('#estado-visualizacao')).toHaveText('Mostrando prévia');
  const downloaded = page.waitForEvent('download');
  await page.locator('#btn-baixar-previa').click();
  const download = await downloaded;
  const bytes = new Uint8Array(await readFile(await download.path()));
  const { json } = processPdf({ operation: 'inspecionar', files: [{ bytes, name: 'girado.pdf' }] });
  expect(json.total_paginas).toBe(3);
  expect(requests.filter(r => r.method !== 'GET' || new URL(r.url).pathname.startsWith('/api/'))).toEqual([]);
  expect(errors).toEqual([]);
});

test('joining works without opening a document first', async ({ page }) => {
  await page.goto('/');
  await page.locator('[data-tab="tab-juntar"]').click();
  await page.locator('#input-multiplos-pdfs').setInputFiles([fixture, fixture]);
  const downloaded = page.waitForEvent('download');
  await page.locator('#btn-executar-acao').click();
  const download = await downloaded;
  const bytes = new Uint8Array(await readFile(await download.path()));
  const { json } = processPdf({ operation: 'inspecionar', files: [{ bytes, name: 'juntado.pdf' }] });
  expect(json.total_paginas).toBe(6);
});

test('invalid PDFs show a local error', async ({ page }) => {
  await page.goto('/');
  await page.locator('#file-input').setInputFiles({ name: 'invalido.pdf', mimeType: 'application/pdf', buffer: Buffer.from('not a pdf') });
  await expect(page.locator('#feedback-message')).toHaveClass(/error/);
});

test('visible tools select the operation before opening a PDF', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'Extrair páginas', exact: true }).click();
  await expect(page.locator('#active-tool-title')).toHaveText('Extrair páginas');
  await expect(page.getByRole('button', { name: 'Extrair páginas', exact: true })).toHaveAttribute('aria-pressed', 'true');
  await page.locator('#file-input').setInputFiles(fixture);
  await expect(page.locator('#file-meta')).toContainText('Páginas: 3');
  await page.locator('#input-paginas-lista').fill('2');
  await page.locator('#btn-executar-acao').click();
  await expect(page.locator('#estado-visualizacao')).toHaveText('Mostrando prévia');
  await expect(page.locator('#span-page-count')).toHaveText('1');
});

test('forms can be filled through labeled fields without writing JSON', async ({ page }) => {
  await page.goto('/');
  await page.locator('#file-input').setInputFiles(fixture);
  await expect(page.locator('#file-meta')).toContainText('Páginas: 3');
  await page.getByRole('button', { name: 'Formulários', exact: true }).click();
  await page.getByRole('button', { name: 'Preencher formulário', exact: true }).click();
  await page.getByLabel('nome', { exact: true }).fill('Maria de Souza');
  await page.getByLabel('aceito', { exact: true }).check();
  await page.locator('#btn-executar-acao').click();
  await expect(page.locator('#estado-visualizacao')).toHaveText('Mostrando prévia');
  const downloaded = page.waitForEvent('download');
  await page.locator('#btn-baixar-previa').click();
  const download = await downloaded;
  const bytes = new Uint8Array(await readFile(await download.path()));
  const { json } = processPdf({ operation: 'formularios/listar', files: [{ bytes, name: 'form.pdf' }] });
  expect(json.campos.map(field => field.valor)).toEqual(['Maria de Souza', 'Yes']);
});

test('mobile tools remain usable without horizontal page overflow', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/');
  await page.getByRole('button', { name: 'Texto', exact: true }).click();
  await page.getByRole('button', { name: 'Adicionar texto', exact: true }).click();
  await page.locator('#file-input').setInputFiles(fixture);
  await expect(page.locator('#file-meta')).toContainText('Páginas: 3');
  await page.locator('#input-add-texto-conteudo').fill('Revisado');
  await page.locator('#btn-executar-acao').click();
  await expect(page.locator('#estado-visualizacao')).toHaveText('Mostrando prévia');
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await expect(page.getByRole('link', { name: 'Código-fonte' })).toBeVisible();
  await expect(page.locator('#footer-file')).toHaveText('browser.pdf');
});

test('existing text can be selected on the page and replaced in a downloaded PDF', async ({ page }) => {
  await page.goto('/');
  await page.locator('#file-input').setInputFiles(fixture);
  await expect(page.locator('#file-meta')).toContainText('Páginas: 3');
  await page.getByRole('button', { name: 'Texto', exact: true }).click();
  await page.getByRole('button', { name: 'Editar: Pagina 1 Ola teste', exact: true }).click();
  await expect(page.locator('#input-edit-substituicao')).toHaveValue('Pagina 1 Ola teste');
  await page.locator('#input-edit-substituicao').fill('Texto corrigido');
  await page.locator('#input-edit-pagina').fill('2');
  await page.locator('#input-edit-pagina').press('Tab');
  await expect(page.locator('#select-edit-linha')).toContainText('Pagina 2 Ola teste');
  await page.locator('#select-edit-linha').selectOption('0');
  await page.locator('#input-edit-substituicao').fill('Segunda página');
  await expect(page.locator('#text-edit-count')).toContainText('2 linhas alteradas');
  await page.locator('#btn-executar-acao').click();
  await expect(page.locator('#estado-visualizacao')).toHaveText('Mostrando prévia');
  const downloaded = page.waitForEvent('download');
  await page.locator('#btn-baixar-previa').click();
  const download = await downloaded;
  const bytes = new Uint8Array(await readFile(await download.path()));
  const { json } = processPdf({ operation: 'texto/extrair', files: [{ bytes, name: 'editado.pdf' }] });
  expect(json.texto).toContain('Texto corrigido');
  expect(json.texto).toContain('Segunda página');
  expect(json.texto).not.toContain('Pagina 1 Ola teste');
  expect(json.texto).not.toContain('Pagina 2 Ola teste');
  expect(json.texto).toContain('Pagina 3 Ola teste');
});

test('OCR text is blocked in the editor', async ({ page }) => {
  const mupdf = await import('../perfectdf/web/static/vendor/mupdf/mupdf.js');
  const doc = new mupdf.PDFDocument(), font = new mupdf.Font('Helvetica');
  doc.insertPage(-1, doc.addPage([0, 0, 595, 842], 0, { Font: { F1: doc.addSimpleFont(font, 'Latin') } }, 'BT /F1 12 Tf 3 Tr 50 790 Td (OCR text) Tj ET'));
  const output = doc.saveToBuffer({});
  const buffer = Buffer.from(output.asUint8Array()); output.destroy(); font.destroy(); doc.destroy();
  await page.goto('/');
  await page.locator('#file-input').setInputFiles({ name: 'scan-ocr.pdf', mimeType: 'application/pdf', buffer });
  await expect(page.locator('#file-meta')).toContainText('Páginas: 1');
  await page.getByRole('button', { name: 'Texto', exact: true }).click();
  await expect(page.locator('#text-edit-status')).toContainText('OCR');
  await expect(page.locator('#text-edit-controls')).toBeHidden();
  await expect(page.locator('#btn-executar-acao')).toBeDisabled();
  await expect(page.locator('.text-target')).toHaveCount(0);
});

test('a delayed merge cannot overwrite another tool or start a stale download', async ({ page }) => {
  let downloads = 0;
  page.on('download', () => downloads++);
  await page.goto('/');
  await page.locator('#file-input').setInputFiles(fixture);
  await expect(page.locator('#span-page-count')).toHaveText('3');
  await page.evaluate(() => {
    const local = window.localPdfRequest;
    window.localPdfRequest = async (...args) => {
      const response = await local(...args);
      if (args[0] === '/api/paginas/juntar') {
        await new Promise(resolve => window.releaseMerge = resolve);
        window.mergeReleased = true;
      }
      return response;
    };
  });
  await page.locator('[data-tab="tab-juntar"]').click();
  await page.locator('#input-multiplos-pdfs').setInputFiles([fixture, fixture]);
  await page.locator('#btn-executar-acao').click();
  await page.waitForFunction(() => typeof window.releaseMerge === 'function');
  await page.locator('[data-tab="tab-paginas"]').click();
  await page.evaluate(() => window.releaseMerge());
  await page.waitForFunction(() => window.mergeReleased);
  await expect(page.locator('#span-page-count')).toHaveText('3');
  await expect(page.locator('#file-name')).toHaveText('browser.pdf');
  await expect(page.locator('#estado-visualizacao')).toHaveText('Mostrando original');
  expect(downloads).toBe(0);
});

test('removing a document invalidates a pending preview', async ({ page }) => {
  await page.goto('/');
  await page.locator('#file-input').setInputFiles(fixture);
  await expect(page.locator('#span-page-count')).toHaveText('3');
  await page.evaluate(() => {
    const local = window.localPdfRequest;
    window.localPdfRequest = async (...args) => {
      const response = await local(...args);
      if (args[0] === '/api/paginas/girar') {
        await new Promise(resolve => window.releasePreview = resolve);
        window.previewReleased = true;
      }
      return response;
    };
  });
  await page.locator('#btn-executar-acao').click();
  await page.waitForFunction(() => typeof window.releasePreview === 'function');
  await page.locator('#btn-remove-file').click();
  await page.evaluate(() => window.releasePreview());
  await page.waitForFunction(() => window.previewReleased);
  await expect(page.locator('#viewer-section')).toBeHidden();
  await expect(page.locator('#btn-baixar-previa')).toBeDisabled();
  await expect(page.locator('#estado-visualizacao')).toHaveText('Nenhum documento aberto');
});

test('viewer workers stay bounded across previews and are released on removal', async ({ page }) => {
  await page.goto('/');
  await page.locator('#file-input').setInputFiles(fixture);
  await expect(page.locator('#span-page-count')).toHaveText('3');
  for (let i = 0; i < 4; i++) {
    await page.locator('#btn-executar-acao').click();
    await expect(page.locator('#btn-executar-acao')).toBeEnabled();
    await expect(page.locator('#estado-visualizacao')).toHaveText('Mostrando prévia');
    await expect.poll(() => page.workers().filter(worker => worker.url().includes('pdf.worker')).length).toBe(1);
  }
  await page.locator('#btn-remove-file').click();
  await expect.poll(() => page.workers().filter(worker => worker.url().includes('pdf.worker')).length).toBe(0);
});

test('local worker requests can be cancelled immediately', async ({ page }) => {
  await page.goto('/');
  const name = await page.evaluate(async () => {
    const body = new FormData(); body.append('arquivo', new File(['invalid'], 'test.pdf'));
    const controller = new AbortController();
    const request = window.localPdfRequest('/api/inspecionar', { body, signal: controller.signal });
    controller.abort();
    try { await request; return 'unexpected success'; } catch (error) { return error.name; }
  });
  expect(name).toBe('AbortError');
  await expect.poll(() => page.workers().filter(worker => worker.url().endsWith('/pdf-worker.js')).length).toBe(0);
  await expect(page.locator('#btn-open-file')).toHaveCount(0);
});

test('license and source links are available in the static distribution', async ({ page, request }) => {
  await page.goto('/');
  await page.getByRole('link', { name: 'Licenças e fontes' }).click();
  await expect(page.getByRole('heading', { name: 'Licenças e código-fonte' })).toBeVisible();
  const links = await page.locator('a[href^="/"]').evaluateAll(anchors => anchors.map(anchor => anchor.getAttribute('href')));
  for (const link of links) {
    const response = await request.head(link);
    expect(response.status(), link).toBe(200);
  }
});

test('a late file read cannot replace a newer document', async ({ page }) => {
  const source = new Uint8Array(await readFile(fixture));
  const second = processPdf({ operation: 'paginas/extrair', fields: { paginas: '1,2' }, files: [{ bytes: source, name: 'original.pdf' }] }).bytes;
  await page.goto('/');
  await page.evaluate(() => {
    const read = File.prototype.arrayBuffer;
    const request = window.localPdfRequest;
    window.localPdfRequest = async (...args) => {
      const response = await request(...args);
      if (args[1].body.get('arquivo')?.name === 'old.pdf') window.oldInspectionFinished = true;
      return response;
    };
    window.releaseReads = [];
    File.prototype.arrayBuffer = async function () {
      if (this.name === 'old.pdf') await new Promise(resolve => window.releaseReads.push(resolve));
      return read.call(this);
    };
  });
  await page.locator('#file-input').setInputFiles({ name: 'old.pdf', mimeType: 'application/pdf', buffer: Buffer.from(source) });
  await page.waitForFunction(() => window.releaseReads.length === 2);
  await page.locator('#file-input').setInputFiles({ name: 'new.pdf', mimeType: 'application/pdf', buffer: Buffer.from(second) });
  await expect(page.locator('#span-page-count')).toHaveText('2');
  await page.evaluate(() => { for (const release of window.releaseReads) release(); });
  await page.waitForFunction(() => window.oldInspectionFinished);
  await expect(page.locator('#file-name')).toHaveText('new.pdf');
  await expect(page.locator('#file-meta')).toContainText('Páginas: 2');
  await expect(page.locator('#span-page-count')).toHaveText('2');
});

test('switching tools while a preview is loading restores the original viewer', async ({ page }) => {
  await page.goto('/');
  await page.locator('#file-input').setInputFiles(fixture);
  await expect(page.locator('#span-page-count')).toHaveText('3');
  await page.evaluate(() => {
    const viewer = window.pdfjsLib;
    let hold = true;
    window.viewerLoadCount = 0;
    window.pdfjsLib = { ...viewer, getDocument(options) {
      window.viewerLoadCount++;
      const task = viewer.getDocument(options);
      if (!hold) return task;
      hold = false;
      return { destroy: () => task.destroy(), promise: task.promise.then(doc => new Promise(resolve => {
        window.releaseViewer = () => { window.oldViewerReleased = true; resolve(doc); };
      })) };
    } };
  });
  await page.locator('#btn-executar-acao').click();
  await page.waitForFunction(() => typeof window.releaseViewer === 'function');
  await page.locator('[data-tab="tab-anotacoes"]').click();
  await expect.poll(() => page.evaluate(() => window.viewerLoadCount)).toBe(2);
  await page.evaluate(() => window.releaseViewer());
  await expect(page.locator('#estado-visualizacao')).toHaveText('Mostrando original');
  await expect(page.locator('#span-page-count')).toHaveText('3');
  await expect.poll(() => page.workers().filter(worker => worker.url().includes('pdf.worker')).length).toBe(1);
});

async function drawSignature(page) {
  await page.locator('#signature-create').click();
  await page.locator('#signature-confirm').click();
  await expect(page.locator('#signature-draw-error')).toContainText('Desenhe');
  const pad = await page.locator('#signature-pad').boundingBox();
  await page.mouse.move(pad.x + 30, pad.y + 70); await page.mouse.down();
  await page.mouse.move(pad.x + 100, pad.y + 35, {steps: 8}); await page.mouse.up();
  await page.locator('#signature-clear').click(); await page.locator('#signature-confirm').click();
  await expect(page.locator('#signature-draw-error')).toContainText('Desenhe');
  await page.mouse.move(pad.x + 30, pad.y + 70); await page.mouse.down();
  await page.mouse.move(pad.x + 100, pad.y + 35, {steps: 8});
  await page.mouse.move(pad.x + 170, pad.y + 100, {steps: 8}); await page.mouse.up();
  await page.locator('#signature-confirm').click();
  await expect(page.locator('.signature-placement')).toBeVisible();
}

test('draw, clear, move, resize and export a signature at the chosen page coordinates', async ({ page }) => {
  await page.goto('/');
  await page.locator('#file-input').setInputFiles(fixture);
  await expect(page.locator('#span-page-count')).toHaveText('3');
  await page.locator('[data-tab="tab-anotacoes"]').click();
  await page.getByRole('button', {name:'Adicionar assinatura',exact:true}).click();
  await drawSignature(page);
  await page.locator('#signature-remove').click();
  await expect(page.locator('.signature-placement')).toHaveCount(0);
  await drawSignature(page);
  await page.locator('#signature-page').fill('2'); await page.locator('#signature-page').press('Tab');
  await expect(page.locator('#input-page-num')).toHaveValue('2');
  const signature = page.locator('.signature-placement');
  const beforeZoom = await signature.evaluate(element => ({ width: element.getBoundingClientRect().width, pageWidth: document.getElementById('pdf-canvas').getBoundingClientRect().width }));
  await page.locator('#btn-zoom-in').click();
  // The old overlay remains visible while PDF.js renders. Wait for the new
  // viewport geometry, not just visibility, before resolving a bounding box.
  await expect.poll(() => page.locator('#pdf-canvas').evaluate(canvas => canvas.getBoundingClientRect().width)).toBeCloseTo(beforeZoom.pageWidth * 1.25, 1);
  await expect.poll(() => signature.evaluate((element, beforeZoom) => {
    const pageWidth = document.getElementById('pdf-canvas').getBoundingClientRect().width;
    return Math.abs(element.getBoundingClientRect().width - beforeZoom.width * pageWidth / beforeZoom.pageWidth);
  }, beforeZoom)).toBeLessThan(.01);
  await expect(page.locator('#span-zoom-level')).toHaveText('125%');
  await expect(signature).toBeVisible();
  const box = await signature.boundingBox();
  expect(box).not.toBeNull();
  await page.mouse.move(box.x + 10, box.y + 10); await page.mouse.down(); await page.mouse.move(box.x + 50, box.y + 40, {steps:5}); await page.mouse.up();
  const handle = await page.locator('.signature-resize').boundingBox();
  await page.mouse.move(handle.x + 12, handle.y + 12); await page.mouse.down(); await page.mouse.move(handle.x + 40, handle.y + 28,{steps:5}); await page.mouse.up();
  const expected = await page.evaluate(() => {
    const canvas = document.getElementById('pdf-canvas').getBoundingClientRect(), box = document.querySelector('.signature-placement').getBoundingClientRect();
    return { x:(box.x-canvas.x)/canvas.width, y:(box.y-canvas.y)/canvas.height, w:box.width/canvas.width, h:box.height/canvas.height };
  });
  const requests=[];page.on('request',r=>requests.push(r.method()));
  await page.locator('#btn-executar-acao').click();
  await expect(page.locator('#estado-visualizacao')).toHaveText('Mostrando prévia');
  await expect(page.locator('.signature-placement')).toHaveCount(0);
  const downloaded = page.waitForEvent('download'); await page.locator('#btn-baixar-previa').click();
  const download=await downloaded, bytes=new Uint8Array(await readFile(await download.path()));
  const m=await import('../perfectdf/web/static/vendor/mupdf/mupdf.js');
  const doc=m.Document.openDocument(bytes,'application/pdf'), p=doc.loadPage(1), pix=p.toPixmap(m.Matrix.identity,m.ColorSpace.DeviceRGB,false);
  const pixels=pix.getPixels();let xs=[],ys=[];
  // The signature is the only non-white content below the sample's first text line.
  for(let y=100;y<pix.getHeight();y++) for(let x=0;x<pix.getWidth();x++) {const i=(y*pix.getWidth()+x)*3;if(pixels[i]<150){xs.push(x);ys.push(y);}}
  expect(xs.length).toBeGreaterThan(30);
  expect(Math.min(...xs)/595).toBeGreaterThanOrEqual(expected.x-.01);
  expect(Math.max(...xs)/595).toBeLessThanOrEqual(expected.x+expected.w+.01);
  expect(Math.min(...ys)/842).toBeGreaterThanOrEqual(expected.y-.01);
  expect(Math.max(...ys)/842).toBeLessThanOrEqual(expected.y+expected.h+.01);
  pix.destroy();p.destroy();doc.destroy();expect(requests.every(method=>method==='GET')).toBe(true);
  await page.locator('#signature-remove').click();
  await expect(page.locator('#btn-baixar-previa')).toBeDisabled();
  await expect(page.locator('#btn-executar-acao')).toBeDisabled();
});

test('signature drawing and placement accept touch pointer events on mobile', async ({ page }) => {
  await page.setViewportSize({width:390,height:844}); await page.goto('/');
  await page.locator('#file-input').setInputFiles(fixture); await expect(page.locator('#span-page-count')).toHaveText('3');
  await page.locator('[data-tab="tab-anotacoes"]').click();
  await page.getByRole('button',{name:'Adicionar assinatura',exact:true}).click();
  await page.locator('#signature-create').click();
  const pad = await page.locator('#signature-pad').boundingBox();
  const touch = await page.context().newCDPSession(page);
  await touch.send('Input.dispatchTouchEvent', {type:'touchStart',touchPoints:[{x:pad.x+30,y:pad.y+60}]});
  await touch.send('Input.dispatchTouchEvent', {type:'touchMove',touchPoints:[{x:pad.x+90,y:pad.y+30}]});
  await touch.send('Input.dispatchTouchEvent', {type:'touchMove',touchPoints:[{x:pad.x+170,y:pad.y+90}]});
  await touch.send('Input.dispatchTouchEvent', {type:'touchEnd',touchPoints:[]});
  await page.locator('#signature-confirm').click(); await expect(page.locator('.signature-placement')).toBeVisible();
  await page.locator('.signature-placement').scrollIntoViewIfNeeded();
  const position = await page.locator('.signature-placement').boundingBox();
  await touch.send('Input.dispatchTouchEvent', {type:'touchStart',touchPoints:[{x:position.x+10,y:position.y+10}]});
  await touch.send('Input.dispatchTouchEvent', {type:'touchMove',touchPoints:[{x:position.x+30,y:position.y+20}]});
  await touch.send('Input.dispatchTouchEvent', {type:'touchEnd',touchPoints:[]});
  await expect.poll(async () => (await page.locator('.signature-placement').boundingBox()).x).toBeGreaterThan(position.x+10);
  await page.locator('.signature-placement').focus(); await page.keyboard.press('ArrowRight');
  await page.locator('#btn-executar-acao').click(); await expect(page.locator('#estado-visualizacao')).toHaveText('Mostrando prévia');
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
});

test('a narrow vertical signature stays inside a mobile page when moved and enlarged', async ({ page }) => {
  await page.setViewportSize({width:390,height:844}); await page.goto('/');
  await page.locator('#file-input').setInputFiles(fixture);
  await expect(page.locator('#span-page-count')).toHaveText('3');
  await page.locator('[data-tab="tab-anotacoes"]').click();
  await page.locator('#signature-create').click();
  const pad = await page.locator('#signature-pad').boundingBox();
  await page.mouse.move(pad.x+60,pad.y+10); await page.mouse.down();
  await page.mouse.move(pad.x+60,pad.y+175,{steps:15}); await page.mouse.up();
  await page.locator('#signature-confirm').click();
  const box = page.locator('.signature-placement');
  await expect(box).toBeVisible();
  const initial = await box.boundingBox(); expect(initial.width).toBeLessThan(24);
  await box.focus(); await page.keyboard.press('ArrowRight');
  expect((await box.boundingBox()).width).toBeCloseTo(initial.width,1);
  await box.scrollIntoViewIfNeeded();
  const position = await box.boundingBox(), touch = await page.context().newCDPSession(page);
  await touch.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x:position.x+3,y:position.y+30}]});
  await touch.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:position.x+35,y:position.y+60}]});
  await touch.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});
  expect((await box.boundingBox()).width).toBeCloseTo(initial.width,1);
  const handle = page.locator('.signature-resize'); await handle.scrollIntoViewIfNeeded();
  const corner = await handle.boundingBox();
  await page.mouse.move(corner.x+12,corner.y+12); await page.mouse.down();
  await page.mouse.move(corner.x+700,corner.y+700,{steps:5}); await page.mouse.up();
  const bounds = await page.evaluate(() => {
    const a=document.querySelector('.signature-placement').getBoundingClientRect(), p=document.getElementById('pdf-canvas').getBoundingClientRect();
    return {left:a.left-p.left,top:a.top-p.top,right:a.right-p.right,bottom:a.bottom-p.bottom};
  });
  expect(bounds.left).toBeGreaterThanOrEqual(-.1);expect(bounds.top).toBeGreaterThanOrEqual(-.1);
  expect(bounds.right).toBeLessThanOrEqual(.1);expect(bounds.bottom).toBeLessThanOrEqual(.1);
  await page.locator('#btn-executar-acao').click();
  await expect(page.locator('#estado-visualizacao')).toHaveText('Mostrando prévia');
  const downloaded=page.waitForEvent('download');await page.locator('#btn-baixar-previa').click();
  const bytes = new Uint8Array(await readFile(await (await downloaded).path()));
  expect(processPdf({operation:'inspecionar',files:[{bytes,name:'signed.pdf'}]}).json.total_paginas).toBe(3);
});

test('preview download requires current edits and the current document', async ({ page }) => {
  let downloads=0; page.on('download',()=>downloads++);
  await page.goto('/'); await page.locator('#file-input').setInputFiles(fixture);
  await expect(page.locator('#span-page-count')).toHaveText('3');
  await page.locator('#btn-executar-acao').click();
  await expect(page.locator('#btn-baixar-previa')).toBeEnabled();
  await page.locator('#input-paginas-lista').fill('2');
  await expect(page.locator('#btn-baixar-previa')).toBeDisabled();
  await expect(page.locator('#aviso-previa-desatualizada')).toContainText('Gere uma nova prévia antes de baixar');
  // The handler must also enforce freshness, independently of the disabled attribute.
  await page.locator('#btn-baixar-previa').evaluate(button=>{button.disabled=false;button.click();});
  await expect(page.locator('#feedback-message')).toContainText('Gere uma nova prévia');
  expect(downloads).toBe(0);
  await page.locator('#btn-executar-acao').click(); await expect(page.locator('#btn-baixar-previa')).toBeEnabled();
  await expect(page.locator('#aviso-previa-desatualizada')).toBeHidden();
  const downloaded=page.waitForEvent('download'); await page.locator('#btn-baixar-previa').click(); await downloaded;
  await page.locator('#file-input').setInputFiles({name:'new.pdf',mimeType:'application/pdf',buffer:await readFile(fixture)});
  await expect(page.locator('#file-name')).toHaveText('new.pdf');
  await expect(page.locator('#btn-baixar-previa')).toBeDisabled();
  await page.locator('#btn-executar-acao').click(); await expect(page.locator('#btn-baixar-previa')).toBeEnabled();
});

test('edits made while a preview is pending require another generation', async ({ page }) => {
  await page.goto('/');await page.locator('#file-input').setInputFiles(fixture);
  await expect(page.locator('#span-page-count')).toHaveText('3');
  await page.locator('#btn-executar-acao').click(); await expect(page.locator('#btn-baixar-previa')).toBeEnabled();
  await page.evaluate(()=>{
    const request=window.localPdfRequest;
    window.localPdfRequest=async (...args)=>{
      const response=await request(...args);
      if(args[0]==='/api/paginas/girar'&&!window.holdUsed){window.holdUsed=true;await new Promise(resolve=>window.releaseCurrentPreview=resolve);}
      return response;
    };
  });
  await page.locator('#btn-executar-acao').click();
  await expect(page.locator('#btn-baixar-previa')).toBeDisabled();
  await page.waitForFunction(()=>typeof window.releaseCurrentPreview==='function');
  await page.locator('#input-paginas-lista').fill('1');
  await page.evaluate(()=>window.releaseCurrentPreview());
  await expect(page.locator('#btn-executar-acao')).toBeEnabled();
  await expect(page.locator('#btn-baixar-previa')).toBeDisabled();
  await expect(page.locator('#aviso-previa-desatualizada')).toBeVisible();
  await page.locator('#btn-executar-acao').click();await expect(page.locator('#btn-baixar-previa')).toBeEnabled();
});

for (const width of [1366, 320]) {
  test(`header uses the correct transparent logo and an icon-only theme action at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 860 });
    await page.emulateMedia({ colorScheme: 'light', reducedMotion: 'reduce' });
    await page.goto('/');
    for (const theme of ['light', 'dark', 'light']) {
      await expectTheme(page, theme);
      const visible = page.locator(theme === 'dark' ? '.brand-logo-on-dark' : '.brand-logo-on-light');
      const hidden = page.locator(theme === 'dark' ? '.brand-logo-on-light' : '.brand-logo-on-dark');
      await expect(visible).toBeVisible();
      await expect(hidden).toBeHidden();
      await expect(visible).toHaveCSS('filter', 'none');
      await expect(page.locator('.brand-mark')).toHaveCSS('background-color', 'rgba(0, 0, 0, 0)');
      expect(await visible.evaluate(img => img.complete && img.naturalWidth > 0)).toBe(true);
      expect((await themeButton(page).innerText()).trim()).toBe('');
      const button = await themeButton(page).boundingBox();
      expect(button.width).toBe(44); expect(button.height).toBe(44);
      const mark = await page.locator('.brand-mark').boundingBox();
      expect(Math.abs(mark.y + mark.height / 2 - button.y - button.height / 2)).toBeLessThan(1);
      await page.getByRole('link', { name: 'PerfectDF, início' }).focus();
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
      // Reload must preserve the manual theme and the corresponding logo/icon.
      await page.reload();
      await expectTheme(page, theme);
      await expect(visible).toBeVisible(); await expect(hidden).toBeHidden();
      await themeButton(page).click();
    }
    const darkSVG = await (await page.request.get('/static/img/monogram-on-dark.svg')).text();
    const favicon = await (await page.request.get('/static/img/favicon.svg')).text();
    expect(await page.evaluate(({ darkSVG, favicon }) => {
      const parse = text => new DOMParser().parseFromString(text, 'image/svg+xml');
      const dark = parse(darkSVG), original = parse(favicon);
      return dark.querySelector('rect,image,filter') === null &&
        dark.querySelectorAll('path')[0].getAttribute('fill') === '#fff' &&
        dark.querySelectorAll('path')[1].outerHTML === original.querySelectorAll('path')[1].outerHTML;
    }, { darkSVG, favicon })).toBe(true);
  });
}

test('signature zoom waits for the new viewport and keeps its PDF-relative placement', async ({ page }, testInfo) => {
  await page.goto('/');
  await page.evaluate(() => {
    const viewer = window.pdfjsLib;
    window.pdfjsLib = { ...viewer, getDocument(options) {
      const task = viewer.getDocument(options);
      return { destroy: () => task.destroy(), promise: task.promise.then(doc => {
        const getPage = doc.getPage.bind(doc);
        doc.getPage = async number => {
          const pdfPage = await getPage(number);
          if (!pdfPage.signatureZoomWrapped) {
            pdfPage.signatureZoomWrapped = true;
            const render = pdfPage.render.bind(pdfPage);
            pdfPage.render = options => {
              const rendering = render(options);
              if (!window.holdSignatureZoom) return rendering;
              window.holdSignatureZoom = false;
              return { cancel: () => rendering.cancel(), promise: rendering.promise.then(() => new Promise(resolve => { window.releaseSignatureZoom = resolve; })) };
            };
          }
          return pdfPage;
        };
        return doc;
      }) };
    } };
  });
  await page.locator('#file-input').setInputFiles(fixture);
  await expect(page.locator('#span-page-count')).toHaveText('3');
  await page.locator('[data-tab="tab-anotacoes"]').click();
  await page.getByRole('button', { name: 'Adicionar assinatura', exact: true }).click();
  await drawSignature(page);
  await page.locator('#signature-page').fill('2');
  await page.locator('#signature-page').press('Tab');
  await expect(page.locator('#input-page-num')).toHaveValue('2');
  const signature = page.locator('.signature-placement');
  await expect(signature).toBeVisible();
  const geometry = () => page.evaluate(() => {
    const box = document.querySelector('.signature-placement'), canvas = document.getElementById('pdf-canvas').getBoundingClientRect();
    if (!box) return null;
    const r = box.getBoundingClientRect();
    return { width: r.width, canvasWidth: canvas.width, x: (r.x-canvas.x)/canvas.width, y: (r.y-canvas.y)/canvas.height, w: r.width/canvas.width, h: r.height/canvas.height, page: document.getElementById('input-page-num').value, view: document.getElementById('estado-visualizacao').textContent, tool: document.body.dataset.tool };
  });
  const before = await geometry(), oldElement = await signature.elementHandle();
  await page.evaluate(() => { window.holdSignatureZoom = true; });
  await page.locator('#btn-zoom-in').click();
  await page.waitForFunction(() => typeof window.releaseSignatureZoom === 'function');
  // Visibility alone is insufficient: the PDF canvas has grown but the old
  // signature still uses the previous viewport until the render completes.
  await expect(signature).toBeVisible();
  const pending = await geometry();
  expect(pending.canvasWidth).toBeCloseTo(before.canvasWidth * 1.25, 1);
  expect(pending.width).toBeCloseTo(before.width, 1);
  expect(await oldElement.evaluate(element => element.isConnected)).toBe(true);
  await page.evaluate(() => window.releaseSignatureZoom());
  await expect.poll(async () => (await geometry())?.width).toBeCloseTo(before.width * 1.25, 1);
  const after = await geometry();
  const oldElementDetached = !(await oldElement.evaluate(element => element.isConnected));
  expect(await signature.boundingBox()).not.toBeNull();
  for (const key of ['x', 'y', 'w', 'h']) expect(after[key], key).toBeCloseTo(before[key], 3);
  expect(after.page).toBe('2'); expect(after.view).toBe('Mostrando original'); expect(after.tool).toBe('tab-anotacoes');
  await testInfo.attach('signature-zoom-states', { body: JSON.stringify({ before, pending, after, oldElementDetached }, null, 2), contentType: 'application/json' });
});
