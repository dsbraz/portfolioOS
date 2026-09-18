import { expect, test } from '@playwright/test';

import { OPERATOR, tokenGuardadoNoNavegador } from './support/app';

/**
 * The gate. Every other spec plants a token and skips this screen, so this is
 * the one place the real login path is exercised — and the one place we prove
 * that an anonymous visitor cannot reach the fund's data.
 */
test.describe('autenticação', () => {
  test('entra pela tela de login e chega ao monitoramento', async ({ page }) => {
    await page.goto('/login');

    await page.getByRole('textbox', { name: 'Usuário' }).fill(OPERATOR.username);
    await page.getByRole('textbox', { name: 'Senha' }).fill(OPERATOR.password);
    await page.getByRole('button', { name: 'Entrar' }).click();

    await expect(page).toHaveURL(/\/portfolio/);
    expect(await tokenGuardadoNoNavegador(page)).toBeTruthy();
  });

  test('recusa credencial errada sem revelar o que falhou', async ({ page }) => {
    await page.goto('/login');

    await page.getByRole('textbox', { name: 'Usuário' }).fill(OPERATOR.username);
    await page.getByRole('textbox', { name: 'Senha' }).fill('senha-errada');
    await page.getByRole('button', { name: 'Entrar' }).click();

    await expect(page).toHaveURL(/\/login/);
    expect(await tokenGuardadoNoNavegador(page)).toBeNull();
  });

  test('visitante anônimo é levado ao login em vez de ver dados', async ({ page }) => {
    await page.goto('/portfolio');

    await expect(page).toHaveURL(/\/login/);
  });
});
