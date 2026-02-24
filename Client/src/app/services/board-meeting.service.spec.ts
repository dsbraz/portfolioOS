import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';

import { BoardMeetingService } from './board-meeting.service';

describe('BoardMeetingService', () => {
  let service: BoardMeetingService;
  let httpMock: HttpTestingController;
  const startupId = 'startup-1';
  const baseUrl = `/api/startups/${startupId}/board-meetings`;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(BoardMeetingService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('should list meetings', () => {
    service.list(startupId).subscribe((res) => expect(res.total).toBe(0));
    const req = httpMock.expectOne(baseUrl);
    expect(req.request.method).toBe('GET');
    req.flush({ items: [], total: 0 });
  });

  it('should create a meeting', () => {
    const payload = { meeting_date: '2026-02-10' };
    service.create(startupId, payload).subscribe();
    const req = httpMock.expectOne(baseUrl);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual(payload);
    req.flush({ id: '1', ...payload });
  });

  it('should update a meeting', () => {
    const payload = { summary: 'Updated' };
    service.update(startupId, 'm1', payload).subscribe();
    const req = httpMock.expectOne(`${baseUrl}/m1`);
    expect(req.request.method).toBe('PATCH');
    expect(req.request.body).toEqual(payload);
    req.flush({});
  });

  it('should delete a meeting', () => {
    service.delete(startupId, 'm1').subscribe();
    const req = httpMock.expectOne(`${baseUrl}/m1`);
    expect(req.request.method).toBe('DELETE');
    req.flush(null);
  });
});
