import { TestBed } from '@angular/core/testing';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { NEVER, of } from 'rxjs';
import { ActivatedRoute, Router } from '@angular/router';
import { MatDialog } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';

import { StartupDetail } from './startup-detail';
import { StartupService } from '../../../services/startup.service';
import { MonthlyIndicatorService } from '../../../services/monthly-indicator.service';
import { BoardMeetingService } from '../../../services/board-meeting.service';
import { ExecutiveService } from '../../../services/executive.service';
import { MonthlyIndicatorTokenService } from '../../../services/monthly-indicator-token.service';
import { MonthlyIndicator } from '../../../models/monthly-indicator.model';
import { Startup, StartupStatus } from '../../../models/startup.model';
import { participationValue } from '../../../models/participation';

describe('StartupDetail (totalParticipation)', () => {
  let component: StartupDetail;
  // Reference is the latest reported indicator; the list arrives API-sorted desc.
  const REF_YEAR = 2026;

  const baseStartup = (equityStake: number | null): Startup => ({
    id: 's1',
    name: 'Acme',
    site: null,
    logo_url: null,
    status: StartupStatus.HEALTHY,
    sector: 'Fintech',
    investment_date: '2025-01-01',
    equity_stake: equityStake,
    notes: null,
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z',
  });

  const indicator = (m: number, y: number, revenue: number | null): MonthlyIndicator =>
    ({
      id: `${y}-${m}`,
      startup_id: 's1',
      month: m,
      year: y,
      total_revenue: revenue,
      recurring_revenue_pct: null,
      gross_margin_pct: null,
      cash_balance: null,
      headcount: null,
      ebitda_burn: null,
      achievements: null,
      challenges: null,
      comments: null,
      created_at: '',
      updated_at: '',
    });

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        { provide: ActivatedRoute, useValue: { snapshot: { paramMap: { get: () => 's1' } } } },
        { provide: Router, useValue: {} },
        { provide: MatDialog, useValue: {} },
        { provide: MatSnackBar, useValue: {} },
        { provide: StartupService, useValue: {} },
        { provide: MonthlyIndicatorService, useValue: {} },
        { provide: BoardMeetingService, useValue: {} },
        { provide: ExecutiveService, useValue: {} },
        { provide: MonthlyIndicatorTokenService, useValue: {} },
      ],
    });
    component = TestBed.createComponent(StartupDetail).componentInstance;
  });

  it('accumulates revenue of the latest indicator year up to its month', () => {
    component.startup.set(baseStartup(5));
    // latestIndicator = first item (April 2026).
    component.indicators.set([
      indicator(4, REF_YEAR, 50000),
      indicator(1, REF_YEAR, 100000),
      indicator(12, REF_YEAR - 1, 999999), // previous year => excluded
    ]);

    // (100000 + 50000) accumulated over 4 months.
    expect(component.totalParticipation).toBe(participationValue(150000, 4, 5));
  });

  it('sums Decimal-as-string revenues without producing NaN', () => {
    // Regression: the API serializes total_revenue as a JSON string.
    component.startup.set(baseStartup(5));
    component.indicators.set([
      indicator(2, REF_YEAR, '50000.00' as any),
      indicator(1, REF_YEAR, '100000.00' as any),
    ]);

    const result = component.totalParticipation;
    expect(Number.isNaN(result as number)).toBe(false);
    expect(result).toBe(participationValue(150000, 2, 5));
  });

  it('treats null revenue within the reference year as zero', () => {
    component.startup.set(baseStartup(5));
    component.indicators.set([indicator(4, REF_YEAR, null), indicator(1, REF_YEAR, 100000)]);

    // Reference month is 4 (latest), accumulated revenue is 100000.
    expect(component.totalParticipation).toBe(participationValue(100000, 4, 5));
  });

  it('returns zero (not null) when equity stake is zero', () => {
    component.startup.set(baseStartup(0));
    component.indicators.set([indicator(1, REF_YEAR, 100000)]);

    expect(component.totalParticipation).toBe(0);
  });

  it('returns null when there is no equity stake', () => {
    component.startup.set(baseStartup(null));
    component.indicators.set([indicator(1, REF_YEAR, 100000)]);

    expect(component.totalParticipation).toBeNull();
  });

  it('returns null when there are no indicators', () => {
    component.startup.set(baseStartup(5));
    component.indicators.set([]);

    expect(component.totalParticipation).toBeNull();
  });
});

