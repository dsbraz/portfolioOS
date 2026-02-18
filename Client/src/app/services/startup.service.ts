import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import {
  Startup,
  StartupCreate,
  StartupListResponse,
  StartupUpdate,
} from '../models/startup.model';

@Injectable({ providedIn: 'root' })
export class StartupService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = '/api/startups';

  list(): Observable<StartupListResponse> {
    return this.http.get<StartupListResponse>(this.baseUrl);
  }

  getById(id: string): Observable<Startup> {
    return this.http.get<Startup>(`${this.baseUrl}/${id}`);
  }

  create(data: StartupCreate): Observable<Startup> {
    return this.http.post<Startup>(this.baseUrl, data);
  }

  update(id: string, data: StartupUpdate): Observable<Startup> {
    return this.http.patch<Startup>(`${this.baseUrl}/${id}`, data);
  }

  delete(id: string): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/${id}`);
  }
}
