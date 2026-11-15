const initializePerfectDF = () => {
  if (window.pdfjsLib) {
    window.pdfjsLib.GlobalWorkerOptions.workerSrc = "/static/vendor/pdfjs/pdf.worker.min.mjs";
  }

  const badge = document.getElementById("api-status-badge");
  const dropZone = document.getElementById("drop-zone");
  const fileInput = document.getElementById("file-input");
  const fileInfoCard = document.getElementById("file-info-card");
  const fileName = document.getElementById("file-name");
  const fileMeta = document.getElementById("file-meta");
  const btnRemoveFile = document.getElementById("btn-remove-file");
  const actionsPanel = document.getElementById("actions-panel");
  const btnExecutar = document.getElementById("btn-executar-acao");
  const btnBaixarPrevia = document.getElementById("btn-baixar-previa");
  const btnMostrarOriginal = document.getElementById("btn-mostrar-original");
  const btnMostrarPrevia = document.getElementById("btn-mostrar-previa");
  const estadoVisualizacao = document.getElementById("estado-visualizacao");
  const avisoPreviaDesatualizada = document.getElementById("aviso-previa-desatualizada");
  const compressionSizeStatus = document.getElementById("compression-size-status");
  const compressionSizeDetail = document.getElementById("compression-size-detail");
  const inputMultiplosPdfs = document.getElementById("input-multiplos-pdfs");
  const listaArquivosJuntar = document.getElementById("lista-arquivos-juntar");
  const viewerWorkspace = document.querySelector(".viewer-workspace");
  const feedbackMessage = document.getElementById("feedback-message");
  const textResultBox = document.getElementById("text-result-box");
  const textResultTitle = document.getElementById("text-result-title");
  const textResultContent = document.getElementById("text-result-content");
  const btnCloseTextResult = document.getElementById("btn-close-text-result");

  const viewerSection = document.getElementById("viewer-section");
  const btnPrevPage = document.getElementById("btn-prev-page");
  const btnNextPage = document.getElementById("btn-next-page");
  const inputPageNum = document.getElementById("input-page-num");
  const spanPageCount = document.getElementById("span-page-count");
  const btnZoomIn = document.getElementById("btn-zoom-in");
  const btnZoomOut = document.getElementById("btn-zoom-out");
  const spanZoomLevel = document.getElementById("span-zoom-level");
  const btnRotate = document.getElementById("btn-rotate");
  const pdfCanvas = document.getElementById("pdf-canvas");

  const tabBtns = document.querySelectorAll(".tab-btn");
  const tabPanes = document.querySelectorAll(".tab-pane");
  let activeTabId = "tab-paginas";

  let currentFile = null;
  let originalFile = null;
  // Mantém a prévia para alternar entre documentos e baixar depois.
  let previewBlob = null;
  let previewDownloadName = "";
  let previewToolKey = "";
  let editRevision = 0, previewRevision = -1, previewSource = null;
  let previewIsStale = false;
  let previewIsGenerating = false;
  let previewChangedDuringRequest = false;
  let previewRequestId = 0;
  let currentViewMode = "none";
  let currentPdfDoc = null;
  let currentPageNum = 1;
  let currentScale = 1.0;
  let currentRotation = 0;
  let isRendering = false;
  let pendingPageNum = null;
  let currentRenderTask = null;
  let viewerLoadingTask = null, viewerGeneration = 0, documentGeneration = 0, viewSelection = 0;
  let viewerDisposal = Promise.resolve();
  let activeJob = null;
  let joinFiles = [];
  let formEditorReady = false;
  let editableFile = null, editableInfo = null, editablePageNumber = 0, selectedTextLine = null, textLoadRequest = 0;
  const textDrafts = new Map();
  const signatureEditor = window.createSignatureEditor({
    active: () => getActiveOperationKey() === 'tab-anotacoes:assinatura',
    original: () => currentViewMode === 'original', pageNumber: () => currentPageNum,
    goPage: async page => { while (isRendering) await new Promise(resolve => setTimeout(resolve, 16)); currentPageNum = page; await renderPage(page); },
    showOriginal: showOriginalDocument,
    changed: () => handleToolFieldChange({ target: document.getElementById('signature-layer') }),
    error: message => showFeedback(message, 'error'), ready: updatePrimaryAction,
  });

  if (badge) {
    badge.textContent = "Processamento local";
    badge.classList.add("online");
    badge.title = "Seus PDFs são processados neste dispositivo, sem upload.";
  }

  function showFeedback(text, type = "info") {
    if (!feedbackMessage) return;
    feedbackMessage.textContent = text;
    feedbackMessage.className = `feedback-message ${type}`;
    if (type === 'success') document.getElementById('footer-operation').textContent = document.getElementById('active-tool-title').textContent;
  }

  function clearFeedback() {
    if (!feedbackMessage) return;
    feedbackMessage.textContent = "";
    feedbackMessage.className = "feedback-message hidden";
  }

  function showTextResult(title, content) {
    if (!textResultBox || !textResultContent) return;
    if (textResultTitle) textResultTitle.textContent = title;
    textResultContent.textContent = content;
    textResultBox.classList.remove("hidden");
  }

  function hideTextResult() {
    if (textResultBox) textResultBox.classList.add("hidden");
  }

  if (btnCloseTextResult) {
    btnCloseTextResult.addEventListener("click", hideTextResult);
  }

  function formatBytes(bytes) {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  }

  function getActiveOperationKey() {
    const selectors = {
      "tab-paginas": "select-sub-paginas",
      "tab-anotacoes": "select-sub-anotacoes",
      "tab-formularios": "select-sub-formularios",
      "tab-texto": "select-sub-texto",
      "tab-seguranca": "select-sub-seguranca",
    };
    const selectorId = selectors[activeTabId];
    const selection = selectorId ? document.getElementById(selectorId)?.value || "" : "";
    return `${activeTabId}:${selection}`;
  }

  function isPreviewOperation() {
    if (activeTabId === "tab-paginas" || activeTabId === "tab-anotacoes") return true;
    if (activeTabId === "tab-formularios") {
      return ["preencher", "achatar"].includes(document.getElementById("select-sub-formularios")?.value);
    }
    if (activeTabId === "tab-texto") {
      return ["adicionar-texto", "editar-metadados", "editar-texto"].includes(document.getElementById("select-sub-texto")?.value);
    }
    return activeTabId === "tab-seguranca"
      && document.getElementById("select-sub-seguranca")?.value === "comprimir";
  }

  function canDownloadPreview() {
    return Boolean(previewBlob && previewSource === currentFile && previewRevision === editRevision
      && previewToolKey === getActiveOperationKey() && !previewIsStale && !previewIsGenerating && !activeJob);
  }

  function updatePreviewDownload() {
    if (btnBaixarPrevia) btnBaixarPrevia.disabled = !canDownloadPreview();
    if (avisoPreviaDesatualizada) {
      const stale = Boolean(previewBlob && (previewIsStale || previewRevision !== editRevision || previewSource !== currentFile));
      avisoPreviaDesatualizada.classList.toggle('hidden', !stale);
      avisoPreviaDesatualizada.textContent = 'O documento ou as edições mudaram. Gere uma nova prévia antes de baixar.';
    }
  }

  function updatePreviewControls() {
    document.getElementById('footer-file').textContent = currentFile?.name || 'Nenhum arquivo';
    document.getElementById('footer-pages').textContent = currentPdfDoc?.numPages || '—';
    syncTextTargets();
    signatureEditor.sync();
    const hasOriginal = Boolean(originalFile);
    const hasPreview = Boolean(previewBlob);
    if (btnMostrarOriginal) {
      btnMostrarOriginal.disabled = !hasOriginal;
      btnMostrarOriginal.classList.toggle("active", currentViewMode === "original");
      btnMostrarOriginal.setAttribute("aria-pressed", String(currentViewMode === "original"));
    }
    if (btnMostrarPrevia) {
      btnMostrarPrevia.disabled = !hasPreview;
      btnMostrarPrevia.classList.toggle("active", currentViewMode === "preview");
      btnMostrarPrevia.setAttribute("aria-pressed", String(currentViewMode === "preview"));
    }
    updatePreviewDownload();
    if (estadoVisualizacao) {
      if (currentViewMode === "preview") {
        estadoVisualizacao.textContent = previewIsStale
          ? "Mostrando prévia desatualizada"
          : "Mostrando prévia";
      } else if (currentViewMode === "original") {
        estadoVisualizacao.textContent = "Mostrando original";
      } else if (currentViewMode === "result") {
        estadoVisualizacao.textContent = "Mostrando resultado";
      } else {
        estadoVisualizacao.textContent = "Nenhum documento aberto";
      }
    }
  }

  function updatePrimaryAction() {
    if (!btnExecutar) return;
    updatePreviewDownload();
    signatureEditor.setBusy(Boolean(activeJob));
    if (activeJob) {
      btnExecutar.disabled = true;
      btnExecutar.textContent = "Gerando...";
      return;
    }
    const operation = getActiveOperationKey().split(':')[1];
    const labels = { listar: 'Ver campos', 'extrair-texto': 'Extrair texto', proteger: 'Proteger e baixar', 'remover-senha': 'Remover senha e baixar' };
    btnExecutar.textContent = isPreviewOperation() ? 'Gerar prévia'
      : activeTabId === 'tab-juntar' ? 'Juntar e baixar' : labels[operation] || 'Aplicar';
    btnExecutar.disabled = (activeTabId === 'tab-juntar' && joinFiles.length < 2)
      || (operation === 'assinatura' && !signatureEditor.ready())
      || (operation === 'preencher' && !formEditorReady)
      || (operation === 'editar-texto' && (!textDrafts.size || [...textDrafts.values()].some(edit => !edit.novo.trim())));
  }

  function downloadBlob(blob, filename) {
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = downloadUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    window.URL.revokeObjectURL(downloadUrl);
    link.remove();
  }

  function cancelOperation() {
    const job = activeJob; activeJob = null;
    job?.controller.abort();
    previewIsGenerating = false;
    if (job && viewerLoadingTask && !currentPdfDoc) disposeViewer();
  }
  function beginOperation() {
    cancelOperation();
    viewSelection++;
    const job = { revision: editRevision, source: currentFile, tool: getActiveOperationKey(), tab: activeTabId, controller: new AbortController() };
    activeJob = job;
    return job;
  }
  function isCurrentJob(job) {
    return activeJob === job && !job.controller.signal.aborted && job.source === currentFile && job.tool === getActiveOperationKey();
  }

  function discardPreview(restoreOriginal = true) {
    const wasLoadingResult = Boolean(activeJob && viewerLoadingTask && !currentPdfDoc);
    cancelOperation();
    const shouldRestoreOriginal = restoreOriginal
      && (currentViewMode === "preview" || wasLoadingResult)
      && Boolean(originalFile);
    previewRequestId += 1;
    previewBlob = null;
    previewRevision = -1; previewSource = null;
    previewDownloadName = "";
    previewToolKey = "";
    previewIsStale = false;
    previewIsGenerating = false;
    previewChangedDuringRequest = false;
    if (compressionSizeStatus) compressionSizeStatus.classList.add("hidden");
    if (currentViewMode === "preview") currentViewMode = originalFile ? "original" : "none";
    updatePreviewControls();
    updatePrimaryAction();
    if (shouldRestoreOriginal) showOriginalDocument();
  }

  async function showOriginalDocument() {
    const file = originalFile, generation = documentGeneration, selection = ++viewSelection;
    if (!file) return;
    const isValid = () => file === originalFile && generation === documentGeneration && selection === viewSelection;
    const loaded = await loadPdfInViewer(await file.arrayBuffer(), isValid);
    if (!loaded || !isValid()) return;
    currentViewMode = 'original'; updatePreviewControls();
  }

  async function showPreviewDocument() {
    const blob = previewBlob, generation = documentGeneration, selection = ++viewSelection;
    if (!blob) return;
    const isValid = () => blob === previewBlob && generation === documentGeneration && selection === viewSelection;
    const loaded = await loadPdfInViewer(await blob.arrayBuffer(), isValid);
    if (!loaded || !isValid()) return;
    currentViewMode = 'preview'; updatePreviewControls();
  }

  function handleToolFieldChange(event) {
    const operationSelectors = new Set([
      "select-sub-paginas",
      "select-sub-anotacoes",
      "select-sub-formularios",
      "select-sub-texto",
      "select-sub-seguranca",
    ]);
    if (operationSelectors.has(event.target.id)) {
      const newKey = getActiveOperationKey();
      if ((activeJob && activeJob.tool !== newKey)
        || (previewBlob && newKey !== previewToolKey)
        || (previewIsGenerating && newKey !== previewToolKey)) {
        discardPreview();
      }
    } else {
      editRevision++;
      if (previewBlob) previewIsStale = true;
      if (previewIsGenerating) previewChangedDuringRequest = true;
      updatePreviewControls();
    }
    updatePrimaryAction();
  }

  tabPanes.forEach((pane) => {
    pane.addEventListener("input", handleToolFieldChange);
    pane.addEventListener("change", handleToolFieldChange);
  });

  if (btnMostrarOriginal) btnMostrarOriginal.addEventListener("click", showOriginalDocument);
  if (btnMostrarPrevia) btnMostrarPrevia.addEventListener("click", showPreviewDocument);
  if (btnBaixarPrevia) {
    btnBaixarPrevia.addEventListener("click", () => {
      if (!canDownloadPreview()) {
        showFeedback('Gere uma nova prévia do documento atual antes de baixar.', 'info');
        updatePreviewDownload();
        return;
      }
      downloadBlob(previewBlob, previewDownloadName || 'previa.pdf');
    });
  }

  function updateJoinActionState() {
    if (!btnExecutar || activeTabId !== "tab-juntar" || btnExecutar.textContent === "Processando...") return;
    btnExecutar.disabled = activeTabId === "tab-juntar" && joinFiles.length < 2;
  }

  function renderJoinFiles() {
    if (activeJob?.tab === "tab-juntar") discardPreview();
    if (!listaArquivosJuntar) return;
    listaArquivosJuntar.replaceChildren();

    if (joinFiles.length === 0) {
      const hint = document.createElement("p");
      hint.className = "join-files-hint";
      hint.textContent = "Adicione pelo menos dois PDFs para juntar.";
      listaArquivosJuntar.appendChild(hint);
      updateJoinActionState();
      return;
    }

    const hint = document.createElement("p");
    hint.className = "join-files-hint";
    hint.textContent = joinFiles.length < 2
      ? "Adicione mais um PDF para continuar."
      : `${joinFiles.length} PDFs na ordem de junção.`;
    listaArquivosJuntar.appendChild(hint);

    joinFiles.forEach((file, index) => {
      const row = document.createElement("div");
      row.className = "join-file-item";

      const detail = document.createElement("div");
      detail.className = "join-file-detail";
      const name = document.createElement("span");
      name.className = "join-file-name";
      name.textContent = file.name;
      const size = document.createElement("span");
      size.className = "join-file-size";
      size.textContent = formatBytes(file.size);
      detail.append(name, size);

      const controls = document.createElement("div");
      controls.className = "join-file-controls";
      const moveUp = document.createElement("button");
      moveUp.type = "button";
      moveUp.className = "btn btn-tool join-order-button";
      moveUp.title = "Subir arquivo";
      moveUp.setAttribute("aria-label", `Mover ${file.name} para cima`);
      moveUp.disabled = index === 0;
      moveUp.innerHTML = '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="m18 15-6-6-6 6"/></svg>';
      moveUp.addEventListener("click", () => moveJoinFile(index, -1));

      const moveDown = document.createElement("button");
      moveDown.type = "button";
      moveDown.className = "btn btn-tool join-order-button";
      moveDown.title = "Descer arquivo";
      moveDown.setAttribute("aria-label", `Mover ${file.name} para baixo`);
      moveDown.disabled = index === joinFiles.length - 1;
      moveDown.innerHTML = '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="m6 9 6 6 6-6"/></svg>';
      moveDown.addEventListener("click", () => moveJoinFile(index, 1));

      const remove = document.createElement("button");
      remove.type = "button";
      remove.className = "btn btn-text join-remove-button";
      remove.title = "Remover arquivo";
      remove.setAttribute("aria-label", `Remover ${file.name}`);
      remove.innerHTML = '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="m18 6-12 12M6 6l12 12"/></svg>';
      remove.addEventListener("click", () => removeJoinFile(index));

      controls.append(moveUp, moveDown, remove);
      row.append(detail, controls);
      listaArquivosJuntar.appendChild(row);
    });

    updateJoinActionState();
  }

  function addJoinFiles(files) {
    const candidates = Array.from(files || []);
    const validFiles = candidates.filter((file) => file.name.toLowerCase().endsWith(".pdf"));
    const invalidFiles = candidates.filter((file) => !file.name.toLowerCase().endsWith(".pdf"));

    if (validFiles.length > 0) joinFiles.push(...validFiles);
    if (invalidFiles.length > 0) {
      const names = invalidFiles.map((file) => file.name).join(", ");
      showFeedback(`Apenas arquivos .pdf podem ser juntados. Ignorados: ${names}.`, "error");
    } else if (validFiles.length > 0) {
      clearFeedback();
    }
    renderJoinFiles();
  }

  function moveJoinFile(index, direction) {
    const targetIndex = index + direction;
    if (targetIndex < 0 || targetIndex >= joinFiles.length) return;
    [joinFiles[index], joinFiles[targetIndex]] = [joinFiles[targetIndex], joinFiles[index]];
    renderJoinFiles();
  }

  function removeJoinFile(index) {
    joinFiles.splice(index, 1);
    renderJoinFiles();
  }

  function updateDropZoneForActiveTab() {
    if (!dropZone) return;
    const heading = dropZone.querySelector("h3");
    const hint = dropZone.querySelector("p");
    const singleFileLabel = dropZone.querySelector("label");
    if (activeTabId === "tab-juntar") {
      if (heading) heading.textContent = "Solte vários PDFs para juntar";
      if (hint) hint.textContent = "Escolha os arquivos e organize a ordem na lista.";
      singleFileLabel?.classList.remove("hidden");
      if (singleFileLabel) { singleFileLabel.htmlFor = "input-multiplos-pdfs"; singleFileLabel.textContent = "Escolher PDFs"; }
    } else {
      if (heading) heading.textContent = "Abra um PDF para editar.";
      if (hint) hint.textContent = "Arraste o arquivo para cá ou escolha no computador.";
      singleFileLabel?.classList.remove("hidden");
      if (singleFileLabel) { singleFileLabel.htmlFor = "file-input"; singleFileLabel.textContent = "Escolher PDF"; }
    }
  }

  tabBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      const previousTabId = activeTabId;
      tabBtns.forEach((b) => b.classList.remove("active"));
      tabPanes.forEach((p) => p.classList.remove("active"));

      btn.classList.add("active");
      activeTabId = btn.getAttribute("data-tab");
      const targetPane = document.getElementById(activeTabId);
      if (targetPane) targetPane.classList.add("active");

      if (previousTabId !== activeTabId) discardPreview();

      if (actionsPanel) {
        if (currentFile || activeTabId === "tab-juntar") {
          actionsPanel.classList.remove("hidden");
        } else {
          actionsPanel.classList.add("hidden");
        }
      }
      updateDropZoneForActiveTab();
      refreshToolNavigation();
      updatePrimaryAction();
      updateJoinActionState();
    });
  });

  if (inputMultiplosPdfs) {
    inputMultiplosPdfs.addEventListener("change", () => {
      addJoinFiles(inputMultiplosPdfs.files);
      inputMultiplosPdfs.value = "";
    });
  }
  renderJoinFiles();

  const selectSubPaginas = document.getElementById("select-sub-paginas");
  const boxPaginasGraus = document.getElementById("box-paginas-graus");
  const boxPaginasLista = document.getElementById("box-paginas-lista");
  const boxPaginasOrdem = document.getElementById("box-paginas-ordem");

  if (selectSubPaginas) {
    selectSubPaginas.addEventListener("change", () => {
      const v = selectSubPaginas.value;
      boxPaginasGraus?.classList.toggle("hidden", v !== "girar");
      boxPaginasLista?.classList.toggle("hidden", v === "reordenar");
      boxPaginasOrdem?.classList.toggle("hidden", v !== "reordenar");
    });
  }

  const selectSubAnotacoes = document.getElementById("select-sub-anotacoes");
  const boxAnotMarca = document.getElementById("box-anot-marcadagua");
  const boxAnotNumerar = document.getElementById("box-anot-numerar");
  const boxAnotNota = document.getElementById("box-anot-nota");
  const boxAnotDestacar = document.getElementById("box-anot-destacar");

  if (selectSubAnotacoes) {
    selectSubAnotacoes.addEventListener("change", () => {
      const v = selectSubAnotacoes.value;
      document.getElementById("box-anot-assinatura").classList.toggle("hidden", v !== "assinatura");
      boxAnotMarca?.classList.toggle("hidden", v !== "marca-dagua");
      boxAnotNumerar?.classList.toggle("hidden", v !== "numerar");
      boxAnotNota?.classList.toggle("hidden", v !== "nota");
      boxAnotDestacar?.classList.toggle("hidden", v !== "destacar");
    });
  }

  const selectSubForm = document.getElementById("select-sub-formularios");
  const boxFormPreencher = document.getElementById("box-form-preencher");
  if (selectSubForm) {
    selectSubForm.addEventListener("change", () => {
      const v = selectSubForm.value;
      boxFormPreencher?.classList.toggle("hidden", v !== "preencher");
    });
  }

  const selectSubTexto = document.getElementById("select-sub-texto");
  const boxTextoAdd = document.getElementById("box-texto-adicionar");
  const boxTextoMeta = document.getElementById("box-texto-metadados");
  if (selectSubTexto) {
    selectSubTexto.addEventListener("change", () => {
      const v = selectSubTexto.value;
      document.getElementById("box-texto-editar").classList.toggle("hidden", v !== "editar-texto");
      boxTextoAdd?.classList.toggle("hidden", v !== "adicionar-texto");
      boxTextoMeta?.classList.toggle("hidden", v !== "editar-metadados");
    });
  }

  const selectSubSeg = document.getElementById("select-sub-seguranca");
  const boxSegComprimir = document.getElementById("box-seg-comprimir");
  const boxSegSenha = document.getElementById("box-seg-senha");
  if (selectSubSeg) {
    selectSubSeg.addEventListener("change", () => {
      const v = selectSubSeg.value;
      boxSegComprimir?.classList.toggle("hidden", v !== "comprimir");
      boxSegSenha?.classList.toggle("hidden", v === "comprimir");
    });
  }

  const toolCopy = {
    assinatura: ['Adicionar assinatura', 'Desenhe, posicione e ajuste a assinatura antes de gerar a prévia.'],
    girar: ['Girar páginas', 'Mude a orientação de todas as páginas ou só das que escolher.'],
    extrair: ['Extrair páginas', 'Crie um novo PDF apenas com as páginas que você precisa.'],
    excluir: ['Excluir páginas', 'Escolha as páginas que quer remover. O original fica preservado.'],
    reordenar: ['Reordenar páginas', 'Escreva a sequência desejada. Por exemplo: 3, 1, 2.'],
    'marca-dagua': ["Marca d’água", 'Adicione uma marca discreta em todas as páginas.'],
    numerar: ['Numerar páginas', 'Escolha o formato e onde os números devem aparecer.'],
    nota: ['Adicionar nota', 'Deixe um comentário na página escolhida.'],
    destacar: ['Destacar texto', 'Encontre um trecho e aplique realce, sublinhado ou risco.'],
    listar: ['Ver campos', 'Veja quais campos podem ser preenchidos neste formulário.'],
    preencher: ['Preencher formulário', 'Preencha os campos abaixo e confira o resultado na prévia.'],
    achatar: ['Fixar preenchimento', 'Torne os campos parte do documento. Eles deixam de ser editáveis.'],
    'extrair-texto': ['Extrair texto', 'Copie o texto do documento. Páginas digitalizadas podem não conter texto selecionável.'],
    'editar-texto': ['Editar texto existente', 'Selecione uma linha e substitua o conteúdo. Apenas texto visível; digitalizações com OCR não são aceitas.'],
    'adicionar-texto': ['Adicionar texto', 'Insira um texto no alto da página escolhida.'],
    'editar-metadados': ['Título e autor', 'Atualize as informações que acompanham o arquivo.'],
    comprimir: ['Reduzir tamanho', 'Otimize a estrutura do PDF sem alterar a aparência das páginas.'],
    proteger: ['Adicionar senha', 'Defina uma senha para abrir o documento. Guarde-a em um lugar seguro.'],
    'remover-senha': ['Remover senha', 'Informe a senha atual para salvar uma cópia sem proteção.'],
    juntar: ['Juntar PDFs', 'Adicione os arquivos e organize a ordem antes de juntar.'],
  };
  const operationSelectors = new Map();
  let formRequest = 0;
  let loadedFormFile = null;

  function refreshToolNavigation() {
    document.body.dataset.tool = activeTabId;
    for (const btn of tabBtns) {
      const active = btn.dataset.tab === activeTabId;
      btn.setAttribute('aria-expanded', String(active));
      btn.nextElementSibling?.classList.toggle('hidden', !active);
    }
    for (const [tab, select] of operationSelectors) {
      document.querySelectorAll(`[data-operation-tab="${tab}"]`).forEach(button => {
        const active = button.dataset.operation === select.value;
        button.classList.toggle('active', active);
        button.setAttribute('aria-pressed', String(active));
      });
    }
    const operation = operationSelectors.get(activeTabId)?.value || 'juntar';
    const [title, description] = toolCopy[operation];
    document.getElementById('active-tool-title').textContent = title;
    document.getElementById('active-tool-description').textContent = description;
    const hint = document.getElementById('page-range-hint');
    if (hint) hint.textContent = operation === 'girar'
      ? 'Deixe vazio para girar todas. Para selecionar, use 1, 3-5.'
      : 'Informe as páginas. Por exemplo: 1, 3-5.';
    updatePrimaryAction();
    if (operation === 'preencher') loadFormEditor();
    if (operation === 'editar-texto') loadEditableText();
    syncTextTargets();
    signatureEditor.sync();
  }

  for (const btn of tabBtns) {
    const tab = btn.dataset.tab;
    const select = document.querySelector(`#${tab} select[id^="select-sub-"]`);
    const list = document.createElement('div');
    list.className = 'operation-list';
    list.id = `${tab}-tools`;
    list.setAttribute('aria-label', `Ferramentas de ${btn.textContent.trim()}`);
    btn.setAttribute('aria-controls', list.id);
    btn.after(list);
    if (!select) continue;
    operationSelectors.set(tab, select);
    select.closest('.form-row').classList.add('hidden');
    for (const option of select.options) {
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'operation-button';
      button.dataset.operation = option.value;
      button.dataset.operationTab = tab;
      button.textContent = toolCopy[option.value][0];
      button.addEventListener('click', () => {
        select.value = option.value;
        select.dispatchEvent(new Event('change', { bubbles: true }));
      });
      list.append(button);
    }
    select.addEventListener('change', refreshToolNavigation);
  }
  const downloadHint = document.createElement('p');
  downloadHint.className = 'action-note';
  downloadHint.textContent = 'Confira a prévia e baixe uma cópia. Seu arquivo original fica preservado.';
  document.querySelector('.action-buttons').append(downloadHint);

  async function loadFormEditor() {
    const editor = document.getElementById('form-fields-editor');
    if (!currentFile || !editor || loadedFormFile === currentFile) return;
    const file = currentFile;
    const request = ++formRequest;
    formEditorReady = false;
    updatePrimaryAction();
    editor.textContent = 'Lendo os campos do documento…';
    try {
      const body = new FormData(); body.append('arquivo', file);
      const response = await window.localPdfRequest('/api/formularios/listar', { body });
      const result = await response.json();
      if (request !== formRequest || currentFile !== file) return;
      editor.replaceChildren();
      loadedFormFile = file;
      const values = {};
      const serialize = () => {
        document.getElementById('input-form-json').value = JSON.stringify(values);
      };
      for (const [index, field] of result.campos.entries()) {
        // A field can appear on several pages; one editor updates all its widgets.
        if (Object.hasOwn(values, field.nome)) continue;
        const row = document.createElement('div'); row.className = 'form-row';
        const label = document.createElement('label'); label.textContent = field.nome;
        const control = document.createElement(field.opcoes?.length ? 'select' : 'input');
        control.id = `pdf-field-${index}`; label.htmlFor = control.id;
        const boolean = ['checkbox', 'radiobutton', 'radio-button'].includes(field.tipo);
        if (boolean) {
          control.type = 'checkbox'; control.checked = field.valor !== 'Off';
          values[field.nome] = control.checked; row.classList.add('form-checkbox');
        } else {
          if (field.opcoes?.length) for (const value of field.opcoes) {
            const option = document.createElement('option'); option.value = value; option.textContent = value; control.append(option);
          }
          control.className = 'input-control'; control.value = field.valor || '';
          values[field.nome] = control.value;
        }
        control.disabled = field.somente_leitura || !['text', 'checkbox', 'radiobutton', 'radio-button', 'listbox', 'combobox'].includes(field.tipo);
        if (control.disabled) { delete values[field.nome]; label.textContent += ' (somente leitura)'; }
        control.addEventListener('input', () => { values[field.nome] = boolean ? control.checked : control.value; serialize(); });
        row.append(label, control); editor.append(row);
      }
      serialize();
      formEditorReady = Object.keys(values).length > 0;
      updatePrimaryAction();
      if (!result.campos.length) editor.textContent = 'Este PDF não tem campos preenchíveis.';
    } catch (error) {
      if (request === formRequest) editor.textContent = error.message;
    }
  }
  function isEditingText() { return getActiveOperationKey() === 'tab-texto:editar-texto'; }

  function syncTextTargets() {
    const layer = document.getElementById('text-target-layer');
    if (!layer) return;
    layer.replaceChildren();
    if (!isEditingText() || currentViewMode !== 'original' || !editableInfo?.disponivel || editablePageNumber !== currentPageNum) return;
    const [x0, y0, x1, y1] = editableInfo.bounds;
    const rotatePoint = (x, y) => {
      const u = (x - x0) / (x1 - x0), v = (y - y0) / (y1 - y0);
      return currentRotation === 90 ? [1 - v, u] : currentRotation === 180 ? [1 - u, 1 - v] : currentRotation === 270 ? [v, 1 - u] : [u, v];
    };
    for (const line of editableInfo.linhas.filter(item => item.supported)) {
      const [left, top, right, bottom] = line.rect;
      const points = [[left, top], [right, top], [left, bottom], [right, bottom]].map(p => rotatePoint(...p));
      const xs = points.map(p => p[0]), ys = points.map(p => p[1]);
      const button = document.createElement('button');
      button.type = 'button'; button.className = 'text-target';
      button.classList.toggle('selected', selectedTextLine?.id === line.id);
      button.setAttribute('aria-label', `Editar: ${line.texto}`);
      button.setAttribute('aria-pressed', String(selectedTextLine?.id === line.id));
      button.title = line.texto;
      Object.assign(button.style, { left: `${Math.min(...xs) * 100}%`, top: `${Math.min(...ys) * 100}%`, width: `${(Math.max(...xs) - Math.min(...xs)) * 100}%`, height: `${(Math.max(...ys) - Math.min(...ys)) * 100}%` });
      button.addEventListener('click', () => { selectEditableLine(line.id); document.getElementById('input-edit-substituicao').focus(); });
      layer.append(button);
    }
  }

  function selectEditableLine(id) {
    selectedTextLine = id === '' ? null : editableInfo?.linhas.find(line => line.id === Number(id) && line.supported) || null;
    const select = document.getElementById('select-edit-linha');
    const input = document.getElementById('input-edit-substituicao');
    select.value = selectedTextLine ? String(selectedTextLine.id) : '';
    input.disabled = !selectedTextLine;
    const draft = textDrafts.get(`${editablePageNumber}:${selectedTextLine?.id}`);
    input.value = selectedTextLine ? draft?.novo ?? selectedTextLine.texto : '';
    document.getElementById('text-edit-font').textContent = selectedTextLine
      ? `Fonte de substituição: ${selectedTextLine.fonte}. O texto pode diminuir para caber no mesmo espaço.` : 'Selecione uma linha no documento ou na lista.';
    syncTextTargets(); updatePrimaryAction();
  }

  function resetTextEditor() {
    textLoadRequest++;
    editableFile = null; editableInfo = null; selectedTextLine = null;
    textDrafts.clear();
    document.getElementById('text-edit-count').textContent = '';
    document.getElementById('text-target-layer').replaceChildren();
  }

  async function loadEditableText() {
    if (!isEditingText() || !originalFile || !currentPdfDoc) return;
    document.getElementById('input-edit-pagina').max = currentPdfDoc.numPages;
    document.getElementById('input-edit-pagina').value = currentPageNum;
    if (editableFile === originalFile && editablePageNumber === currentPageNum && editableInfo) { syncTextTargets(); return; }
    const request = ++textLoadRequest, source = originalFile, pageNumber = currentPageNum;
    const status = document.getElementById('text-edit-status');
    const controls = document.getElementById('text-edit-controls');
    status.textContent = 'Verificando o texto desta página…'; controls.classList.add('hidden');
    selectedTextLine = null; editableInfo = null; syncTextTargets(); updatePrimaryAction();
    try {
      const body = new FormData(); body.append('arquivo', source); body.append('pagina', String(pageNumber));
      const response = await window.localPdfRequest('/api/texto/listar-editaveis', { body });
      const info = await response.json();
      if (request !== textLoadRequest || source !== originalFile || pageNumber !== currentPageNum) return;
      editableFile = source; editablePageNumber = pageNumber; editableInfo = info;
      status.textContent = info.disponivel ? 'Clique numa linha do documento ou escolha na lista.' : info.motivo;
      status.classList.toggle('unavailable', !info.disponivel);
      controls.classList.toggle('hidden', !info.disponivel);
      const select = document.getElementById('select-edit-linha');
      select.replaceChildren(new Option('Escolha uma linha…', ''));
      for (const line of info.linhas) {
        const option = new Option(line.texto + (line.supported ? '' : ' (estilo não suportado)'), String(line.id));
        option.disabled = !line.supported; select.append(option);
      }
      selectEditableLine('');
    } catch (error) {
      if (request === textLoadRequest) { status.textContent = error.message; status.classList.add('unavailable'); }
    }
  }
  document.getElementById('select-edit-linha').addEventListener('change', event => {
    if (event.target.value === '') { selectedTextLine = null; document.getElementById('input-edit-substituicao').disabled = true; syncTextTargets(); return; }
    selectEditableLine(event.target.value);
  });
  document.getElementById('input-edit-substituicao').addEventListener('input', event => {
    if (!selectedTextLine) return;
    const key = `${editablePageNumber}:${selectedTextLine.id}`, value = event.target.value;
    if (value === selectedTextLine.texto) textDrafts.delete(key);
    else textDrafts.set(key, { pagina: editablePageNumber, linha: selectedTextLine.id, original: selectedTextLine.texto, novo: value });
    document.getElementById('text-edit-count').textContent = textDrafts.size ? `${textDrafts.size} ${textDrafts.size === 1 ? 'linha alterada' : 'linhas alteradas'}. Gere a prévia para conferir.` : '';
    updatePrimaryAction();
  });
  document.getElementById('input-edit-pagina').addEventListener('change', event => {
    const number = Number(event.target.value);
    if (!Number.isInteger(number) || number < 1 || number > (currentPdfDoc?.numPages || 0)) { event.target.value = currentPageNum; return; }
    currentPageNum = number; queueRenderPage(number); loadEditableText();
  });

  selectSubAnotacoes.dispatchEvent(new Event("change", { bubbles: true }));
  selectSubTexto.dispatchEvent(new Event("change", { bubbles: true }));
  refreshToolNavigation();

  function disposeViewer() {
    viewerGeneration++;
    currentRenderTask?.cancel(); currentRenderTask = null;
    const task = viewerLoadingTask, doc = currentPdfDoc;
    viewerLoadingTask = null; currentPdfDoc = null;
    pendingPageNum = null; isRendering = false;
    viewerDisposal = Promise.allSettled([viewerDisposal, task ? task.destroy() : doc?.destroy()]).then(() => undefined);
    return viewerDisposal;
  }

  async function loadPdfInViewer(arrayBuffer, isValid = () => true) {
    if (!window.pdfjsLib || !isValid()) return false;
    const disposal = disposeViewer();
    const generation = viewerGeneration;
    await disposal;
    if (generation !== viewerGeneration || !isValid()) return false;
    const loadingTask = window.pdfjsLib.getDocument({
      data: arrayBuffer, isEvalSupported: false,
      cMapUrl: '/static/vendor/pdfjs/cmaps/', cMapPacked: true,
      standardFontDataUrl: '/static/vendor/pdfjs/standard_fonts/',
      wasmUrl: '/static/vendor/pdfjs/wasm/',
    });
    viewerLoadingTask = loadingTask;
    try {
      const doc = await loadingTask.promise;
      const firstPage = await doc.getPage(1);
      if (generation !== viewerGeneration || !isValid()) {
        if (viewerLoadingTask === loadingTask) await disposeViewer();
        else await loadingTask.destroy();
        return false;
      }
      currentPdfDoc = doc;
      const pageWidth = firstPage.getViewport({ scale: 1 }).width;
      currentScale = Math.min(1, Math.max(.15, (viewerWorkspace.clientWidth - 32) / pageWidth));
      if (spanZoomLevel) spanZoomLevel.textContent = `${Math.round(currentScale * 100)}%`;
      currentPageNum = 1; currentRotation = 0;
      if (spanPageCount) spanPageCount.textContent = doc.numPages;
      if (inputPageNum) { inputPageNum.max = doc.numPages; inputPageNum.value = 1; }
      viewerSection?.classList.remove('hidden');
      renderPage(1); updatePreviewControls();
      return true;
    } catch (error) {
      if (generation === viewerGeneration && isValid()) {
        await disposeViewer();
        showFeedback(`Não foi possível exibir o PDF: ${error.message}`, 'error');
      }
      return false;
    }
  }

  function queueRenderPage(num) {
    if (isRendering) pendingPageNum = num;
    else renderPage(num);
  }

  async function renderPage(num) {
    if (!currentPdfDoc || !pdfCanvas) return;
    const doc = currentPdfDoc, generation = viewerGeneration;
    isRendering = true;
    let task;
    try {
      const page = await doc.getPage(num);
      if (generation !== viewerGeneration || doc !== currentPdfDoc) return;
      const viewport = page.getViewport({ scale: currentScale, rotation: (page.rotate + currentRotation) % 360 });
      const outputScale = window.devicePixelRatio || 1;
      pdfCanvas.width = Math.floor(viewport.width * outputScale);
      pdfCanvas.height = Math.floor(viewport.height * outputScale);
      pdfCanvas.style.width = `${viewport.width}px`;
      pdfCanvas.style.height = `${viewport.height}px`;
      task = page.render({ canvas: pdfCanvas, canvasContext: pdfCanvas.getContext('2d'), viewport,
        transform: outputScale !== 1 ? [outputScale, 0, 0, outputScale, 0, 0] : null });
      currentRenderTask = task;
      await task.promise;
      if (generation !== viewerGeneration || doc !== currentPdfDoc) return;
      if (inputPageNum) inputPageNum.value = num;
      signatureEditor.viewport(viewport, num, doc.numPages);
      if (isEditingText()) loadEditableText();
    } catch (error) {
      if (generation === viewerGeneration && error.name !== 'RenderingCancelledException') console.error('Erro na renderização da página:', error);
    } finally {
      if (generation === viewerGeneration && doc === currentPdfDoc) {
        if (currentRenderTask === task) currentRenderTask = null;
        isRendering = false;
        if (pendingPageNum !== null) {
          const next = pendingPageNum; pendingPageNum = null; renderPage(next);
        }
      }
    }
  }

  async function handleFile(file) {
    if (!file) return;
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      showFeedback("Por favor, selecione apenas arquivos com extensão .pdf", "error");
      return;
    }

    discardPreview(false);
    documentGeneration++; viewSelection++; disposeViewer();
    currentFile = file;
    resetTextEditor();
    signatureEditor.reset();
    loadedFormFile = null;
    formEditorReady = false;
    originalFile = file;
    currentViewMode = "original";
    updatePreviewControls();
    clearFeedback();
    hideTextResult();

    if (fileName) fileName.textContent = file.name;
    if (fileMeta) fileMeta.textContent = `Tamanho: ${formatBytes(file.size)} | Analisando...`;
    if (fileInfoCard) fileInfoCard.classList.remove("hidden");
    if (actionsPanel) actionsPanel.classList.remove("hidden");

    const generation = documentGeneration;
    const isValid = () => generation === documentGeneration && currentFile === file;
    // This asynchronous read must not replace a newer file or a newer preview.
    const selection = viewSelection;
    file.arrayBuffer().then(buffer => loadPdfInViewer(buffer, () => isValid() && selection === viewSelection));

    const formData = new FormData();
    formData.append("arquivo", file);

    try {
      const res = await window.localPdfRequest("/api/inspecionar", {
        method: "POST",
        body: formData,
      });

      if (res.ok) {
        const data = await res.json();
        if (currentFile !== file) return;
        if (selectSubForm?.value === "preencher") loadFormEditor();
        if (fileMeta) {
          fileMeta.textContent = `Tamanho: ${formatBytes(data.tamanho)} | Páginas: ${data.total_paginas}`;
        }
      } else {
        const err = await res.json().catch(() => ({}));
        showFeedback(err.erro || err.detail || "Erro ao ler metadados do PDF.", "error");
      }
    } catch (err) {
      if (!isValid()) return;
      showFeedback(err.message, "error");
      if (fileMeta) fileMeta.textContent = `Tamanho: ${formatBytes(file.size)}`;
    }
  }

  function resetFile() {
    documentGeneration++; viewSelection++; disposeViewer();
    currentFile = null;
    resetTextEditor();
    signatureEditor.reset();
    originalFile = null;
    currentPdfDoc = null;
    document.getElementById('footer-operation').textContent = 'Aguardando';
    discardPreview(false);
    currentViewMode = "none";
    updatePreviewControls();
    if (fileInput) fileInput.value = "";
    if (fileInfoCard) fileInfoCard.classList.add("hidden");
    if (actionsPanel) actionsPanel.classList.toggle("hidden", activeTabId !== "tab-juntar");
    if (viewerSection) viewerSection.classList.add("hidden");
    clearFeedback();
    hideTextResult();
  }

  if (dropZone) {
    ["dragenter", "dragover"].forEach((eventName) => {
      dropZone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropZone.classList.add("dragover");
      });
    });

    ["dragleave", "drop"].forEach((eventName) => {
      dropZone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropZone.classList.remove("dragover");
      });
    });

    dropZone.addEventListener("drop", (e) => {
      const files = e.dataTransfer?.files;
      if (files && files.length > 0) {
        if (activeTabId === "tab-juntar") {
          addJoinFiles(files);
        } else {
          handleFile(files[0]);
        }
      }
    });
  }

  if (viewerWorkspace) {
    ["dragenter", "dragover"].forEach((eventName) => {
      viewerWorkspace.addEventListener(eventName, (e) => {
        if (activeTabId !== "tab-juntar") return;
        e.preventDefault();
        viewerWorkspace.classList.add("join-dragover");
      });
    });
    ["dragleave", "drop"].forEach((eventName) => {
      viewerWorkspace.addEventListener(eventName, (e) => {
        if (activeTabId !== "tab-juntar") return;
        viewerWorkspace.classList.remove("join-dragover");
        if (eventName === "drop") {
          e.preventDefault();
          addJoinFiles(e.dataTransfer?.files);
        }
      });
    });
  }

  if (fileInput) {
    fileInput.addEventListener("change", (e) => {
      const files = e.target.files;
      if (files && files.length > 0) {
        handleFile(files[0]);
      }
    });
  }

  if (btnRemoveFile) {
    btnRemoveFile.addEventListener("click", resetFile);
  }

  if (btnPrevPage) {
    btnPrevPage.addEventListener("click", () => {
      if (currentPageNum <= 1) return;
      currentPageNum--;
      queueRenderPage(currentPageNum);
    });
  }

  if (btnNextPage) {
    btnNextPage.addEventListener("click", () => {
      if (!currentPdfDoc || currentPageNum >= currentPdfDoc.numPages) return;
      currentPageNum++;
      queueRenderPage(currentPageNum);
    });
  }

  if (inputPageNum) {
    inputPageNum.addEventListener("change", () => {
      if (!currentPdfDoc) return;
      let val = parseInt(inputPageNum.value, 10);
      if (isNaN(val) || val < 1) val = 1;
      if (val > currentPdfDoc.numPages) val = currentPdfDoc.numPages;
      currentPageNum = val;
      queueRenderPage(currentPageNum);
    });
  }

  if (btnZoomIn) {
    btnZoomIn.addEventListener("click", () => {
      if (currentScale >= 2.5) return;
      currentScale += 0.25;
      if (spanZoomLevel) spanZoomLevel.textContent = `${Math.round(currentScale * 100)}%`;
      queueRenderPage(currentPageNum);
    });
  }

  if (btnZoomOut) {
    btnZoomOut.addEventListener("click", () => {
      if (currentScale <= 0.5) return;
      currentScale -= 0.25;
      if (spanZoomLevel) spanZoomLevel.textContent = `${Math.round(currentScale * 100)}%`;
      queueRenderPage(currentPageNum);
    });
  }

  if (btnRotate) {
    btnRotate.addEventListener("click", () => {
      currentRotation = (currentRotation + 90) % 360;
      queueRenderPage(currentPageNum);
    });
  }

  async function handlePdfDownloadResponse(response, fallbackName, job) {
    if (!isCurrentJob(job)) return;
    let downloadName = fallbackName;
    const disposition = response.headers.get("Content-Disposition");
    if (disposition && disposition.includes("filename=")) {
      const match = disposition.match(/filename="?([^"]+)"?/);
      if (match && match[1]) {
        downloadName = match[1];
      }
    }

    const blob = await response.blob();

    if (!isCurrentJob(job)) return;
    if (job.tool === 'tab-seguranca:proteger') {
      downloadBlob(blob, downloadName);
      showFeedback(`PDF protegido. Arquivo '${downloadName}' baixado.`, 'success');
      return;
    }
    const processedBuffer = await blob.arrayBuffer();
    if (!isCurrentJob(job)) return;
    await loadPdfInViewer(processedBuffer, () => isCurrentJob(job));
    if (!isCurrentJob(job)) return;

    if (job.tab === "tab-juntar") {
      discardPreview(false);
      currentFile = new File([blob], downloadName, { type: blob.type || "application/pdf" });
      originalFile = currentFile;
      resetTextEditor();
      signatureEditor.reset();
      currentViewMode = "original";
      if (fileInfoCard) fileInfoCard.classList.remove("hidden");
      if (fileName) fileName.textContent = downloadName;
      if (fileMeta) fileMeta.textContent = currentPdfDoc
        ? `Resultado da junção | Páginas: ${currentPdfDoc.numPages}`
        : "Resultado da junção";
      if (actionsPanel) actionsPanel.classList.remove("hidden");
    } else {
      currentViewMode = "result";
    }
    updatePreviewControls();

    downloadBlob(blob, downloadName);

    showFeedback(`Sucesso! Operação concluída. Arquivo '${downloadName}' baixado.`, "success");
  }

  if (btnExecutar) {
    btnExecutar.addEventListener("click", async () => {
      if (activeTabId === "tab-juntar") {
        const files = [...joinFiles];
        if (files.length < 2) {
          showFeedback("Selecione pelo menos 2 arquivos PDF para juntar.", "error");
          return;
        }
        const invalidFiles = files.filter((file) => !file.name.toLowerCase().endsWith(".pdf"));
        if (invalidFiles.length > 0) {
          showFeedback("Apenas arquivos com extensão .pdf podem ser juntados.", "error");
          return;
        }

        const job = beginOperation();
        btnExecutar.disabled = true;
        btnExecutar.textContent = "Processando...";
        showFeedback("Juntando arquivos PDF...", "info");

        const formData = new FormData();
        files.forEach((file) => formData.append("arquivos", file));

        try {
          const res = await window.localPdfRequest("/api/paginas/juntar", {
            method: "POST",
            body: formData, signal: job.controller.signal,
          });
          if (!isCurrentJob(job)) return;

          if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.erro || err.detail || `Erro HTTP ${res.status}`);
          }

          await handlePdfDownloadResponse(res, "documento_juntado.pdf", job);
        } catch (e) {
          if (isCurrentJob(job) && e.name !== "AbortError") showFeedback(`Falha ao juntar PDFs: ${e.message}`, "error");
        } finally {
          if (activeJob === job) activeJob = null;
          updatePrimaryAction();
        }
        return;
      }

      if (!currentFile) {
        showFeedback("Selecione um arquivo PDF antes de executar.", "error");
        return;
      }

      const job = beginOperation();
      const previewMode = isPreviewOperation();
      const operationKey = getActiveOperationKey();
      const requestId = previewMode ? ++previewRequestId : null;
      if (previewMode) {
        previewIsGenerating = true;
        previewChangedDuringRequest = false;
        previewToolKey = operationKey;
        updatePrimaryAction();
        showFeedback("Gerando prévia...", "info");
      } else {
        btnExecutar.disabled = true;
        btnExecutar.textContent = "Processando...";
        showFeedback("Processando PDF neste dispositivo...", "info");
      }

      const formData = new FormData();
      formData.append("arquivo", currentFile);

      let url = "";
      let isJsonResult = false;

      if (activeTabId === "tab-paginas") {
        const acao = selectSubPaginas?.value;
        if (acao === "girar") {
          url = "/api/paginas/girar";
          formData.append("graus", document.getElementById("input-paginas-graus")?.value || "90");
          formData.append("paginas", document.getElementById("input-paginas-lista")?.value || "");
        } else if (acao === "extrair") {
          url = "/api/paginas/extrair";
          formData.append("paginas", document.getElementById("input-paginas-lista")?.value || "");
        } else if (acao === "excluir") {
          url = "/api/paginas/excluir";
          formData.append("paginas", document.getElementById("input-paginas-lista")?.value || "");
        } else if (acao === "reordenar") {
          url = "/api/paginas/reordenar";
          formData.append("ordem", document.getElementById("input-paginas-ordem")?.value || "");
        }
      } else if (activeTabId === "tab-anotacoes") {
        const acao = selectSubAnotacoes?.value;
        if (acao === "assinatura") {
          url = "/api/assinatura/adicionar";
          formData.append("assinatura", JSON.stringify(signatureEditor.data()));
        } else if (acao === "marca-dagua") {
          url = "/api/anotacoes/marca-dagua";
          formData.append("texto", document.getElementById("input-marca-texto")?.value || "");
          formData.append("opacidade", document.getElementById("input-marca-opacidade")?.value || "0.3");
        } else if (acao === "numerar") {
          url = "/api/anotacoes/numerar";
          formData.append("formato", document.getElementById("input-num-formato")?.value || "");
          formData.append("posicao", document.getElementById("select-num-posicao")?.value || "");
        } else if (acao === "nota") {
          url = "/api/anotacoes/nota";
          formData.append("texto", document.getElementById("input-nota-texto")?.value || "");
          formData.append("pagina", document.getElementById("input-nota-pagina")?.value || "1");
        } else if (acao === "destacar") {
          url = "/api/anotacoes/destacar";
          formData.append("termo", document.getElementById("input-destaque-termo")?.value || "");
          formData.append("tipo", document.getElementById("select-destaque-tipo")?.value || "destaque");
        }
      } else if (activeTabId === "tab-formularios") {
        const acao = selectSubForm?.value;
        if (acao === "listar") {
          url = "/api/formularios/listar";
          isJsonResult = true;
        } else if (acao === "preencher") {
          url = "/api/formularios/preencher";
          formData.append("dados_json", document.getElementById("input-form-json")?.value || "{}");
        } else if (acao === "achatar") {
          url = "/api/formularios/achatar";
        }
      } else if (activeTabId === "tab-texto") {
        const acao = selectSubTexto?.value;
        if (acao === "editar-texto") {
          url = "/api/texto/editar";
          formData.append("edicoes", JSON.stringify([...textDrafts.values()]));
        } else if (acao === "extrair-texto") {
          url = "/api/texto/extrair";
          isJsonResult = true;
        } else if (acao === "adicionar-texto") {
          url = "/api/texto/adicionar";
          formData.append("texto", document.getElementById("input-add-texto-conteudo")?.value || "");
          formData.append("pagina", document.getElementById("input-add-texto-pagina")?.value || "1");
          formData.append("cor", document.getElementById("select-add-texto-cor")?.value || "preto");
        } else if (acao === "editar-metadados") {
          url = "/api/metadados/editar";
          formData.append("titulo", document.getElementById("input-meta-titulo")?.value || "");
          formData.append("autor", document.getElementById("input-meta-autor")?.value || "");
        }
      } else if (activeTabId === "tab-seguranca") {
        const acao = selectSubSeg?.value;
        if (acao === "comprimir") {
          url = "/api/compressao/comprimir";
          formData.append("nivel", document.getElementById("select-seg-nivel")?.value || "medio");
        } else if (acao === "proteger") {
          url = "/api/seguranca/proteger";
          formData.append("senha_usuario", document.getElementById("input-seg-senha")?.value || "");
        } else if (acao === "remover-senha") {
          url = "/api/seguranca/remover-senha";
          formData.append("senha", document.getElementById("input-seg-senha")?.value || "");
        }
      }

      try {
        const response = await window.localPdfRequest(url, {
          method: "POST",
          body: formData, signal: job.controller.signal,
        });
        if (!isCurrentJob(job)) return;

        if (!response.ok) {
          const errData = await response.json().catch(() => ({}));
          throw new Error(errData.erro || errData.detail || `Erro HTTP ${response.status}`);
        }

        if (isJsonResult) {
          const jsonRes = await response.json();
          if (jsonRes.texto !== undefined) {
            showTextResult("Texto Extraído do PDF", jsonRes.texto || "(Nenhum texto encontrado)");
          } else if (jsonRes.campos !== undefined) {
            showTextResult(`Campos Encontrados (${jsonRes.total})`, JSON.stringify(jsonRes.campos, null, 2));
          }
          showFeedback("Consulta realizada com sucesso!", "success");
        } else if (previewMode) {
          if (requestId !== previewRequestId) return;
          const blob = await response.blob();
          const disposition = response.headers.get("Content-Disposition");
          const filenameMatch = disposition?.match(/filename="?([^";]+)"?/);
          previewDownloadName = filenameMatch?.[1] || `processado_${currentFile.name}`;
          const loaded = await loadPdfInViewer(await blob.arrayBuffer(), () => isCurrentJob(job) && requestId === previewRequestId);
          if (!isCurrentJob(job) || requestId !== previewRequestId) return;
          if (!loaded) throw new Error("Não foi possível abrir a prévia do PDF.");

          previewBlob = blob;
          previewRevision = job.revision; previewSource = job.source;
          previewToolKey = operationKey;
          previewIsStale = previewChangedDuringRequest || previewRevision !== editRevision;
          currentViewMode = "preview";
          updatePreviewControls();
          if (activeTabId === "tab-seguranca" && selectSubSeg?.value === "comprimir") {
            if (compressionSizeDetail && originalFile) {
              compressionSizeDetail.textContent = `${formatBytes(originalFile.size)} antes · ${formatBytes(blob.size)} depois`;
            }
            compressionSizeStatus?.classList.remove("hidden");
          } else {
            compressionSizeStatus?.classList.add("hidden");
          }
          showFeedback(previewIsStale
            ? "Prévia pronta, mas campos foram alterados durante a geração."
            : "Prévia pronta. Revise antes de baixar.", "success");
        } else {
          await handlePdfDownloadResponse(response, `processado_${job.source.name}`, job);
        }
      } catch (err) {
        if (isCurrentJob(job) && err.name !== "AbortError") showFeedback(`Erro ao processar: ${err.message}`, "error");
      } finally {
        if (activeJob === job) activeJob = null;
        if (previewMode) {
          if (requestId === previewRequestId) {
            previewIsGenerating = false;
            updatePrimaryAction();
            updatePreviewControls();
          }
        } else {
          btnExecutar.disabled = false;
          updatePrimaryAction();
        }
      }
    });
  }
};
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initializePerfectDF, { once: true });
else initializePerfectDF();
