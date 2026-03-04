import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';

import { TokenGenerateDialog } from './token-generate-dialog';

describe('TokenGenerateDialog', () => {
  let component: TokenGenerateDialog;
  let fixture: ComponentFixture<TokenGenerateDialog>;
  const dialogRefSpy = { close: vi.fn() };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TokenGenerateDialog],
      providers: [
        provideNoopAnimations(),
        { provide: MatDialogRef, useValue: dialogRefSpy },
        { provide: MAT_DIALOG_DATA, useValue: { month: 2, year: 2026 } },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(TokenGenerateDialog);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should initialize with provided month and year', () => {
    expect(component.form.value.month).toBe(2);
    expect(component.form.value.year).toBe(2026);
  });

  it('should block future period', () => {
    const now = new Date();
    const futureMonth = now.getMonth() === 11 ? 1 : now.getMonth() + 2;
    const futureYear = now.getMonth() === 11 ? now.getFullYear() + 1 : now.getFullYear();

    component.form.patchValue({ month: futureMonth, year: futureYear });

    expect(component.form.hasError('futurePeriod')).toBe(true);
  });

  it('should close dialog on submit with period', () => {
    dialogRefSpy.close.mockClear();
    component.form.patchValue({ month: 3, year: 2026 });

    component.onSubmit();

    expect(dialogRefSpy.close).toHaveBeenCalledWith(
      expect.objectContaining({ month: 3, year: 2026 }),
    );
  });
});
