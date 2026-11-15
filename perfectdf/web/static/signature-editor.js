// Geometry is stored in native PDF user units, never canvas pixels.
export function createSignatureEditor({ active, original, pageNumber, goPage, showOriginal, changed, error, ready }) {
  const $ = id => document.getElementById(id);
  const dialog = $('signature-dialog'), pad = $('signature-pad'), ctx = pad.getContext('2d');
  const layer = $('signature-layer'), pageInput = $('signature-page');
  let strokes = [], drawing = null, ink = null, placement = null, viewport = null, displayedPage = 0, busy = false, gesture = null, revision = 0;
  const map = (m, x, y) => [m[0] * x + m[2] * y + m[4], m[1] * x + m[3] * y + m[5]];
  const point = event => { const r = pad.getBoundingClientRect(); return [Math.max(0, Math.min(pad.width, (event.clientX - r.left) * pad.width / r.width)), Math.max(0, Math.min(pad.height, (event.clientY - r.top) * pad.height / r.height))]; };
  function paint() {
    ctx.clearRect(0, 0, pad.width, pad.height); ctx.strokeStyle = '#20252a'; ctx.lineWidth = 2.5; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    for (const stroke of strokes) { ctx.beginPath(); stroke.forEach(([x, y], i) => i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)); ctx.stroke(); }
  }
  pad.addEventListener('pointerdown', event => {
    if (event.button !== 0 || drawing) return;
    event.preventDefault(); pad.setPointerCapture(event.pointerId); drawing = { id: event.pointerId, stroke: [point(event)] }; strokes.push(drawing.stroke); $('signature-draw-error').textContent = '';
  });
  pad.addEventListener('pointermove', event => { if (drawing?.id === event.pointerId) { drawing.stroke.push(point(event)); paint(); } });
  const finish = event => { if (drawing?.id === event.pointerId) { drawing = null; paint(); } };
  for (const type of ['pointerup', 'pointercancel', 'lostpointercapture']) pad.addEventListener(type, finish);
  $('signature-clear').addEventListener('click', () => { drawing = null; strokes = []; paint(); $('signature-draw-error').textContent = ''; });
  $('signature-cancel').addEventListener('click', () => dialog.close());
  $('signature-create').addEventListener('click', () => { strokes = []; drawing = null; paint(); $('signature-draw-error').textContent = ''; dialog.showModal(); });
  $('signature-confirm').addEventListener('click', async () => {
    const points = strokes.filter(s => s.length > 1).flat();
    if (points.length < 2) { $('signature-draw-error').textContent = 'Desenhe sua assinatura antes de confirmar.'; return; }
    if (points.length > 50000) { $('signature-draw-error').textContent = 'O desenho ficou muito grande. Apague e tente novamente.'; return; }
    const xs = points.map(p => p[0]), ys = points.map(p => p[1]);
    const left = Math.min(...xs) - 5, top = Math.min(...ys) - 5, width = Math.max(...xs) - left + 5, height = Math.max(...ys) - top + 5;
    if (width < 14 && height < 14) { $('signature-draw-error').textContent = 'O desenho está muito pequeno. Desenhe novamente.'; return; }
    const next = { aspect: height / width, pen: 2.5 / width, strokes: strokes.filter(s => s.length > 1).map(s => s.map(([x, y]) => [(x - left) / width, (y - top) / width])) };
    const request = ++revision;
    dialog.close();
    try { if (!original()) await showOriginal(); if (request !== revision || !active()) return; if (!viewport) throw new Error('Aguarde o PDF carregar antes de posicionar a assinatura.'); ink = next; place(); changed(); }
    catch (e) { error(e.message); }
  });
  function matrixAt(x, y, width) {
    const a = viewport.convertToPdfPoint(x, y), b = viewport.convertToPdfPoint(x + width, y), c = viewport.convertToPdfPoint(x, y + width);
    return [b[0] - a[0], b[1] - a[1], c[0] - a[0], c[1] - a[1], ...a];
  }
  function place() {
    const width = Math.min(180, viewport.width * .6, viewport.height * .6 / ink.aspect);
    placement = { page: displayedPage, matrix: matrixAt((viewport.width - width) / 2, (viewport.height - width * ink.aspect) / 2, width) }; render();
  }
  function projected(matrix = placement.matrix) {
    return [[0, 0], [1, 0], [0, ink.aspect], [1, ink.aspect]].map(p => viewport.convertToViewportPoint(...map(matrix, ...p)));
  }
  function render() {
    layer.replaceChildren();
    $('signature-remove').disabled = !placement || busy;
    $('signature-create').disabled = busy;
    pageInput.disabled = !ink || busy;
    $('signature-status').textContent = !ink ? 'Crie a assinatura para posicioná-la no documento.' : `Assinatura na página ${placement?.page || displayedPage}. Arraste para mover; use o canto para redimensionar.`;
    if (!active() || !original() || !placement || !viewport || placement.page !== displayedPage) return;
    const corners = projected(), xs = corners.map(p => p[0]), ys = corners.map(p => p[1]);
    const x = Math.min(...xs), y = Math.min(...ys), width = Math.max(...xs) - x, height = Math.max(...ys) - y;
    const box = document.createElement('div'); box.className = 'signature-placement'; box.tabIndex = 0; box.role = 'group'; box.setAttribute('aria-label', 'Assinatura: arraste ou use as setas para mover');
    Object.assign(box.style, { left: `${x}px`, top: `${y}px`, width: `${width}px`, height: `${height}px` });
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg'); svg.setAttribute('viewBox', `0 0 ${width} ${height}`); svg.setAttribute('aria-hidden', 'true');
    // Project every vector through the current PDF.js viewport (including page rotation).
    const penScale = Math.hypot(corners[1][0] - corners[0][0], corners[1][1] - corners[0][1]);
    for (const stroke of ink.strokes) {
      const path = document.createElementNS(svg.namespaceURI, 'polyline');
      path.setAttribute('points', stroke.map(p => { const q = viewport.convertToViewportPoint(...map(placement.matrix, ...p)); return `${q[0] - x},${q[1] - y}`; }).join(' '));
      path.setAttribute('fill', 'none'); path.setAttribute('stroke', '#20252a'); path.setAttribute('stroke-width', ink.pen * penScale); path.setAttribute('stroke-linecap', 'round'); path.setAttribute('stroke-linejoin', 'round'); svg.append(path);
    }
    const resize = document.createElement('button'); resize.type = 'button'; resize.className = 'signature-resize'; resize.setAttribute('aria-label', 'Redimensionar assinatura');
    const start = event => {
      if (busy || event.button !== 0) return; event.preventDefault();
      const surface = $('pdf-canvas').getBoundingClientRect();
      gesture = { id: event.pointerId, resize: event.target === resize, start: [event.clientX, event.clientY], corners, x, y, width, height, surface };
      layer.setPointerCapture(event.pointerId);
    };
    box.addEventListener('pointerdown', start);
    box.addEventListener('keydown', event => {
      if (busy || !['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', '+', '-', 'Delete', 'Backspace'].includes(event.key)) return;
      event.preventDefault();
      if (['Delete', 'Backspace'].includes(event.key)) { remove(); return; }
      const step = event.shiftKey ? 10 : 1;
      transform(event.key === 'ArrowLeft' ? -step : event.key === 'ArrowRight' ? step : 0, event.key === 'ArrowUp' ? -step : event.key === 'ArrowDown' ? step : 0, event.key === '+' ? 1.05 : event.key === '-' ? .95 : 1, { x, y, width, height, corners }, event.key === '+' || event.key === '-');
      layer.querySelector('.signature-placement')?.focus();
    });
    box.append(svg, resize); layer.append(box);
  }
  function transform(dx, dy, factor, base, resizing = false) {
    // Fitting the page takes priority over the preferred 24px resize minimum.
    // Moving a narrow signature must not enlarge it as a side effect.
    const maximum = Math.min(viewport.width / base.width, viewport.height / base.height);
    const minimum = resizing ? Math.min(24 / base.width, maximum) : 0;
    factor = Math.min(maximum, Math.max(minimum, factor));
    const x = Math.max(0, Math.min(base.x + dx, viewport.width - base.width * factor));
    const y = Math.max(0, Math.min(base.y + dy, viewport.height - base.height * factor));
    const convert = q => viewport.convertToPdfPoint(x + (q[0] - base.x) * factor, y + (q[1] - base.y) * factor);
    const a = convert(base.corners[0]), b = convert(base.corners[1]), c = convert(base.corners[2]);
    placement.matrix = [b[0] - a[0], b[1] - a[1], (c[0] - a[0]) / ink.aspect, (c[1] - a[1]) / ink.aspect, ...a];
    changed(); render();
  }
  layer.addEventListener('pointermove', event => {
    if (gesture?.id !== event.pointerId) return;
    const surface = $('pdf-canvas').getBoundingClientRect();
    const dx = event.clientX - gesture.start[0] + gesture.surface.left - surface.left, dy = event.clientY - gesture.start[1] + gesture.surface.top - surface.top;
    transform(gesture.resize ? 0 : dx, gesture.resize ? 0 : dy, gesture.resize ? Math.max((gesture.width + dx) / gesture.width, (gesture.height + dy) / gesture.height) : 1, gesture, gesture.resize);
  });
  for (const type of ['pointerup', 'pointercancel', 'lostpointercapture']) layer.addEventListener(type, () => { gesture = null; });
  function remove() { revision++; placement = null; ink = null; changed(); render(); }
  $('signature-remove').addEventListener('click', remove);
  pageInput.addEventListener('change', async () => {
    const page = Number(pageInput.value); if (!Number.isInteger(page) || page < 1 || page > Number(pageInput.max)) { error('Escolha uma página válida.'); pageInput.value = placement?.page || pageNumber(); return; }
    if (!ink || busy) return;
    const request = ++revision, drawingInk = ink, previous = placement;
    try {
      if (!original()) await showOriginal();
      if (request !== revision || drawingInk !== ink || !active()) return;
      placement = null; await goPage(page);
      if (request !== revision || drawingInk !== ink || !active()) return;
      if (displayedPage !== page) throw new Error('Não foi possível abrir a página escolhida. Tente novamente.');
      place(); changed();
    } catch (e) { if (request === revision) { placement = previous; render(); error(e.message); } }
  });
  return {
    ready: () => Boolean(ink && placement),
    data: () => { if (!ink || !placement) throw new Error('Crie e posicione uma assinatura antes de aplicar.'); return { ...ink, ...placement }; },
    setBusy(value) { if (busy === value) return; busy = value; if (busy) gesture = null; render(); },
    sync() { render(); },
    viewport(value, page, count) { viewport = value; displayedPage = page; pageInput.max = count; pageInput.value = placement?.page || page; render(); ready(); },
    reset() { revision++; if (dialog.open) dialog.close(); ink = null; placement = null; viewport = null; gesture = null; strokes = []; render(); },
  };
}
