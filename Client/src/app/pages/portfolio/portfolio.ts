import { Component, inject, OnInit, signal } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { MatTableModule } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatCardModule } from '@angular/material/card';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';

import {
  PortfolioSummary,
  RevenueVariationDirection,
  StartupSummary,
} from '../../models/portfolio.model';
import { KpiCardTone } from '../../components/kpi-card/kpi-card';
import { MONTH_LABELS } from '../../models/monthly-indicator.model';
import { PortfolioService } from '../../services/portfolio.service';
import { StartupService } from '../../services/startup.service';
import { StatusBadge } from '../../components/status-badge/status-badge';
import { KpiCard } from '../../components/kpi-card/kpi-card';
import { HealthBar } from '../../components/health-bar/health-bar';
import {
  StartupFormDialog,
  StartupFormDialogData,
} from '../startups/startup-form-dialog/startup-form-dialog';

@Component({
  selector: 'app-portfolio',
  imports: [
    MatTableModule,
    MatButtonModule,
    MatIconModule,
    MatCardModule,
    MatDialogModule,
    MatSnackBarModule,
    StatusBadge,
    KpiCard,
    HealthBar,
  ],
  templateUrl: './portfolio.html',
  styleUrl: './portfolio.scss',
})
export class Portfolio implements OnInit {
  private readonly monitoringService = inject(PortfolioService);
  private readonly startupService = inject(StartupService);
  private readonly route = inject(ActivatedRoute);
  private readonly dialog = inject(MatDialog);
  private readonly snackBar = inject(MatSnackBar);
  private readonly router = inject(Router);
  private readonly today = new Date();
  private readonly defaultPeriod = this.getPreviousPeriod(this.today.getMonth() + 1, this.today.getFullYear());

  readonly summaryByPeriod = signal<PortfolioSummary | null>(null);
  readonly loading = signal(false);
  readonly selectedMonth = signal(this.defaultPeriod.month);
  readonly selectedYear = signal(this.defaultPeriod.year);
  readonly monthLabels = MONTH_LABELS;

  readonly displayedColumns = [
    'name',
    'status',
    'total_revenue',
    'cash_balance',
    'ebitda_burn',
    'headcount',
  ];

  ngOnInit(): void {
    this.route.queryParamMap.subscribe((params) => {
      const period = this.resolvePeriodFromQuery(params.get('month'), params.get('year'));
      if (!this.isCanonicalPeriodQuery(params.get('month'), params.get('year'), period.month, period.year)) {
        this.updatePeriodQueryParams(period.month, period.year, true);
        return;
      }

      this.selectedMonth.set(period.month);
      this.selectedYear.set(period.year);
      this.loadSummary();
    });
  }

  loadSummary(): void {
    this.loading.set(true);
    this.monitoringService.getSummary(this.selectedMonth(), this.selectedYear()).subscribe({
      next: (data) => {
        this.summaryByPeriod.set(data);
        this.loading.set(false);
      },
      error: (err) => {
        this.snackBar.open(err.error?.detail || 'Erro ao carregar monitoramento', 'Fechar', { duration: 3000 });
        this.loading.set(false);
      },
    });
  }

  formatCurrency(value: number | null): string {
    if (value == null) return '-';
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value);
  }

  navigateToStartup(item: StartupSummary): void {
    this.router.navigate(['/startup', item.startup.id]);
  }

  revenueVariationLabel(): string {
    const summary = this.summaryByPeriod();
    if (!summary || summary.revenue_variation_pct === null) return 'Sem base';

    const signal = summary.revenue_variation_pct > 0 ? '+' : '';
    return `${signal}${summary.revenue_variation_pct.toFixed(1)}% vs mes anterior`;
  }

  revenueTrendIcon(): string {
    const direction = this.summaryByPeriod()?.revenue_variation_direction ?? 'neutral';
    if (direction === 'up') return 'trending_up';
    if (direction === 'down') return 'trending_down';
    return 'trending_flat';
  }

  revenueCardTone(): KpiCardTone {
    const direction: RevenueVariationDirection =
      this.summaryByPeriod()?.revenue_variation_direction ?? 'neutral';
    if (direction === 'up') return 'positive';
    if (direction === 'down') return 'negative';
    return 'neutral';
  }

  selectedPeriodLabel(): string {
    return `${this.monthLabels[this.selectedMonth()]}/${this.selectedYear()}`;
  }

  goToPreviousMonth(): void {
    const month = this.selectedMonth();
    const year = this.selectedYear();
    if (month === 1) {
      this.updatePeriodQueryParams(12, year - 1);
      return;
    }
    this.updatePeriodQueryParams(month - 1, year);
  }

  goToNextMonth(): void {
    if (this.isCurrentMonthSelected()) return;

    const month = this.selectedMonth();
    const year = this.selectedYear();
    if (month === 12) {
      this.updatePeriodQueryParams(1, year + 1);
      return;
    }
    this.updatePeriodQueryParams(month + 1, year);
  }

  isCurrentMonthSelected(): boolean {
    return this.selectedMonth() === this.today.getMonth() + 1 && this.selectedYear() === this.today.getFullYear();
  }

  openCreateDialog(): void {
    const dialogRef = this.dialog.open(StartupFormDialog, {
      width: '560px',
      data: {} as StartupFormDialogData,
    });

    dialogRef.afterClosed().subscribe((result) => {
      if (result) {
        this.startupService.create(result).subscribe({
          next: () => {
            this.snackBar.open('Startup criada com sucesso', 'Fechar', { duration: 3000 });
            this.loadSummary();
          },
          error: (err) =>
            this.snackBar.open(err.error?.detail || 'Erro ao criar startup', 'Fechar', { duration: 3000 }),
        });
      }
    });
  }

  private resolvePeriodFromQuery(
    monthParam: string | null,
    yearParam: string | null,
  ): { month: number; year: number } {
    const fallback = this.defaultPeriod;
    if (!monthParam || !yearParam) return fallback;

    const month = Number(monthParam);
    const year = Number(yearParam);
    if (!Number.isInteger(month) || !Number.isInteger(year)) return fallback;
    if (month < 1 || month > 12 || year < 1) return fallback;
    if (year > this.today.getFullYear() || (year === this.today.getFullYear() && month > this.today.getMonth() + 1)) {
      return fallback;
    }

    return { month, year };
  }

  private isCanonicalPeriodQuery(
    monthParam: string | null,
    yearParam: string | null,
    month: number,
    year: number,
  ): boolean {
    return monthParam === String(month) && yearParam === String(year);
  }

  private updatePeriodQueryParams(month: number, year: number, replaceUrl = false): void {
    this.router.navigate([], {
      relativeTo: this.route,
      queryParams: { month, year },
      replaceUrl,
    });
  }

  private getPreviousPeriod(month: number, year: number): { month: number; year: number } {
    if (month === 1) return { month: 12, year: year - 1 };
    return { month: month - 1, year };
  }
}
