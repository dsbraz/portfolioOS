import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';

import { DealFormDialog } from './deal-form-dialog';
import { DealStage } from '../../../models/deal.model';

describe('DealFormDialog', () => {
  const dialogRefSpy = { close: vi.fn() };

  describe('create mode', () => {
    let component: DealFormDialog;
    let fixture: ComponentFixture<DealFormDialog>;

    beforeEach(async () => {
      await TestBed.configureTestingModule({
        imports: [DealFormDialog],
        providers: [
          provideNoopAnimations(),
          { provide: MatDialogRef, useValue: dialogRefSpy },
          { provide: MAT_DIALOG_DATA, useValue: { defaultStage: DealStage.NEW } },
        ],
      }).compileComponents();

      fixture = TestBed.createComponent(DealFormDialog);
      component = fixture.componentInstance;
      fixture.detectChanges();
    });

    it('should require company name', () => {
      expect(component.form.invalid).toBe(true);
      component.form.patchValue({ company: 'Acme' });
      expect(component.form.valid).toBe(true);
    });

    it('should default stage to provided defaultStage', () => {
      expect(component.form.value.stage).toBe(DealStage.NEW);
    });

    it('should close dialog with form data on submit', () => {
      dialogRefSpy.close.mockClear();
      component.form.patchValue({ company: 'Acme', sector: 'tech' });
      component.onSubmit();
      expect(dialogRefSpy.close).toHaveBeenCalledWith(
        expect.objectContaining({ company: 'Acme', sector: 'tech' }),
      );
    });
  });

  describe('edit mode', () => {
    let component: DealFormDialog;
    let fixture: ComponentFixture<DealFormDialog>;

    beforeEach(async () => {
      await TestBed.configureTestingModule({
        imports: [DealFormDialog],
        providers: [
          provideNoopAnimations(),
          { provide: MatDialogRef, useValue: dialogRefSpy },
          {
            provide: MAT_DIALOG_DATA,
            useValue: {
              deal: { company: 'Existing', sector: 'fintech', stage: DealStage.ANALYZING },
            },
          },
        ],
      }).compileComponents();

      fixture = TestBed.createComponent(DealFormDialog);
      component = fixture.componentInstance;
      fixture.detectChanges();
    });

    it('should populate form in edit mode', () => {
      expect(component.isEditMode).toBe(true);
      expect(component.form.value.company).toBe('Existing');
      expect(component.form.value.stage).toBe(DealStage.ANALYZING);
    });
  });
});
