import { defineConfig, devices } from '@playwright/test';

/**
 * End-to-end suite for the platform.
 *
 * It drives the app through the same contract the skills and assistive tech
 * use — roles and accessible names, never CSS internals. A rename that breaks a
 * spec here breaks an agent in the field, which is exactly the coupling we
 * want.
 *
 * The stack comes from `docker-compose.e2e.yml`: its own database, seeded to a
 * deterministic scenario, unreachable from the development stack.
 */
export default defineConfig({
  testDir: './e2e',
  // The seeded scenario is shared state: two specs writing the same period
  // would race. Sequential keeps failures meaningful.
  workers: 1,
  fullyParallel: false,
  // A test that only passes on retry is a flaky test; surface it instead.
  retries: 0,
  reporter: [['list'], ['html', { outputFolder: 'e2e-results/html', open: 'never' }]],
  outputDir: 'e2e-results/artifacts',
  timeout: 30_000,
  expect: { timeout: 10_000 },
  use: {
    baseURL: process.env.E2E_BASE_URL ?? 'http://localhost:4200',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'off',
    // Matches the app's language, so date and currency assertions read the way
    // a user sees them.
    locale: 'pt-BR',
    timezoneId: 'America/Sao_Paulo',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
});
