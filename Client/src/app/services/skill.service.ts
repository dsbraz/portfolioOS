import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { SkillListResponse } from '../models/skill.model';

@Injectable({ providedIn: 'root' })
export class SkillService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = '/api/skills';

  list(): Observable<SkillListResponse> {
    return this.http.get<SkillListResponse>(this.baseUrl);
  }

  downloadPack(): Observable<Blob> {
    return this.http.get(`${this.baseUrl}.zip`, { responseType: 'blob' });
  }
}
