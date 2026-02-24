import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';

import { MonthlyIndicatorService } from './monthly-indicator.service';

describe('MonthlyIndicatorService', () => {
  let service: MonthlyIndicatorService;
  let httpMock: HttpTestingController;
  const startupId = 'startup-1';
  const baseUrl = `/api/startups/${startupId}/monthly-indicators`;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(MonthlyIndicatorService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('should list indicators', () => {
    service.list(startupId).subscribe((res) => expect(res.total).toBe(0));
    const req = httpMock.expectOne(baseUrl);
    expect(req.request.method).toBe('GET');
    req.flush({ items: [], total: 0 });
  });

  it('should create an indicator', () => {
    const payload = { month: 2, year: 2026 };
    service.create(startupId, payload).subscribe();
    const req = httpMock.expectOne(baseUrl);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual(payload);
    req.flush({ id: '1', ...payload });
  });

  it('should update an indicator', () => {
    const payload = { headcount: 15 };
    service.update(startupId, 'i1', payload).subscribe();
    const req = httpMock.expectOne(`${baseUrl}/i1`);
    expect(req.request.method).toBe('PATCH');
    expect(req.request.body).toEqual(payload);
    req.flush({});
  });

  it('should delete an indicator', () => {
    service.delete(startupId, 'i1').subscribe();
    const req = httpMock.expectOne(`${baseUrl}/i1`);
    expect(req.request.method).toBe('DELETE');
    req.flush(null);
  });
});
