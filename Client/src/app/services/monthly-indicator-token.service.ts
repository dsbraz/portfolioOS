import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import {
  MonthlyIndicatorToken,
  MonthlyIndicatorTokenListResponse,
  PublicIndicatorForm,
  PublicIndicatorSubmit,
} from '../models/monthly-indicator-token.model';

@Injectable({ providedIn: 'root' })
export class MonthlyIndicatorTokenService {
  private readonly http = inject(HttpClient);

  create(startupId: string): Observable<MonthlyIndicatorToken> {
    return this.http.post<MonthlyIndicatorToken>(
      `/api/startups/${startupId}/monthly-indicator-tokens`,
      {},
    );
  }

  list(startupId: string): Observable<MonthlyIndicatorTokenListResponse> {
    return this.http.get<MonthlyIndicatorTokenListResponse>(
      `/api/startups/${startupId}/monthly-indicator-tokens`,
    );
  }

  getPublicForm(token: string): Observable<PublicIndicatorForm> {
    return this.http.get<PublicIndicatorForm>(`/api/monthly-indicator/${token}`);
  }

  submitPublicForm(token: string, data: PublicIndicatorSubmit): Observable<void> {
    return this.http.post<void>(`/api/monthly-indicator/${token}`, data);
  }
}
