import { TestBed } from '@angular/core/testing';
import {
  provideHttpClient,
  withInterceptors,
  HttpClient,
} from '@angular/common/http';
import {
  HttpTestingController,
  provideHttpClientTesting,
} from '@angular/common/http/testing';

import { authInterceptor } from './auth.interceptor';
import { AuthService } from '../services/auth.service';
import { provideRouter, Router } from '@angular/router';

describe('authInterceptor', () => {
  afterEach(() => localStorage.clear());

  describe('without token', () => {
    let http: HttpClient;
    let httpMock: HttpTestingController;
    let authService: AuthService;
    let router: Router;

    beforeEach(() => {
      localStorage.clear();
      TestBed.configureTestingModule({
        providers: [
          provideHttpClient(withInterceptors([authInterceptor])),
          provideHttpClientTesting(),
          provideRouter([]),
        ],
      });
      http = TestBed.inject(HttpClient);
      httpMock = TestBed.inject(HttpTestingController);
      authService = TestBed.inject(AuthService);
      router = TestBed.inject(Router);
    });

    afterEach(() => httpMock.verify());

    it('should not add Authorization header when no token', () => {
      http.get('/api/test').subscribe();

      const req = httpMock.expectOne('/api/test');
      expect(req.request.headers.has('Authorization')).toBe(false);
      req.flush({});
    });

    it('should logout and redirect on 401 response', () => {
      vi.spyOn(authService, 'logout');
      vi.spyOn(router, 'navigate').mockResolvedValue(true);

      http.get('/api/test').subscribe({ error: () => {} });

      const req = httpMock.expectOne('/api/test');
      req.flush('Unauthorized', { status: 401, statusText: 'Unauthorized' });

      expect(authService.logout).toHaveBeenCalled();
      expect(router.navigate).toHaveBeenCalledWith(['/login']);
    });
  });

  describe('with token', () => {
    let http: HttpClient;
    let httpMock: HttpTestingController;

    beforeEach(() => {
      localStorage.setItem('access_token', 'my-jwt');
      TestBed.configureTestingModule({
        providers: [
          provideHttpClient(withInterceptors([authInterceptor])),
          provideHttpClientTesting(),
          provideRouter([]),
        ],
      });
      http = TestBed.inject(HttpClient);
      httpMock = TestBed.inject(HttpTestingController);
    });

    afterEach(() => httpMock.verify());

    it('should add Authorization header when token exists', () => {
      http.get('/api/test').subscribe();

      const req = httpMock.expectOne('/api/test');
      expect(req.request.headers.get('Authorization')).toBe('Bearer my-jwt');
      req.flush({});
    });
  });
});
