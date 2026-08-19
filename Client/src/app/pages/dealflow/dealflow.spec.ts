import { TestBed } from '@angular/core/testing';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { MatDialog } from '@angular/material/dialog';
import { of } from 'rxjs';

import { Deal } from '../../models/deal.model';
import { DealService } from '../../services/deal.service';
import { Dealflow } from './dealflow';

describe('Dealflow', () => {
  const deal = {
    id: 'd1',
    company: 'Cardume',
    stage: 'novo',
    sector: 'SaaS',
    position: 0,
  } as unknown as Deal;

  const dealService = { list: vi.fn(() => of({ items: [deal], total: 1 })) };
  const dialog = { open: vi.fn(() => ({ afterClosed: () => of(undefined) })) };

  async function render(): Promise<HTMLElement> {
    await TestBed.configureTestingModule({
      imports: [Dealflow],
      providers: [
        provideNoopAnimations(),
        { provide: DealService, useValue: dealService },
      ],
    })
      // MatDialogModule (imported by the component) provides its own MatDialog;
      // overrideProvider wins over that, a plain provider does not.
      .overrideProvider(MatDialog, { useValue: dialog })
      .compileComponents();

    const fixture = TestBed.createComponent(Dealflow);
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
    return fixture.nativeElement as HTMLElement;
  }

  afterEach(() => {
    TestBed.resetTestingModule();
    vi.clearAllMocks();
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
});
