import { Component, computed, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatButtonModule } from '@angular/material/button';
import { MatRadioModule } from '@angular/material/radio';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';

import { DialogHeader } from '../../../components/dialog-header/dialog-header';
import { CurrencyInput } from '../../../directives/currency-input';
import { Executive } from '../../../models/executive.model';
import { buildReportedIndicatorForm, futurePeriodValidator } from '../../../models/indicator-form';
import {
  MONTH_LABELS,
  MonthlyIndicator,
  MonthlyIndicatorCreate,
} from '../../../models/monthly-indicator.model';
import { MonthlyIndicatorToken } from '../../../models/monthly-indicator-token.model';
import { MonthlyIndicatorService } from '../../../services/monthly-indicator.service';
import { MonthlyIndicatorTokenService } from '../../../services/monthly-indicator-token.service';
import { TokenPanel } from '../token-panel/token-panel';

export interface AddIndicatorDialogData {
  startupId: string;
  indicators: MonthlyIndicator[];
  tokens: MonthlyIndicatorToken[];
  executives: Executive[];
}

type Mode = 'fill' | 'link';

/**
 * The single entry point for a period's indicator (PRD-001 item 2): pick the
 * period, then choose whether to fill it now or generate a link for the
 * investee. It replaces the two separate entry points ("Adicionar indicador"
 * and "Gerar link") the header carried before. Context comes from the records
 * the page already loaded — no network call on open.
 */
@Component({
  selector: 'app-add-indicator-dialog',
  imports: [
    ReactiveFormsModule,
    MatDialogModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatButtonModule,
    MatRadioModule,
    MatSnackBarModule,
    DialogHeader,
    CurrencyInput,
    TokenPanel,
  ],
  templateUrl: './add-indicator-dialog.html',
  styleUrl: './add-indicator-dialog.scss',
})
export class AddIndicatorDialog {
  private readonly fb = inject(FormBuilder);
  private readonly dialogRef = inject(MatDialogRef<AddIndicatorDialog>);
  private readonly indicatorService = inject(MonthlyIndicatorService);
  private readonly tokenService = inject(MonthlyIndicatorTokenService);
  private readonly snackBar = inject(MatSnackBar);
  readonly data: AddIndicatorDialogData = inject(MAT_DIALOG_DATA);

  readonly monthOptions = Array.from({ length: 12 }, (_, i) => i + 1);
  readonly monthLabels = MONTH_LABELS;

  readonly mode = signal<Mode>('fill');
  readonly submitting = signal(false);
  /** The link once generated; while set, link mode shows the panel instead. */
  readonly generatedToken = signal<MonthlyIndicatorToken | null>(null);

  private readonly previousPeriod = AddIndicatorDialog.previousMonthPeriod();

  // month/year live on the parent group so futurePeriodValidator can read them;
  // the reportable zone comes from the shared factory (nested), so its limits
  // never drift from the public form; comments is the admin-only fund note.
  readonly form = this.fb.group(
    {
      month: [this.previousPeriod.month, [Validators.required]],
      year: [this.previousPeriod.year, [Validators.required]],
      reported: buildReportedIndicatorForm(this.fb),
      comments: [''],
    },
    { validators: [futurePeriodValidator] },
  );

  /** The selected period, tracked as a signal so context updates live. */
  private readonly period = signal({ month: this.previousPeriod.month, year: this.previousPeriod.year });

  constructor() {
    this.form.controls.month.valueChanges.subscribe((month) =>
      this.period.set({ ...this.period(), month: month ?? this.period().month }),
    );
    this.form.controls.year.valueChanges.subscribe((year) =>
      this.period.set({ ...this.period(), year: year ?? this.period().year }),
    );
  }

  readonly periodLabel = computed(() => {
    const { month, year } = this.period();
    return `${MONTH_LABELS[month]}/${year}`;
  });

  readonly hasIndicator = computed(() => {
    const { month, year } = this.period();
    return this.data.indicators.some((i) => i.month === month && i.year === year);
  });

  readonly hasLink = computed(() => {
    const { month, year } = this.period();
    return this.data.tokens.some((t) => t.month === month && t.year === year);
  });

  setMode(mode: Mode): void {
    // Switching hides the other mode's controls; the form persists, so what was
    // typed survives the switch (PRD-001 criterion 6.1.6).
    this.mode.set(mode);
  }

  submit(): void {
    if (this.submitting()) return;
    if (this.mode() === 'fill') {
      this.saveIndicator();
    } else {
      this.generateLink();
    }
  }

  private saveIndicator(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    this.submitting.set(true);
    this.indicatorService.create(this.data.startupId, this.buildPayload()).subscribe({
      next: () => this.dialogRef.close(true),
      error: (err) => {
        this.submitting.set(false);
        this.snackBar.open(err.error?.detail || 'Erro ao salvar indicador', 'Fechar', {
          duration: 3000,
        });
      },
    });
  }

  private generateLink(): void {
    const { month, year } = this.form.controls;
    if (this.form.hasError('futurePeriod') || !month.value || !year.value) {
      this.form.markAllAsTouched();
      return;
    }
    this.submitting.set(true);
    this.tokenService
      .create(this.data.startupId, { month: month.value, year: year.value })
      .subscribe({
        next: (token) => {
          this.submitting.set(false);
          this.generatedToken.set(token);
        },
        error: (err) => {
          this.submitting.set(false);
          this.snackBar.open(err.error?.detail || 'Erro ao gerar link', 'Fechar', {
            duration: 3000,
          });
        },
      });
  }

  /** Absence is not erasure: a blank string is normalised to null so an empty
   * field does not wipe stored text on the upsert (PRD-001 §6.1/§8). */
  private buildPayload(): MonthlyIndicatorCreate {
    const raw = this.form.getRawValue();
    const blankToNull = (v: string | null | undefined) => (v?.trim() ? v : null);
    return {
      month: raw.month!,
      year: raw.year!,
      total_revenue: raw.reported.total_revenue,
      recurring_revenue_pct: raw.reported.recurring_revenue_pct,
      gross_margin_pct: raw.reported.gross_margin_pct,
      cash_balance: raw.reported.cash_balance,
      headcount: raw.reported.headcount,
      ebitda_burn: raw.reported.ebitda_burn,
      achievements: blankToNull(raw.reported.achievements),
      challenges: blankToNull(raw.reported.challenges),
      comments: blankToNull(raw.comments),
    };
  }

  private static previousMonthPeriod(): { month: number; year: number } {
    const today = new Date();
    // getMonth() is 0-indexed, so its 1-based value already names last month.
    if (today.getMonth() === 0) {
      return { month: 12, year: today.getFullYear() - 1 };
    }
    return { month: today.getMonth(), year: today.getFullYear() };
  }
}
