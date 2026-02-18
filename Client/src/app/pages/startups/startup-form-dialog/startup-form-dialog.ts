import { Component, inject, OnInit } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatButtonModule } from '@angular/material/button';
import { provideNativeDateAdapter } from '@angular/material/core';

import { Startup, StartupStatus, STARTUP_STATUS_CONFIG } from '../../../models/startup.model';

export interface StartupFormDialogData {
  startup?: Startup;
}

@Component({
  selector: 'app-startup-form-dialog',
  imports: [
    ReactiveFormsModule,
    MatDialogModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatDatepickerModule,
    MatButtonModule,
  ],
  providers: [provideNativeDateAdapter()],
  templateUrl: './startup-form-dialog.html',
  styleUrl: './startup-form-dialog.scss',
})
export class StartupFormDialog implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly dialogRef = inject(MatDialogRef<StartupFormDialog>);
  readonly data: StartupFormDialogData = inject(MAT_DIALOG_DATA);

  readonly statusOptions = Object.values(StartupStatus);
  readonly statusConfig = STARTUP_STATUS_CONFIG;
  readonly isEditMode = !!this.data?.startup;

  readonly form = this.fb.group({
    name: ['', [Validators.required, Validators.maxLength(255)]],
    site: [''],
    logo_url: [''],
    status: [StartupStatus.HEALTHY, Validators.required],
    sector: ['', [Validators.required, Validators.maxLength(255)]],
    investment_date: [null as Date | null, Validators.required],
    notes: [''],
  });

  ngOnInit(): void {
    if (this.data?.startup) {
      const s = this.data.startup;
      this.form.patchValue({
        ...s,
        investment_date: new Date(s.investment_date + 'T00:00:00'),
      });
    }
  }

  onSubmit(): void {
    if (this.form.invalid) return;
    const raw = this.form.getRawValue();
    const result = {
      ...raw,
      investment_date: raw.investment_date
        ? raw.investment_date.toISOString().split('T')[0]
        : null,
    };
    this.dialogRef.close(result);
  }

  onCancel(): void {
    this.dialogRef.close();
  }
}
