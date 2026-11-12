import { ComponentFixture, TestBed } from '@angular/core/testing';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';

import { StartupFormDialog } from './startup-form-dialog';
import { StartupStatus } from '../../../models/startup.model';

describe('StartupFormDialog', () => {
  let component: StartupFormDialog;
  let fixture: ComponentFixture<StartupFormDialog>;
  const dialogRefSpy = { close: vi.fn() };

  describe('create mode', () => {
    beforeEach(async () => {
      await TestBed.configureTestingModule({
        imports: [StartupFormDialog],
        providers: [
          provideAnimationsAsync(),
          { provide: MatDialogRef, useValue: dialogRefSpy },
          { provide: MAT_DIALOG_DATA, useValue: {} },
        ],
      }).compileComponents();
      fixture = TestBed.createComponent(StartupFormDialog);
      component = fixture.componentInstance;
      fixture.detectChanges();
    });

    it('should start with empty form', () => {
      expect(component.form.controls.name.value).toBe('');
      expect(component.isEditMode).toBe(false);
    });

    it('should require name, sector, and investment_date', () => {
      expect(component.form.valid).toBe(false);
      component.form.patchValue({
        name: 'Test',
        sector: 'Tech',
        investment_date: new Date('2024-01-01'),
      });
      expect(component.form.valid).toBe(true);
    });

    it('should close dialog with form data on submit', () => {
      component.form.patchValue({
        name: 'Test',
        sector: 'Tech',
        investment_date: new Date('2024-01-01'),
      });
      component.onSubmit();
      expect(dialogRefSpy.close).toHaveBeenCalledWith(
        expect.objectContaining({ name: 'Test', sector: 'Tech' }),
      );
    });

    it('should leave the monthly e-mail off by default and submit the choice', () => {
      expect(component.form.controls.monthly_report_enabled.value).toBe(false);
      const toggle = fixture.nativeElement.querySelector('mat-slide-toggle button');
      expect(toggle.getAttribute('aria-describedby')).toContain('h-2ea6-monthly_report');

      component.form.patchValue({
        name: 'Test',
        sector: 'Tech',
        investment_date: new Date('2024-01-01'),
        monthly_report_enabled: true,
      });
      component.onSubmit();

      expect(dialogRefSpy.close).toHaveBeenLastCalledWith(
        expect.objectContaining({ monthly_report_enabled: true }),
      );
    });
  });

  describe('edit mode', () => {
    const mockStartup = {
      id: '123',
      name: 'EditCorp',
      site: 'https://edit.com',
      logo_url: null,
      status: StartupStatus.WARNING,
      sector: 'Fintech',
      investment_date: '2024-06-15',
      notes: 'Some note',
      monthly_report_enabled: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    };

    beforeEach(async () => {
      await TestBed.configureTestingModule({
        imports: [StartupFormDialog],
        providers: [
          provideAnimationsAsync(),
          { provide: MatDialogRef, useValue: dialogRefSpy },
          { provide: MAT_DIALOG_DATA, useValue: { startup: mockStartup } },
        ],
      }).compileComponents();
      fixture = TestBed.createComponent(StartupFormDialog);
      component = fixture.componentInstance;
      fixture.detectChanges();
    });

    it('should populate form in edit mode', () => {
      expect(component.isEditMode).toBe(true);
      expect(component.form.controls.name.value).toBe('EditCorp');
      expect(component.form.controls.status.value).toBe(StartupStatus.WARNING);
      expect(component.form.controls.monthly_report_enabled.value).toBe(true);
    });
  });
});
