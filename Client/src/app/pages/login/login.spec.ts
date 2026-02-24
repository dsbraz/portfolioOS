import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { provideRouter, Router } from '@angular/router';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';

import { Login } from './login';

describe('Login', () => {
  let component: Login;
  let fixture: ComponentFixture<Login>;
  let httpMock: HttpTestingController;
  let router: Router;

  beforeEach(async () => {
    localStorage.clear();
    await TestBed.configureTestingModule({
      imports: [Login],
      providers: [
        provideNoopAnimations(),
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(Login);
    component = fixture.componentInstance;
    httpMock = TestBed.inject(HttpTestingController);
    router = TestBed.inject(Router);
    fixture.detectChanges();
  });

  afterEach(() => {
    httpMock.verify();
    localStorage.clear();
  });

  it('should start with invalid form', () => {
    expect(component.form.invalid).toBe(true);
  });

  it('should not submit when form is invalid', () => {
    component.onSubmit();
    expect(component.loading()).toBe(false);
    httpMock.expectNone('/api/auth/login');
  });

  it('should submit and navigate on success', () => {
    vi.spyOn(router, 'navigate').mockResolvedValue(true);
    component.form.setValue({ username: 'admin', password: 'pass123' });
    component.onSubmit();

    expect(component.loading()).toBe(true);

    const req = httpMock.expectOne('/api/auth/login');
    req.flush({ access_token: 'jwt-token', token_type: 'bearer' });

    expect(router.navigate).toHaveBeenCalledWith(['/portfolio']);
  });

  it('should show error on failed login', () => {
    component.form.setValue({ username: 'admin', password: 'wrong' });
    component.onSubmit();

    const req = httpMock.expectOne('/api/auth/login');
    req.flush({ detail: 'Credenciais invalidas' }, { status: 401, statusText: 'Unauthorized' });

    expect(component.loading()).toBe(false);
    expect(component.errorMessage()).toBe('Credenciais invalidas');
  });
});
