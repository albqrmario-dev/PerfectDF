import { readFile, writeFile, mkdir, copyFile, cp, access, rm } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';

const json = async path => JSON.parse(await readFile(path, 'utf8'));
const sha256 = async path => createHash('sha256').update(await readFile(path)).digest('hex');

export async function publishSources() {
  const sources = await json('licenses/sources.json');
  const mupdf = await json('node_modules/mupdf/package.json');
  const pdfjs = await json('node_modules/pdfjs-dist/package.json');
  if (mupdf.version !== sources.mupdf.version || pdfjs.version !== sources.pdfjs.version) {
    throw new Error('Atualize o manifesto de fontes/licenças ao mudar as versões das bibliotecas.');
  }
  await mkdir('.cache/perfectdf', { recursive: true });
  const archive = `.cache/perfectdf/mupdf-${mupdf.version}-source.tar.gz`;
  let cached = true;
  try { await access(archive); } catch { cached = false; }
  if (!cached) {
    const response = await fetch(sources.mupdf.sourceUrl, { signal: AbortSignal.timeout(180000) });
    if (!response.ok) throw new Error(`Download das fontes MuPDF falhou: HTTP ${response.status}`);
    const data = new Uint8Array(await response.arrayBuffer());
    if (createHash('sha256').update(data).digest('hex') !== sources.mupdf.sha256) throw new Error('Checksum das fontes MuPDF inválido.');
    await writeFile(archive, data);
  }
  if (await sha256(archive) !== sources.mupdf.sha256) {
    await rm(archive);
    throw new Error('Cache das fontes MuPDF inválido. Execute o build novamente para baixar uma cópia verificada.');
  }
  await mkdir('dist/sources', { recursive: true });
  await copyFile(archive, `dist/sources/mupdf-${mupdf.version}-source.tar.gz`);
  await cp('licenses', 'dist/licenses', { recursive: true });
  await copyFile('THIRD_PARTY.md', 'dist/licenses/THIRD_PARTY.md');
  // Explicit allowlist: never archive the working directory, Git metadata or caches.
  const entries = ['LICENSE', 'THIRD_PARTY.md', 'README.md', 'package.json', 'package-lock.json',
    'requirements.txt', 'requirements-dev.txt', 'pytest.ini', 'vercel.json', 'playwright.config.mjs',
    'scripts', 'perfectdf', 'tests', 'docs', 'licenses', '.gitignore'];
  execFileSync('tar', ['-czf', 'dist/sources/perfectdf-source.tar.gz',
    '--exclude=__pycache__', '--exclude=*.pyc', '--exclude=.env', '--exclude=.env.*',
    '--exclude=*.pem', '--exclude=*.key', '--exclude=.DS_Store', '--exclude=perfectdf/web/static/vendor/mupdf',
    '--exclude=perfectdf/web/static/vendor/pdfjs', ...entries]);
  const hashes = {};
  for (const path of ['static/vendor/mupdf/mupdf.js', 'static/vendor/mupdf/mupdf-wasm.js',
    'static/vendor/mupdf/mupdf-wasm.wasm', 'static/vendor/pdfjs/pdf.min.mjs',
    'static/vendor/pdfjs/pdf.worker.min.mjs', 'sources/perfectdf-source.tar.gz']) {
    hashes[path] = await sha256(`dist/${path}`);
  }
  await writeFile('dist/sources/manifest.json', JSON.stringify({
    perfectdf: { version: (await json('package.json')).version, source: '/sources/perfectdf-source.tar.gz' },
    mupdf: { ...sources.mupdf, source: `/sources/mupdf-${mupdf.version}-source.tar.gz` },
    pdfjs: sources.pdfjs, sha256: hashes,
  }, null, 2) + '\n');
  await copyFile('perfectdf/web/static/licenses.html', 'dist/licenses.html');
}
