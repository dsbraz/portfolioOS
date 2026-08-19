import { Component, inject, OnInit } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';

import { Executive } from '../../../models/executive.model';
import { emailValidator, normalizeContactEmail } from '../../../models/email';
import {
  formatPhone,
  normalizeInternationalPhone,
  phoneCountryPrefixValidator,
} from '../../../models/whatsapp';

export interface ExecutiveFormDialogData {
  executive?: Executive;
  readonly?: boolean;
}

import { DialogHeader } from '../../../components/dialog-header/dialog-header';
import { ReadSection, ReadView } from '../../../components/read-view/read-view';

@Component({
  selector: 'app-executive-form-dialog',
  imports: [
    DialogHeader,
    ReadView,
    ReactiveFormsModule,
    MatDialogModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
  ],
  templateUrl: './executive-form-dialog.html',
  styleUrl: './executive-form-dialog.scss',
})
export class ExecutiveFormDialog implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly dialogRef = inject(MatDialogRef<ExecutiveFormDialog>);
  readonly data: ExecutiveFormDialogData = inject(MAT_DIALOG_DATA);

  readonly isEditMode = !!this.data?.executive;
  readonly isReadonly = !!this.data?.readonly;

  readonly form = this.fb.group({
    name: ['', [Validators.required, Validators.maxLength(255)]],
    role: [''],
    // The e-mail is a send channel, so an address we cannot compose to is
    // refused here rather than discovered at send time.
    email: ['', [emailValidator]],
    // The country prefix is mandatory: the fund's executives are not all in
    // Brazil, so a local-format number cannot be told apart from a foreign one.
    phone: ['', [phoneCountryPrefixValidator]],
    linkedin: [''],
  });

  /** Ver [[ReadView]]: o modo leitura deixou de ser um formulário desabilitado. */
  readonly readSections: ReadSection[] = this.buildReadSections();

  /** O executivo não tem grupos no modo de edição, então também não tem aqui. */
  private buildReadSections(): ReadSection[] {
    const e = this.data?.executive;
    if (!e) return [];

    return [
      {
        items: [
          { label: 'Nome', value: e.name || null },
          { label: 'Cargo', value: e.role || null },
          { label: 'Email', value: e.email || null },
          // Falls back to the raw value so a legacy record without the prefix
          // is shown as it is, rather than disappearing behind a "—".
          { label: 'Telefone', value: formatPhone(e.phone) ?? e.phone ?? null },
          { label: 'LinkedIn', value: e.linkedin || null, kind: 'long' },
        ],
      },
    ];
  }

  ngOnInit(): void {
    if (this.data?.executive) {
      this.form.patchValue(this.data.executive);
    }
  }

  onSubmit(): void {
    if (this.form.invalid) {
      // Reveal the error instead of doing nothing silently.
      this.form.markAllAsTouched();
      return;
    }
    const raw = this.form.getRawValue();
    // Stored in the same shapes the server persists: E.164 and a lowercased
    // address.
    this.dialogRef.close({
      ...raw,
      phone: normalizeInternationalPhone(raw.phone),
      email: normalizeContactEmail(raw.email),
    });
  }

  onCancel(): void {
    this.dialogRef.close();
  }
}
