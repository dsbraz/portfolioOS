import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';

import { MeetingFormDialog } from './meeting-form-dialog';

describe('MeetingFormDialog', () => {
  let component: MeetingFormDialog;
  let fixture: ComponentFixture<MeetingFormDialog>;
  const dialogRefSpy = { close: vi.fn() };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MeetingFormDialog],
      providers: [
        provideNoopAnimations(),
        { provide: MatDialogRef, useValue: dialogRefSpy },
        { provide: MAT_DIALOG_DATA, useValue: {} },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(MeetingFormDialog);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create in add mode', () => {
    expect(component).toBeTruthy();
    expect(component.isEditMode).toBe(false);
  });

  it('should not submit when form is invalid', () => {
    dialogRefSpy.close.mockClear();
    component.onSubmit();
    expect(dialogRefSpy.close).not.toHaveBeenCalled();
  });

  it('should close dialog on cancel', () => {
    dialogRefSpy.close.mockClear();
    component.onCancel();
    expect(dialogRefSpy.close).toHaveBeenCalledWith();
  });
});
