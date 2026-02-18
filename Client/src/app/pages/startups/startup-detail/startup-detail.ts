import { Component, ElementRef, inject, OnInit, signal, viewChild } from '@angular/core';
import { DatePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatCardModule } from '@angular/material/card';
import { MatDatepicker, MatDatepickerModule } from '@angular/material/datepicker';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatNativeDateModule } from '@angular/material/core';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatTableModule } from '@angular/material/table';
import { MatMenuModule } from '@angular/material/menu';
import { MatTooltipModule } from '@angular/material/tooltip';
import { forkJoin } from 'rxjs';

import { Startup, StartupStatus, STARTUP_STATUS_CONFIG } from '../../../models/startup.model';
import { MonthlyIndicator, MONTH_LABELS } from '../../../models/monthly-indicator.model';
import { BoardMeeting } from '../../../models/board-meeting.model';
import { Executive } from '../../../models/executive.model';
import { StartupService } from '../../../services/startup.service';
import { MonthlyIndicatorService } from '../../../services/monthly-indicator.service';
import { BoardMeetingService } from '../../../services/board-meeting.service';
import { ExecutiveService } from '../../../services/executive.service';
import { ReportTokenService } from '../../../services/report-token.service';
import { ReportToken } from '../../../models/report-token.model';
import { StatusBadge } from '../../../components/status-badge/status-badge';
import {
  StartupFormDialog,
  StartupFormDialogData,
} from '../startup-form-dialog/startup-form-dialog';
import {
  IndicatorFormDialog,
  IndicatorFormDialogData,
} from '../indicator-form-dialog/indicator-form-dialog';
import {
  MeetingFormDialog,
  MeetingFormDialogData,
} from '../meeting-form-dialog/meeting-form-dialog';
import {
  ExecutiveFormDialog,
  ExecutiveFormDialogData,
} from '../executive-form-dialog/executive-form-dialog';
import {
  ReportTokenListDialog,
  ReportTokenListDialogData,
} from '../report-token-list-dialog/report-token-list-dialog';

