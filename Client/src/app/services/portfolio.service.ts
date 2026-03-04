import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { PortfolioSummary } from '../models/portfolio.model';

@Injectable({ providedIn: 'root' })
export class PortfolioService {
  private readonly http = inject(HttpClient);

  getSummary(month: number, year: number): Observable<PortfolioSummary> {
    const params = new HttpParams().set('month', month).set('year', year);
    return this.http.get<PortfolioSummary>('/api/portfolio/summary', { params });
  }
}
