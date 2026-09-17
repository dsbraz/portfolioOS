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
import {
  formatCurrencyBRL,
  formatInteger,
  formatPercent,
  formatPeriod,
} from '../../../models/formatters';
import { ReadSection, ReadView } from '../../../components/read-view/read-view';

export interface IndicatorFormDialogData {
  indicator?: MonthlyIndicator;
  readonly?: boolean;
}

import { DialogHeader } from '../../../components/dialog-header/dialog-header';

@Component({
  selector: 'app-indicator-form-dialog',
  imports: [
    DialogHeader,
    ReadView,
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
  readonly isReadonly = !!this.data?.readonly;
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

  /**
   * In read mode the form is not rendered — the record becomes a definition
   * list. It used to be shown with `form.disable()`, and the data inherited the
   * inactive control color: 2.46:1 in the light theme, against 18.7:1 for the
   * label next to it. WCAG exempts inactive components, so the audit passed; but
   * the control's text was the dialog's entire information.
   */
  readonly readSections: ReadSection[] = this.buildReadSections();

  /** Same groups as edit mode, in the same order: the period on its own at the top,
   *  then Quantitativos and Qualitativos. */
  private buildReadSections(): ReadSection[] {
    const ind = this.data?.indicator;
    if (!ind) return [];

    return [
      {
        items: [{ label: 'Período', value: formatPeriod(ind.month, ind.year) }],
      },
      {
        title: 'Quantitativos',
        items: [
          { label: 'Receita do mês', value: formatCurrencyBRL(ind.total_revenue), kind: 'num' },
          {
            label: 'Percentual de receita recorrente',
            value: formatPercent(ind.recurring_revenue_pct),
            kind: 'num',
          },
          { label: 'Margem bruta', value: formatPercent(ind.gross_margin_pct), kind: 'num' },
          { label: 'Saldo em caixa', value: formatCurrencyBRL(ind.cash_balance), kind: 'num' },
          { label: 'Headcount', value: formatInteger(ind.headcount), kind: 'num' },
          { label: 'Burn / EBITDA', value: formatCurrencyBRL(ind.ebitda_burn), kind: 'num' },
        ],
      },
      {
        title: 'Qualitativos',
        // `|| null` because blank text means absence here: a never-filled
        // textarea arrives as an empty string and would render an empty value.
        items: [
          { label: 'Conquistas do mês', value: ind.achievements || null, kind: 'long' },
          { label: 'Desafios do mês', value: ind.challenges || null, kind: 'long' },
          { label: 'Comentários', value: ind.comments || null, kind: 'long' },
        ],
      },
    ];
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
