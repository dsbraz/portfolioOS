import { Component, inject, OnInit, signal } from '@angular/core';
import { ReactiveFormsModule, FormBuilder, Validators, AbstractControl, ValidationErrors } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';

import { MonthlyIndicatorTokenService } from '../../services/monthly-indicator-token.service';
import { PublicIndicatorForm } from '../../models/monthly-indicator-token.model';
import { MONTH_LABELS } from '../../models/monthly-indicator.model';

const MAX_MONEY = 9_999_999_999_999.99;
const MIN_MONEY = -9_999_999_999_999.99;
const MAX_PCT = 99_999.99;

function integerValidator(control: AbstractControl): ValidationErrors | null {
  const value = control.value;
  if (value === null || value === undefined || value === '') return null;
  return Number.isInteger(Number(value)) ? null : { integer: true };
}

@Component({
  selector: 'app-report-form',
  imports: [
    ReactiveFormsModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    MatCardModule,
    MatIconModule,
    MatProgressSpinnerModule,
    MatSnackBarModule,
  ],
  templateUrl: './report-form.html',
  styleUrl: './report-form.scss',
})
export default class ReportForm implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly service = inject(MonthlyIndicatorTokenService);
  private readonly snackBar = inject(MatSnackBar);
  private readonly fb = inject(FormBuilder);

  readonly context = signal<PublicIndicatorForm | null>(null);
  readonly loading = signal(true);
  readonly submitting = signal(false);
  readonly submitted = signal(false);
  readonly error = signal<string | null>(null);
  readonly monthLabels = MONTH_LABELS;

  private token = '';

  readonly form = this.fb.group({
    total_revenue: [null as number | null, [Validators.min(MIN_MONEY), Validators.max(MAX_MONEY)]],
    cash_balance: [null as number | null, [Validators.min(MIN_MONEY), Validators.max(MAX_MONEY)]],
    ebitda_burn: [null as number | null, [Validators.min(MIN_MONEY), Validators.max(MAX_MONEY)]],
    recurring_revenue_pct: [null as number | null, [Validators.min(0), Validators.max(MAX_PCT)]],
    gross_margin_pct: [null as number | null, [Validators.min(0), Validators.max(MAX_PCT)]],
    headcount: [null as number | null, [Validators.min(0), integerValidator]],
    achievements: [''],
    challenges: [''],
  });

  ngOnInit(): void {
    this.token = this.route.snapshot.paramMap.get('token')!;
    this.service.getPublicForm(this.token).subscribe({
      next: (ctx) => {
        this.context.set(ctx);
        if (ctx.existing_indicator) {
          this.form.patchValue({
            total_revenue: ctx.existing_indicator.total_revenue,
            cash_balance: ctx.existing_indicator.cash_balance,
            ebitda_burn: ctx.existing_indicator.ebitda_burn,
            recurring_revenue_pct: ctx.existing_indicator.recurring_revenue_pct,
            gross_margin_pct: ctx.existing_indicator.gross_margin_pct,
            headcount: ctx.existing_indicator.headcount,
            achievements: ctx.existing_indicator.achievements ?? '',
            challenges: ctx.existing_indicator.challenges ?? '',
          });
        }
        this.loading.set(false);
      },
      error: () => {
        this.error.set('Link invalido ou expirado.');
        this.loading.set(false);
      },
    });
  }

  onSubmit(): void {
    if (this.form.invalid || this.submitting()) return;
    this.submitting.set(true);
    this.service.submitPublicForm(this.token, this.form.getRawValue()).subscribe({
      next: () => {
        this.submitted.set(true);
        this.submitting.set(false);
      },
      error: (err) => {
        let message: string;
        if (typeof err.error?.detail === 'string') {
          message = err.error.detail;
        } else if (err.status === 422) {
          message = 'Dados invalidos. Verifique os campos e tente novamente.';
        } else {
          message = 'Erro ao enviar relatorio. Tente novamente.';
        }
        this.snackBar.open(message, 'Fechar', { duration: 5000 });
        this.submitting.set(false);
      },
    });
  }
}
