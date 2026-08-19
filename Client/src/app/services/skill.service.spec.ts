import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { SkillListResponse } from '../models/skill.model';
import { SkillService } from './skill.service';

describe('SkillService', () => {
  let service: SkillService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(SkillService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('should list the skill catalog from the relative API URL', () => {
    const response: SkillListResponse = {
      items: [
        {
          name: 'preparar-agenda',
          description: 'Prepara uma agenda para a próxima conversa.',
          version: '2026-08-11',
          writes: false,
          reads_external: true,
          published: true,
          files: ['SKILL.md'],
        },
      ],
      total: 1,
    };

    service.list().subscribe((result) => expect(result).toEqual(response));

    const request = httpMock.expectOne('/api/skills');
    expect(request.request.method).toBe('GET');
    request.flush(response);
  });

  it('should download the complete package as a blob through HttpClient', () => {
    const packageBlob = new Blob(['portfolioOS'], { type: 'application/zip' });

    service.downloadPack().subscribe((result) => expect(result).toBe(packageBlob));

    const request = httpMock.expectOne('/api/skills.zip');
    expect(request.request.method).toBe('GET');
    expect(request.request.responseType).toBe('blob');
    request.flush(packageBlob);
  });
});
