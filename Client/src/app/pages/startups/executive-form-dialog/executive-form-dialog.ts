import { Component, inject, OnInit } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';

import { Executive } from '../../../models/executive.model';

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
    email: [''],
    phone: [''],
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
          { label: 'Telefone', value: e.phone || null },
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
    if (this.form.invalid) return;
    this.dialogRef.close(this.form.getRawValue());
  }

  onCancel(): void {
    this.dialogRef.close();
  }
}
