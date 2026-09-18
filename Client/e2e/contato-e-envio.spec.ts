import { expect, test } from '@playwright/test';

import {
  CENARIO,
  abrirInvestida,
  entrarComoOperador,
  gerarLinkDeIndicador,
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

  test('recusa telefone sem código do país e aceita o mesmo número com prefixo', async ({
    page,
  }) => {
    // Nome e número únicos por execução. O seed roda uma vez, quando o servidor
    // sobe, mas a suíte é rodada várias vezes contra o mesmo stack — com um
    // número fixo, a segunda execução acha duas células iguais e o Playwright
    // para por ambiguidade. Mesmo padrão do `dealflow.spec.ts`.
    const sufixo = `${Date.now()}`.slice(-7);
    const nome = `John Miller ${sufixo}`;
    const nacional = `(415) ${sufixo.slice(0, 3)}-${sufixo.slice(3)}`;
    const internacional = `+1 415 ${sufixo.slice(0, 3)} ${sufixo.slice(3)}`;
    const guardado = `+1415${sufixo}`;

    await abrirInvestida(page, CENARIO.auditada);
    await page.getByRole('tab', { name: /Executivos/ }).click();
    await page.getByRole('button', { name: 'Adicionar executivo' }).click();
    const dialogo = page.getByRole('dialog');

    await dialogo.getByLabel('Nome').fill(nome);
    await dialogo.getByLabel('Telefone').fill(nacional);
    await dialogo.getByRole('button', { name: 'Adicionar' }).click();

    // Recusado — e dizendo o porquê, no campo.
    await expect(dialogo).toBeVisible();
    await expect(
      dialogo.getByText('Informe o telefone com o código do país'),
    ).toBeVisible();

    // O mesmo número, agora inequívoco, é aceito.
    await dialogo.getByLabel('Telefone').fill(internacional);
    await dialogo.getByRole('button', { name: 'Adicionar' }).click();
    await expect(dialogo).toBeHidden();

    // Guardado em E.164, a forma única que todo consumidor lê.
    await expect(page.getByRole('cell', { name: guardado })).toBeVisible();
  });

  test('o painel oferece WhatsApp primeiro, e-mail como alternativa, e bloqueia quem não tem contato', async ({
    page,
  }) => {
    await abrirInvestida(page, CENARIO.auditada);
    const { dialogo } = await gerarLinkDeIndicador(page);

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
