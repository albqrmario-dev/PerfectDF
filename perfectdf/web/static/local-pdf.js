// Adapter for local workers. Aborting a request also releases its WASM memory.
window.localPdfRequest = async (path, { body, signal } = {}) => {
  signal?.throwIfAborted();
  const fields = {}, files = [];
  for (const [key, value] of body.entries()) {
    if (value instanceof File) files.push({ name: value.name, bytes: await value.arrayBuffer() });
    else fields[key] = value;
    signal?.throwIfAborted();
  }
  return new Promise((resolve, reject) => {
    const worker = new Worker('/static/pdf-worker.js', { type: 'module' });
    const finish = () => { clearTimeout(timeout); signal?.removeEventListener('abort', abort); worker.terminate(); };
    const abort = () => { finish(); reject(new DOMException('Operação cancelada.', 'AbortError')); };
    const timeout = setTimeout(() => { finish(); reject(new Error('O processamento demorou demais. Tente um documento menor.')); }, 300000);
    signal?.addEventListener('abort', abort, { once: true });
    if (signal?.aborted) { abort(); return; }
    worker.onerror = () => { finish(); reject(new Error('Não foi possível iniciar o editor local. Recarregue a página ou tente um documento menor.')); };
    worker.onmessage = ({ data }) => {
      if (data.ready) {
        worker.postMessage({ operation: path.replace(/^\/api\//, ''), fields, files }, files.map(file => file.bytes));
        return;
      }
      finish();
      if (data.error) { reject(new Error(data.error)); return; }
      if (data.json) resolve(new Response(JSON.stringify(data.json), { headers: { 'Content-Type': 'application/json' } }));
      else resolve(new Response(data.bytes, { headers: {
        'Content-Type': 'application/pdf',
        'Content-Disposition': `attachment; filename="${data.filename.replace(/[\r\n"\\]/g, '_').replace(/[^\x20-\x7e]/g, '_')}"`,
      } }));
    };
  });
};
