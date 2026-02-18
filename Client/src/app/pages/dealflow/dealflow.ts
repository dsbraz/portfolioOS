import { Component, inject, OnInit, signal } from '@angular/core';
import { CdkDragDrop, CdkDrag, CdkDropList, moveItemInArray, transferArrayItem } from '@angular/cdk/drag-drop';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatCardModule } from '@angular/material/card';
import { MatMenuModule } from '@angular/material/menu';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatChipsModule } from '@angular/material/chips';

import {
  Deal,
  DealColumn,
  DEAL_COLUMN_CONFIG,
} from '../../models/deal.model';
import { DealService } from '../../services/deal.service';
import {
  DealFormDialog,
  DealFormDialogData,
} from './deal-form-dialog/deal-form-dialog';

@Component({
  selector: 'app-dealflow',
  imports: [
    MatButtonModule,
    MatIconModule,
    MatCardModule,
    MatMenuModule,
    MatDialogModule,
    MatSnackBarModule,
    MatChipsModule,
    CdkDropList,
    CdkDrag,
  ],
  templateUrl: './dealflow.html',
  styleUrl: './dealflow.scss',
})
export class Dealflow implements OnInit {
  private readonly dealService = inject(DealService);
  private readonly dialog = inject(MatDialog);
  private readonly snackBar = inject(MatSnackBar);

  readonly deals = signal<Deal[]>([]);
  readonly loading = signal(false);
  readonly dealsByColumn = signal<Record<string, Deal[]>>({});

  readonly columns = Object.values(DealColumn);
  readonly columnConfig = DEAL_COLUMN_CONFIG;

  readonly otherColumns = (current: DealColumn): DealColumn[] =>
    this.columns.filter(c => c !== current);

  ngOnInit(): void {
    this.loadDeals();
  }

  loadDeals(): void {
    this.loading.set(true);
    this.dealService.list().subscribe({
      next: (response) => {
        this.deals.set(response.items);
        this.groupDealsByColumn(response.items);
        this.loading.set(false);
      },
      error: (err) => {
        this.snackBar.open(err.error?.detail || 'Erro ao carregar deals', 'Fechar', { duration: 3000 });
        this.loading.set(false);
      },
    });
  }

  private groupDealsByColumn(deals: Deal[]): void {
    const grouped: Record<string, Deal[]> = {};
    for (const col of this.columns) {
      grouped[col] = deals.filter(d => d.column === col);
    }
    this.dealsByColumn.set(grouped);
  }

  onDealDrop(event: CdkDragDrop<Deal[]>): void {
    const targetColumn = event.container.id as DealColumn;
    const deal: Deal = event.item.data;

    if (event.previousContainer === event.container) {
      moveItemInArray(event.container.data, event.previousIndex, event.currentIndex);
    } else {
      transferArrayItem(
        event.previousContainer.data,
        event.container.data,
        event.previousIndex,
        event.currentIndex,
      );
    }

    this.dealService.move(deal.id, { column: targetColumn, position: event.currentIndex }).subscribe({
      error: (err) => {
        this.snackBar.open(err.error?.detail || 'Erro ao mover deal', 'Fechar', { duration: 3000 });
        this.loadDeals();
      },
    });
  }

  openCreateDialog(column?: DealColumn): void {
    const dialogRef = this.dialog.open(DealFormDialog, {
      width: '560px',
      data: { defaultColumn: column ?? DealColumn.NEW } as DealFormDialogData,
    });

    dialogRef.afterClosed().subscribe((result) => {
      if (result) {
        this.dealService.create(result).subscribe({
          next: () => {
            this.snackBar.open('Deal criado', 'Fechar', { duration: 3000 });
            this.loadDeals();
          },
          error: (err) => this.snackBar.open(err.error?.detail || 'Erro ao criar deal', 'Fechar', { duration: 3000 }),
        });
      }
    });
  }

  openEditDialog(deal: Deal): void {
    const dialogRef = this.dialog.open(DealFormDialog, {
      width: '560px',
      data: { deal } as DealFormDialogData,
    });

    dialogRef.afterClosed().subscribe((result) => {
      if (result) {
        this.dealService.update(deal.id, result).subscribe({
          next: () => {
            this.snackBar.open('Deal atualizado', 'Fechar', { duration: 3000 });
            this.loadDeals();
          },
          error: (err) => this.snackBar.open(err.error?.detail || 'Erro ao atualizar deal', 'Fechar', { duration: 3000 }),
        });
      }
    });
  }

  moveDeal(deal: Deal, column: DealColumn): void {
    this.dealService.move(deal.id, { column, position: 0 }).subscribe({
      next: () => {
        this.snackBar.open(
          `Deal movido para "${this.columnConfig[column].label}"`,
          'Fechar',
          { duration: 3000 },
        );
        this.loadDeals();
      },
      error: (err) => this.snackBar.open(err.error?.detail || 'Erro ao mover deal', 'Fechar', { duration: 3000 }),
    });
  }

  deleteDeal(deal: Deal): void {
    if (!confirm(`Excluir "${deal.company}"?`)) return;
    this.dealService.delete(deal.id).subscribe({
      next: () => {
        this.snackBar.open('Deal excluido', 'Fechar', { duration: 3000 });
        this.loadDeals();
      },
      error: (err) => this.snackBar.open(err.error?.detail || 'Erro ao excluir deal', 'Fechar', { duration: 3000 }),
    });
  }
}
