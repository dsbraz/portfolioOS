import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { MonthlyReportDispatchListResponse } from '../models/monthly-report.model';

/** Read-only: the sends come from the scheduled job, never from the screen. */
@Injectable({ providedIn: 'root' })
export class MonthlyReportService {
  private readonly http = inject(HttpClient);

  listDispatches(startupId: string): Observable<MonthlyReportDispatchListResponse> {
    return this.http.get<MonthlyReportDispatchListResponse>(
      `/api/startups/${startupId}/monthly-report-dispatches`,
    );
  }
}
