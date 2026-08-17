import { Component, inject, OnInit } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatButtonModule } from '@angular/material/button';

import {
  INDICATOR_LIMITS,
  futurePeriodValidator,
  integerValidator,
} from '../../../models/indicator-form';
import { MonthlyIndicator, MONTH_LABELS } from '../../../models/monthly-indicator.model';
import {
  formatCurrencyBRL,
  formatInteger,
  formatPercent,
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

  // The reportable fields carry the same limits as the shared factory, so an
  // out-of-range value is caught here on edit and not only by the server's 422.
  readonly form = this.fb.group(
    {
      month: [new Date().getMonth() + 1, [Validators.required, Validators.min(1), Validators.max(12)]],
      year: [this.currentYear, [Validators.required, Validators.min(2000), Validators.max(2100)]],
      total_revenue: [
        null as number | null,
        [Validators.min(INDICATOR_LIMITS.MIN_MONEY), Validators.max(INDICATOR_LIMITS.MAX_MONEY)],
      ],
      recurring_revenue_pct: [
        null as number | null,
        [Validators.min(0), Validators.max(INDICATOR_LIMITS.MAX_PCT)],
      ],
      gross_margin_pct: [
        null as number | null,
        [Validators.min(0), Validators.max(INDICATOR_LIMITS.MAX_PCT)],
      ],
      cash_balance: [
        null as number | null,
        [Validators.min(INDICATOR_LIMITS.MIN_MONEY), Validators.max(INDICATOR_LIMITS.MAX_MONEY)],
      ],
      headcount: [
        null as number | null,
        [Validators.min(0), Validators.max(INDICATOR_LIMITS.MAX_HEADCOUNT), integerValidator],
      ],
      ebitda_burn: [
        null as number | null,
        [Validators.min(INDICATOR_LIMITS.MIN_MONEY), Validators.max(INDICATOR_LIMITS.MAX_MONEY)],
      ],
      achievements: [''],
      challenges: [''],
      comments: [''],
    },
    { validators: [futurePeriodValidator] },
  );

  /**
   * No modo leitura o formulário não é renderizado — o registro vira uma lista
   * de definição. Antes ele era exibido com `form.disable()`, e o dado herdava a
   * cor de controle inativo: 2,46:1 no tema claro, contra 18,7:1 do rótulo ao
   * lado. A WCAG isenta componentes inativos, então a auditoria passava; só que
   * o texto do controle era a informação inteira do diálogo.
   */
  readonly readSections: ReadSection[] = this.buildReadSections();

  /** Mesmos grupos do modo de edição, na mesma ordem: o período solto no topo,
   *  depois Quantitativos e Qualitativos. */
  private buildReadSections(): ReadSection[] {
    const ind = this.data?.indicator;
    if (!ind) return [];

    return [
      {
        items: [{ label: 'Período', value: `${MONTH_LABELS[ind.month]}/${ind.year}` }],
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
        // `|| null` porque texto em branco é ausência aqui: um textarea nunca
        // preenchido chega como string vazia e renderizaria um valor vazio.
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
