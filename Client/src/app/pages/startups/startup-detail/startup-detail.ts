import { Component, ElementRef, computed, inject, OnInit, signal, viewChild, viewChildren } from '@angular/core';
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
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSortModule } from '@angular/material/sort';
import { MatTableModule } from '@angular/material/table';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatMenuModule } from '@angular/material/menu';
import { MatTooltipModule } from '@angular/material/tooltip';
import { forkJoin } from 'rxjs';

import { Startup, StartupStatus, STARTUP_STATUS_CONFIG } from '../../../models/startup.model';
import { MonthlyIndicator, MONTH_LABELS } from '../../../models/monthly-indicator.model';
import { formatCurrencyBRL } from '../../../models/formatters';
import { formatPhone as toDisplayPhone } from '../../../models/whatsapp';
import { SortState, applySort } from '../../../models/sorting';
import { participationValue } from '../../../models/participation';
import { BoardMeeting } from '../../../models/board-meeting.model';
import { Executive } from '../../../models/executive.model';
import { StartupService } from '../../../services/startup.service';
import { MonthlyIndicatorService } from '../../../services/monthly-indicator.service';
import { BoardMeetingService } from '../../../services/board-meeting.service';
import { ExecutiveService } from '../../../services/executive.service';
import { MonthlyIndicatorTokenService } from '../../../services/monthly-indicator-token.service';
import { MonthlyIndicatorToken } from '../../../models/monthly-indicator-token.model';
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
  TokenListDialog,
  TokenListDialogData,
} from '../token-list-dialog/token-list-dialog';
import {
  AddIndicatorDialog,
  AddIndicatorDialogData,
} from '../add-indicator-dialog/add-indicator-dialog';

import { KpiCard } from '../../../components/kpi-card/kpi-card';

