import { Component, computed, effect, inject, OnInit, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { BreakpointObserver } from '@angular/cdk/layout';
import { NavigationEnd, Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { filter, map } from 'rxjs/operators';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';

import { AuthService } from './services/auth.service';
import { ThemeService } from './services/theme.service';

/** Below this, the sidebar covers the content instead of sharing the width. */
const COMPACT = '(max-width: 64em)';

@Component({
  selector: 'app-root',
  imports: [
    RouterOutlet,
    RouterLink,
    RouterLinkActive,
    MatSidenavModule,
    MatIconModule,
    MatButtonModule,
  ],
  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class App implements OnInit {
  private readonly router = inject(Router);
  private readonly authService = inject(AuthService);

  readonly theme = inject(ThemeService);
  private readonly breakpoints = inject(BreakpointObserver);

  /**
   * Below 64em the sidebar stops sharing the width and covers the content
   * instead. Pinned in `mode="side"` it took 248px of a 390px screen, leaving
   * ~140px for everything else. Same behavior as the reference shell.
   */
  readonly isCompact = toSignal(
    this.breakpoints.observe(COMPACT).pipe(map((state) => state.matches)),
    { initialValue: this.breakpoints.isMatched(COMPACT) },
  );

  readonly sidenavMode = computed<'over' | 'side'>(() => (this.isCompact() ? 'over' : 'side'));

  /**
   * The bar is the APP TOP whenever the drawer is an overlay: in compact mode it
   * sits behind the backdrop, so removing it on open hides nothing — it only
   * reflows the content on every open/close, because the bar takes space in the flow.
   * It only goes away when the sidebar is DOCKED and sharing the width,
   * where it would repeat what is already in view.
   */
  readonly showOpenBar = computed(() => this.isCompact() || !this.sidenavOpened());

  // Initial state follows the current breakpoint: in compact mode the sidebar
  // starts closed, otherwise it covers the whole screen on load.
  readonly sidenavOpened = signal(!this.breakpoints.isMatched(COMPACT));

  private wasCompact: boolean | null = null;

  constructor() {
    effect(() => {
      const compact = this.isCompact();
      // Only acts on a breakpoint TRANSITION. Reacting to every run would make the
      // effect overwrite the manual toggle — the user's intent would only win until
      // the next flush.
      if (this.wasCompact !== null && this.wasCompact !== compact) {
        this.sidenavOpened.set(!compact);
      }
      this.wasCompact = compact;
    });
  }


  /** Label for the CURRENT state, not the next action: with three states, "Modo
   *  escuro" would be ambiguous (is it the current one or the next?). */
  readonly themeLabel = computed(() => {
    const t = this.theme.theme();
    if (t === 'light') return 'Tema claro';
    if (t === 'dark') return 'Tema escuro';
    return 'Tema do sistema';
  });

  readonly themeIcon = computed(() => {
    const t = this.theme.theme();
    if (t === 'light') return 'light_mode';
    if (t === 'dark') return 'dark_mode';
    return 'brightness_auto';
  });
  readonly isPublicRoute = signal(false);

  ngOnInit(): void {
    this.router.events
      .pipe(filter((e): e is NavigationEnd => e instanceof NavigationEnd))
      .subscribe(() => {
        let child = this.router.routerState.snapshot.root;
        while (child.firstChild) {
          child = child.firstChild;
        }
        this.isPublicRoute.set(child.data['public'] === true);
      });
  }

  /** In drawer mode, navigating must close it — otherwise the content stays covered. */
  closeOnCompact(): void {
    if (this.isCompact()) this.sidenavOpened.set(false);
  }

  toggleSidenav(): void {
    this.sidenavOpened.update(opened => !opened);
  }

  logout(): void {
    this.authService.logout();
    this.router.navigate(['/login']);
  }
}
