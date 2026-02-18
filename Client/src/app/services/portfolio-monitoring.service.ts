import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { MonitoringSummary } from '../models/portfolio-monitoring.model';

@Injectable({ providedIn: 'root' })
export class PortfolioMonitoringService {
  private readonly http = inject(HttpClient);

  getSummary(): Observable<MonitoringSummary> {
    return this.http.get<MonitoringSummary>('/api/portfolio-monitoring/summary');
  }
}
