import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';

import { DealService } from './deal.service';
import { DealStage } from '../models/deal.model';

describe('DealService', () => {
  let service: DealService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(DealService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('should list deals', () => {
    service.list().subscribe((res) => expect(res.total).toBe(0));
    const req = httpMock.expectOne('/api/deals');
    expect(req.request.method).toBe('GET');
    req.flush({ items: [], total: 0 });
  });

  it('should create a deal', () => {
    const payload = { company: 'Acme' };
    service.create(payload).subscribe();
    const req = httpMock.expectOne('/api/deals');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual(payload);
    req.flush({ id: '1', ...payload });
  });

  it('should update a deal', () => {
    const payload = { company: 'Updated' };
    service.update('d1', payload).subscribe();
    const req = httpMock.expectOne('/api/deals/d1');
    expect(req.request.method).toBe('PATCH');
    expect(req.request.body).toEqual(payload);
    req.flush({});
  });

  it('should move a deal', () => {
    const payload = { stage: DealStage.ANALYZING, position: 2 };
    service.move('d1', payload).subscribe();
    const req = httpMock.expectOne('/api/deals/d1');
    expect(req.request.method).toBe('PATCH');
    expect(req.request.body).toEqual(payload);
    req.flush({});
  });

  it('should delete a deal', () => {
    service.delete('d1').subscribe();
    const req = httpMock.expectOne('/api/deals/d1');
    expect(req.request.method).toBe('DELETE');
    req.flush(null);
  });
});