describe('StartupDetail (carregamento e ARIA)', () => {
  const startup: Startup = {
    id: 's1',
    name: 'Acme',
    site: null,
    logo_url: null,
    status: StartupStatus.HEALTHY,
    sector: 'Fintech',
    investment_date: '2025-01-01',
    equity_stake: 5,
    notes: null,
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z',
  };

  const lista = (items: unknown[]) => ({ items, total: items.length });

  /** `pendente` deixa as chamadas sem emitir, que é o estado de carregando. */
  const montar = async (pendente = false) => {
    const resposta = <T,>(valor: T) => (pendente ? NEVER : of(valor));

    TestBed.resetTestingModule();
    await TestBed.configureTestingModule({
      imports: [StartupDetail],
      providers: [
        provideNoopAnimations(),
        { provide: ActivatedRoute, useValue: { snapshot: { paramMap: { get: () => 's1' } } } },
        { provide: Router, useValue: {} },
        { provide: MatDialog, useValue: {} },
        { provide: MatSnackBar, useValue: { open: vi.fn() } },
        { provide: StartupService, useValue: { getById: () => resposta(startup) } },
        {
          provide: MonthlyIndicatorService,
          useValue: { list: () => resposta(lista([indicatorFixture])) },
        },
        { provide: BoardMeetingService, useValue: { list: () => resposta(lista([])) } },
        { provide: ExecutiveService, useValue: { list: () => resposta(lista([])) } },
        { provide: MonthlyIndicatorTokenService, useValue: { list: () => resposta(lista([])) } },
      ],
    }).compileComponents();

    const fixture = TestBed.createComponent(StartupDetail);
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
    return fixture.nativeElement as HTMLElement;
  };

  const indicatorFixture: MonthlyIndicator = {
    id: 'i1',
    startup_id: 's1',
    month: 7,
    year: 2026,
    total_revenue: 1000,
    recurring_revenue_pct: null,
    gross_margin_pct: null,
    cash_balance: null,
    headcount: null,
    ebitda_burn: null,
    achievements: null,
    challenges: null,
    comments: null,
    created_at: '',
    updated_at: '',
  };

  // Antes a página não renderizava NADA enquanto carregava, e um container
  // vazio é indistinguível de "não há dados" — para quem lê a tela e para
  // qualquer agente que raspe o DOM cedo demais.
  it('should announce that it is loading instead of rendering an empty page', async () => {
    const el = await montar(true);

    expect(el.querySelector('[aria-busy="true"]')).toBeTruthy();
    expect(el.querySelector('[role="status"]')?.textContent).toContain('Carregando');
    expect(el.querySelector('[role="tabpanel"]')).toBeNull();
  });

  it('should drop the busy state once the data arrives', async () => {
    const el = await montar();

    expect(el.querySelector('[aria-busy="true"]')).toBeNull();
    expect(el.querySelector('h1')?.textContent).toContain('Acme');
  });

  // Regressão: as abas declaram `aria-controls`, mas só o painel ativo era
  // renderizado — duas das três referências apontavam para ids inexistentes.
  it('should point every tab at a panel that exists', async () => {
    const el = await montar();

    const abas = [...el.querySelectorAll('[role="tab"]')];
    expect(abas.length).toBe(3);

    for (const aba of abas) {
      const id = aba.getAttribute('aria-controls');
      expect(id).toBeTruthy();
      expect(el.querySelector(`#${id}`)).toBeTruthy();
    }
  });

  it('should keep only the selected panel visible', async () => {
    const el = await montar();

    const paineis = [...el.querySelectorAll('[role="tabpanel"]')];
    expect(paineis.length).toBe(3);
    expect(paineis.filter(p => !p.hasAttribute('hidden')).length).toBe(1);
  });

  // Três botões `more_vert` iguais por tabela apareciam como "button" sem
  // rótulo: nada distinguia a linha a que cada um pertence.
  it('should name every row action button with its row', async () => {
    const el = await montar();

    const acoes = [...el.querySelectorAll('button[mat-icon-button][aria-haspopup], button[mat-icon-button]')]
      .filter(b => b.closest('td'));
    expect(acoes.length).toBeGreaterThan(0);
    for (const botao of acoes) {
      expect(botao.getAttribute('aria-label')).toBeTruthy();
    }
    expect(el.querySelector('td button[mat-icon-button]')?.getAttribute('aria-label'))
      .toBe('Ações do indicador de Jul/2026');
  });
});

describe('StartupDetail (ordenação)', () => {
  const criar = () => {
    TestBed.resetTestingModule();
    TestBed.configureTestingModule({
      providers: [
        { provide: ActivatedRoute, useValue: { snapshot: { paramMap: { get: () => 's1' } } } },
        { provide: Router, useValue: {} },
        { provide: MatDialog, useValue: {} },
        { provide: MatSnackBar, useValue: {} },
        { provide: StartupService, useValue: {} },
        { provide: MonthlyIndicatorService, useValue: {} },
        { provide: BoardMeetingService, useValue: {} },
        { provide: ExecutiveService, useValue: {} },
        { provide: MonthlyIndicatorTokenService, useValue: {} },
      ],
    });
    return TestBed.createComponent(StartupDetail).componentInstance;
  };

  const ind = (m: number, y: number, revenue: number | null = null): MonthlyIndicator =>
    ({
      id: `${y}-${m}`, startup_id: 's1', month: m, year: y,
      total_revenue: revenue, recurring_revenue_pct: null, gross_margin_pct: null,
      cash_balance: null, headcount: null, ebitda_burn: null,
      achievements: null, challenges: null, comments: null,
      created_at: '', updated_at: '',
    });

  // "Período" mostra `Jul/2026`. Ordenado como texto, Ago viria antes de Jul e
  // Dez antes de Fev — a coluna precisa ordenar pelo que ela É.
  it('should sort the period column chronologically, not alphabetically', () => {
    const component = criar();
    component.indicators.set([ind(7, 2026), ind(8, 2026), ind(12, 2025), ind(2, 2026)]);
    component.indicatorSort.set({ active: 'period', direction: 'asc' });

    expect(component.sortedIndicators().map(i => `${i.month}/${i.year}`))
      .toEqual(['12/2025', '2/2026', '7/2026', '8/2026']);
  });

  it('should keep indicators without revenue last when sorting by revenue', () => {
    const component = criar();
    component.indicators.set([ind(1, 2026, null), ind(2, 2026, 500), ind(3, 2026, 100)]);
    component.indicatorSort.set({ active: 'total_revenue', direction: 'desc' });

    expect(component.sortedIndicators().map(i => i.total_revenue)).toEqual([500, 100, null]);
  });

  it('should leave the rows untouched while no column is active', () => {
    const component = criar();
    const rows = [ind(2, 2026), ind(1, 2026)];
    component.indicators.set(rows);

    expect(component.sortedIndicators().map(i => i.month)).toEqual([2, 1]);
  });
});
