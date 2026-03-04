import { Component, input } from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';

export type KpiCardTone = 'default' | 'positive' | 'negative' | 'neutral';

@Component({
  selector: 'app-kpi-card',
  imports: [MatCardModule, MatIconModule],
  templateUrl: './kpi-card.html',
  styleUrl: './kpi-card.scss',
})
export class KpiCard {
  readonly icon = input.required<string>();
  readonly label = input.required<string>();
  readonly value = input.required<string>();
  readonly subtitle = input<string>('');
  readonly tone = input<KpiCardTone>('default');
  readonly supportingIcon = input<string | null>(null);
}
