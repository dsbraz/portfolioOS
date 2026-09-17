import { ApplicationRef, Component } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { MAT_DIALOG_DEFAULT_OPTIONS, MatDialog, MatDialogModule } from '@angular/material/dialog';

import { dialogDefaults } from './app.config';

@Component({ template: '<p>conteúdo</p>' })
class TestDialog {}

describe('dialogDefaults', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MatDialogModule, TestDialog],
      providers: [
        provideNoopAnimations(),
        { provide: MAT_DIALOG_DEFAULT_OPTIONS, useValue: dialogDefaults },
      ],
    }).compileComponents();
  });

  // Regression: `MAT_DIALOG_DEFAULT_OPTIONS` REPLACES Material's default
  // config. Without declaring `role` here, the container came out with
  // `aria-modal="true"` and no role — and `aria-modal` only has meaning on a
  // `role="dialog"`. Assistive tech stopped announcing the dialog as a dialog.
  it('should open dialogs with both role and aria-modal', () => {
    const dialog = TestBed.inject(MatDialog);
    dialog.open(TestDialog);
    // The container attributes only reach the DOM after change detection.
    TestBed.inject(ApplicationRef).tick();
    const container = document.querySelector('.mat-mdc-dialog-container');
    expect(container?.getAttribute('role')).toBe('dialog');
    expect(container?.getAttribute('aria-modal')).toBe('true');

    dialog.closeAll();
  });
});
