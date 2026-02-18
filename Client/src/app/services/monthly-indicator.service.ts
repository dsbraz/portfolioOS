import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import {
  MonthlyIndicator,
  MonthlyIndicatorCreate,
  MonthlyIndicatorListResponse,
  MonthlyIndicatorUpdate,
} from '../models/monthly-indicator.model';

@Injectable({ providedIn: 'root' })
export class MonthlyIndicatorService {
  private readonly http = inject(HttpClient);

  private baseUrl(startupId: string): string {
    return `/api/startups/${startupId}/indicators`;
  }

  list(startupId: string): Observable<MonthlyIndicatorListResponse> {
    return this.http.get<MonthlyIndicatorListResponse>(this.baseUrl(startupId));
  }

  getById(startupId: string, indicatorId: string): Observable<MonthlyIndicator> {
    return this.http.get<MonthlyIndicator>(`${this.baseUrl(startupId)}/${indicatorId}`);
  }

  create(startupId: string, data: MonthlyIndicatorCreate): Observable<MonthlyIndicator> {
    return this.http.post<MonthlyIndicator>(this.baseUrl(startupId), data);
  }

  update(
    startupId: string,
    indicatorId: string,
    data: MonthlyIndicatorUpdate,
  ): Observable<MonthlyIndicator> {
    return this.http.patch<MonthlyIndicator>(
      `${this.baseUrl(startupId)}/${indicatorId}`,
      data,
    );
  }

  delete(startupId: string, indicatorId: string): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl(startupId)}/${indicatorId}`);
  }
}
