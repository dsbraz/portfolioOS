import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';

import { StartupService } from './startup.service';
import { StartupStatus } from '../models/startup.model';

describe('StartupService', () => {
  let service: StartupService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(StartupService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('should list startups', () => {
    const mockResponse = { items: [], total: 0 };
    service.list().subscribe((res) => {
      expect(res.total).toBe(0);
      expect(res.items).toEqual([]);
    });
    const req = httpMock.expectOne('/api/startups');
    expect(req.request.method).toBe('GET');
    req.flush(mockResponse);
  });

  it('should create a startup', () => {
    const payload = {
      name: 'Test',
      sector: 'Tech',
      investment_date: '2024-01-01',
    };
    service.create(payload).subscribe((res) => {
      expect(res.name).toBe('Test');
    });
    const req = httpMock.expectOne('/api/startups');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual(payload);
    req.flush({
      ...payload,
      id: '123',
      status: 'saudavel',
      site: null,
      logo_url: null,
      notes: null,
      created_at: '',
      updated_at: '',
    });
  });

  it('should update a startup', () => {
    service.update('123', { status: StartupStatus.CRITICAL }).subscribe();
    const req = httpMock.expectOne('/api/startups/123');
    expect(req.request.method).toBe('PATCH');
    req.flush({});
  });

  it('should delete a startup', () => {
    service.delete('123').subscribe();
    const req = httpMock.expectOne('/api/startups/123');
    expect(req.request.method).toBe('DELETE');
    req.flush(null);
  });
});
