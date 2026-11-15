import { cp, mkdir, rm, copyFile } from 'node:fs/promises';
import { publishSources } from './publish-sources.mjs';
const source = 'perfectdf/web/static';
await mkdir(`${source}/vendor/mupdf`, { recursive: true });
for (const name of ['mupdf.js', 'mupdf-wasm.js', 'mupdf-wasm.wasm']) {
  await copyFile(`node_modules/mupdf/dist/${name}`, `${source}/vendor/mupdf/${name}`);
}
const pdfjs = `${source}/vendor/pdfjs`;
await rm(pdfjs, { recursive: true, force: true });
await mkdir(pdfjs, { recursive: true });
for (const name of ['pdf.min.mjs', 'pdf.worker.min.mjs']) {
  await copyFile(`node_modules/pdfjs-dist/build/${name}`, `${pdfjs}/${name}`);
}
for (const folder of ['cmaps', 'standard_fonts', 'wasm', 'iccs']) {
  await cp(`node_modules/pdfjs-dist/${folder}`, `${pdfjs}/${folder}`, { recursive: true });
}
await copyFile('node_modules/pdfjs-dist/LICENSE', `${pdfjs}/LICENSE`);
await rm('dist', { recursive: true, force: true });
await mkdir('dist', { recursive: true });
await cp(source, 'dist/static', { recursive: true });
await copyFile(`${source}/index.html`, 'dist/index.html');
await copyFile('LICENSE', 'dist/LICENSE');

await publishSources();
