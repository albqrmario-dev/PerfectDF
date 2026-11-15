import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir: './tests', testMatch: 'browser-ui.spec.mjs',
  use: { baseURL: 'http://127.0.0.1:8765', headless: true },
  webServer: { command: 'python3 -m http.server 8765 --bind 127.0.0.1 --directory dist', port: 8765, reuseExistingServer: false },
});
