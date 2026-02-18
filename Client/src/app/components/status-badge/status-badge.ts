import { Component, computed, input } from '@angular/core';
import { MatChipsModule } from '@angular/material/chips';
import { MatIconModule } from '@angular/material/icon';

import { StartupStatus, STARTUP_STATUS_CONFIG } from '../../models/startup.model';

@Component({
  selector: 'app-status-badge',
  imports: [MatChipsModule, MatIconModule],
  templateUrl: './status-badge.html',
  styleUrl: './status-badge.scss',
})
export class StatusBadge {
  readonly status = input.required<StartupStatus>();
  readonly config = computed(() => STARTUP_STATUS_CONFIG[this.status()]);
}
