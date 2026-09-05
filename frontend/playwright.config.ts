import { defineConfig, devices } from "@playwright/test";

const MOCK_BASE = "http://127.0.0.1:3100";

export default defineConfig({
  testDir: "./e2e",
  timeout: 120000,
  // One retry absorbs transient loopback/proxy flakes on small/dev boxes.
  // Strict gates stay green-first-try: backend pytest, vitest, typecheck.
  retries: 1,
  // Single worker: deterministic on small/dev boxes; the mock backend is a
  // single-process dev server and parallel SSE streams flake loopback.
  workers: 1,
  fullyParallel: false,
  use: { baseURL: MOCK_BASE, ...devices["Desktop Chrome"] },
  projects: [
    { name: "setup", testMatch: /auth\.setup\.ts/ },
    {
      name: "mock",
      testMatch: /(run|v02|coding|appsec|contracts|protocols|run-controls|ops)\.spec\.ts/,
      dependencies: ["setup"],
      use: { storageState: "./e2e/.auth.json" },
    },
    {
      name: "live",
      testMatch: /live\.spec\.ts/,
    },
  ],
  webServer: [
    {
      command: "python -m uvicorn sklab_web.main:app --host 127.0.0.1 --port 8787",
      cwd: "../backend",
      env: {
        SKLAB_MOCK_MODE: "1",
        AUTH_MODE: "token",
        SKLAB_AUTH_TOKEN: "e2e-token-123",
        SKLAB_ALLOWED_ROOTS: "/srv/sklab/repos",
        SKLAB_MOCK_STEP_MS: "400",
      },
      port: 8787,
      reuseExistingServer: true,
      timeout: 60000,
    },
    {
      command: "node .next/standalone/server.js",
      env: {
        SKLAB_BACKEND_URL: "http://127.0.0.1:8787",
        NODE_ENV: "production",
        PORT: "3100",
        HOSTNAME: "127.0.0.1",
      },
      port: 3100,
      reuseExistingServer: true,
      timeout: 120000,
    },
  ],
});
