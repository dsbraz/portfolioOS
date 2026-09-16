import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { By } from '@angular/platform-browser';
import { MatSidenav } from '@angular/material/sidenav';
import { BreakpointObserver } from '@angular/cdk/layout';
import { of } from 'rxjs';
import { App } from './app';

/** Compact viewport: the drawer becomes an overlay over the content. */
function compactObserver(): BreakpointObserver {
  return {
    observe: () => of({ matches: true, breakpoints: {} }),
    isMatched: () => true,
  } as unknown as BreakpointObserver;
}

describe('App on a compact viewport', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [App],
      providers: [
        provideRouter([]),
        provideAnimationsAsync(),
        { provide: BreakpointObserver, useValue: compactObserver() },
      ],
    }).compileComponents();
  });

  it('should start with the drawer closed', () => {
    const fixture = TestBed.createComponent(App);
    expect(fixture.componentInstance.sidenavOpened()).toBe(false);
  });

  // Regression: the bar disappeared when the drawer opened. Here the drawer is
  // an overlay that sits ON TOP of it, so hiding it hid nothing in practice — it
  // only pulled a block with height out of the flow, reflowing the content on
  // every open/close.
  it('should keep the open bar mounted while the drawer is open', async () => {
    const fixture = TestBed.createComponent(App);
    const app = fixture.componentInstance;
    fixture.detectChanges();
    await fixture.whenStable();

    expect(app.isCompact()).toBe(true);
    expect(fixture.nativeElement.querySelector('.sidenav-open-bar')).toBeTruthy();

    app.toggleSidenav();
    fixture.detectChanges();
    await fixture.whenStable();

    expect(app.sidenavOpened()).toBe(true);
    expect(fixture.nativeElement.querySelector('.sidenav-open-bar')).toBeTruthy();
  });
});

describe('App', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [App],
      providers: [provideRouter([]), provideAnimationsAsync()],
    }).compileComponents();
  });

  it('should render sidebar with logo', async () => {
    const fixture = TestBed.createComponent(App);
    fixture.detectChanges();
    await fixture.whenStable();
    const compiled = fixture.nativeElement as HTMLElement;
    const logo = compiled.querySelector('.app-logo img') as HTMLImageElement;
    expect(logo).toBeTruthy();
    expect(logo.alt).toBe('BRQ Portfolio');
  });

  it('should start with sidenav opened', () => {
    const fixture = TestBed.createComponent(App);
    const app = fixture.componentInstance;
    expect(app.sidenavOpened()).toBe(true);
  });

  it('should toggle sidenav state when toggleSidenav is called', () => {
    const fixture = TestBed.createComponent(App);
    const app = fixture.componentInstance;
    expect(app.sidenavOpened()).toBe(true);
    app.toggleSidenav();
    expect(app.sidenavOpened()).toBe(false);
    app.toggleSidenav();
    expect(app.sidenavOpened()).toBe(true);
  });

  it('should show close button inside sidenav when opened', async () => {
    const fixture = TestBed.createComponent(App);
    fixture.detectChanges();
    await fixture.whenStable();
    const compiled = fixture.nativeElement as HTMLElement;
    const toggleBtn = compiled.querySelector('.sidenav-toggle');
    expect(toggleBtn).toBeTruthy();
  });

  // Regression: an `effect` reacting on every run overwrote the manual toggle —
  // the sidebar reopened by itself on the next flush. It may only act on a
  // breakpoint TRANSITION.
  it('should keep the manual toggle after change detection', async () => {
    const fixture = TestBed.createComponent(App);
    const app = fixture.componentInstance;
    fixture.detectChanges();
    await fixture.whenStable();

    app.toggleSidenav();
    fixture.detectChanges();
    await fixture.whenStable();

    expect(app.sidenavOpened()).toBe(false);
  });

  // Regression: the bar scrolled off screen along with the content. With the
  // drawer closed it is the only way back to navigation — once off screen, the
  // app loses navigation from the first scroll, and on mobile the drawer starts
  // closed, so this applied to every page.
  it('should keep the open bar pinned while the content scrolls', async () => {
    const fixture = TestBed.createComponent(App);
    const app = fixture.componentInstance;
    app.toggleSidenav();
    fixture.detectChanges();
    await fixture.whenStable();

    const bar = fixture.nativeElement.querySelector('.sidenav-open-bar') as HTMLElement;
    expect(bar).toBeTruthy();
    expect(getComputedStyle(bar).position).toBe('sticky');
  });

  // Regression: `[opened]` is a ONE-WAY binding. When the drawer is closed via
  // the backdrop or Escape, Material changes its own state without touching the
  // signal. The signal kept saying "open", the bar — which only exists when it
  // says "closed" — never came back, and the app was left with no path to
  // navigation. On mobile, where closing via the backdrop is the natural
  // gesture, opening and closing the menu once was enough to lose navigation.
  it('should restore the open bar when the drawer closes on its own', async () => {
    const fixture = TestBed.createComponent(App);
    const app = fixture.componentInstance;
    fixture.detectChanges();
    await fixture.whenStable();

    app.sidenavOpened.set(true);
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('.sidenav-open-bar')).toBeNull();

    // What backdrop and Escape fire internally.
    fixture.debugElement
      .query(By.directive(MatSidenav))
      .triggerEventHandler('openedChange', false);
    fixture.detectChanges();
    await fixture.whenStable();

    expect(app.sidenavOpened()).toBe(false);
    expect(fixture.nativeElement.querySelector('.sidenav-open-bar')).toBeTruthy();
  });

  // The other half of the rule: when docked, the sidebar is already in view and
  // the bar would be redundant.
  it('should hide the open bar while the sidebar is docked open', async () => {
    const fixture = TestBed.createComponent(App);
    fixture.detectChanges();
    await fixture.whenStable();

    expect(fixture.componentInstance.isCompact()).toBe(false);
    expect(fixture.nativeElement.querySelector('.sidenav-open-bar')).toBeNull();
  });

  it('should show open button in content area when sidenav is closed', async () => {
    const fixture = TestBed.createComponent(App);
    const app = fixture.componentInstance;
    app.toggleSidenav();
    fixture.detectChanges();
    await fixture.whenStable();
    const compiled = fixture.nativeElement as HTMLElement;
    const openBtn = compiled.querySelector('.sidenav-open-btn');
    expect(openBtn).toBeTruthy();
  });

});
