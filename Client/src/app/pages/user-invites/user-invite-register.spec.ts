import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ActivatedRoute, convertToParamMap, provideRouter } from '@angular/router';

import UserInviteRegister from './user-invite-register';

describe('UserInviteRegister', () => {
  let component: UserInviteRegister;
  let fixture: ComponentFixture<UserInviteRegister>;
  let httpMock: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [UserInviteRegister],
      providers: [
        provideNoopAnimations(),
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
        {
          provide: ActivatedRoute,
          useValue: {
            snapshot: {
              paramMap: convertToParamMap({ token: 'test-token' }),
            },
          },
        },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(UserInviteRegister);
    component = fixture.componentInstance;
    httpMock = TestBed.inject(HttpTestingController);
    fixture.detectChanges();

    const req = httpMock.expectOne('/api/user-invites/test-token');
    req.flush({ expires_at: '2030-01-01T00:00:00Z' });
  });

  afterEach(() => httpMock.verify());

  it('should reject username with spaces in form validation', () => {
    component.form.setValue({
      email: 'invitee@example.com',
      username: 'invalid user',
      password: 'password123',
      confirmPassword: 'password123',
    });

    expect(component.form.controls.username.hasError('pattern')).toBe(true);
    expect(component.canSubmit()).toBe(false);
  });

  it('should allow submit when username has no spaces', () => {
    component.form.setValue({
      email: 'invitee@example.com',
      username: 'validuser',
      password: 'password123',
      confirmPassword: 'password123',
    });

    expect(component.canSubmit()).toBe(true);
  });
});
