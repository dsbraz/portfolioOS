import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';

import { UserFormDialog } from './user-form-dialog';

describe('UserFormDialog', () => {
  const dialogRefSpy = { close: vi.fn() };

  describe('create mode', () => {
    let component: UserFormDialog;
    let fixture: ComponentFixture<UserFormDialog>;
    let httpMock: HttpTestingController;

    beforeEach(async () => {
      await TestBed.configureTestingModule({
        imports: [UserFormDialog],
        providers: [
          provideNoopAnimations(),
          provideHttpClient(),
          provideHttpClientTesting(),
          { provide: MatDialogRef, useValue: dialogRefSpy },
          { provide: MAT_DIALOG_DATA, useValue: {} },
        ],
      }).compileComponents();

      fixture = TestBed.createComponent(UserFormDialog);
      component = fixture.componentInstance;
      httpMock = TestBed.inject(HttpTestingController);
      fixture.detectChanges();
    });

    afterEach(() => httpMock.verify());

    it('should require username, email, and password', () => {
      expect(component.form.invalid).toBe(true);
      component.form.setValue({
        username: 'testuser',
        email: 'test@example.com',
        password: 'password123',
        is_active: true,
      });
      expect(component.form.valid).toBe(true);
    });

    it('should not submit when form is invalid', () => {
      dialogRefSpy.close.mockClear();
      component.onSubmit();
      expect(dialogRefSpy.close).not.toHaveBeenCalled();
    });

    it('should submit and close on success', () => {
      dialogRefSpy.close.mockClear();
      component.form.setValue({
        username: 'newuser',
        email: 'new@example.com',
        password: 'password123',
        is_active: true,
      });
      component.onSubmit();

      const req = httpMock.expectOne('/api/users');
      expect(req.request.method).toBe('POST');
      req.flush({ id: '1', username: 'newuser' });

      expect(dialogRefSpy.close).toHaveBeenCalledWith(true);
    });
  });

  describe('edit mode', () => {
    let component: UserFormDialog;
    let fixture: ComponentFixture<UserFormDialog>;
    let httpMock: HttpTestingController;

    beforeEach(async () => {
      await TestBed.configureTestingModule({
        imports: [UserFormDialog],
        providers: [
          provideNoopAnimations(),
          provideHttpClient(),
          provideHttpClientTesting(),
          { provide: MatDialogRef, useValue: dialogRefSpy },
          {
            provide: MAT_DIALOG_DATA,
            useValue: {
              user: { id: '1', username: 'existing', email: 'ex@test.com', is_active: true },
            },
          },
        ],
      }).compileComponents();

      fixture = TestBed.createComponent(UserFormDialog);
      component = fixture.componentInstance;
      httpMock = TestBed.inject(HttpTestingController);
      fixture.detectChanges();
    });

    afterEach(() => httpMock.verify());

    it('should populate form in edit mode', () => {
      expect(component.isEditMode).toBe(true);
      expect(component.form.value.username).toBe('existing');
      expect(component.form.value.email).toBe('ex@test.com');
    });

    it('should not require password in edit mode', () => {
      expect(component.form.valid).toBe(true);
    });
  });
});
