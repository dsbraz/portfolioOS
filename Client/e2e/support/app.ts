import { Page, Locator, APIRequestContext, expect } from '@playwright/test';

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
  /**
   * The period the chase flow is about — `CHASE_MISSING_MONTH/YEAR` in
   * `seed_demo.py`, the one Aurora never reported.
   *
   * Absolute on purpose. The dialog opens on the month BEFORE the wall clock
   * (`AddIndicatorDialog.previousMonthPeriod`), so a spec that accepted that
   * default would mint a link for whatever month the run happens to fall in
   * and then assert on a row the seed never creates — green in the month it
   * was written, red on the first day of the next one.
   */
  periodo: { rotulo: 'Jul', ano: 2026 },
} as const;

const API = process.env.E2E_API_URL ?? 'http://localhost:8000';

/** The storage key the app reads; kept here so a rename fails in one place. */
const TOKEN_KEY = 'access_token';

/**
 * The session token, taken straight from the API.
 *
 * Memoised per worker: the operator never changes, and bcrypt makes every
 * `beforeEach` login a real ~200ms of verification for a token we already have.
 */
let tokenDoOperador: Promise<string> | null = null;

export function loginViaApi(request: APIRequestContext): Promise<string> {
  tokenDoOperador ??= (async () => {
    const resposta = await request.post(`${API}/api/auth/login`, { data: OPERATOR });
    expect(resposta.ok(), 'login da API falhou — o stack subiu semeado?').toBeTruthy();
    return (await resposta.json()).access_token as string;
  })();
  return tokenDoOperador;
}

/**
 * Signs in without driving the login screen.
 *
 * The login form has its own spec; making every other journey retype it would
 * buy nothing and pay for it in wall clock. The token is planted before the app
 * boots, so the first render is already authenticated.
 */
export async function entrarComoOperador(page: Page, token: string): Promise<void> {
  // Mirrors TOKEN_KEY in `services/auth.service.ts`.
  await page.addInitScript(
    ([chave, valor]) => window.localStorage.setItem(chave, valor),
    [TOKEN_KEY, token],
  );
}

/** What the app actually stored — the assertion side of the same key. */
export async function tokenGuardadoNoNavegador(page: Page): Promise<string | null> {
  return page.evaluate((chave) => window.localStorage.getItem(chave), TOKEN_KEY);
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

/**
 * Mints a reporting link from an open startup, leaving the panel on screen.
 *
 * The dialog's pt-BR labels live here, once: three specs walk this same
 * sequence, and a wording change should cost one edit, not three.
 */
export async function gerarLinkDeIndicador(
  page: Page,
  periodo: { rotulo: string; ano: number } = CENARIO.periodo,
): Promise<{ dialogo: Locator; url: string }> {
  await page.getByRole('button', { name: 'Adicionar indicador' }).click();
  const dialogo = page.getByRole('dialog');
  await expect(dialogo).toBeVisible();

  // O período é escolhido, nunca herdado do relógio — ver `CENARIO.periodo`.
  await dialogo.getByRole('combobox', { name: 'Mês' }).click();
  await page.getByRole('option', { name: periodo.rotulo, exact: true }).click();
  await dialogo.getByLabel('Ano', { exact: true }).fill(String(periodo.ano));

  // O cabeçalho anuncia o período: se a escolha não pegou, a falha é aqui, e
  // não trinta linhas adiante numa linha de tabela que nunca existiu.
  // `level: 2` é o título do diálogo (`app-dialog-header`); o corpo tem h3s.
  await expect(dialogo.getByRole('heading', { level: 2 })).toContainText(
    `${periodo.rotulo}/${periodo.ano}`,
  );

  await dialogo.getByRole('radio', { name: 'Gerar link para a investida' }).click();
  await dialogo.getByRole('button', { name: 'Gerar link', exact: true }).click();

  // O link precisa estar visível como TEXTO — nenhum passo do fluxo pode
  // depender da área de transferência (PRD-001 6.5).
  const url = await dialogo.locator('.link-text').innerText();
  return { dialogo, url };
}
