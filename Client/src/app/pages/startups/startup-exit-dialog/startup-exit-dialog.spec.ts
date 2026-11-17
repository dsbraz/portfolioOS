import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { of, throwError } from 'rxjs';

import { ExitType, Startup, StartupStatus } from '../../../models/startup.model';
import { StartupService } from '../../../services/startup.service';
import { StartupExitDialog } from './startup-exit-dialog';

describe('StartupExitDialog', () => {
  const startup: Startup = {
    id: 's1',
    name: 'Acme',
    site: null,
    logo_url: null,
    status: StartupStatus.HEALTHY,
    sector: 'Fintech',
    investment_date: '2024-01-10',
    equity_stake: 5,
    notes: null,
    exited_on: null,
    exit_type: null,
    exit_notes: null,
    created_at: '',
    updated_at: '',
  };

  let fixture: ComponentFixture<StartupExitDialog>;
  let component: StartupExitDialog;
  const dialogRef = { close: vi.fn() };
  const startupService = { recordExit: vi.fn() };

  beforeEach(async () => {
    dialogRef.close.mockReset();
    startupService.recordExit.mockReset();
    TestBed.resetTestingModule();
    await TestBed.configureTestingModule({
      imports: [StartupExitDialog],
      providers: [
        provideNoopAnimations(),
        { provide: MatDialogRef, useValue: dialogRef },
        { provide: MAT_DIALOG_DATA, useValue: { startup } },
        { provide: StartupService, useValue: startupService },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(StartupExitDialog);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  const fill = () =>
    component.form.setValue({
      exited_on: new Date(2026, 2, 20),
      exit_type: ExitType.WRITE_OFF,
      exit_notes: '  Encerrou as operações  ',
    });

  it('sends the local calendar date, the type and the trimmed notes', () => {
    startupService.recordExit.mockReturnValue(of({ ...startup, exited_on: '2026-03-20' }));
    fill();

    component.onSubmit();

    expect(startupService.recordExit).toHaveBeenCalledWith('s1', {
      exited_on: '2026-03-20',
      exit_type: ExitType.WRITE_OFF,
      exit_notes: 'Encerrou as operações',
    });
    expect(dialogRef.close).toHaveBeenCalledWith(true);
  });

  it('sends blank notes as absent', () => {
    startupService.recordExit.mockReturnValue(of(startup));
    fill();
    component.form.controls.exit_notes.setValue('   ');

    component.onSubmit();

    expect(startupService.recordExit.mock.calls[0][1].exit_notes).toBeNull();
  });

  it('does not submit without date and type', () => {
    component.onSubmit();

    expect(startupService.recordExit).not.toHaveBeenCalled();
  });

  it('stays open with what was typed and shows the refusal', () => {
    startupService.recordExit.mockReturnValue(
      throwError(() => ({ error: { detail: 'Saída da startup já registrada' } })),
    );
    fill();

    component.onSubmit();
    fixture.detectChanges();

    expect(dialogRef.close).not.toHaveBeenCalled();
    expect(component.form.controls.exit_type.value).toBe(ExitType.WRITE_OFF);
    const alert = (fixture.nativeElement as HTMLElement).querySelector('[role="alert"]');
    expect(alert?.textContent).toContain('Saída da startup já registrada');
    expect(component.saving()).toBe(false);
  });
});
