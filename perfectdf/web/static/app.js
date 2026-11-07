// PerfectDF - Frontend Base
document.addEventListener("DOMContentLoaded", () => {
  const badge = document.getElementById("api-status-badge");
  const text = document.getElementById("api-status-text");

  fetch("/api/ping")
    .then((res) => {
      if (!res.ok) {
        throw new Error(`Erro HTTP: ${res.status}`);
      }
      return res.json();
    })
    .then((data) => {
      if (badge && text) {
        badge.textContent = "Online";
        badge.classList.remove("offline");
        badge.classList.add("online");
        text.textContent = `Online (${data.message})`;
      }
    })
    .catch((err) => {
      if (badge && text) {
        badge.textContent = "Offline";
        badge.classList.remove("online");
        badge.classList.add("offline");
        text.textContent = `Falha ao conectar: ${err.message}`;
      }
    });
});
