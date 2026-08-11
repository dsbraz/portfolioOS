/**
 * Formatação de apresentação, compartilhada entre páginas e diálogos.
 *
 * Retornam `null` para valor ausente em vez de um traço: quem exibe decide como
 * representar o vazio — uma tabela usa "-", a vista de leitura usa um traço com
 * texto alternativo para leitor de tela. Embutir o símbolo aqui tiraria essa
 * escolha de quem tem o contexto.
 */

const MOEDA = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' });

const DECIMAL = new Intl.NumberFormat('pt-BR', {
  minimumFractionDigits: 0,
  maximumFractionDigits: 2,
});

export function formatCurrencyBRL(value: number | null | undefined): string | null {
  if (value == null) return null;
  return MOEDA.format(value);
}

export function formatPercent(value: number | null | undefined): string | null {
  if (value == null) return null;
  return `${DECIMAL.format(value)}%`;
}

export function formatInteger(value: number | null | undefined): string | null {
  if (value == null) return null;
  return DECIMAL.format(value);
}

/** Data ISO (`YYYY-MM-DD`) para `dd/MM/yyyy`. */
export function formatIsoDate(value: string | null | undefined): string | null {
  if (!value) return null;
  // `T00:00:00` mantém a data no fuso local: sem isso o ISO puro é lido como
  // UTC e a data volta um dia em fusos negativos, que é o caso do Brasil.
  const date = new Date(`${value}T00:00:00`);
  if (Number.isNaN(date.getTime())) return null;
  return date.toLocaleDateString('pt-BR');
}
