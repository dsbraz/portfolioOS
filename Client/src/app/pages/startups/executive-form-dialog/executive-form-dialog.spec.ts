import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';

import { Executive } from '../../../models/executive.model';
import { ExecutiveFormDialog } from './executive-form-dialog';

describe('ExecutiveFormDialog em modo leitura', () => {
  it('should render the record as text instead of disabled form controls', async () => {
    const executivo = {
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
        { provide: MAT_DIALOG_DATA, useValue: { executive: executivo, readonly: true } },
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
});
