import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';

import { BoardMeeting } from '../../../models/board-meeting.model';
import { MeetingFormDialog } from './meeting-form-dialog';

describe('MeetingFormDialog em modo leitura', () => {
  // Aqui era o pior caso: quatro textareas de texto corrido, todas herdando a
  // cor de controle inativo (2,46:1) por causa do `form.disable()`.
  it('should render the record as text instead of disabled form controls', async () => {
    const reuniao = {
      meeting_date: '2026-07-01',
      participants: 'Ana, Bruno',
      summary: 'Revisão do trimestre.',
      attention_points: null,
      next_steps: '',
    } as unknown as BoardMeeting;

    await TestBed.configureTestingModule({
      imports: [MeetingFormDialog],
      providers: [
        provideNoopAnimations(),
        { provide: MatDialogRef, useValue: { close: vi.fn() } },
        { provide: MAT_DIALOG_DATA, useValue: { meeting: reuniao, readonly: true } },
      ],
    }).compileComponents();

    const fixture = TestBed.createComponent(MeetingFormDialog);
    fixture.detectChanges();
    await fixture.whenStable();
    const el = fixture.nativeElement as HTMLElement;

    expect(el.querySelector('form')).toBeNull();
    expect(el.querySelectorAll('input, textarea').length).toBe(0);
    // A data ISO cai um dia se for lida como UTC; o Brasil é fuso negativo.
    expect(el.textContent).toContain('01/07/2026');
    expect(el.textContent).toContain('Revisão do trimestre.');
    expect(el.querySelectorAll('.read-value--empty').length).toBe(2);
  });
});

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
