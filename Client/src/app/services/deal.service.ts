import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import {
  Deal,
  DealCreate,
  DealListResponse,
  DealMoveRequest,
  DealUpdate,
} from '../models/deal.model';

@Injectable({ providedIn: 'root' })
export class DealService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = '/api/deals';

  list(): Observable<DealListResponse> {
    return this.http.get<DealListResponse>(this.baseUrl);
  }

  getById(id: string): Observable<Deal> {
    return this.http.get<Deal>(`${this.baseUrl}/${id}`);
  }

  create(data: DealCreate): Observable<Deal> {
    return this.http.post<Deal>(this.baseUrl, data);
  }

  update(id: string, data: DealUpdate): Observable<Deal> {
    return this.http.patch<Deal>(`${this.baseUrl}/${id}`, data);
  }

  move(id: string, data: DealMoveRequest): Observable<Deal> {
    return this.http.patch<Deal>(`${this.baseUrl}/${id}/move`, data);
  }

  delete(id: string): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/${id}`);
  }
}
