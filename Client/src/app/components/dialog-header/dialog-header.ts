import { Component, input } from '@angular/core';
import { MatDialogModule } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';

/**
 * Dialog header — title plus a close control.
 *
 * Every dialog in the app uses this so the close affordance and the title
 * typography cannot drift apart. Ported from `BrqDialog` in the px-operations
 * redesign, where the header carries the title, an optional description and the
 * close button on the trailing edge.
 *
 * `mat-dialog-title` stays on the heading: Material reads it to build the
 * dialog's `aria-labelledby`, and the directive resolves its `MatDialogRef`
 * through DI, so nesting it inside this component keeps that wiring intact.
 */
@Component({
  selector: 'app-dialog-header',
  imports: [MatDialogModule, MatIconModule],
  templateUrl: './dialog-header.html',
  styleUrl: './dialog-header.scss',
})
export class DialogHeader {
  readonly title = input.required<string>();
  readonly description = input<string>('');
}
