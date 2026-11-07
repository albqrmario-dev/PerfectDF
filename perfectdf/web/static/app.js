// PerfectDF - Frontend JS Completo
document.addEventListener("DOMContentLoaded", () => {
  // Configuração do Worker local do pdf.js
  if (window.pdfjsLib) {
    window.pdfjsLib.GlobalWorkerOptions.workerSrc = "/static/vendor/pdfjs/pdf.worker.min.js";
  }

  // Elementos globais
  const badge = document.getElementById("api-status-badge");
  const dropZone = document.getElementById("drop-zone");
  const fileInput = document.getElementById("file-input");
  const fileInfoCard = document.getElementById("file-info-card");
  const fileName = document.getElementById("file-name");
  const fileMeta = document.getElementById("file-meta");
  const btnRemoveFile = document.getElementById("btn-remove-file");
  const actionsPanel = document.getElementById("actions-panel");
  const btnExecutar = document.getElementById("btn-executar-acao");
  const feedbackMessage = document.getElementById("feedback-message");
  const textResultBox = document.getElementById("text-result-box");
  const textResultTitle = document.getElementById("text-result-title");
  const textResultContent = document.getElementById("text-result-content");
  const btnCloseTextResult = document.getElementById("btn-close-text-result");

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

  // Abas
  const tabBtns = document.querySelectorAll(".tab-btn");
  const tabPanes = document.querySelectorAll(".tab-pane");
  let activeTabId = "tab-paginas";

  // Estado
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

  // Controle de Abas
  tabBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      tabBtns.forEach((b) => b.classList.remove("active"));
      tabPanes.forEach((p) => p.classList.remove("active"));

      btn.classList.add("active");
      activeTabId = btn.getAttribute("data-tab");
      const targetPane = document.getElementById(activeTabId);
      if (targetPane) targetPane.classList.add("active");
    });
  });

  // Controles dinâmicos de sub-opções
  // Páginas
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

  // Anotações
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

  // Formulários
  const selectSubForm = document.getElementById("select-sub-formularios");
  const boxFormPreencher = document.getElementById("box-form-preencher");
  if (selectSubForm) {
    selectSubForm.addEventListener("change", () => {
      const v = selectSubForm.value;
      boxFormPreencher?.classList.toggle("hidden", v !== "preencher");
    });
  }

  // Texto
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

  // Segurança
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

  // Funções do Visualizador PDF (pdf.js)
  async function loadPdfInViewer(arrayBuffer) {
    if (!window.pdfjsLib) return;
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
      showFeedback(`Não foi possível exibir o PDF: ${err.message}`, "error");
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
    hideTextResult();

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
    currentPdfDoc = null;
    if (fileInput) fileInput.value = "";
    if (fileInfoCard) fileInfoCard.classList.add("hidden");
    if (actionsPanel) actionsPanel.classList.add("hidden");
    if (viewerSection) viewerSection.classList.add("hidden");
    clearFeedback();
    hideTextResult();
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

  // Helper para disparar download e atualizar visualizador com novo PDF
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

    // Atualiza visualização na tela
    const processedBuffer = await blob.arrayBuffer();
    await loadPdfInViewer(processedBuffer);

    // Dispara download
    const downloadUrl = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = downloadUrl;
    a.download = downloadName;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(downloadUrl);
    a.remove();

    showFeedback(`Sucesso! Operação concluída. Arquivo '${downloadName}' baixado.`, "success");
  }

  // Execução da Ação Selecionada
  if (btnExecutar) {
    btnExecutar.addEventListener("click", async () => {
      // Caso especial: Juntar PDFs
      if (activeTabId === "tab-juntar") {
        const inputMulti = document.getElementById("input-multiplos-pdfs");
        const files = inputMulti?.files;
        if (!files || files.length < 2) {
          showFeedback("Selecione pelo menos 2 arquivos PDF para juntar.", "error");
          return;
        }

        btnExecutar.disabled = true;
        btnExecutar.textContent = "Processando...";
        showFeedback("Juntando arquivos PDF...", "info");

        const formData = new FormData();
        for (let i = 0; i < files.length; i++) {
          formData.append("arquivos", files[i]);
        }

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
          btnExecutar.disabled = false;
          btnExecutar.textContent = "Executar Operação";
        }
        return;
      }

      // Demais abas necessitam de currentFile
      if (!currentFile) {
        showFeedback("Selecione um arquivo PDF antes de executar.", "error");
        return;
      }

      btnExecutar.disabled = true;
      btnExecutar.textContent = "Processando...";
      showFeedback("Processando arquivo PDF com PerfectDF...", "info");

      const formData = new FormData();
      formData.append("arquivo", currentFile);

      let url = "";
      let isJsonResult = false;

      // Monta os parâmetros conforme a aba ativa
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
        } else {
          await handlePdfDownloadResponse(response, `processado_${currentFile.name}`);
        }
      } catch (err) {
        showFeedback(`Erro ao processar: ${err.message}`, "error");
      } finally {
        btnExecutar.disabled = false;
        btnExecutar.textContent = "Executar Operação";
      }
    });
  }
});
