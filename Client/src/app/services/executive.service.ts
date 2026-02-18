import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import {
  Executive,
  ExecutiveCreate,
  ExecutiveListResponse,
  ExecutiveUpdate,
} from '../models/executive.model';

@Injectable({ providedIn: 'root' })
export class ExecutiveService {
  private readonly http = inject(HttpClient);

  private baseUrl(startupId: string): string {
    return `/api/startups/${startupId}/executives`;
  }

  list(startupId: string): Observable<ExecutiveListResponse> {
    return this.http.get<ExecutiveListResponse>(this.baseUrl(startupId));
  }

  getById(startupId: string, executiveId: string): Observable<Executive> {
    return this.http.get<Executive>(`${this.baseUrl(startupId)}/${executiveId}`);
  }

  create(startupId: string, data: ExecutiveCreate): Observable<Executive> {
    return this.http.post<Executive>(this.baseUrl(startupId), data);
  }

  update(
    startupId: string,
    executiveId: string,
    data: ExecutiveUpdate,
  ): Observable<Executive> {
    return this.http.patch<Executive>(
      `${this.baseUrl(startupId)}/${executiveId}`,
      data,
    );
  }

  delete(startupId: string, executiveId: string): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl(startupId)}/${executiveId}`);
  }
}
