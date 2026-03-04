import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';

import { PortfolioService } from './portfolio.service';

describe('PortfolioService', () => {
  let service: PortfolioService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(PortfolioService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('should get portfolio summary', () => {
    const mockData = {
      total_startups: 3,
      revenue: 500000,
      revenue_variation_pct: 10.5,
      revenue_variation_direction: 'up',
      health: { healthy: 2, warning: 1, critical: 0 },
      monthly_report_pct: 66.7,
      routines_up_to_date_pct: 33.3,
      startups: [],
    };

    service.getSummary(2, 2026).subscribe((res) => {
      expect(res.total_startups).toBe(3);
      expect(res.revenue).toBe(500000);
    });

    const req = httpMock.expectOne((request) => request.url === '/api/portfolio/summary');
    expect(req.request.method).toBe('GET');
    expect(req.request.params.get('month')).toBe('2');
    expect(req.request.params.get('year')).toBe('2026');
    req.flush(mockData);
  });
});
