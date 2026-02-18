import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import {
  ReportFormContext,
  ReportToken,
  ReportTokenListResponse,
  PublicReportSubmit,
} from '../models/report-token.model';

@Injectable({ providedIn: 'root' })
export class ReportTokenService {
  private readonly http = inject(HttpClient);

  generateToken(startupId: string, month: number, year: number): Observable<ReportToken> {
    return this.http.post<ReportToken>(
      `/api/startups/${startupId}/report-tokens`,
      { month, year },
    );
  }

  listTokens(startupId: string): Observable<ReportTokenListResponse> {
    return this.http.get<ReportTokenListResponse>(
      `/api/startups/${startupId}/report-tokens`,
    );
  }

  getFormContext(token: string): Observable<ReportFormContext> {
    return this.http.get<ReportFormContext>(`/api/report/${token}`);
  }

  submitReport(token: string, data: PublicReportSubmit): Observable<void> {
    return this.http.post<void>(`/api/report/${token}/submit`, data);
  }
}
