document.addEventListener("DOMContentLoaded", () => {
  if (window.pdfjsLib) {
    window.pdfjsLib.GlobalWorkerOptions.workerSrc = "/static/vendor/pdfjs/pdf.worker.min.js";
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
  let joinFiles = [];

  fetch("/api/ping")
    .then((res) => {
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return res.json();
    })
    .then(() => {
      if (badge) {
        badge.textContent = "Online";
        badge.classList.remove("offline");
        badge.classList.add("online");
      }
    })
    .catch(() => {
      if (badge) {
        badge.textContent = "Offline";
        badge.classList.remove("online");
        badge.classList.add("offline");
      }
    });

  function showFeedback(text, type = "info") {
    if (!feedbackMessage) return;
    feedbackMessage.textContent = text;
    feedbackMessage.className = `feedback-message ${type}`;
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
      return ["adicionar-texto", "editar-metadados"].includes(document.getElementById("select-sub-texto")?.value);
    }
    return activeTabId === "tab-seguranca"
      && document.getElementById("select-sub-seguranca")?.value === "comprimir";
  }

  function updatePreviewControls() {
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
    if (btnBaixarPrevia) btnBaixarPrevia.disabled = !hasPreview;
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
    if (avisoPreviaDesatualizada) {
      avisoPreviaDesatualizada.classList.toggle("hidden", !previewIsStale);
    }
  }

  function updatePrimaryAction() {
    if (!btnExecutar) return;
    if (previewIsGenerating) {
      btnExecutar.disabled = true;
      btnExecutar.textContent = "Gerando...";
      return;
    }
    btnExecutar.textContent = isPreviewOperation() ? "Pré-visualizar" : "Aplicar";
    btnExecutar.disabled = activeTabId === "tab-juntar" && joinFiles.length < 2;
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

  function discardPreview(restoreOriginal = true) {
    const shouldRestoreOriginal = restoreOriginal
      && currentViewMode === "preview"
      && Boolean(originalFile);
    previewRequestId += 1;
    previewBlob = null;
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
    if (!originalFile) return;
    const loaded = await loadPdfInViewer(await originalFile.arrayBuffer());
    if (!loaded) return;
    currentViewMode = "original";
    updatePreviewControls();
  }

  async function showPreviewDocument() {
    if (!previewBlob) return;
    const loaded = await loadPdfInViewer(await previewBlob.arrayBuffer());
    if (!loaded) return;
    currentViewMode = "preview";
    updatePreviewControls();
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
      if ((previewBlob && newKey !== previewToolKey)
        || (previewIsGenerating && newKey !== previewToolKey)) {
        discardPreview();
      }
    } else {
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
      if (previewBlob) downloadBlob(previewBlob, previewDownloadName || "previa.pdf");
    });
  }

  function updateJoinActionState() {
    if (!btnExecutar || btnExecutar.textContent === "Processando...") return;
    btnExecutar.disabled = activeTabId === "tab-juntar" && joinFiles.length < 2;
  }

  function renderJoinFiles() {
    if (!listaArquivosJuntar) return;
    listaArquivosJuntar.replaceChildren();

    if (joinFiles.length === 0) {
      const hint = document.createElement("p");
      hint.className = "join-files-hint";
      hint.textContent = "Selecione ao menos dois PDFs para habilitar Aplicar.";
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
    const singleFileLabel = dropZone.querySelector('label[for="file-input"]');
    if (activeTabId === "tab-juntar") {
      if (heading) heading.textContent = "Solte vários PDFs para juntar";
      if (hint) hint.textContent = "Ou use o seletor múltiplo na faixa de ferramentas.";
      singleFileLabel?.classList.add("hidden");
    } else {
      if (heading) heading.textContent = "Arraste e solte seu arquivo PDF aqui";
      if (hint) hint.textContent = "ou clique no botão abaixo para selecionar";
      singleFileLabel?.classList.remove("hidden");
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

  async function loadPdfInViewer(arrayBuffer) {
    if (!window.pdfjsLib) return false;
    try {
      const loadingTask = window.pdfjsLib.getDocument({ data: arrayBuffer });
      currentPdfDoc = await loadingTask.promise;
      currentPageNum = 1;
      currentRotation = 0;

      if (spanPageCount) spanPageCount.textContent = currentPdfDoc.numPages;
      if (inputPageNum) {
        inputPageNum.max = currentPdfDoc.numPages;
        inputPageNum.value = 1;
      }
      if (viewerSection) viewerSection.classList.remove("hidden");

      renderPage(currentPageNum);
      return true;
    } catch (err) {
      console.error("Erro ao carregar visualizador:", err);
      showFeedback(`Não foi possível exibir o PDF: ${err.message}`, "error");
      return false;
    }
  }

  function queueRenderPage(num) {
    if (isRendering) {
      pendingPageNum = num;
    } else {
      renderPage(num);
    }
  }

  async function renderPage(num) {
    if (!currentPdfDoc || !pdfCanvas) return;
    isRendering = true;

    try {
      const page = await currentPdfDoc.getPage(num);
      const viewport = page.getViewport({
        scale: currentScale,
        rotation: (page.rotate + currentRotation) % 360,
      });

      const ctx = pdfCanvas.getContext("2d");
      const outputScale = window.devicePixelRatio || 1;

      pdfCanvas.width = Math.floor(viewport.width * outputScale);
      pdfCanvas.height = Math.floor(viewport.height * outputScale);
      pdfCanvas.style.width = Math.floor(viewport.width) + "px";
      pdfCanvas.style.height = Math.floor(viewport.height) + "px";

      const transform = outputScale !== 1 ? [outputScale, 0, 0, outputScale, 0, 0] : null;

      const renderContext = {
        canvasContext: ctx,
        transform: transform,
        viewport: viewport,
      };

      if (currentRenderTask) {
        currentRenderTask.cancel();
      }

      currentRenderTask = page.render(renderContext);
      await currentRenderTask.promise;
      currentRenderTask = null;
      isRendering = false;

      if (inputPageNum) inputPageNum.value = num;

      if (pendingPageNum !== null) {
        const next = pendingPageNum;
        pendingPageNum = null;
        renderPage(next);
      }
    } catch (err) {
      if (err.name !== "RenderingCancelledException") {
        console.error("Erro na renderização da página:", err);
      }
      isRendering = false;
    }
  }

  async function handleFile(file) {
    if (!file) return;
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      showFeedback("Por favor, selecione apenas arquivos com extensão .pdf", "error");
      return;
    }

    discardPreview(false);
    currentFile = file;
    originalFile = file;
    currentViewMode = "original";
    updatePreviewControls();
    clearFeedback();
    hideTextResult();

    if (fileName) fileName.textContent = file.name;
    if (fileMeta) fileMeta.textContent = `Tamanho: ${formatBytes(file.size)} | Analisando...`;
    if (fileInfoCard) fileInfoCard.classList.remove("hidden");
    if (actionsPanel) actionsPanel.classList.remove("hidden");

    const reader = new FileReader();
    reader.onload = async (e) => {
      const arrayBuffer = e.target.result;
      await loadPdfInViewer(arrayBuffer);
    };
    reader.readAsArrayBuffer(file);

    const formData = new FormData();
    formData.append("arquivo", file);

    try {
      const res = await fetch("/api/inspecionar", {
        method: "POST",
        body: formData,
      });

      if (res.ok) {
        const data = await res.json();
        if (fileMeta) {
          fileMeta.textContent = `Tamanho: ${formatBytes(data.tamanho)} | Páginas: ${data.total_paginas}`;
        }
      } else {
        const err = await res.json().catch(() => ({}));
        showFeedback(err.erro || err.detail || "Erro ao ler metadados do PDF.", "error");
      }
    } catch (err) {
      if (fileMeta) fileMeta.textContent = `Tamanho: ${formatBytes(file.size)}`;
    }
  }

  function resetFile() {
    currentFile = null;
    originalFile = null;
    currentPdfDoc = null;
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

  async function handlePdfDownloadResponse(response, fallbackName) {
    let downloadName = fallbackName;
    const disposition = response.headers.get("Content-Disposition");
    if (disposition && disposition.includes("filename=")) {
      const match = disposition.match(/filename="?([^"]+)"?/);
      if (match && match[1]) {
        downloadName = match[1];
      }
    }

    const blob = await response.blob();

    const processedBuffer = await blob.arrayBuffer();
    await loadPdfInViewer(processedBuffer);

    if (activeTabId === "tab-juntar") {
      discardPreview(false);
      currentFile = new File([blob], downloadName, { type: blob.type || "application/pdf" });
      originalFile = currentFile;
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
        const files = joinFiles;
        if (files.length < 2) {
          showFeedback("Selecione pelo menos 2 arquivos PDF para juntar.", "error");
          return;
        }
        const invalidFiles = files.filter((file) => !file.name.toLowerCase().endsWith(".pdf"));
        if (invalidFiles.length > 0) {
          showFeedback("Apenas arquivos com extensão .pdf podem ser juntados.", "error");
          return;
        }

        btnExecutar.disabled = true;
        btnExecutar.textContent = "Processando...";
        showFeedback("Juntando arquivos PDF...", "info");

        const formData = new FormData();
        files.forEach((file) => formData.append("arquivos", file));

        try {
          const res = await fetch("/api/paginas/juntar", {
            method: "POST",
            body: formData,
          });

          if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.erro || err.detail || `Erro HTTP ${res.status}`);
          }

          await handlePdfDownloadResponse(res, "documento_juntado.pdf");
        } catch (e) {
          showFeedback(`Falha ao juntar PDFs: ${e.message}`, "error");
        } finally {
          btnExecutar.disabled = activeTabId === "tab-juntar" && joinFiles.length < 2;
          btnExecutar.textContent = "Aplicar";
        }
        return;
      }

      if (!currentFile) {
        showFeedback("Selecione um arquivo PDF antes de executar.", "error");
        return;
      }

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
        showFeedback("Processando arquivo PDF com PerfectDF...", "info");
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
        if (acao === "marca-dagua") {
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
        if (acao === "extrair-texto") {
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
        const response = await fetch(url, {
          method: "POST",
          body: formData,
        });

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
          const loaded = await loadPdfInViewer(await blob.arrayBuffer());
          if (requestId !== previewRequestId) {
            if (originalFile) await showOriginalDocument();
            return;
          }
          if (!loaded) throw new Error("Não foi possível abrir a prévia do PDF.");

          previewBlob = blob;
          previewToolKey = operationKey;
          previewIsStale = previewChangedDuringRequest;
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
          await handlePdfDownloadResponse(response, `processado_${currentFile.name}`);
        }
      } catch (err) {
        showFeedback(`Erro ao processar: ${err.message}`, "error");
      } finally {
        if (previewMode) {
          if (requestId === previewRequestId) {
            previewIsGenerating = false;
            updatePrimaryAction();
          }
        } else {
          btnExecutar.disabled = false;
          btnExecutar.textContent = "Aplicar";
        }
      }
    });
  }
});
