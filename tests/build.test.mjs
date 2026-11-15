import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFile, stat } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';

test('published sources match the verified MuPDF archive and current application code', async () => {
  const manifest = JSON.parse(await readFile('dist/sources/manifest.json', 'utf8'));
  const hash = bytes => createHash('sha256').update(bytes).digest('hex');
  assert.equal(hash(await readFile('dist' + manifest.mupdf.source)), manifest.mupdf.sha256);
  for (const [path, digest] of Object.entries(manifest.sha256)) assert.equal(hash(await readFile(`dist/${path}`)), digest, path);
  const source = 'dist/sources/perfectdf-source.tar.gz';
  const entries = execFileSync('tar', ['-tzf', source], { encoding: 'utf8' }).split('\n');
  assert.ok(entries.includes('package-lock.json'));
  assert.ok(entries.includes('scripts/publish-sources.mjs'));
  assert.ok(!entries.some(path => /(^|\/)(?:\.git|\.env|node_modules|\.cache|venv)(?:\/|$)/.test(path)));
  const bundled = execFileSync('tar', ['-xOf', source, 'perfectdf/web/static/app.js']);
  assert.deepEqual(bundled, await readFile('perfectdf/web/static/app.js'));
});

test('the build ships complete license files and replaces the old viewer', async () => {
  for (const path of ['dist/LICENSE', 'dist/licenses/mupdf-1.28.6/COPYING',
    'dist/licenses/mupdf-1.28.6/thirdparty/freetype/docs/FTL.TXT',
    'dist/static/vendor/pdfjs/LICENSE', 'dist/static/vendor/pdfjs/wasm/LICENSE_OPENJPEG',
    'dist/static/vendor/pdfjs/standard_fonts/LICENSE_FOXIT', 'dist/static/licenses.html']) {
    assert.ok((await stat(path)).size > 100, path);
  }
  const lock = JSON.parse(await readFile('package-lock.json', 'utf8'));
  assert.equal(lock.packages['node_modules/pdfjs-dist'].version, '6.5.438');
  await assert.rejects(stat('dist/static/vendor/pdfjs/pdf.min.js'), { code: 'ENOENT' });
});
