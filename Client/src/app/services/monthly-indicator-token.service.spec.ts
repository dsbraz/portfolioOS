import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';

import { MonthlyIndicatorTokenService } from './monthly-indicator-token.service';

describe('MonthlyIndicatorTokenService', () => {
  let service: MonthlyIndicatorTokenService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(MonthlyIndicatorTokenService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('should create a token', () => {
    const mockToken = {
      id: 'abc',
      token: 'tok-uuid',
      startup_id: 'sid',
      month: 1,
      year: 2025,
      created_at: '',
    };
    service.create('sid', 1, 2025).subscribe((res) => {
      expect(res.token).toBe('tok-uuid');
    });
    const req = httpMock.expectOne('/api/startups/sid/monthly-indicator-tokens');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ month: 1, year: 2025 });
    req.flush(mockToken);
  });

  it('should list tokens', () => {
    const mockResponse = { items: [], total: 0 };
    service.list('sid').subscribe((res) => {
      expect(res.total).toBe(0);
    });
    const req = httpMock.expectOne('/api/startups/sid/monthly-indicator-tokens');
    expect(req.request.method).toBe('GET');
    req.flush(mockResponse);
  });

  it('should get public form', () => {
    const mockCtx = {
      startup_name: 'Acme',
      startup_logo_url: null,
      month: 3,
      year: 2025,
      existing_indicator: null,
    };
    service.getPublicForm('my-token').subscribe((res) => {
      expect(res.startup_name).toBe('Acme');
    });
    const req = httpMock.expectOne('/api/monthly-indicator/my-token');
    expect(req.request.method).toBe('GET');
    req.flush(mockCtx);
  });

  it('should submit public form', () => {
    const payload = {
      total_revenue: 100000,
      cash_balance: null,
      ebitda_burn: null,
      recurring_revenue_pct: null,
      gross_margin_pct: null,
      headcount: 5,
      achievements: null,
      challenges: null,
    };
    service.submitPublicForm('my-token', payload).subscribe();
    const req = httpMock.expectOne('/api/monthly-indicator/my-token');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual(payload);
    req.flush(null, { status: 204, statusText: 'No Content' });
  });
});
