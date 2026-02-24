import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';

import { ExecutiveService } from './executive.service';

describe('ExecutiveService', () => {
  let service: ExecutiveService;
  let httpMock: HttpTestingController;
  const startupId = 'startup-1';
  const baseUrl = `/api/startups/${startupId}/executives`;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(ExecutiveService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('should list executives', () => {
    service.list(startupId).subscribe((res) => expect(res.total).toBe(0));
    const req = httpMock.expectOne(baseUrl);
    expect(req.request.method).toBe('GET');
    req.flush({ items: [], total: 0 });
  });

  it('should create an executive', () => {
    const payload = { name: 'Maria Silva' };
    service.create(startupId, payload).subscribe();
    const req = httpMock.expectOne(baseUrl);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual(payload);
    req.flush({ id: '1', ...payload });
  });

  it('should update an executive', () => {
    const payload = { role: 'CTO' };
    service.update(startupId, 'e1', payload).subscribe();
    const req = httpMock.expectOne(`${baseUrl}/e1`);
    expect(req.request.method).toBe('PATCH');
    expect(req.request.body).toEqual(payload);
    req.flush({});
  });

  it('should delete an executive', () => {
    service.delete(startupId, 'e1').subscribe();
    const req = httpMock.expectOne(`${baseUrl}/e1`);
    expect(req.request.method).toBe('DELETE');
    req.flush(null);
  });
});