@Component({
  selector: 'app-startup-detail',
  imports: [
    DatePipe,
    FormsModule,
    MatButtonModule,
    MatIconModule,
    MatCardModule,
    MatDatepickerModule,
    MatDialogModule,
    MatFormFieldModule,
    MatInputModule,
    MatNativeDateModule,
    MatSnackBarModule,
    MatTableModule,
    MatMenuModule,
    MatTooltipModule,
    StatusBadge,
  ],
  templateUrl: './startup-detail.html',
  styleUrl: './startup-detail.scss',
})
export class StartupDetail implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly dialog = inject(MatDialog);
  private readonly snackBar = inject(MatSnackBar);
  private readonly startupService = inject(StartupService);
  private readonly indicatorService = inject(MonthlyIndicatorService);
  private readonly meetingService = inject(BoardMeetingService);
  private readonly executiveService = inject(ExecutiveService);
  private readonly reportTokenService = inject(ReportTokenService);

  readonly startup = signal<Startup | null>(null);
  readonly indicators = signal<MonthlyIndicator[]>([]);
  readonly meetings = signal<BoardMeeting[]>([]);
  readonly executives = signal<Executive[]>([]);
  readonly reportTokens = signal<ReportToken[]>([]);
  readonly loading = signal(false);
  readonly monthLabels = MONTH_LABELS;
  readonly statusConfig = STARTUP_STATUS_CONFIG;
  readonly statusOptions = Object.entries(STARTUP_STATUS_CONFIG).map(
    ([value, cfg]) => ({ value: value as StartupStatus, ...cfg })
  );

  private startupId = '';

  readonly editingField = signal<'name' | 'sector' | 'date' | null>(null);
  editValue = '';
  editDateValue: Date | null = null;

  readonly nameInput = viewChild<ElementRef<HTMLInputElement>>('nameInput');
  readonly sectorInput = viewChild<ElementRef<HTMLInputElement>>('sectorInput');
  readonly datePicker = viewChild<MatDatepicker<Date>>('picker');

  readonly indicatorColumns = ['period', 'total_revenue', 'cash_balance', 'ebitda_burn', 'headcount', 'actions'];
  readonly meetingColumns = ['meeting_date', 'summary', 'actions'];
  readonly executiveColumns = ['name', 'role', 'email', 'actions'];

  ngOnInit(): void {
    this.startupId = this.route.snapshot.paramMap.get('id')!;
    this.loadAll();
  }

  loadAll(): void {
    this.loading.set(true);
    forkJoin({
      startup: this.startupService.getById(this.startupId),
      indicators: this.indicatorService.list(this.startupId),
      meetings: this.meetingService.list(this.startupId),
      executives: this.executiveService.list(this.startupId),
      reportTokens: this.reportTokenService.listTokens(this.startupId),
    }).subscribe({
      next: ({ startup, indicators, meetings, executives, reportTokens }) => {
        this.startup.set(startup);
        this.indicators.set(indicators.items);
        this.meetings.set(meetings.items);
        this.executives.set(executives.items);
        this.reportTokens.set(reportTokens.items);
        this.loading.set(false);
      },
      error: (err) => {
        this.snackBar.open(err.error?.detail || 'Erro ao carregar dados', 'Fechar', { duration: 3000 });
        this.loading.set(false);
      },
    });
  }

  get latestIndicator(): MonthlyIndicator | null {
    const list = this.indicators();
    return list.length > 0 ? list[0] : null;
  }

  goBack(): void {
    this.router.navigate(['/portfolio-monitoring']);
  }

  formatCurrency(value: number | null): string {
    if (value == null) return '-';
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value);
  }

  extractDomain(url: string): string {
    try {
      return new URL(url).hostname.replace(/^www\./, '');
    } catch {
      return url;
    }
  }

  // Startup edit
  openEditStartup(): void {
    const s = this.startup();
    if (!s) return;
    const dialogRef = this.dialog.open(StartupFormDialog, {
      width: '560px',
      data: { startup: s } as StartupFormDialogData,
    });
    dialogRef.afterClosed().subscribe((result) => {
      if (result) {
        this.startupService.update(this.startupId, result).subscribe({
          next: () => {
            this.snackBar.open('Startup atualizada', 'Fechar', { duration: 3000 });
            this.loadAll();
          },
          error: (err) => this.snackBar.open(err.error?.detail || 'Erro ao atualizar startup', 'Fechar', { duration: 3000 }),
        });
      }
    });
  }

  onStatusChange(newStatus: StartupStatus): void {
    this.startupService.update(this.startupId, { status: newStatus }).subscribe({
      next: () => {
        this.snackBar.open('Status atualizado', 'Fechar', { duration: 3000 });
        this.loadAll();
      },
      error: (err) => this.snackBar.open(err.error?.detail || 'Erro ao atualizar status', 'Fechar', { duration: 3000 }),
    });
  }

  startEditing(field: 'name' | 'sector'): void {
    const s = this.startup();
    if (!s) return;
    this.editValue = s[field];
    this.editingField.set(field);
    setTimeout(() => {
      const inputRef = field === 'name' ? this.nameInput() : this.sectorInput();
      inputRef?.nativeElement.focus();
      inputRef?.nativeElement.select();
    });
  }

  openDatePicker(): void {
    const s = this.startup();
    if (!s) return;
    this.editDateValue = new Date(s.investment_date + 'T00:00:00');
    this.editingField.set('date');
    setTimeout(() => this.datePicker()?.open());
  }

  cancelEditing(): void {
    this.editingField.set(null);
  }

  saveField(field: 'name' | 'sector'): void {
    const trimmed = this.editValue.trim();
    const s = this.startup();
    if (!trimmed || !s || trimmed === s[field]) {
      this.cancelEditing();
      return;
    }
    this.editingField.set(null);
    this.startupService.update(this.startupId, { [field]: trimmed }).subscribe({
      next: () => {
        this.snackBar.open('Startup atualizada', 'Fechar', { duration: 3000 });
        this.loadAll();
      },
      error: (err) => this.snackBar.open(err.error?.detail || 'Erro ao atualizar startup', 'Fechar', { duration: 3000 }),
    });
  }

  onDateChange(date: Date | null): void {
    if (!date) return;
    const s = this.startup();
    const iso = date.toISOString().split('T')[0];
    if (!s || iso === s.investment_date) {
      this.cancelEditing();
      return;
    }
    this.editingField.set(null);
    this.startupService.update(this.startupId, { investment_date: iso }).subscribe({
      next: () => {
        this.snackBar.open('Startup atualizada', 'Fechar', { duration: 3000 });
        this.loadAll();
      },
      error: (err) => this.snackBar.open(err.error?.detail || 'Erro ao atualizar startup', 'Fechar', { duration: 3000 }),
    });
  }

  onFieldKeydown(event: KeyboardEvent, field: 'name' | 'sector'): void {
    if (event.key === 'Enter') {
      this.saveField(field);
    } else if (event.key === 'Escape') {
      this.cancelEditing();
    }
  }

  onDatePickerClosed(): void {
    setTimeout(() => {
      if (this.editingField() === 'date') {
        this.cancelEditing();
      }
    }, 200);
  }

  // Indicators
  openCreateIndicator(): void {
    const dialogRef = this.dialog.open(IndicatorFormDialog, {
      width: '560px',
      data: {} as IndicatorFormDialogData,
    });
    dialogRef.afterClosed().subscribe((result) => {
      if (result) {
        this.indicatorService.create(this.startupId, result).subscribe({
          next: () => {
            this.snackBar.open('Indicador criado', 'Fechar', { duration: 3000 });
            this.loadAll();
          },
          error: (err) => this.snackBar.open(err.error?.detail || 'Erro ao criar indicador', 'Fechar', { duration: 3000 }),
        });
      }
    });
  }

  openEditIndicator(indicator: MonthlyIndicator): void {
    const dialogRef = this.dialog.open(IndicatorFormDialog, {
      width: '560px',
      data: { indicator } as IndicatorFormDialogData,
    });
    dialogRef.afterClosed().subscribe((result) => {
      if (result) {
        this.indicatorService.update(this.startupId, indicator.id, result).subscribe({
          next: () => {
            this.snackBar.open('Indicador atualizado', 'Fechar', { duration: 3000 });
            this.loadAll();
          },
          error: (err) => this.snackBar.open(err.error?.detail || 'Erro ao atualizar indicador', 'Fechar', { duration: 3000 }),
        });
      }
    });
  }

  deleteIndicator(indicator: MonthlyIndicator): void {
    if (!confirm('Excluir este indicador?')) return;
    this.indicatorService.delete(this.startupId, indicator.id).subscribe({
      next: () => {
        this.snackBar.open('Indicador excluido', 'Fechar', { duration: 3000 });
        this.loadAll();
      },
      error: (err) => this.snackBar.open(err.error?.detail || 'Erro ao excluir indicador', 'Fechar', { duration: 3000 }),
    });
  }

  // Meetings
  openCreateMeeting(): void {
    const dialogRef = this.dialog.open(MeetingFormDialog, {
      width: '560px',
      data: {} as MeetingFormDialogData,
    });
    dialogRef.afterClosed().subscribe((result) => {
      if (result) {
        this.meetingService.create(this.startupId, result).subscribe({
          next: () => {
            this.snackBar.open('Reuniao criada', 'Fechar', { duration: 3000 });
            this.loadAll();
          },
          error: (err) => this.snackBar.open(err.error?.detail || 'Erro ao criar reunião', 'Fechar', { duration: 3000 }),
        });
      }
    });
  }

  openEditMeeting(meeting: BoardMeeting): void {
    const dialogRef = this.dialog.open(MeetingFormDialog, {
      width: '560px',
      data: { meeting } as MeetingFormDialogData,
    });
    dialogRef.afterClosed().subscribe((result) => {
      if (result) {
        this.meetingService.update(this.startupId, meeting.id, result).subscribe({
          next: () => {
            this.snackBar.open('Reuniao atualizada', 'Fechar', { duration: 3000 });
            this.loadAll();
          },
          error: (err) => this.snackBar.open(err.error?.detail || 'Erro ao atualizar reunião', 'Fechar', { duration: 3000 }),
        });
      }
    });
  }

  deleteMeeting(meeting: BoardMeeting): void {
    if (!confirm('Excluir esta reuniao?')) return;
    this.meetingService.delete(this.startupId, meeting.id).subscribe({
      next: () => {
        this.snackBar.open('Reuniao excluida', 'Fechar', { duration: 3000 });
        this.loadAll();
      },
      error: (err) => this.snackBar.open(err.error?.detail || 'Erro ao excluir reunião', 'Fechar', { duration: 3000 }),
    });
  }

  // Executives
  openCreateExecutive(): void {
    const dialogRef = this.dialog.open(ExecutiveFormDialog, {
      width: '480px',
      data: {} as ExecutiveFormDialogData,
    });
    dialogRef.afterClosed().subscribe((result) => {
      if (result) {
        this.executiveService.create(this.startupId, result).subscribe({
          next: () => {
            this.snackBar.open('Executivo criado', 'Fechar', { duration: 3000 });
            this.loadAll();
          },
          error: (err) => this.snackBar.open(err.error?.detail || 'Erro ao criar executivo', 'Fechar', { duration: 3000 }),
        });
      }
    });
  }

  openEditExecutive(executive: Executive): void {
    const dialogRef = this.dialog.open(ExecutiveFormDialog, {
      width: '480px',
      data: { executive } as ExecutiveFormDialogData,
    });
    dialogRef.afterClosed().subscribe((result) => {
      if (result) {
        this.executiveService.update(this.startupId, executive.id, result).subscribe({
          next: () => {
            this.snackBar.open('Executivo atualizado', 'Fechar', { duration: 3000 });
            this.loadAll();
          },
          error: (err) => this.snackBar.open(err.error?.detail || 'Erro ao atualizar executivo', 'Fechar', { duration: 3000 }),
        });
      }
    });
  }

  deleteExecutive(executive: Executive): void {
    if (!confirm(`Excluir "${executive.name}"?`)) return;
    this.executiveService.delete(this.startupId, executive.id).subscribe({
      next: () => {
        this.snackBar.open('Executivo excluido', 'Fechar', { duration: 3000 });
        this.loadAll();
      },
      error: (err) => this.snackBar.open(err.error?.detail || 'Erro ao excluir executivo', 'Fechar', { duration: 3000 }),
    });
  }

  // Report Tokens
  generateReportToken(): void {
    const now = new Date();
    const month = now.getMonth() + 1;
    const year = now.getFullYear();
    this.reportTokenService.generateToken(this.startupId, month, year).subscribe({
      next: (token) => {
        const url = `${window.location.origin}/report/${token.token}`;
        navigator.clipboard.writeText(url).then(() => {
          this.snackBar.open('Link gerado e copiado!', 'Fechar', { duration: 3000 });
        });
        this.loadAll();
      },
      error: (err) => this.snackBar.open(err.error?.detail || 'Erro ao gerar link', 'Fechar', { duration: 3000 }),
    });
  }

  openTokenListDialog(): void {
    this.dialog.open(ReportTokenListDialog, {
      width: '400px',
      data: { tokens: this.reportTokens() } as ReportTokenListDialogData,
    });
  }
}
