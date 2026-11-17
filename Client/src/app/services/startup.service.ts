import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import {
  Startup,
  StartupCreate,
  StartupExitRecord,
  StartupListResponse,
  StartupUpdate,
} from '../models/startup.model';

@Injectable({ providedIn: 'root' })
export class StartupService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = '/api/startups';

  /** `tracked: true` lists the startups still followed, `false` the exited ones. */
  list(options: { tracked?: boolean } = {}): Observable<StartupListResponse> {
    if (options.tracked === undefined) {
      return this.http.get<StartupListResponse>(this.baseUrl);
    }
    return this.http.get<StartupListResponse>(this.baseUrl, {
      params: { tracked: String(options.tracked) },
    });
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

  recordExit(id: string, data: StartupExitRecord): Observable<Startup> {
    return this.http.put<Startup>(`${this.baseUrl}/${id}/exit`, data);
  }

  undoExit(id: string): Observable<Startup> {
    return this.http.delete<Startup>(`${this.baseUrl}/${id}/exit`);
  }

  delete(id: string): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/${id}`);
  }
}
