import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';

import { IndicatorFormDialog } from './indicator-form-dialog';

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

  it('should create in add mode', () => {
    expect(component).toBeTruthy();
    expect(component.isEditMode).toBe(false);
  });

  it('should have default month and year', () => {
    const now = new Date();
    expect(component.form.value.month).toBe(now.getMonth() + 1);
    expect(component.form.value.year).toBe(now.getFullYear());
  });

  it('should close dialog on submit with form data', () => {
    component.form.patchValue({ month: 2, year: 2026, headcount: 10 });
    component.onSubmit();
    expect(dialogRefSpy.close).toHaveBeenCalled();
  });

  it('should close dialog without data on cancel', () => {
    dialogRefSpy.close.mockClear();
    component.onCancel();
    expect(dialogRefSpy.close).toHaveBeenCalledWith();
  });
});
