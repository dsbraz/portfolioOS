import { AbstractControl, FormBuilder, ValidationErrors, Validators } from '@angular/forms';

/**
 * Single client-side source of the reportable-indicator contract.
 *
 * The backend is the authority on the limits; these mirror it and must stay in
 * step with `Server/app/domain/schemas/monthly_indicator.py:11-16`
 * (`_MIN_MONEY` / `_MAX_MONEY` / `_MAX_PCT` / `_MAX_HEADCOUNT`). The admin dialog
 * and the public report form both build their reportable zone through
 * `buildReportedIndicatorForm`, so a limit cannot drift between the two — that
 * divergence is what let a -999-billion value reach the database before.
 */
export const INDICATOR_LIMITS = {
  MIN_MONEY: -9_999_999_999_999.99,
  MAX_MONEY: 9_999_999_999_999.99,
  MAX_PCT: 99_999.99,
  MIN_HEADCOUNT: 0,
  // Upper bound of the Integer (int32) column behind headcount; a larger value
  // cannot be stored and the API refuses it with 422.
  MAX_HEADCOUNT: 2_147_483_647,
} as const;

/** Rejects a non-integer headcount, while leaving absence (null/empty) valid. */
export function integerValidator(control: AbstractControl): ValidationErrors | null {
  const value = control.value;
  if (value === null || value === undefined || value === '') return null;
  return Number.isInteger(Number(value)) ? null : { integer: true };
}

/**
 * Group validator: a period at or before the current month is valid; a period
 * ahead of it is not. Shared by every entry point so the rule has one source.
 */
export function futurePeriodValidator(group: AbstractControl): ValidationErrors | null {
  const month = group.get('month')?.value;
  const year = group.get('year')?.value;
  if (!month || !year) return null;
  const now = new Date();
  if (year > now.getFullYear() || (year === now.getFullYear() && month > now.getMonth() + 1)) {
    return { futurePeriod: true };
  }
  return null;
}

/**
 * The reportable zone shared by the admin dialog and the public form: the eight
 * fields reported for a period, with identical validators. The fund note
 * (`comments`) is deliberately absent — it is an admin-only annotation, so each
 * caller adds it around this group rather than inside it.
 *
 * The return type is inferred (a typed `FormGroup`) so consumers keep
 * field-level control typing in their templates.
 */
export function buildReportedIndicatorForm(fb: FormBuilder) {
  const { MIN_MONEY, MAX_MONEY, MAX_PCT, MIN_HEADCOUNT, MAX_HEADCOUNT } = INDICATOR_LIMITS;
  return fb.group({
    total_revenue: [null as number | null, [Validators.min(MIN_MONEY), Validators.max(MAX_MONEY)]],
    cash_balance: [null as number | null, [Validators.min(MIN_MONEY), Validators.max(MAX_MONEY)]],
    ebitda_burn: [null as number | null, [Validators.min(MIN_MONEY), Validators.max(MAX_MONEY)]],
    recurring_revenue_pct: [null as number | null, [Validators.min(0), Validators.max(MAX_PCT)]],
    gross_margin_pct: [null as number | null, [Validators.min(0), Validators.max(MAX_PCT)]],
    headcount: [
      null as number | null,
      [Validators.min(MIN_HEADCOUNT), Validators.max(MAX_HEADCOUNT), integerValidator],
    ],
    achievements: [''],
    challenges: [''],
  });
}
