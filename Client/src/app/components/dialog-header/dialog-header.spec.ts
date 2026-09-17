import { ApplicationRef, Component } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { MatDialog, MatDialogRef } from '@angular/material/dialog';
import { OverlayContainer } from '@angular/cdk/overlay';
import { firstValueFrom } from 'rxjs';

import { DialogHeader } from './dialog-header';

@Component({
  selector: 'app-dialog-header-host',
  imports: [DialogHeader],
  template: `<app-dialog-header title="Nova startup" description="Preencha os dados" />`,
})
class DialogHeaderHost {}

// The header is rendered inside a REAL dialog: `mat-dialog-title` and
// `mat-dialog-close` resolve the `MatDialogRef` through DI, and that wiring is
// exactly what nesting them in a shared component could silently break.
describe('DialogHeader', () => {
  let dialogRef: MatDialogRef<DialogHeaderHost>;
  let overlay: HTMLElement;

  const settle = async () => {
    TestBed.inject(ApplicationRef).tick();
    await new Promise((resolve) => setTimeout(resolve));
    TestBed.inject(ApplicationRef).tick();
  };

  beforeEach(async () => {
    TestBed.configureTestingModule({ providers: [provideNoopAnimations()] });
    overlay = TestBed.inject(OverlayContainer).getContainerElement();
    dialogRef = TestBed.inject(MatDialog).open(DialogHeaderHost);
    await settle();
  });

  afterEach(() => {
    TestBed.inject(MatDialog).closeAll();
  });

  it('should render the title in a heading marked as the dialog title', () => {
    const heading = overlay.querySelector('h2');

    expect(heading?.textContent?.trim()).toBe('Nova startup');
    expect(heading?.hasAttribute('mat-dialog-title')).toBe(true);
  });

  it('should render the description when given', () => {
    expect(overlay.querySelector('.dialog-description')?.textContent?.trim()).toBe(
      'Preencha os dados',
    );
  });

  // Without this, screen readers announce the dialog with no name.
  it('should label the dialog with its heading', () => {
    const heading = overlay.querySelector('h2')!;
    const dialog = overlay.querySelector('[role="dialog"]')!;

    expect(heading.id).toBeTruthy();
    expect(dialog.getAttribute('aria-labelledby')).toBe(heading.id);
  });

  it('should give the icon-only close button an accessible name', () => {
    const close = overlay.querySelector<HTMLButtonElement>('button.dialog-close');

    expect(close?.getAttribute('aria-label')).toBe('Fechar diálogo');
  });

  it('should close the dialog when the close button is clicked', async () => {
    const closed = firstValueFrom(dialogRef.afterClosed());

    overlay.querySelector<HTMLButtonElement>('button.dialog-close')!.click();
    await settle();
    await closed;

    expect(overlay.querySelector('app-dialog-header')).toBeNull();
  });
});
