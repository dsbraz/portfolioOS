import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';

import { MonthlyIndicator } from '../../../models/monthly-indicator.model';
import { IndicatorFormDialog } from './indicator-form-dialog';

describe('IndicatorFormDialog em modo leitura', () => {
  const indicador = {
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
        { provide: MAT_DIALOG_DATA, useValue: { indicator: indicador, readonly: true } },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(IndicatorFormDialog);
    fixture.detectChanges();
    await fixture.whenStable();
    el = fixture.nativeElement;
  });

  // O ponto da mudança. Antes o modo leitura era o formulário com
  // `form.disable()`, e o valor herdava a cor de controle inativo: medi 2,46:1
  // no tema claro, contra 18,7:1 do rótulo ao lado. A WCAG isenta componentes
  // inativos, então a auditoria não acusava — mas o dado era o conteúdo inteiro
  // do diálogo.
  it('should render the record as text instead of disabled form controls', () => {
    expect(el.querySelector('app-read-view')).toBeTruthy();
    expect(el.querySelector('form')).toBeNull();
    expect(el.querySelectorAll('input, textarea, mat-select').length).toBe(0);
  });

  // Ler e editar precisam apresentar o registro com os mesmos grupos: são as
  // seções que o modo de edição já tem.
  it('should keep the quantitative and qualitative sections apart', () => {
    const titulos = [...el.querySelectorAll('h3')].map((h) => h.textContent?.trim());
    // The fund note is its own section, separate from the reportable zone.
    expect(titulos).toEqual(['Quantitativos', 'Qualitativos', 'Anotações do fundo']);

    const listas = el.querySelectorAll('dl');
    // Período solto no topo, depois os três grupos.
    expect(listas.length).toBe(4);
    expect(listas[1].textContent).toContain('Receita do mês');
    expect(listas[2].textContent).toContain('Conquistas do mês');
  });

  it('should show the formatted values', () => {
    const texto = el.textContent ?? '';
    expect(texto).toContain('Jul/2026');
    expect(texto).toContain('767.776,43');
    expect(texto).toContain('72%');
    expect(texto).toContain('Fechamos o contrato com a rede.');
  });

  // Nulo e texto em branco viram o mesmo "não informado": um textarea nunca
  // preenchido chega como string vazia e renderizaria um valor vazio.
  it('should mark absent values as such, including blank text', () => {
    const vazios = [...el.querySelectorAll('.read-value--empty')];
    expect(vazios.length).toBe(3); // margem bruta, desafios, comentários
    expect(
      vazios.every(
        (v) => v.querySelector('.visually-hidden')?.textContent?.trim() === 'Não informado',
      ),
    ).toBe(true);
  });

  // Zero é dado. Um `||` no lugar de `== null` nos formatadores faria o mês de
  // caixa zerado — o mais importante de todos — sumir da tela.
  it('should show a zero value instead of hiding it', async () => {
    TestBed.resetTestingModule();
    await TestBed.configureTestingModule({
      imports: [IndicatorFormDialog],
      providers: [
        provideNoopAnimations(),
        { provide: MatDialogRef, useValue: { close: vi.fn() } },
        {
          provide: MAT_DIALOG_DATA,
          useValue: { indicator: { ...indicador, cash_balance: 0 }, readonly: true },
        },
      ],
    }).compileComponents();

    const zerado = TestBed.createComponent(IndicatorFormDialog);
    zerado.detectChanges();
    await zerado.whenStable();
    expect((zerado.nativeElement as HTMLElement).textContent).toContain('0,00');
  });

  it('should preserve the qualitative labels used by read-only skills', () => {
    const labels = [...el.querySelectorAll('dt')].map((label) => label.textContent?.trim());

    expect(labels.slice(-3)).toEqual([
      'Conquistas do mês',
      'Desafios do mês',
      'Comentários do fundo',
    ]);
    expect(el.querySelector('mat-dialog-actions button')?.textContent?.trim()).toBe('Fechar');
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

  // Regressão: um `input[type=number]` focado tem seu valor alterado pela roda
  // do mouse. Rolar a página sobre o formulário reescrevia um indicador em
  // silêncio — e o campo já preenchido é justamente o que ninguém relê.
  it('should release focus from number inputs on wheel, so scrolling cannot change a value', () => {
    const numericos = fixture.nativeElement.querySelectorAll('input[type="number"]');
    expect(numericos.length).toBeGreaterThan(0);

    for (const input of numericos) {
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
