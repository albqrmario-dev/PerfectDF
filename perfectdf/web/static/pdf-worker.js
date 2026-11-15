import { processPdf } from './pdf-engine.js';
self.onmessage = event => {
  try {
    const result = processPdf(event.data);
    self.postMessage(result, result.bytes ? [result.bytes.buffer] : []);
  } catch (error) {
    self.postMessage({ error: error.message || 'Não foi possível processar este PDF.' });
  }
};

self.postMessage({ ready: true });
