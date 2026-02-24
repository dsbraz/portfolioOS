import { TestBed } from '@angular/core/testing';
import { Router, ActivatedRouteSnapshot } from '@angular/router';
import { provideHttpClient } from '@angular/common/http';

import { authGuard } from './auth.guard';

describe('authGuard', () => {
  function runGuard(routeData: Record<string, unknown> = {}): boolean | string {
    const route = { data: routeData } as unknown as ActivatedRouteSnapshot;
    return TestBed.runInInjectionContext(() =>
      authGuard(route, {} as never),
    ) as boolean | string;
  }

  afterEach(() => localStorage.clear());

  describe('unauthenticated', () => {
    let router: Router;

    beforeEach(() => {
      localStorage.clear();
      TestBed.configureTestingModule({
        providers: [
          provideHttpClient(),
          { provide: Router, useValue: { createUrlTree: vi.fn(() => '/login') } },
        ],
      });
      router = TestBed.inject(Router);
    });

    it('should allow public routes regardless of auth', () => {
      expect(runGuard({ public: true })).toBe(true);
    });

    it('should redirect to login when not authenticated', () => {
      const result = runGuard();
      expect(result).toBe('/login');
      expect(router.createUrlTree).toHaveBeenCalledWith(['/login']);
    });
  });

  describe('authenticated', () => {
    beforeEach(() => {
      localStorage.setItem('access_token', 'valid-token');
      TestBed.configureTestingModule({
        providers: [
          provideHttpClient(),
          { provide: Router, useValue: { createUrlTree: vi.fn(() => '/login') } },
        ],
      });
    });

    it('should allow access when authenticated', () => {
      expect(runGuard()).toBe(true);
    });
  });
});
