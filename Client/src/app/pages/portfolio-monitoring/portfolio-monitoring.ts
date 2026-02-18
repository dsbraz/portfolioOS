import { Component, inject, OnInit, signal } from '@angular/core';
import { Router } from '@angular/router';
import { MatTableModule } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatCardModule } from '@angular/material/card';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';

import { MonitoringSummary, StartupMonitoringItem } from '../../models/portfolio-monitoring.model';
import { PortfolioMonitoringService } from '../../services/portfolio-monitoring.service';
import { StartupService } from '../../services/startup.service';
import { StatusBadge } from '../../components/status-badge/status-badge';
import { KpiCard } from '../../components/kpi-card/kpi-card';
import { HealthBar } from '../../components/health-bar/health-bar';
import {
  StartupFormDialog,
  StartupFormDialogData,
} from '../startups/startup-form-dialog/startup-form-dialog';

@Component({
  selector: 'app-portfolio-monitoring',
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
  templateUrl: './portfolio-monitoring.html',
  styleUrl: './portfolio-monitoring.scss',
})
export class PortfolioMonitoring implements OnInit {
  private readonly monitoringService = inject(PortfolioMonitoringService);
  private readonly startupService = inject(StartupService);
  private readonly dialog = inject(MatDialog);
  private readonly snackBar = inject(MatSnackBar);
  private readonly router = inject(Router);

  readonly summary = signal<MonitoringSummary | null>(null);
  readonly loading = signal(false);

  readonly displayedColumns = [
    'name',
    'status',
    'total_revenue',
    'cash_balance',
    'ebitda_burn',
    'headcount',
  ];

  ngOnInit(): void {
    this.loadSummary();
  }

  loadSummary(): void {
    this.loading.set(true);
    this.monitoringService.getSummary().subscribe({
      next: (data) => {
        this.summary.set(data);
        this.loading.set(false);
      },
      error: () => {
        this.snackBar.open('Erro ao carregar monitoramento', 'Fechar', { duration: 3000 });
        this.loading.set(false);
      },
    });
  }

  formatCurrency(value: number | null): string {
    if (value == null) return '-';
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value);
  }

  navigateToStartup(item: StartupMonitoringItem): void {
    this.router.navigate(['/startup', item.startup.id]);
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
          error: () =>
            this.snackBar.open('Erro ao criar startup', 'Fechar', { duration: 3000 }),
        });
      }
    });
  }
}
