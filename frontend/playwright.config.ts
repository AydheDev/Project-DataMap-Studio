import { defineConfig } from '@playwright/test';
import path from 'node:path';
const python = path.resolve(
  process.platform === 'win32' ? '../.venv/Scripts/python.exe' : '../.venv/bin/python'
);
const backend = path.resolve('../backend');
export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  workers: 1,
  use: {
    baseURL: 'http://127.0.0.1:8000',
    viewport: { width: 1440, height: 1000 },
    launchOptions: process.env.BROWSER_EXECUTABLE
      ? { executablePath: process.env.BROWSER_EXECUTABLE }
      : {},
    screenshot: 'only-on-failure',
  },
  webServer: {
    command: `"${python}" -m uvicorn app.main:app --app-dir "${backend}" --host 127.0.0.1 --port 8000 --no-access-log`,
    url: 'http://127.0.0.1:8000/api/health',
    reuseExistingServer: false,
    env: { DATAMAP_STORAGE: path.resolve('../storage/e2e') },
    timeout: 30000,
  },
});
