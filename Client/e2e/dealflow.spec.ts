import { expect, test } from '@playwright/test';

import { criarNegocioViaApi, entrarComoOperador, loginViaApi } from './support/app';

/**
 * The board, driven the way a person drives it.
 *
 * The unit spec can only dispatch a synthetic drop event; here the pointer
 * actually drags, which is the only way to know the CDK wiring survives — and
 * the only way to catch a broken drop target.
 *
 * The board has no seeded scenario (the demo seed covers the AI flows), so each
 * spec plants its own deal through the API: fast, and named uniquely so one
 * spec never sees another's card.
 */
test.describe('dealflow', () => {
  let empresa: string;

  test.beforeEach(async ({ page, request }, testInfo) => {
    const token = await loginViaApi(request);
    empresa = `E2E ${testInfo.title.slice(0, 12)} ${Date.now()}`;
    await criarNegocioViaApi(request, token, empresa);

    await entrarComoOperador(page, token);
    await page.goto('/dealflow');
    await expect(page.getByRole('heading', { name: 'Dealflow' })).toBeVisible();
  });

  test('move um negócio entre estágios arrastando de verdade', async ({ page }) => {
    const card = page.getByRole('button', { name: `Abrir negócio ${empresa}` });
    await expect(card).toBeVisible();

    const origem = await card.boundingBox();
    // Índice 3 = Comite, na ordem declarada em `DealStage`.
    const destino = await page.locator('.kanban-column').nth(3).boundingBox();
    expect(origem && destino).toBeTruthy();

    // O CDK exige movimento em passos: um único `mouse.move` não vence o
    // limiar que inicia o arrasto.
    await page.mouse.move(origem!.x + origem!.width / 2, origem!.y + origem!.height / 2);
    await page.mouse.down();
    for (let passo = 1; passo <= 10; passo++) {
      await page.mouse.move(
        origem!.x + ((destino!.x + destino!.width / 2 - origem!.x) * passo) / 10,
        origem!.y + ((destino!.y + 120 - origem!.y) * passo) / 10,
      );
    }
    await page.mouse.up();

    // Persistiu: recarregar traz o card no estágio novo. Se o PATCH tivesse
    // falhado, o board teria ressincronizado de volta ao estágio antigo.
    await page.reload();
    await expect(
      page.locator('.kanban-column').nth(3).getByRole('button', {
        name: `Abrir negócio ${empresa}`,
      }),
    ).toBeVisible();
  });

  test('o card é operável por teclado, sem depender do mouse', async ({ page }) => {
    const card = page.getByRole('button', { name: `Abrir negócio ${empresa}` });
    await card.focus();
    await expect(card).toBeFocused();

    await page.keyboard.press('Enter');

    await expect(page.getByRole('dialog')).toBeVisible();
  });
});
