import { Component, input } from '@angular/core';
import { MatIconModule } from '@angular/material/icon';

export type KpiCardTone = 'default' | 'positive' | 'negative' | 'neutral';

@Component({
  selector: 'app-kpi-card',
  imports: [MatIconModule],
  templateUrl: './kpi-card.html',
  styleUrl: './kpi-card.scss',
})
export class KpiCard {
  readonly label = input.required<string>();
  readonly value = input.required<string>();
  readonly subtitle = input<string>('');
  readonly tone = input<KpiCardTone>('default');
  /** Pairs with `tone` on the footnote so a trend is never color alone. */
  readonly supportingIcon = input<string | null>(null);
}
