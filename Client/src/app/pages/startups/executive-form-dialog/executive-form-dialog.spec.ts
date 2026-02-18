import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';

import { ExecutiveFormDialog } from './executive-form-dialog';

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

  it('should create in add mode', () => {
    expect(component).toBeTruthy();
    expect(component.isEditMode).toBe(false);
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
    expect(dialogRefSpy.close).toHaveBeenCalled();
  });
});
