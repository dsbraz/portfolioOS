import {
  formatCurrencyBRL,
  formatDateTime,
  formatIsoDate,
  formatInteger,
  formatPercent,
} from './formatters';

// `Intl` separa o símbolo do número com espaço NÃO SEPARÁVEL (U+00A0), para que
// "R$" nunca fique órfão no fim da linha. Escrever um espaço comum aqui faria o
// teste falhar por um caractere invisível.
const NBSP = ' ';

describe('formatters', () => {
  it('should format currency in pt-BR', () => {
    expect(formatCurrencyBRL(1250000)).toBe(`R$${NBSP}1.250.000,00`);
  });

  it('should format negative currency for burn', () => {
    expect(formatCurrencyBRL(-138200)).toBe(`-R$${NBSP}138.200,00`);
  });

  it('should format percent without trailing zeros', () => {
    expect(formatPercent(72)).toBe('72%');
    expect(formatPercent(72.5)).toBe('72,5%');
  });

  it('should format integers', () => {
    expect(formatInteger(19)).toBe('19');
  });

  // O ISO puro é interpretado como UTC. Em fuso negativo — o caso do Brasil —
  // isso devolve o dia anterior, e uma reunião de 01/07 aparecia como 30/06.
  it('should keep an ISO date on its own day in a negative timezone', () => {
    expect(formatIsoDate('2026-07-01')).toBe('01/07/2026');
  });

  // A timestamp without an offset is read as local time, so this assertion
  // does not depend on the timezone the tests run in.
  it('should format a timestamp as short date and time in pt-BR', () => {
    expect(formatDateTime('2026-07-01T14:30:00')).toBe('01/07/2026, 14:30');
  });

  // `Intl.DateTimeFormat#format` throws `RangeError` on an invalid date, which
  // would take down the whole table instead of a single cell.
  it('should return null for an unparseable timestamp instead of throwing', () => {
    expect(formatDateTime('not-a-date')).toBeNull();
  });

  it('should return null for absent values so the caller decides how to show it', () => {
    expect(formatCurrencyBRL(null)).toBeNull();
    expect(formatPercent(null)).toBeNull();
    expect(formatInteger(null)).toBeNull();
    expect(formatIsoDate(null)).toBeNull();
    expect(formatIsoDate('')).toBeNull();
    expect(formatDateTime(null)).toBeNull();
    expect(formatDateTime(undefined)).toBeNull();
    expect(formatDateTime('')).toBeNull();
  });

  // Zero é dado, não ausência. Um `!value` no lugar de `== null` faria a receita
  // zerada de um mês ruim desaparecer da tela.
  it('should treat zero as a value, not as absence', () => {
    expect(formatCurrencyBRL(0)).toBe(`R$${NBSP}0,00`);
    expect(formatPercent(0)).toBe('0%');
    expect(formatInteger(0)).toBe('0');
  });
});
