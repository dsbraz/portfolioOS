import { expect, test } from '@playwright/test';

import {
  CENARIO,
  criarInvestidaViaApi,
  entrarComoOperador,
  loginViaApi,
  removerInvestidaViaApi,
} from './support/app';

/**
 * Recording an exit: the startup stops being tracked after the exit month and
 * stays reachable under `Encerradas`, with its history.
 *
 * The exit falls in `CENARIO.periodo` (Jul/2026), chosen explicitly, and the
 * monitoring is checked on that month and the next one — never on whatever
 * month the wall clock is in. Mid-month on purpose, so no time zone can move
 * the date into another month.
 */
test.describe('saída da investida', () => {
  let nome: string;
  let id: string;
  let token: string;

  test.beforeEach(async ({ page, request }) => {
    token = await loginViaApi(request);
    nome = `E2E Saída ${Date.now()}`;
    id = await criarInvestidaViaApi(request, token, nome);
    await entrarComoOperador(page, token);
  });

  test.afterEach(async ({ request }) => {
    await removerInvestidaViaApi(request, token, id);
  });

  test('registrar a saída encerra o acompanhamento sem apagar a investida', async ({ page }) => {
    await page.goto(`/startup/${id}`);
    await expect(page.getByRole('heading', { level: 1, name: nome })).toBeVisible();

    await page.getByRole('button', { name: 'Mais ações' }).click();
    await page.getByRole('menuitem', { name: 'Registrar saída' }).click();

    const dialogo = page.getByRole('dialog');
    await expect(dialogo.getByRole('heading', { name: 'Registrar saída' })).toBeVisible();
    // US month/day/year: the native date adapter parses it as a local date.
    await dialogo.getByLabel('Data da saída').fill('7/15/2026');
    await dialogo.getByRole('combobox', { name: 'Tipo de saída' }).click();
    await page.getByRole('option', { name: 'Venda (M&A ou secundária)' }).click();
    await dialogo.getByLabel('Observações').fill('Comprada por um estratégico');
    await dialogo.getByRole('button', { name: 'Registrar saída' }).click();
    await expect(dialogo).toBeHidden();

    const aviso = page.getByRole('region', { name: 'Acompanhamento encerrado' });
    await expect(aviso).toContainText('15/07/2026');
    await expect(aviso).toContainText('Venda (M&A ou secundária)');
    await expect(page.getByRole('button', { name: 'Adicionar indicador' })).toHaveCount(0);

    // No reporting link survives the exit: neither a new one nor the history.
    await page.getByRole('button', { name: 'Mais ações' }).click();
    await expect(page.getByRole('menuitem', { name: 'Desfazer saída' })).toBeVisible();
    await expect(page.getByRole('menuitem', { name: 'Links anteriores' })).toHaveCount(0);
    await page.keyboard.press('Escape');

    const monitoradas = page.getByRole('region', { name: /startups monitoradas/ });
    const encerradas = page.getByRole('region', { name: /startups encerradas/ });

    // The exit month still counts: the startup usually reported it.
    await page.goto(`/portfolio?month=7&year=${CENARIO.periodo.ano}`);
    await expect(monitoradas.getByRole('link', { name: nome, exact: true })).toBeVisible();

    // From the next month on it is no longer tracked — but still one click away.
    await page.goto(`/portfolio?month=8&year=${CENARIO.periodo.ano}`);
    await expect(monitoradas).toBeVisible();
    await expect(monitoradas.getByRole('link', { name: nome, exact: true })).toHaveCount(0);
    await encerradas.getByRole('link', { name: nome, exact: true }).click();
    await expect(page.getByRole('heading', { level: 1, name: nome })).toBeVisible();
  });
});
