import { expect, test } from '@playwright/test';

import {
  CENARIO,
  abrirInvestida,
  entrarComoOperador,
  loginViaApi,
} from './support/app';

/**
 * The one journey nothing else covers end to end: the reporting link crosses
 * the authenticated/anonymous boundary.
 *
 * The admin mints it, an investee with NO session fills the public form, and
 * the value comes back into the fund's table — with the fund's private note
 * untouched. Unit tests cover each half; only this proves the seam.
 */
test.describe('ciclo do link de indicador', () => {
  test.beforeEach(async ({ page, request }) => {
    await entrarComoOperador(page, await loginViaApi(request));
  });

  test('admin gera o link, a investida reporta sem sessão, e o dado volta para o fundo', async ({
    page,
    browser,
  }) => {
    await abrirInvestida(page, CENARIO.atrasada);

    // --- 1. O fundo gera o link para o período em aberto -------------------
    await page.getByRole('button', { name: 'Adicionar indicador' }).click();
    const dialogo = page.getByRole('dialog');
    await expect(dialogo).toBeVisible();

    await dialogo.getByRole('radio', { name: 'Gerar link para a investida' }).click();
    await dialogo.getByRole('button', { name: 'Gerar link', exact: true }).click();

    // O link precisa estar visível como TEXTO — nenhum passo do fluxo pode
    // depender da área de transferência (PRD-001 6.5).
    const urlDoFormulario = await dialogo.locator('.link-text').innerText();
    expect(urlDoFormulario).toContain('/monthly-indicator/');

    // --- 2. A investida abre o link SEM sessão ----------------------------
    const contextoAnonimo = await browser.newContext();
    const paginaPublica = await contextoAnonimo.newPage();
    const caminho = new URL(urlDoFormulario).pathname;
    await paginaPublica.goto(caminho);

    // Identifica quem está reportando e qual período, antes de qualquer campo.
    await expect(paginaPublica.getByText(CENARIO.atrasada)).toBeVisible();

    // A anotação do fundo é interna: não pode aparecer no formulário público.
    await expect(paginaPublica.getByText('Comentários do fundo')).toHaveCount(0);

    // --- 3. A investida preenche e envia ----------------------------------
    await paginaPublica.getByLabel('Receita do mês').fill('4210050');
    await paginaPublica.getByLabel('Headcount').fill('33');
    await paginaPublica
      .getByLabel('Destaques do mês')
      .fill('Primeiro contrato enterprise assinado.');
    await paginaPublica.getByRole('button', { name: /Enviar/ }).click();

    await expect(paginaPublica.getByText('Relatório enviado')).toBeVisible();
    await contextoAnonimo.close();

    // --- 4. O dado chega na tabela do fundo -------------------------------
    await abrirInvestida(page, CENARIO.atrasada);
    const linhaDoPeriodo = page.getByRole('row', { name: /Jul\/2026/ });
    await expect(linhaDoPeriodo).toBeVisible();
    // A máscara pt-BR: 4210050 centavos viram R$ 42.100,50.
    await expect(linhaDoPeriodo).toContainText('42.100,50');
    await expect(linhaDoPeriodo).toContainText('33');
  });

  test('gerar o link duas vezes devolve o mesmo link, sem duplicar o período', async ({
    page,
  }) => {
    await abrirInvestida(page, CENARIO.auditada);

    const gerar = async (): Promise<string> => {
      await page.getByRole('button', { name: 'Adicionar indicador' }).click();
      const dialogo = page.getByRole('dialog');
      await dialogo.getByRole('radio', { name: 'Gerar link para a investida' }).click();
      await dialogo.getByRole('button', { name: 'Gerar link', exact: true }).click();
      const url = await dialogo.locator('.link-text').innerText();
      // `exact`: o cabeçalho do diálogo também tem um "Fechar diálogo" (o X).
      await dialogo.getByRole('button', { name: 'Fechar', exact: true }).click();
      return url;
    };

    const primeiro = await gerar();
    const segundo = await gerar();

    // Um link por (investida, período) é o contrato — inclusive quando alguém
    // clica de novo por engano.
    expect(segundo).toBe(primeiro);
  });
});
