import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';

import { AuthService } from './auth.service';

describe('AuthService', () => {
  let service: AuthService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(AuthService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
    localStorage.clear();
  });

  it('should start unauthenticated when no token in storage', () => {
    expect(service.isAuthenticated()).toBe(false);
    expect(service.getToken()).toBeNull();
  });

  it('should login and store token', () => {
    const credentials = { username: 'admin', password: 'pass123' };
    service.login(credentials).subscribe((res) => {
      expect(res.access_token).toBe('jwt-token');
    });

    const req = httpMock.expectOne('/api/auth/login');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual(credentials);
    req.flush({ access_token: 'jwt-token', token_type: 'bearer' });

    expect(service.isAuthenticated()).toBe(true);
    expect(service.getToken()).toBe('jwt-token');
    expect(localStorage.getItem('access_token')).toBe('jwt-token');
  });

  it('should logout and clear token', () => {
    localStorage.setItem('access_token', 'jwt-token');
    const freshService = TestBed.inject(AuthService);

    freshService.logout();

    expect(freshService.isAuthenticated()).toBe(false);
    expect(freshService.getToken()).toBeNull();
    expect(localStorage.getItem('access_token')).toBeNull();
  });

  it('should create a user', () => {
    const payload = { username: 'new', email: 'new@test.com', password: 'pass123' };
    service.createUser(payload).subscribe();

    const req = httpMock.expectOne('/api/users');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual(payload);
    req.flush({ id: '1', ...payload });
  });

  it('should update a user', () => {
    const payload = { username: 'updated' };
    service.updateUser('123', payload).subscribe();

    const req = httpMock.expectOne('/api/users/123');
    expect(req.request.method).toBe('PATCH');
    expect(req.request.body).toEqual(payload);
    req.flush({});
  });

  it('should list users', () => {
    service.listUsers().subscribe((res) => {
      expect(res.total).toBe(1);
    });

    const req = httpMock.expectOne('/api/users');
    expect(req.request.method).toBe('GET');
    req.flush({ items: [{ id: '1', username: 'admin' }], total: 1 });
  });
});
