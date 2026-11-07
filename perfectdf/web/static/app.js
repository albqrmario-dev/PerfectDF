// PerfectDF - Frontend JS
document.addEventListener("DOMContentLoaded", () => {
  // Elementos da interface
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

  let currentFile = null;

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

  // Manipulação de arquivo selecionado
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

    // Inspeciona o arquivo no backend para obter total de páginas
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
        showFeedback(err.detail || "Erro ao ler metadados do PDF.", "error");
      }
    } catch (err) {
      // Ignora erro secundário de inspeção, mantém arquivo pronto
      if (fileMeta) fileMeta.textContent = `Tamanho: ${formatBytes(file.size)}`;
    }
  }

  function resetFile() {
    currentFile = null;
    if (fileInput) fileInput.value = "";
    if (fileInfoCard) fileInfoCard.classList.add("hidden");
    if (actionsPanel) actionsPanel.classList.add("hidden");
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

  // Evento de seleção via input file
  if (fileInput) {
    fileInput.addEventListener("change", (e) => {
      const files = e.target.files;
      if (files && files.length > 0) {
        handleFile(files[0]);
      }
    });
  }

  // Remoção do arquivo
  if (btnRemoveFile) {
    btnRemoveFile.addEventListener("click", resetFile);
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

        // Recupera o nome sugerido para o arquivo
        let downloadName = `processado_${currentFile.name}`;
        const disposition = response.headers.get("Content-Disposition");
        if (disposition && disposition.includes("filename=")) {
          const match = disposition.match(/filename="?([^"]+)"?/);
          if (match && match[1]) {
            downloadName = match[1];
          }
        }

        // Gera o blob e dispara o download automático
        const blob = await response.blob();
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
