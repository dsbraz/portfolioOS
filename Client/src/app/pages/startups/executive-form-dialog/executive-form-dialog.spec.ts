import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';

import { Executive } from '../../../models/executive.model';
import { ExecutiveFormDialog } from './executive-form-dialog';

describe('ExecutiveFormDialog in read mode', () => {
  it('should render the record as text instead of disabled form controls', async () => {
    const executive = {
      name: 'Ana Ribeiro',
      role: 'CEO',
      email: 'ana@cardume.com.br',
      phone: null,
      linkedin: '',
    } as unknown as Executive;

    await TestBed.configureTestingModule({
      imports: [ExecutiveFormDialog],
      providers: [
        provideNoopAnimations(),
        { provide: MatDialogRef, useValue: { close: vi.fn() } },
        { provide: MAT_DIALOG_DATA, useValue: { executive, readonly: true } },
      ],
    }).compileComponents();

    const fixture = TestBed.createComponent(ExecutiveFormDialog);
    fixture.detectChanges();
    await fixture.whenStable();
    const el = fixture.nativeElement as HTMLElement;

    expect(el.querySelector('form')).toBeNull();
    expect(el.querySelectorAll('input, textarea').length).toBe(0);
    expect(el.textContent).toContain('Ana Ribeiro');
    expect(el.textContent).toContain('ana@cardume.com.br');
    expect(el.querySelectorAll('.read-value--empty').length).toBe(2);
    expect(el.textContent).toContain('Link mensal por e-mail');
    expect(el.textContent).toContain('Não recebe');
  });
});

describe('ExecutiveFormDialog', () => {
  let component: ExecutiveFormDialog;
  let fixture: ComponentFixture<ExecutiveFormDialog>;
  const dialogRefSpy = { close: vi.fn() };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ExecutiveFormDialog],
      providers: [
        provideNoopAnimations(),
        { provide: MatDialogRef, useValue: dialogRefSpy },
        { provide: MAT_DIALOG_DATA, useValue: {} },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(ExecutiveFormDialog);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should not submit when name is empty', () => {
    dialogRefSpy.close.mockClear();
    component.onSubmit();
    expect(dialogRefSpy.close).not.toHaveBeenCalled();
  });

  it('should submit with valid data', () => {
    dialogRefSpy.close.mockClear();
    component.form.patchValue({ name: 'Joao Silva', role: 'CEO' });
    component.onSubmit();
    expect(dialogRefSpy.close).toHaveBeenCalledWith(
      expect.objectContaining({ name: 'Joao Silva', role: 'CEO' }),
    );
  });

  it('should refuse the monthly link without an e-mail', () => {
    dialogRefSpy.close.mockClear();
    component.form.patchValue({ name: 'Ana Souza', receives_monthly_report: true });
    fixture.detectChanges();

    component.onSubmit();

    expect(dialogRefSpy.close).not.toHaveBeenCalled();
    const alert = fixture.nativeElement.querySelector('[role="alert"]');
    expect(alert.textContent).toContain('Informe o e-mail');
  });

  it('should submit the monthly link choice with an e-mail', () => {
    dialogRefSpy.close.mockClear();
    component.form.patchValue({
      name: 'Ana Souza',
      email: 'ana@payface.com',
      receives_monthly_report: true,
    });

    component.onSubmit();

    expect(dialogRefSpy.close).toHaveBeenCalledWith(
      expect.objectContaining({ receives_monthly_report: true }),
    );
  });

  it.each(['(415) 555-1234', '+12'])('should refuse the phone %s', (phone) => {
    dialogRefSpy.close.mockClear();
    component.form.patchValue({ name: 'John Miller', phone });

    component.onSubmit();

    expect(component.form.controls.phone.hasError('pattern')).toBe(true);
    expect(dialogRefSpy.close).not.toHaveBeenCalled();
  });

  it('should accept a foreign number that carries its prefix', () => {
    dialogRefSpy.close.mockClear();
    component.form.patchValue({ name: 'John Miller', phone: '+1 415 555 1234' });

    component.onSubmit();

    expect(dialogRefSpy.close).toHaveBeenCalledWith(
      expect.objectContaining({ phone: '+1 415 555 1234' }),
    );
  });

  it('should keep an empty phone valid — an executive may have none', () => {
    dialogRefSpy.close.mockClear();
    component.form.patchValue({ name: 'Joao Silva', phone: '' });

    component.onSubmit();

    expect(dialogRefSpy.close).toHaveBeenCalledWith(
      expect.objectContaining({ phone: '' }),
    );
  });
});
