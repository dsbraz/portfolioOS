import { FormBuilder } from '@angular/forms';

import {
  INDICATOR_LIMITS,
  buildReportedIndicatorForm,
  futurePeriodValidator,
  integerValidator,
} from './indicator-form';

const fb = new FormBuilder();

describe('buildReportedIndicatorForm — the shared reportable contract', () => {
  const { MIN_MONEY, MAX_MONEY, MAX_PCT, MAX_HEADCOUNT } = INDICATOR_LIMITS;

  // Each money/pct/headcount field, with the boundary values it must accept and
  // reject. Because the admin dialog and the public form both build from this
  // one factory, asserting the boundaries here IS the RFC-001 §6 parity check:
  // there is a single source, so the two forms cannot diverge.
  const boundaries: { field: string; accept: number[]; reject: number[] }[] = [
    { field: 'total_revenue', accept: [MIN_MONEY, 0, MAX_MONEY], reject: [MIN_MONEY - 1000, MAX_MONEY + 1000] },
    { field: 'cash_balance', accept: [MIN_MONEY, 0, MAX_MONEY], reject: [MIN_MONEY - 1000, MAX_MONEY + 1000] },
    { field: 'ebitda_burn', accept: [MIN_MONEY, 0, MAX_MONEY], reject: [MIN_MONEY - 1000, MAX_MONEY + 1000] },
    { field: 'recurring_revenue_pct', accept: [0, MAX_PCT], reject: [-1, MAX_PCT + 1] },
    { field: 'gross_margin_pct', accept: [0, MAX_PCT], reject: [-1, MAX_PCT + 1] },
    { field: 'headcount', accept: [0, 25, MAX_HEADCOUNT], reject: [-1, MAX_HEADCOUNT + 1, 3.5] },
  ];

  for (const { field, accept, reject } of boundaries) {
    for (const value of accept) {
      it(`accepts ${field} = ${value}`, () => {
        const control = buildReportedIndicatorForm(fb).get(field)!;
        control.setValue(value);
        expect(control.valid, `${field}=${value} should be valid`).toBe(true);
      });
    }
    for (const value of reject) {
      it(`rejects ${field} = ${value}`, () => {
        const control = buildReportedIndicatorForm(fb).get(field)!;
        control.setValue(value);
        expect(control.valid, `${field}=${value} should be invalid`).toBe(false);
      });
    }
  }

  it('treats every reportable field as optional (absence is valid)', () => {
    const form = buildReportedIndicatorForm(fb);
    expect(form.valid).toBe(true);
  });

  it('does not carry the fund note — comments is admin-only', () => {
    expect(buildReportedIndicatorForm(fb).get('comments')).toBeNull();
  });
});

describe('integerValidator', () => {
  it('leaves absence valid', () => {
    for (const empty of [null, undefined, '']) {
      const control = fb.control(empty);
      expect(integerValidator(control)).toBeNull();
    }
  });

  it('rejects a fractional value and accepts a whole one', () => {
    expect(integerValidator(fb.control(3.5))).toEqual({ integer: true });
    expect(integerValidator(fb.control(10))).toBeNull();
  });
});

describe('futurePeriodValidator', () => {
  it('accepts the current month and rejects the next', () => {
    const now = new Date();
    const current = fb.group({ month: [now.getMonth() + 1], year: [now.getFullYear()] });
    expect(futurePeriodValidator(current)).toBeNull();

    const nextMonth = now.getMonth() === 11 ? 1 : now.getMonth() + 2;
    const nextYear = now.getMonth() === 11 ? now.getFullYear() + 1 : now.getFullYear();
    const ahead = fb.group({ month: [nextMonth], year: [nextYear] });
    expect(futurePeriodValidator(ahead)).toEqual({ futurePeriod: true });
  });

  it('is inconclusive (null) until both month and year are present', () => {
    expect(futurePeriodValidator(fb.group({ month: [null], year: [2026] }))).toBeNull();
  });
});
