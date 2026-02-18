import { Component, inject, OnInit } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatButtonModule } from '@angular/material/button';

import {
  Deal,
  DealColumn,
  DEAL_COLUMN_CONFIG,
  DEAL_STAGE_OPTIONS,
} from '../../../models/deal.model';

export interface DealFormDialogData {
  deal?: Deal;
  defaultColumn?: DealColumn;
}

@Component({
  selector: 'app-deal-form-dialog',
  imports: [
    ReactiveFormsModule,
    MatDialogModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatButtonModule,
  ],
  templateUrl: './deal-form-dialog.html',
  styleUrl: './deal-form-dialog.scss',
})
export class DealFormDialog implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly dialogRef = inject(MatDialogRef<DealFormDialog>);
  readonly data: DealFormDialogData = inject(MAT_DIALOG_DATA);

  readonly isEditMode = !!this.data?.deal;
  readonly columnOptions = Object.values(DealColumn);
  readonly columnConfig = DEAL_COLUMN_CONFIG;
  readonly stageOptions = DEAL_STAGE_OPTIONS;

  readonly form = this.fb.group({
    company: ['', [Validators.required, Validators.maxLength(255)]],
    sector: [''],
    stage: [''],
    founders: [''],
    column: [this.data?.defaultColumn ?? DealColumn.NEW],
    notes: [''],
    next_step: [''],
    internal_owner: [''],
  });

  ngOnInit(): void {
    if (this.data?.deal) {
      this.form.patchValue(this.data.deal);
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
