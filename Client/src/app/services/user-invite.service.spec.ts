import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import {
  HttpTestingController,
  provideHttpClientTesting,
} from '@angular/common/http/testing';

import { UserInviteService } from './user-invite.service';

describe('UserInviteService', () => {
  let service: UserInviteService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(UserInviteService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('should create invite', () => {
    service.createInvite({ email: 'invitee@example.com' }).subscribe();

    const req = httpMock.expectOne('/api/user-invites');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ email: 'invitee@example.com' });
    req.flush({
      id: '1',
      token: 'token',
      email: 'invitee@example.com',
      expires_at: '2026-03-10T00:00:00Z',
      used_at: null,
      created_at: '2026-03-07T00:00:00Z',
    });
  });

  it('should fetch public invite context', () => {
    service.getPublicInvite('abc').subscribe((res) => {
      expect(res.expires_at).toBe('2026-03-10T00:00:00Z');
    });

    const req = httpMock.expectOne('/api/user-invites/abc');
    expect(req.request.method).toBe('GET');
    req.flush({
      expires_at: '2026-03-10T00:00:00Z',
    });
  });

  it('should list active invites', () => {
    service.listActiveInvites().subscribe((res) => {
      expect(res.total).toBe(1);
    });

    const req = httpMock.expectOne('/api/user-invites');
    expect(req.request.method).toBe('GET');
    req.flush({
      items: [
        {
          id: '1',
          token: 'token',
          email: 'invitee@example.com',
          expires_at: '2026-03-10T00:00:00Z',
          used_at: null,
          created_at: '2026-03-07T00:00:00Z',
        },
      ],
      total: 1,
    });
  });

  it('should consume invite', () => {
    service.consumeInvite('abc', {
      email: 'invitee@example.com',
      username: 'newuser',
      password: 'password123',
    }).subscribe();

    const req = httpMock.expectOne('/api/user-invites/abc');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({
      email: 'invitee@example.com',
      username: 'newuser',
      password: 'password123',
    });
    req.flush(null, { status: 204, statusText: 'No Content' });
  });
});