@Component({
  selector: 'app-startup-detail',
  imports: [
    KpiCard,
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
    MatProgressSpinnerModule,
    MatSortModule,
    MatTableModule,
    MatExpansionModule,
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
  private readonly tokenService = inject(MonthlyIndicatorTokenService);

  readonly startup = signal<Startup | null>(null);
  readonly indicators = signal<MonthlyIndicator[]>([]);
  readonly meetings = signal<BoardMeeting[]>([]);
  readonly executives = signal<Executive[]>([]);
  readonly tokens = signal<MonthlyIndicatorToken[]>([]);
  readonly loading = signal(false);
  readonly monthLabels = MONTH_LABELS;
  readonly statusConfig = STARTUP_STATUS_CONFIG;

  private startupId = '';

  readonly tabButtons = viewChildren<ElementRef<HTMLButtonElement>>('tabBtn');

  /** Seções da página. A ordem define a navegação por setas do tablist. */
  readonly sections = [
    { id: 'indicadores' as const, label: 'Indicadores Mensais' },
    { id: 'reunioes' as const, label: 'Reuniões de Conselho' },
    { id: 'executivos' as const, label: 'Executivos' },
  ];
  readonly activeSection = signal<'indicadores' | 'reunioes' | 'executivos'>('indicadores');

  selectSection(id: 'indicadores' | 'reunioes' | 'executivos'): void {
    this.activeSection.set(id);
  }

  countFor(id: 'indicadores' | 'reunioes' | 'executivos'): number {
    if (id === 'indicadores') return this.indicators().length;
    if (id === 'reunioes') return this.meetings().length;
    return this.executives().length;
  }

  /**
   * Arrow-key navigation for the tablist (WAI-ARIA APG). Tab moves OUT of the
   * tablist; moving BETWEEN tabs is the arrow keys' job, which is why the
   * inactive tabs carry `tabindex="-1"` (roving tabindex).
   */
  onTabKeydown(event: KeyboardEvent, index: number): void {
    const last = this.sections.length - 1;
    let next: number | null = null;

    if (event.key === 'ArrowRight') next = index === last ? 0 : index + 1;
    else if (event.key === 'ArrowLeft') next = index === 0 ? last : index - 1;
    else if (event.key === 'Home') next = 0;
    else if (event.key === 'End') next = last;
    if (next === null) return;

    event.preventDefault();
    this.selectSection(this.sections[next].id);
    this.tabButtons()[next]?.nativeElement.focus();
  }

  readonly indicatorColumns = ['period', 'total_revenue', 'cash_balance', 'ebitda_burn', 'headcount', 'actions'];
  readonly meetingColumns = ['meeting_date', 'summary', 'actions'];
  readonly executiveColumns = ['name', 'role', 'email', 'phone', 'actions'];

  readonly indicatorSort = signal<SortState>({ active: '', direction: '' });
  readonly meetingSort = signal<SortState>({ active: '', direction: '' });
  readonly executiveSort = signal<SortState>({ active: '', direction: '' });

  /**
   * "Período" mostra `Jul/2026`, mas ordena por ano e mês. Comparar o texto
   * poria Ago antes de Jul, e 2025 no meio de 2026.
   */
  readonly sortedIndicators = computed(() =>
    applySort(this.indicators(), this.indicatorSort(), {
      period: (i) => i.year * 100 + i.month,
      total_revenue: (i) => i.total_revenue,
      cash_balance: (i) => i.cash_balance,
      ebitda_burn: (i) => i.ebitda_burn,
      headcount: (i) => i.headcount,
    }),
  );

  readonly sortedMeetings = computed(() =>
    applySort(this.meetings(), this.meetingSort(), {
      // Data ISO (`YYYY-MM-DD`) já ordena corretamente como texto.
      meeting_date: (m) => m.meeting_date,
      summary: (m) => m.summary,
    }),
  );

  readonly sortedExecutives = computed(() =>
    applySort(this.executives(), this.executiveSort(), {
      name: (e) => e.name,
      role: (e) => e.role,
      email: (e) => e.email,
      phone: (e) => e.phone,
    }),
  );

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
      tokens: this.tokenService.list(this.startupId),
    }).subscribe({
      next: ({ startup, indicators, meetings, executives, tokens }) => {
        this.startup.set(startup);
        this.indicators.set(indicators.items);
        this.meetings.set(meetings.items);
        this.executives.set(executives.items);
        this.tokens.set(tokens.items);
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

  get totalParticipation(): number | null {
    const s = this.startup();
    const ref = this.latestIndicator;
    if (!s || !ref) return null;

    // Reference period = latest reported indicator (same as the Resumo Atual card).
    // Accumulate that year's revenue up to the reference month, then annualize over it.
    const accumulated = this.indicators()
      .filter((i) => i.year === ref.year && i.month <= ref.month)
      .reduce((acc, i) => acc + Number(i.total_revenue ?? 0), 0);
    return participationValue(accumulated, ref.month, s.equity_stake);
  }

  formatCurrency(value: number | null): string {
    return formatCurrencyBRL(value) ?? '-';
  }

  /** Falls back to the stored value so a legacy record without the country
   *  prefix stays visible — and visibly in need of a fix. */
  formatPhone(value: string | null): string {
    return toDisplayPhone(value) ?? value ?? '-';
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

  deleteStartup(): void {
    const s = this.startup();
    if (!s) return;
    if (!confirm(`Excluir a startup "${s.name}"? Esta ação não pode ser desfeita.`)) return;
    this.startupService.delete(this.startupId).subscribe({
      next: () => {
        this.snackBar.open('Startup excluída', 'Fechar', { duration: 3000 });
        this.router.navigate(['/portfolio']);
      },
      error: (err) => this.snackBar.open(err.error?.detail || 'Erro ao excluir startup', 'Fechar', { duration: 3000 }),
    });
  }

  // Indicators
  openViewIndicator(indicator: MonthlyIndicator): void {
    this.dialog.open(IndicatorFormDialog, {
      width: '560px',
      data: { indicator, readonly: true } as IndicatorFormDialogData,
    });
  }

  openCreateIndicator(): void {
    // The single entry point: pick the period, then fill now or generate a link.
    // The dialog does the create/generate itself and closes truthy on a change,
    // so there is no false "Indicador criado" over an upsert here.
    const dialogRef = this.dialog.open(AddIndicatorDialog, {
      width: '640px',
      data: {
        startupId: this.startupId,
        indicators: this.indicators(),
        tokens: this.tokens(),
        executives: this.executives(),
      } as AddIndicatorDialogData,
    });
    dialogRef.afterClosed().subscribe((changed) => {
      if (changed) this.loadAll();
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
  openViewMeeting(meeting: BoardMeeting): void {
    this.dialog.open(MeetingFormDialog, {
      width: '560px',
      data: { meeting, readonly: true } as MeetingFormDialogData,
    });
  }

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
  openViewExecutive(executive: Executive): void {
    this.dialog.open(ExecutiveFormDialog, {
      width: '480px',
      data: { executive, readonly: true } as ExecutiveFormDialogData,
    });
  }

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

  openTokenListDialog(): void {
    this.dialog.open(TokenListDialog, {
      width: '400px',
      data: { tokens: this.tokens(), executives: this.executives() } as TokenListDialogData,
    });
  }
}
