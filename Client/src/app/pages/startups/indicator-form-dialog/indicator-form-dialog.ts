import { Component, inject, OnInit } from '@angular/core';
import {
  AbstractControl,
  FormBuilder,
  ReactiveFormsModule,
  ValidationErrors,
  Validators,
} from '@angular/forms';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatButtonModule } from '@angular/material/button';

import { MonthlyIndicator, MONTH_LABELS } from '../../../models/monthly-indicator.model';

export interface IndicatorFormDialogData {
  indicator?: MonthlyIndicator;
}

@Component({
  selector: 'app-indicator-form-dialog',
  imports: [
    ReactiveFormsModule,
    MatDialogModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatButtonModule,
  ],
  templateUrl: './indicator-form-dialog.html',
  styleUrl: './indicator-form-dialog.scss',
})
export class IndicatorFormDialog implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly dialogRef = inject(MatDialogRef<IndicatorFormDialog>);
  readonly data: IndicatorFormDialogData = inject(MAT_DIALOG_DATA);

  readonly isEditMode = !!this.data?.indicator;
  readonly monthOptions = Array.from({ length: 12 }, (_, i) => i + 1);
  readonly monthLabels = MONTH_LABELS;
  readonly currentYear = new Date().getFullYear();

  readonly form = this.fb.group({
    month: [new Date().getMonth() + 1, [Validators.required, Validators.min(1), Validators.max(12)]],
    year: [this.currentYear, [Validators.required, Validators.min(2000), Validators.max(2100)]],
    total_revenue: [null as number | null],
    recurring_revenue_pct: [null as number | null],
    gross_margin_pct: [null as number | null],
    cash_balance: [null as number | null],
    headcount: [null as number | null],
    ebitda_burn: [null as number | null],
    achievements: [''],
    challenges: [''],
    comments: [''],
  }, { validators: [IndicatorFormDialog.futurePeriodValidator] });

  private static futurePeriodValidator(group: AbstractControl): ValidationErrors | null {
    const month = group.get('month')?.value;
    const year = group.get('year')?.value;
    if (!month || !year) return null;
    const now = new Date();
    if (year > now.getFullYear() || (year === now.getFullYear() && month > now.getMonth() + 1)) {
      return { futurePeriod: true };
    }
    return null;
  }

  ngOnInit(): void {
    if (this.data?.indicator) {
      this.form.patchValue(this.data.indicator);
    }
  }

  onSubmit(): void {
    if (this.form.invalid) return;
    this.dialogRef.close(this.form.getRawValue());
  }

  onCancel(): void {
    this.dialogRef.close();
  }
}
