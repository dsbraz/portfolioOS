import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { By } from '@angular/platform-browser';
import { MatSidenav } from '@angular/material/sidenav';
import { BreakpointObserver } from '@angular/cdk/layout';
import { of } from 'rxjs';
import { App } from './app';

/** Viewport compacta: a gaveta vira overlay sobre o conteúdo. */
function compactObserver(): BreakpointObserver {
  return {
    observe: () => of({ matches: true, breakpoints: {} }),
    isMatched: () => true,
  } as unknown as BreakpointObserver;
}

describe('App em viewport compacta', () => {
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

  // Regressão: a barra sumia ao abrir a gaveta. Aqui a gaveta é um overlay e
  // fica POR CIMA dela, então esconder não escondia nada de fato — apenas tirava
  // do fluxo um bloco que ocupa altura, refluindo o conteúdo a cada abre/fecha.
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

  it('should expose the navigation labels used by people and browser agents', async () => {
    const fixture = TestBed.createComponent(App);
    fixture.detectChanges();
    await fixture.whenStable();
    const links = Array.from(
      (fixture.nativeElement as HTMLElement).querySelectorAll<HTMLAnchorElement>('nav a'),
    );

    expect(
      links.some((link) => link.querySelector('span')?.textContent?.trim() === 'Monitoramento'),
    ).toBe(true);
    const aiLink = links.find(
      (link) => link.querySelector('span')?.textContent?.trim() === 'IA na plataforma',
    );
    expect(aiLink?.getAttribute('href')).toBe('/ia');
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

  // Regressão: um `effect` reagindo a toda execução sobrescrevia o toggle
  // manual — a sidebar reabria sozinha no flush seguinte. Ele só pode agir na
  // TRANSIÇÃO de breakpoint.
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

  // Regressão: a barra rolava para fora da tela junto com o conteúdo. Com a
  // gaveta fechada ela é o único caminho de volta para a navegação — saindo da
  // tela, o app fica sem navegar a partir do primeiro scroll, e no mobile a
  // gaveta nasce fechada, então isso valia para todas as páginas.
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

  // Regressão: `[opened]` é binding de MÃO ÚNICA. Fechando a gaveta pelo
  // backdrop ou pelo Escape, o Material muda o próprio estado sem tocar no
  // sinal. O sinal seguia dizendo "aberta", a barra — que só existe quando ele
  // diz "fechada" — não voltava, e o app ficava sem nenhum caminho para a
  // navegação. No mobile, onde fechar pelo backdrop é o gesto natural, bastava
  // abrir e fechar o menu uma vez para perder a navegação.
  it('should restore the open bar when the drawer closes on its own', async () => {
    const fixture = TestBed.createComponent(App);
    const app = fixture.componentInstance;
    fixture.detectChanges();
    await fixture.whenStable();

    app.sidenavOpened.set(true);
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('.sidenav-open-bar')).toBeNull();

    // O que backdrop e Escape disparam por dentro.
    fixture.debugElement.query(By.directive(MatSidenav)).triggerEventHandler('openedChange', false);
    fixture.detectChanges();
    await fixture.whenStable();

    expect(app.sidenavOpened()).toBe(false);
    expect(fixture.nativeElement.querySelector('.sidenav-open-bar')).toBeTruthy();
  });

  // A outra metade da regra: acoplada, a sidebar já está à vista e a barra
  // seria repetição.
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
