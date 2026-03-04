import { Component, inject } from '@angular/core';
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

import { MONTH_LABELS } from '../../../models/monthly-indicator.model';
import { MonthlyIndicatorTokenCreate } from '../../../models/monthly-indicator-token.model';

export interface TokenGenerateDialogData {
  month: number;
  year: number;
}

@Component({
  selector: 'app-token-generate-dialog',
  imports: [
    ReactiveFormsModule,
    MatDialogModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatButtonModule,
  ],
  templateUrl: './token-generate-dialog.html',
  styleUrl: './token-generate-dialog.scss',
})
export class TokenGenerateDialog {
  private readonly fb = inject(FormBuilder);
  private readonly dialogRef = inject(MatDialogRef<TokenGenerateDialog>);
  readonly data: TokenGenerateDialogData = inject(MAT_DIALOG_DATA);

  readonly monthOptions = Array.from({ length: 12 }, (_, i) => i + 1);
  readonly monthLabels = MONTH_LABELS;

  readonly form = this.fb.group(
    {
      month: [this.data.month, [Validators.required, Validators.min(1), Validators.max(12)]],
      year: [this.data.year, [Validators.required, Validators.min(2000), Validators.max(2100)]],
    },
    { validators: [TokenGenerateDialog.futurePeriodValidator] },
  );

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

  onSubmit(): void {
    if (this.form.invalid) return;
    const value = this.form.getRawValue() as MonthlyIndicatorTokenCreate;
    this.dialogRef.close(value);
  }

  onCancel(): void {
    this.dialogRef.close();
  }
}
