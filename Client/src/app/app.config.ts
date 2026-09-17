import { ApplicationConfig, provideBrowserGlobalErrorListeners } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { MAT_DIALOG_DEFAULT_OPTIONS, MatDialogConfig } from '@angular/material/dialog';
import { MAT_FORM_FIELD_DEFAULT_OPTIONS } from '@angular/material/form-field';

import { routes } from './app.routes';
import { authInterceptor } from './interceptors/auth.interceptor';

/**
 * Dialog defaults.
 *
 * `ariaModal` matters: Material ships `aria-modal="false"`, which tells
 * assistive tech the content behind the dialog is still reachable. Every dialog
 * here is genuinely modal, so it has to say so.
 */
export const dialogDefaults: MatDialogConfig = {
  // This object REPLACES Material's whole default config instead of merging
  // with it, so start from Material's defaults (`role: 'dialog'`,
  // `restoreFocus`, `hasBackdrop`, `closeOnNavigation`...) and override only
  // what the brand changes. Without `role`, `aria-modal` means nothing.
  ...new MatDialogConfig(),
  ariaModal: true,
  // `first-tabbable` would land on the close button, since it leads the header
  // in DOM order. WAI-ARIA APG calls that out: when the first focusable element
  // is the dismiss control, focus the dialog itself instead. Doing so also gets
  // the title announced, and works for the dialogs that have no input at all.
  autoFocus: 'dialog',
  maxWidth: 'min(92vw, 42rem)',
  width: 'min(34rem, 92vw)',
};

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideRouter(routes),
    provideHttpClient(withInterceptors([authInterceptor])),
    provideAnimationsAsync(),
    { provide: MAT_DIALOG_DEFAULT_OPTIONS, useValue: dialogDefaults },
    {
      // `subscriptSizing` stays `fixed` on purpose. `dynamic` reclaims the strip
      // reserved under each field, but that strip is what keeps a validation
      // error from shoving every field below it down the moment it appears.
      // Density is bought on the field's own height instead — see `styles.scss`.
      provide: MAT_FORM_FIELD_DEFAULT_OPTIONS,
      useValue: { appearance: 'outline', subscriptSizing: 'fixed' },
    },
  ]
};
