import { Component, inject, OnInit } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatButtonModule } from '@angular/material/button';
import { provideNativeDateAdapter } from '@angular/material/core';

import { BoardMeeting } from '../../../models/board-meeting.model';

export interface MeetingFormDialogData {
  meeting?: BoardMeeting;
}

@Component({
  selector: 'app-meeting-form-dialog',
  imports: [
    ReactiveFormsModule,
    MatDialogModule,
    MatFormFieldModule,
    MatInputModule,
    MatDatepickerModule,
    MatButtonModule,
  ],
  providers: [provideNativeDateAdapter()],
  templateUrl: './meeting-form-dialog.html',
  styleUrl: './meeting-form-dialog.scss',
})
export class MeetingFormDialog implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly dialogRef = inject(MatDialogRef<MeetingFormDialog>);
  readonly data: MeetingFormDialogData = inject(MAT_DIALOG_DATA);

  readonly isEditMode = !!this.data?.meeting;

  readonly form = this.fb.group({
    meeting_date: [null as Date | null, Validators.required],
    participants: [''],
    summary: [''],
    attention_points: [''],
    next_steps: [''],
  });

  ngOnInit(): void {
    if (this.data?.meeting) {
      const m = this.data.meeting;
      this.form.patchValue({
        ...m,
        meeting_date: new Date(m.meeting_date + 'T00:00:00'),
      });
    }
  }

  onSubmit(): void {
    if (this.form.invalid) return;
    const raw = this.form.getRawValue();
    const result = {
      ...raw,
      meeting_date: raw.meeting_date ? raw.meeting_date.toISOString().split('T')[0] : null,
    };
    this.dialogRef.close(result);
  }

  onCancel(): void {
    this.dialogRef.close();
  }
}
