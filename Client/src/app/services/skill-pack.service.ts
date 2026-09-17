import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { SkillPackManifest } from '../models/skill-pack.model';

const MANIFEST_URL = '/api/static/portfolioos-manifest.json';

@Injectable({ providedIn: 'root' })
export class SkillPackService {
  private readonly http = inject(HttpClient);

  getManifest(): Observable<SkillPackManifest> {
    return this.http.get<SkillPackManifest>(MANIFEST_URL);
  }
}
