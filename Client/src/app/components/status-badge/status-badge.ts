import { Component, computed, input } from '@angular/core';

import { StartupStatus, STARTUP_STATUS_CONFIG } from '../../models/startup.model';

@Component({
  selector: 'app-status-badge',
  templateUrl: './status-badge.html',
  styleUrl: './status-badge.scss',
})
export class StatusBadge {
  readonly status = input.required<StartupStatus>();
  readonly config = computed(() => STARTUP_STATUS_CONFIG[this.status()]);
}
