import { Component, inject, OnInit, signal } from '@angular/core';
import { ReactiveFormsModule, FormBuilder } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';

import { ReportTokenService } from '../../services/report-token.service';
import { ReportFormContext } from '../../models/report-token.model';
import { MONTH_LABELS } from '../../models/monthly-indicator.model';

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
  private readonly service = inject(ReportTokenService);
  private readonly snackBar = inject(MatSnackBar);
  private readonly fb = inject(FormBuilder);

  readonly context = signal<ReportFormContext | null>(null);
  readonly loading = signal(true);
  readonly submitting = signal(false);
  readonly submitted = signal(false);
  readonly error = signal<string | null>(null);
  readonly monthLabels = MONTH_LABELS;

  private token = '';

  readonly form = this.fb.group({
    total_revenue: [null as number | null],
    cash_balance: [null as number | null],
    ebitda_burn: [null as number | null],
    recurring_revenue_pct: [null as number | null],
    gross_margin_pct: [null as number | null],
    headcount: [null as number | null],
    achievements: [''],
    challenges: [''],
  });

  ngOnInit(): void {
    this.token = this.route.snapshot.paramMap.get('token')!;
    this.service.getFormContext(this.token).subscribe({
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
    this.service.submitReport(this.token, this.form.getRawValue()).subscribe({
      next: () => {
        this.submitted.set(true);
        this.submitting.set(false);
      },
      error: (err) => {
        this.snackBar.open(
          err.error?.detail || 'Erro ao enviar relatorio. Tente novamente.',
          'Fechar',
          { duration: 5000 },
        );
        this.submitting.set(false);
      },
    });
  }
}
