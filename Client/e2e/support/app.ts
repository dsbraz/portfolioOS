import { Page, APIRequestContext, expect } from '@playwright/test';

/** Matches `Server/scripts/seed_e2e.py`. */
export const OPERATOR = { username: 'e2e', password: 'e2e-password-123' };

/** Matches `Server/scripts/seed_demo.py` — the deterministic scenario. */
export const CENARIO = {
  auditada: 'Lumina Demo IA',
  /** Behind on July/2026 on purpose, so the chase flow has a target. */
  atrasada: 'Aurora Demo IA',
  /** Reachable by both channels. */
  executivoCompleto: 'Ana Costa',
  /** No phone: exercises the e-mail fallback. */
  executivoSoEmail: 'Bruno Lima',
  /** Neither channel: exercises the blocked state. */
  executivoSemContato: 'Carla Reis',
} as const;

const API = process.env.E2E_API_URL ?? 'http://localhost:8000';

/** The session token, taken straight from the API. */
export async function loginViaApi(request: APIRequestContext): Promise<string> {
  const resposta = await request.post(`${API}/api/auth/login`, { data: OPERATOR });
  expect(resposta.ok(), 'login da API falhou — o stack subiu semeado?').toBeTruthy();
  return (await resposta.json()).access_token;
}

/**
 * Signs in without driving the login screen.
 *
 * The login form has its own spec; making every other journey retype it would
 * buy nothing and pay for it in wall clock. The token is planted before the app
 * boots, so the first render is already authenticated.
 */
export async function entrarComoOperador(page: Page, token: string): Promise<void> {
  await page.addInitScript((valor) => {
    // Mirrors TOKEN_KEY in `services/auth.service.ts`.
    window.localStorage.setItem('access_token', valor as string);
  }, token);
}

/** The storage key the app reads; kept here so a rename fails loudly in one place. */
export async function tokenGuardadoNoNavegador(page: Page): Promise<string | null> {
  return page.evaluate(() => window.localStorage.getItem('access_token'));
}

/**
 * Creates a deal straight through the API.
 *
 * The board's own scenario is not part of the AI demo seed, and driving the
 * creation dialog in every spec would test the dialog over and over instead of
 * the thing under test. A unique name keeps parallel-safe isolation if workers
 * ever grow past one.
 */
export async function criarNegocioViaApi(
  request: APIRequestContext,
  token: string,
  empresa: string,
): Promise<void> {
  const resposta = await request.post(`${API}/api/deals`, {
    headers: { Authorization: `Bearer ${token}` },
    data: { company: empresa, stage: 'novo' },
  });
  expect(resposta.ok(), `não consegui criar o negócio ${empresa}`).toBeTruthy();
}

/** Opens a startup from the monitoring table by its own named link. */
export async function abrirInvestida(page: Page, nome: string): Promise<void> {
  await page.goto('/portfolio');
  await page.getByRole('link', { name: nome, exact: true }).click();
  await expect(page.getByRole('tab', { name: /Indicadores Mensais/ })).toBeVisible();
}
