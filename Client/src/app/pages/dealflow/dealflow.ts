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
  DealStage,
  DEAL_STAGE_CONFIG,
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
  readonly dealsByStage = signal<Record<string, Deal[]>>({});

  readonly stages = Object.values(DealStage);
  readonly stageConfig = DEAL_STAGE_CONFIG;

  readonly otherStages = (current: DealStage): DealStage[] =>
    this.stages.filter(s => s !== current);

  ngOnInit(): void {
    this.loadDeals();
  }

  loadDeals(): void {
    this.loading.set(true);
    this.dealService.list().subscribe({
      next: (response) => {
        this.deals.set(response.items);
        this.groupDealsByStage(response.items);
        this.loading.set(false);
      },
      error: (err) => {
        this.snackBar.open(err.error?.detail || 'Erro ao carregar deals', 'Fechar', { duration: 3000 });
        this.loading.set(false);
      },
    });
  }

  private groupDealsByStage(deals: Deal[]): void {
    const grouped: Record<string, Deal[]> = {};
    for (const stage of this.stages) {
      grouped[stage] = deals.filter(d => d.stage === stage);
    }
    this.dealsByStage.set(grouped);
  }

  onDealDrop(event: CdkDragDrop<Deal[]>): void {
    const targetStage = event.container.id as DealStage;
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
      deal.stage = targetStage;
    }

    this.dealService.move(deal.id, { stage: targetStage, position: event.currentIndex }).subscribe({
      error: (err) => {
        this.snackBar.open(err.error?.detail || 'Erro ao mover deal', 'Fechar', { duration: 3000 });
        this.loadDeals();
      },
    });
  }

  openCreateDialog(stage?: DealStage): void {
    const dialogRef = this.dialog.open(DealFormDialog, {
      width: '560px',
      data: { defaultStage: stage ?? DealStage.NEW } as DealFormDialogData,
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

  moveDeal(deal: Deal, stage: DealStage): void {
    this.dealService.move(deal.id, { stage, position: 0 }).subscribe({
      next: () => {
        this.snackBar.open(
          `Deal movido para "${this.stageConfig[stage].label}"`,
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
