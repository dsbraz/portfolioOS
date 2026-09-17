import { Component, inject, OnInit } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatButtonModule } from '@angular/material/button';

import { buildReportedIndicatorForm, futurePeriodValidator } from '../../../models/indicator-form';
import { MonthlyIndicator, MONTH_LABELS } from '../../../models/monthly-indicator.model';
import {
  formatCurrencyBRL,
  formatInteger,
  formatPercent,
  formatPeriod,
} from '../../../models/formatters';
import { ReadSection, ReadView } from '../../../components/read-view/read-view';
import { CurrencyInput } from '../../../directives/currency-input';

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
    CurrencyInput,
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

  // The reportable fields come from the shared factory, so an out-of-range
  // value is caught here on edit and not only by the server's 422.
  readonly form = this.fb.group(
    {
      month: [new Date().getMonth() + 1, [Validators.required, Validators.min(1), Validators.max(12)]],
      year: [this.currentYear, [Validators.required, Validators.min(2000), Validators.max(2100)]],
      ...buildReportedIndicatorForm(this.fb).controls,
      comments: [''],
    },
    { validators: [futurePeriodValidator] },
  );

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
          { label: 'Destaques do mês', value: ind.achievements || null, kind: 'long' },
          { label: 'Próximos passos e necessidades', value: ind.challenges || null, kind: 'long' },
        ],
      },
      {
        // A anotação do fundo é interna — nunca vai no formulário da investida —
        // e por isso é uma seção própria, separada da zona reportável.
        title: 'Anotações do fundo',
        items: [{ label: 'Comentários do fundo', value: ind.comments || null, kind: 'long' }],
      },
    ];
  }

  ngOnInit(): void {
    if (this.data?.indicator) {
      this.form.patchValue(this.data.indicator);
    }
  }

  onSubmit(): void {
    // Reveal the errors instead of silently doing nothing — the primary button
    // stays enabled so a click on an out-of-range value points at the field.
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    this.dialogRef.close(this.form.getRawValue());
  }

  onCancel(): void {
    this.dialogRef.close();
  }
}
