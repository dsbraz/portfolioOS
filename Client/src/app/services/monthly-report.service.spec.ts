import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';

import { MonthlyReportService } from './monthly-report.service';

describe('MonthlyReportService', () => {
  let service: MonthlyReportService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(MonthlyReportService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('should list the automatic dispatches of a startup', () => {
    service.listDispatches('startup-1').subscribe((res) => expect(res.total).toBe(0));
    const req = httpMock.expectOne('/api/startups/startup-1/monthly-report-dispatches');
    expect(req.request.method).toBe('GET');
    req.flush({ items: [], total: 0 });
  });
});
