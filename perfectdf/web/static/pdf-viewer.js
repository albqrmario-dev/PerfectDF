import * as pdfjsLib from './vendor/pdfjs/pdf.min.mjs';
import { createSignatureEditor } from './signature-editor.js';
window.createSignatureEditor = createSignatureEditor;
window.pdfjsLib = pdfjsLib;
await import('./app.js');
