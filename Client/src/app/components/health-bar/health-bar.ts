import { Component, computed, input } from '@angular/core';
import { MatTooltipModule } from '@angular/material/tooltip';

import { HealthDistribution } from '../../models/portfolio-monitoring.model';
import { STARTUP_STATUS_CONFIG, StartupStatus } from '../../models/startup.model';

@Component({
  selector: 'app-health-bar',
  imports: [MatTooltipModule],
  templateUrl: './health-bar.html',
  styleUrl: './health-bar.scss',
})
export class HealthBar {
  readonly distribution = input.required<HealthDistribution>();

  readonly total = computed(() => {
    const d = this.distribution();
    return d.healthy + d.warning + d.critical;
  });

  readonly segments = computed(() => {
    const d = this.distribution();
    const t = this.total();
    if (t === 0) return [];
    return [
      { label: 'Saudavel', count: d.healthy, pct: (d.healthy / t) * 100, color: STARTUP_STATUS_CONFIG[StartupStatus.HEALTHY].color },
      { label: 'Atencao', count: d.warning, pct: (d.warning / t) * 100, color: STARTUP_STATUS_CONFIG[StartupStatus.WARNING].color },
      { label: 'Critico', count: d.critical, pct: (d.critical / t) * 100, color: STARTUP_STATUS_CONFIG[StartupStatus.CRITICAL].color },
    ].filter(s => s.count > 0);
  });
}
