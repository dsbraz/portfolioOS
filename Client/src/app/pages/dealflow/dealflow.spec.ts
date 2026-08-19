import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { MatDialog } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';
import { of, throwError } from 'rxjs';

import { Deal } from '../../models/deal.model';
import { DealService } from '../../services/deal.service';
import { Dealflow } from './dealflow';

describe('Dealflow', () => {
  let deal: Deal;
  let lastFixture: ComponentFixture<Dealflow> | null = null;

  const dealService = {
    list: vi.fn(),
    move: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
  };
  const dialog = { open: vi.fn() };
  const snackBar = { open: vi.fn() };

  beforeEach(() => {
    // Rebuilt per test: onDealDrop mutates the deal's stage in place.
    deal = {
      id: 'd1',
      company: 'Cardume',
      stage: 'novo',
      sector: 'SaaS',
      position: 0,
    } as unknown as Deal;
    dealService.list = vi.fn(() => of({ items: [deal], total: 1 }));
    dialog.open = vi.fn(() => ({ afterClosed: () => of(undefined) })) as never;
  });

  async function render(): Promise<HTMLElement> {
    await TestBed.configureTestingModule({
      imports: [Dealflow],
      providers: [
        provideNoopAnimations(),
        { provide: DealService, useValue: dealService },
      ],
    })
      // Material modules imported by the component provide their own MatDialog
      // and MatSnackBar; overrideProvider wins over that, a plain provider
      // does not.
      .overrideProvider(MatDialog, { useValue: dialog })
      .overrideProvider(MatSnackBar, { useValue: snackBar })
      .compileComponents();

    lastFixture = TestBed.createComponent(Dealflow);
    lastFixture.detectChanges();
    await lastFixture.whenStable();
    lastFixture.detectChanges();
    return lastFixture.nativeElement as HTMLElement;
  }

  afterEach(() => {
    TestBed.resetTestingModule();
    vi.clearAllMocks();
    vi.restoreAllMocks();
  });

  // Regressão: o card era pointer-only. Um card que só responde a clique não é
  // um controle — sem papel, sem nome e sem caminho por teclado —, então nem
  // leitor de tela nem agente conseguiam abrir um negócio.
  it('opens a deal from a named, keyboard-reachable control', async () => {
    const element = await render();

    const opener = element.querySelector<HTMLButtonElement>(
      '[aria-label="Abrir negócio Cardume"]',
    );

    expect(opener?.tagName).toBe('BUTTON');
    opener!.click();
    expect(dialog.open).toHaveBeenCalled();
  });

  it('groups deals under their stage column', async () => {
    const element = await render();

    expect(element.textContent).toContain('Cardume');
    // The grouped map places the deal under its own stage and nowhere else.
    const grouped = fixtureComponentOf(element).dealsByStage();
    expect(grouped['novo'].map((d) => d.company)).toEqual(['Cardume']);
    expect(grouped['investido']).toEqual([]);
  });

  it('moves a deal via the menu and reports the target stage by name', async () => {
    dealService.move = vi.fn(() => of(deal));
    const element = await render();
    const component = fixtureComponentOf(element);

    component.moveDeal(deal, 'comite' as never);

    expect(dealService.move).toHaveBeenCalledWith('d1', { stage: 'comite', position: 0 });
    expect(snackBar.open).toHaveBeenCalledWith(
      'Deal movido para "Comite"',
      'Fechar',
      expect.anything(),
    );
  });

  it('reloads after a failed board drop, so the screen never lies about the stage', async () => {
    dealService.move = vi.fn(() => throwError(() => ({ error: { detail: 'boom' } })));
    const element = await render();
    const component = fixtureComponentOf(element);
    const origem = [deal];
    const destino: Deal[] = [];
    const drop = {
      container: { id: 'comite', data: destino },
      previousContainer: { id: 'novo', data: origem },
      item: { data: deal },
      previousIndex: 0,
      currentIndex: 0,
    } as never;

    component.onDealDrop(drop);

    // The optimistic move happened locally…
    expect(destino).toContain(deal);
    expect(deal.stage).toBe('comite');
    // …but the server refused, so the board re-syncs from the source of truth.
    expect(snackBar.open).toHaveBeenCalledWith('boom', 'Fechar', expect.anything());
    expect(dealService.list).toHaveBeenCalledTimes(2);
  });

  it('deletes only after the person confirms, and never on refusal', async () => {
    dealService.delete = vi.fn(() => of(void 0));
    const element = await render();
    const component = fixtureComponentOf(element);

    vi.spyOn(window, 'confirm').mockReturnValueOnce(false);
    component.deleteDeal(deal);
    expect(dealService.delete).not.toHaveBeenCalled();

    vi.spyOn(window, 'confirm').mockReturnValueOnce(true);
    component.deleteDeal(deal);
    expect(dealService.delete).toHaveBeenCalledWith('d1');
  });

  it('creates a deal from the dialog result and refreshes the board', async () => {
    dealService.create = vi.fn(() => of(deal));
    dialog.open = vi.fn(() => ({
      afterClosed: () => of({ company: 'Nova Co', stage: 'novo' }),
    })) as never;
    const element = await render();
    const component = fixtureComponentOf(element);

    component.openCreateDialog();

    expect(dealService.create).toHaveBeenCalledWith({ company: 'Nova Co', stage: 'novo' });
    expect(dealService.list).toHaveBeenCalledTimes(2);
  });

  it('surfaces a load failure instead of an empty board', async () => {
    dealService.list = vi.fn(() =>
      throwError(() => ({ error: { detail: 'sem acesso' } })),
    );
    await render();

    expect(snackBar.open).toHaveBeenCalledWith('sem acesso', 'Fechar', expect.anything());
  });

  function fixtureComponentOf(_el: HTMLElement): Dealflow {
    return lastFixture!.componentInstance;
  }
});
