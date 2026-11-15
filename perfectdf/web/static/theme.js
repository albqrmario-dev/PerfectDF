// Run before the stylesheet so the saved/system theme is used on the first paint.
(() => {
  const key = 'perfectdf-theme';
  const root = document.documentElement;
  const system = window.matchMedia('(prefers-color-scheme: dark)');
  const valid = value => value === 'light' || value === 'dark' ? value : null;
  let choice = null;
  try { choice = valid(localStorage.getItem(key)); } catch { /* Storage can be blocked. */ }

  function apply() {
    const theme = choice ?? (system.matches ? 'dark' : 'light');
    root.dataset.theme = theme;
    root.style.colorScheme = theme;
    document.querySelector('meta[name="theme-color"]')?.setAttribute('content', theme === 'dark' ? '#151e29' : '#f1f3f5');
    for (const button of document.querySelectorAll('[data-theme-toggle]')) {
      const action = theme === 'dark' ? 'Ativar tema claro' : 'Ativar tema escuro';
      button.setAttribute('aria-label', action);
      button.title = action;
    }
  }

  apply();
  function connect() {
    apply();
    for (const button of document.querySelectorAll('[data-theme-toggle]')) {
      button.addEventListener('click', () => {
        choice = root.dataset.theme === 'dark' ? 'light' : 'dark';
        try { localStorage.setItem(key, choice); } catch { /* Keep this session usable. */ }
        apply();
      });
    }
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', connect, { once: true });
  else connect();
  system.addEventListener('change', () => { if (!choice) apply(); });
  window.addEventListener('storage', event => {
    if (event.key !== key && event.key !== null) return;
    try { choice = valid(localStorage.getItem(key)); } catch { return; }
    apply();
  });
})();
