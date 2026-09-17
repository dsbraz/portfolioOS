import { Component, input } from '@angular/core';

export type ReadItemKind = 'text' | 'num' | 'long';

export interface ReadItem {
  label: string;
  value: string | null;
  /** `num` aligns in tabular mono; `long` spans the whole row. */
  kind?: ReadItemKind;
}

export interface ReadSection {
  /** Without a title, the section renders only the pairs — the case for records without groups. */
  title?: string;
  items: ReadItem[];
}

/**
 * READ view of a record.
 *
 * Replaces the disabled form that used to serve as read-only mode. There the
 * data inherited the inactive control color — `#121212` at 38%, measured at 2.46:1
 * in the light theme — while the label next to it sat at 18.7:1. WCAG 1.4.3 exempts
 * inactive components from contrast, so no automated checker complained; but here
 * the control's text WAS the information, and the exemption ended up excusing
 * unreadable data.
 *
 * A definition list describes what the thing is: label/value pairs in full ink,
 * without boxes pretending to be editable. The sections mirror those of edit
 * mode, so reading and editing present the record in the same order and with
 * the same groupings.
 */
@Component({
  selector: 'app-read-view',
  templateUrl: './read-view.html',
  styleUrl: './read-view.scss',
})
export class ReadView {
  readonly sections = input.required<ReadSection[]>();
}
