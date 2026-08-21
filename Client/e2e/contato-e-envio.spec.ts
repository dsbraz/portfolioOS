import { expect, test } from '@playwright/test';

import {
  CENARIO,
  abrirInvestida,
  entrarComoOperador,
  loginViaApi,
} from './support/app';

/**
 * The contact rules, exercised through the screens that enforce them.
 *
 * The dangerous case is not a rejected form — it is a number that is ACCEPTED
 * as the wrong person. `(415) 555-1234` used to gain a `+55` by guess and land
 * on a stranger's line in Paraná, carrying write access to the period.
 */
test.describe('cadastro de contato e canais de envio', () => {
  test.beforeEach(async ({ page, request }) => {
    await entrarComoOperador(page, await loginViaApi(request));
  });

  async function abrirAbaExecutivos(page: import('@playwright/test').Page) {
    await abrirInvestida(page, CENARIO.auditada);
    await page.getByRole('tab', { name: /Executivos/ }).click();
  }

  test('recusa telefone sem código do país e aceita o mesmo número com prefixo', async ({
    page,
  }) => {
    await abrirAbaExecutivos(page);
    await page.getByRole('button', { name: 'Adicionar executivo' }).click();
    const dialogo = page.getByRole('dialog');

    await dialogo.getByLabel('Nome').fill('John Miller');
    await dialogo.getByLabel('Telefone').fill('(415) 555-1234');
    await dialogo.getByRole('button', { name: 'Adicionar' }).click();

    // Recusado — e dizendo o porquê, no campo.
    await expect(dialogo).toBeVisible();
    await expect(
      dialogo.getByText('Informe o telefone com o código do país'),
    ).toBeVisible();

    // O mesmo número, agora inequívoco, é aceito.
    await dialogo.getByLabel('Telefone').fill('+1 415 555 1234');
    await dialogo.getByRole('button', { name: 'Adicionar' }).click();
    await expect(dialogo).toBeHidden();

    // Guardado em E.164, a forma única que todo consumidor lê.
    await expect(page.getByRole('cell', { name: '+14155551234' })).toBeVisible();
  });

  test('o painel oferece WhatsApp primeiro, e-mail como alternativa, e bloqueia quem não tem contato', async ({
    page,
  }) => {
    await abrirInvestida(page, CENARIO.auditada);
    await page.getByRole('button', { name: 'Adicionar indicador' }).click();

    const dialogo = page.getByRole('dialog');
    await dialogo.getByRole('radio', { name: 'Gerar link para a investida' }).click();
    await dialogo.getByRole('button', { name: 'Gerar link', exact: true }).click();

    // Ana tem os dois canais — e o WhatsApp vem primeiro, sempre.
    const acoes = dialogo.getByRole('link', { name: /^Enviar por/ });
    await expect(acoes.first()).toHaveAttribute(
      'aria-label',
      `Enviar por WhatsApp para ${CENARIO.executivoCompleto}`,
    );

    // O envio é um href real, presente ANTES de qualquer clique: um agente lê
    // o destino em vez de precisar clicar para descobri-lo.
    const whatsapp = dialogo.getByRole('link', {
      name: `Enviar por WhatsApp para ${CENARIO.executivoCompleto}`,
    });
    await expect(whatsapp).toHaveAttribute('href', /^https:\/\/wa\.me\/55\d+\?text=/);

    // Bruno não tem telefone: alcançável só por e-mail.
    const email = dialogo.getByRole('link', {
      name: `Enviar por e-mail para ${CENARIO.executivoSoEmail}`,
    });
    await expect(email).toHaveAttribute('href', /^mailto:.+\?subject=/);
    await expect(
      dialogo.getByRole('link', {
        name: `Enviar por WhatsApp para ${CENARIO.executivoSoEmail}`,
      }),
    ).toHaveCount(0);

    // Carla não tem nenhum: impedida, com o motivo visível.
    await expect(dialogo.getByText(CENARIO.executivoSemContato)).toBeVisible();
    await expect(dialogo.getByText('Sem canal de envio')).toBeVisible();
  });
});
