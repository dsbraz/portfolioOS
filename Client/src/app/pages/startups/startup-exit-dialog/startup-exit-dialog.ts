import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { provideNativeDateAdapter } from '@angular/material/core';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';

import { DialogHeader } from '../../../components/dialog-header/dialog-header';
import { EXIT_TYPE_LABELS, ExitType, Startup } from '../../../models/startup.model';
import { StartupService } from '../../../services/startup.service';

export interface StartupExitDialogData {
  startup: Startup;
}

/**
 * Records that the fund left a startup. Transactional: it calls the service
 * itself, so a refusal from the server (a date before the investment, an exit
 * already recorded) keeps what was typed and shows why. Closes `true` only on
 * success; until then nothing changed, so every other way out reports nothing.
 */
@Component({
  selector: 'app-startup-exit-dialog',
  imports: [
    DialogHeader,
    ReactiveFormsModule,
    MatButtonModule,
    MatDatepickerModule,
    MatDialogModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
  ],
  providers: [provideNativeDateAdapter()],
  templateUrl: './startup-exit-dialog.html',
  styleUrl: './startup-exit-dialog.scss',
})
export class StartupExitDialog {
  private readonly fb = inject(FormBuilder);
  private readonly startupService = inject(StartupService);
  private readonly dialogRef = inject(MatDialogRef<StartupExitDialog>);
  readonly data: StartupExitDialogData = inject(MAT_DIALOG_DATA);

  readonly exitTypes = Object.values(ExitType);
  readonly exitTypeLabels = EXIT_TYPE_LABELS;
  readonly today = new Date();
  readonly minDate = new Date(this.data.startup.investment_date + 'T00:00:00');

  readonly form = this.fb.group({
    exited_on: [null as Date | null, Validators.required],
    exit_type: [null as ExitType | null, Validators.required],
    exit_notes: [''],
  });

  readonly saving = signal(false);
  readonly error = signal<string | null>(null);

  onSubmit(): void {
    if (this.form.invalid || this.saving()) return;
    const { exited_on, exit_type, exit_notes } = this.form.getRawValue();

    this.saving.set(true);
    this.error.set(null);
    this.startupService
      .recordExit(this.data.startup.id, {
        exited_on: toIsoDate(exited_on!),
        exit_type: exit_type!,
        exit_notes: exit_notes?.trim() || null,
      })
      .subscribe({
        next: () => this.dialogRef.close(true),
        error: (err) => {
          this.saving.set(false);
          this.error.set(err.error?.detail || 'Não foi possível registrar a saída.');
        },
      });
  }
}

/** Local calendar date, so a date near midnight never shifts a day in UTC. */
function toIsoDate(value: Date): string {
  const month = String(value.getMonth() + 1).padStart(2, '0');
  const day = String(value.getDate()).padStart(2, '0');
  return `${value.getFullYear()}-${month}-${day}`;
}
