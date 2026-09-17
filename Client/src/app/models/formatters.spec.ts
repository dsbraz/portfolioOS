import {
  formatCurrencyBRL,
  formatDateTime,
  formatIsoDate,
  formatInteger,
  formatPercent,
} from './formatters';

// `Intl` separates the symbol from the number with a NON-BREAKING space (U+00A0),
// so "R$" is never orphaned at the end of a line. Writing a regular space here
// would make the test fail over an invisible character.
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

  // A bare ISO date is parsed as UTC. In a negative timezone — Brazil's case —
  // that yields the previous day, and a meeting on 01/07 showed up as 30/06.
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

  // Zero is data, not absence. A `!value` instead of `== null` would make the
  // zero revenue of a bad month disappear from the screen.
  it('should treat zero as a value, not as absence', () => {
    expect(formatCurrencyBRL(0)).toBe(`R$${NBSP}0,00`);
    expect(formatPercent(0)).toBe('0%');
    expect(formatInteger(0)).toBe('0');
  });
});
