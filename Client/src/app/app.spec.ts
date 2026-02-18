import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { App } from './app';

describe('App', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [App],
      providers: [provideRouter([]), provideAnimationsAsync()],
    }).compileComponents();
  });

  it('should create the app', () => {
    const fixture = TestBed.createComponent(App);
    const app = fixture.componentInstance;
    expect(app).toBeTruthy();
  });

  it('should render sidebar with PortfolioOS title', async () => {
    const fixture = TestBed.createComponent(App);
    await fixture.whenStable();
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('.app-logo')?.textContent).toContain('PortfolioOS');
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

  it('should not show open button in content area when sidenav is opened', async () => {
    const fixture = TestBed.createComponent(App);
    fixture.detectChanges();
    await fixture.whenStable();
    const compiled = fixture.nativeElement as HTMLElement;
    const openBtn = compiled.querySelector('.sidenav-open-btn');
    expect(openBtn).toBeFalsy();
  });
});
