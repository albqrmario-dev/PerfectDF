// PerfectDF - Frontend JS
document.addEventListener("DOMContentLoaded", () => {
  // Configuração do Worker local do pdf.js
  if (window.pdfjsLib) {
    window.pdfjsLib.GlobalWorkerOptions.workerSrc = "/static/vendor/pdfjs/pdf.worker.min.js";
  }

  // Elementos de status e upload
  const badge = document.getElementById("api-status-badge");
  const dropZone = document.getElementById("drop-zone");
  const fileInput = document.getElementById("file-input");
  const fileInfoCard = document.getElementById("file-info-card");
  const fileName = document.getElementById("file-name");
  const fileMeta = document.getElementById("file-meta");
  const btnRemoveFile = document.getElementById("btn-remove-file");
  const actionsPanel = document.getElementById("actions-panel");
  const selectOperacao = document.getElementById("select-operacao");
  const paramsComprimir = document.getElementById("params-comprimir");
  const paramsGirar = document.getElementById("params-girar");
  const selectNivel = document.getElementById("select-nivel");
  const inputGraus = document.getElementById("input-graus");
  const btnProcessar = document.getElementById("btn-processar");
  const feedbackMessage = document.getElementById("feedback-message");

  // Elementos do Visualizador PDF
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

  let currentFile = null;
  let currentPdfDoc = null;
  let currentPageNum = 1;
  let currentScale = 1.0;
  let currentRotation = 0;
  let isRendering = false;
  let pendingPageNum = null;
  let currentRenderTask = null;

  // 1. Verificação de status da API
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

  // Funções de feedback
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

  function formatBytes(bytes) {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  }

  // Funções do Visualizador PDF (pdf.js)
  async function loadPdfInViewer(arrayBuffer) {
    if (!window.pdfjsLib) {
      console.warn("pdf.js não encontrado.");
      return;
    }

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
    } catch (err) {
      console.error("Erro ao carregar visualizador:", err);
      showFeedback(`Não foi possível exibir o PDF na tela: ${err.message}`, "error");
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

  // Manipulação do arquivo selecionado
  async function handleFile(file) {
    if (!file) return;
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      showFeedback("Por favor, selecione apenas arquivos com extensão .pdf", "error");
      return;
    }

    currentFile = file;
    clearFeedback();

    if (fileName) fileName.textContent = file.name;
    if (fileMeta) fileMeta.textContent = `Tamanho: ${formatBytes(file.size)} | Analisando...`;
    if (fileInfoCard) fileInfoCard.classList.remove("hidden");
    if (actionsPanel) actionsPanel.classList.remove("hidden");

    // Lê os bytes para o visualizador imediatamente no navegador
    const reader = new FileReader();
    reader.onload = async (e) => {
      const arrayBuffer = e.target.result;
      await loadPdfInViewer(arrayBuffer);
    };
    reader.readAsArrayBuffer(file);

    // Inspeciona no backend
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
      }
    } catch (err) {
      // Ignora erro secundário de inspeção
      if (fileMeta) fileMeta.textContent = `Tamanho: ${formatBytes(file.size)}`;
    }
  }

  function resetFile() {
    currentFile = null;
    currentPdfDoc = null;
    if (fileInput) fileInput.value = "";
    if (fileInfoCard) fileInfoCard.classList.add("hidden");
    if (actionsPanel) actionsPanel.classList.add("hidden");
    if (viewerSection) viewerSection.classList.add("hidden");
    clearFeedback();
  }

  // Eventos de Drag & Drop
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
        handleFile(files[0]);
      }
    });
  }

  // Seleção de arquivo por input
  if (fileInput) {
    fileInput.addEventListener("change", (e) => {
      const files = e.target.files;
      if (files && files.length > 0) {
        handleFile(files[0]);
      }
    });
  }

  // Remoção de arquivo
  if (btnRemoveFile) {
    btnRemoveFile.addEventListener("click", resetFile);
  }

  // Controles do Visualizador (Toolbar)
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

  // Alternância de parâmetros da operação
  if (selectOperacao) {
    selectOperacao.addEventListener("change", () => {
      const op = selectOperacao.value;
      if (op === "comprimir") {
        paramsComprimir?.classList.remove("hidden");
        paramsGirar?.classList.add("hidden");
      } else if (op === "girar") {
        paramsComprimir?.classList.add("hidden");
        paramsGirar?.classList.remove("hidden");
      }
    });
  }

  // Processamento e download do PDF
  if (btnProcessar) {
    btnProcessar.addEventListener("click", async () => {
      if (!currentFile) {
        showFeedback("Selecione um arquivo PDF antes de processar.", "error");
        return;
      }

      btnProcessar.disabled = true;
      btnProcessar.textContent = "Processando...";
      showFeedback("Processando arquivo PDF com PerfectDF...", "info");

      const operacao = selectOperacao?.value || "comprimir";
      const formData = new FormData();
      formData.append("arquivo", currentFile);
      formData.append("operacao", operacao);

      if (operacao === "comprimir" && selectNivel) {
        formData.append("nivel", selectNivel.value);
      } else if (operacao === "girar" && inputGraus) {
        formData.append("graus", inputGraus.value);
      }

      try {
        const response = await fetch("/api/processar", {
          method: "POST",
          body: formData,
        });

        if (!response.ok) {
          const errData = await response.json().catch(() => ({}));
          throw new Error(errData.detail || `Erro HTTP ${response.status}`);
        }

        let downloadName = `processado_${currentFile.name}`;
        const disposition = response.headers.get("Content-Disposition");
        if (disposition && disposition.includes("filename=")) {
          const match = disposition.match(/filename="?([^"]+)"?/);
          if (match && match[1]) {
            downloadName = match[1];
          }
        }

        const blob = await response.blob();

        // Atualiza a visualização na tela com o PDF processado
        const processedBuffer = await blob.arrayBuffer();
        await loadPdfInViewer(processedBuffer);

        // Dispara o download
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = downloadUrl;
        a.download = downloadName;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(downloadUrl);
        a.remove();

        showFeedback(`Sucesso! O arquivo '${downloadName}' foi processado e baixado.`, "success");
      } catch (err) {
        showFeedback(`Falha no processamento: ${err.message}`, "error");
      } finally {
        btnProcessar.disabled = false;
        btnProcessar.textContent = "Processar e Baixar PDF";
      }
    });
  }
});
