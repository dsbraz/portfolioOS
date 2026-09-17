import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';

import { SkillPackService } from './skill-pack.service';

describe('SkillPackService', () => {
  let service: SkillPackService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(SkillPackService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('reads the manifest published beside the package', () => {
    service.getManifest().subscribe((manifest) => expect(manifest.revised_at).toBe('2026-09-17'));

    const req = httpMock.expectOne('/api/static/portfolioos-manifest.json');
    expect(req.request.method).toBe('GET');
    req.flush({ revised_at: '2026-09-17', content_sha256: 'x', published: [], unpublished: [] });
  });
});
