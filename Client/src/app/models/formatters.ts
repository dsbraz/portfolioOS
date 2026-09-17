/**
 * Presentation formatting, shared across pages and dialogs.
 *
 * They return `null` for a missing value instead of a dash: the caller decides how
 * to represent emptiness — a table uses "-", the read view uses a dash with
 * alternative text for screen readers. Baking the symbol in here would take that
 * choice away from whoever has the context.
 */

import { MONTH_LABELS } from './monthly-indicator.model';

const CURRENCY = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' });

const DECIMAL = new Intl.NumberFormat('pt-BR', {
  minimumFractionDigits: 0,
  maximumFractionDigits: 2,
});

const DATE_TIME = new Intl.DateTimeFormat('pt-BR', {
  dateStyle: 'short',
  timeStyle: 'short',
});

export function formatCurrencyBRL(value: number | null | undefined): string | null {
  if (value == null) return null;
  return CURRENCY.format(value);
}

export function formatPercent(value: number | null | undefined): string | null {
  if (value == null) return null;
  return `${DECIMAL.format(value)}%`;
}

export function formatInteger(value: number | null | undefined): string | null {
  if (value == null) return null;
  return DECIMAL.format(value);
}

/** Reference period as `Mmm/YYYY` (e.g. `Jan/2026`). */
export function formatPeriod(month: number, year: number): string {
  return `${MONTH_LABELS[month]}/${year}`;
}

/** ISO date (`YYYY-MM-DD`) to `dd/MM/yyyy`. */
export function formatIsoDate(value: string | null | undefined): string | null {
  if (!value) return null;
  // `T00:00:00` keeps the date in the local time zone: without it the bare ISO is
  // read as UTC and the date shifts back a day in negative offsets, as in Brazil.
  const date = new Date(`${value}T00:00:00`);
  if (Number.isNaN(date.getTime())) return null;
  return date.toLocaleDateString('pt-BR');
}

/** ISO timestamp as `dd/MM/yyyy, HH:mm` in the user's local timezone. */
export function formatDateTime(value: string | null | undefined): string | null {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return null;
  return DATE_TIME.format(date);
}
