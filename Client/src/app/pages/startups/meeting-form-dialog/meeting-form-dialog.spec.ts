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

  it('should not submit when form is invalid', () => {
    dialogRefSpy.close.mockClear();
    component.onSubmit();
    expect(dialogRefSpy.close).not.toHaveBeenCalled();
  });

  it('should submit with valid data', () => {
    dialogRefSpy.close.mockClear();
    component.form.patchValue({
      meeting_date: new Date('2026-02-15'),
      participants: 'Joao, Maria',
      summary: 'Reuniao mensal',
    });
    component.onSubmit();
    expect(dialogRefSpy.close).toHaveBeenCalledWith(
      expect.objectContaining({
        meeting_date: '2026-02-15',
        participants: 'Joao, Maria',
        summary: 'Reuniao mensal',
      }),
    );
  });

  it('should close dialog on cancel', () => {
    dialogRefSpy.close.mockClear();
    component.onCancel();
    expect(dialogRefSpy.close).toHaveBeenCalledWith();
  });
});
