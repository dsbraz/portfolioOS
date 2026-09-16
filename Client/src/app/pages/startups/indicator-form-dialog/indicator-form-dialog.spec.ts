import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';

import { MonthlyIndicator } from '../../../models/monthly-indicator.model';
import { IndicatorFormDialog } from './indicator-form-dialog';

describe('IndicatorFormDialog in read mode', () => {
  const indicator = {
    month: 7,
    year: 2026,
    total_revenue: 767776.43,
    recurring_revenue_pct: 72,
    gross_margin_pct: null,
    cash_balance: 1262431.76,
    headcount: 19,
    ebitda_burn: -138199.76,
    achievements: 'Fechamos o contrato com a rede.',
    challenges: '',
    comments: null,
  } as unknown as MonthlyIndicator;

  let fixture: ComponentFixture<IndicatorFormDialog>;
  let el: HTMLElement;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [IndicatorFormDialog],
      providers: [
        provideNoopAnimations(),
        { provide: MatDialogRef, useValue: { close: vi.fn() } },
        { provide: MAT_DIALOG_DATA, useValue: { indicator, readonly: true } },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(IndicatorFormDialog);
    fixture.detectChanges();
    await fixture.whenStable();
    el = fixture.nativeElement;
  });

  // The point of the change. Read mode used to be the form with
  // `form.disable()`, and the value inherited the inactive-control color:
  // measured 2.46:1 in the light theme, against 18.7:1 for the label beside it.
  // WCAG exempts inactive components, so the audit did not flag it — but the
  // data was the entire content of the dialog.
  it('should render the record as text instead of disabled form controls', () => {
    expect(el.querySelector('app-read-view')).toBeTruthy();
    expect(el.querySelector('form')).toBeNull();
    expect(el.querySelectorAll('input, textarea, mat-select').length).toBe(0);
  });

  // Reading and editing must present the record with the same groups: the
  // sections the edit mode already has.
  it('should keep the quantitative and qualitative sections apart', () => {
    const titles = [...el.querySelectorAll('h3')].map(h => h.textContent?.trim());
    expect(titles).toEqual(['Quantitativos', 'Qualitativos']);

    const lists = el.querySelectorAll('dl');
    // Standalone period at the top, then the two groups.
    expect(lists.length).toBe(3);
    expect(lists[1].textContent).toContain('Receita do mês');
    expect(lists[2].textContent).toContain('Conquistas do mês');
  });

  it('should show the formatted values', () => {
    const text = el.textContent ?? '';
    expect(text).toContain('Jul/2026');
    expect(text).toContain('767.776,43');
    expect(text).toContain('72%');
    expect(text).toContain('Fechamos o contrato com a rede.');
  });

  // Null and blank text become the same "not provided": a textarea never
  // filled in arrives as an empty string and would render an empty value.
  it('should mark absent values as such, including blank text', () => {
    const empties = [...el.querySelectorAll('.read-value--empty')];
    expect(empties.length).toBe(3); // gross margin, challenges, comments
    expect(empties.every(v => v.querySelector('.visually-hidden')?.textContent?.trim() === 'Não informado')).toBe(true);
  });

  // Zero is data. A `||` instead of `== null` in the formatters would make the
  // month with zero cash — the most important one of all — vanish from the screen.
  it('should show a zero value instead of hiding it', async () => {
    TestBed.resetTestingModule();
    await TestBed.configureTestingModule({
      imports: [IndicatorFormDialog],
      providers: [
        provideNoopAnimations(),
        { provide: MatDialogRef, useValue: { close: vi.fn() } },
        {
          provide: MAT_DIALOG_DATA,
          useValue: { indicator: { ...indicator, cash_balance: 0 }, readonly: true },
        },
      ],
    }).compileComponents();

    const zeroed = TestBed.createComponent(IndicatorFormDialog);
    zeroed.detectChanges();
    await zeroed.whenStable();
    expect((zeroed.nativeElement as HTMLElement).textContent).toContain('0,00');
  });
});

describe('IndicatorFormDialog', () => {
  let component: IndicatorFormDialog;
  let fixture: ComponentFixture<IndicatorFormDialog>;
  const dialogRefSpy = { close: vi.fn() };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [IndicatorFormDialog],
      providers: [
        provideNoopAnimations(),
        { provide: MatDialogRef, useValue: dialogRefSpy },
        { provide: MAT_DIALOG_DATA, useValue: {} },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(IndicatorFormDialog);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should have default month and year', () => {
    const now = new Date();
    expect(component.form.value.month).toBe(now.getMonth() + 1);
    expect(component.form.value.year).toBe(now.getFullYear());
  });

  it('should close dialog on submit with form data', () => {
    component.form.patchValue({ month: 2, year: 2026, headcount: 10 });
    component.onSubmit();
    expect(dialogRefSpy.close).toHaveBeenCalledWith(
      expect.objectContaining({ month: 2, year: 2026, headcount: 10 }),
    );
  });

  // Regression: a focused `input[type=number]` has its value changed by the
  // mouse wheel. Scrolling the page over the form silently rewrote an
  // indicator — and an already-filled field is exactly what nobody rereads.
  it('should release focus from number inputs on wheel, so scrolling cannot change a value', () => {
    const numberInputs = fixture.nativeElement.querySelectorAll('input[type="number"]');
    expect(numberInputs.length).toBeGreaterThan(0);

    for (const input of numberInputs) {
      input.focus();
      expect(document.activeElement).toBe(input);

      input.dispatchEvent(new WheelEvent('wheel', { bubbles: true }));
      expect(document.activeElement).not.toBe(input);
    }
  });

  it('should close dialog without data on cancel', () => {
    dialogRefSpy.close.mockClear();
    component.onCancel();
    expect(dialogRefSpy.close).toHaveBeenCalledWith();
  });
});
