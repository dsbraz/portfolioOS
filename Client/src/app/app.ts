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

/** Abaixo disto a sidebar cobre o conteúdo em vez de dividir a largura. */
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
   * Abaixo de 64em a sidebar deixa de dividir a largura e passa a cobrir o
   * conteúdo. Fixa em `mode="side"` ela consumia 248px de uma tela de 390px,
   * sobrando ~140px para tudo. Mesmo comportamento do shell de referência.
   */
  readonly isCompact = toSignal(
    this.breakpoints.observe(COMPACT).pipe(map((state) => state.matches)),
    { initialValue: this.breakpoints.isMatched(COMPACT) },
  );

  readonly sidenavMode = computed<'over' | 'side'>(() => (this.isCompact() ? 'over' : 'side'));

  /**
   * A barra é o TOPO DO APP sempre que a gaveta for um overlay: no compacto ela
   * fica atrás do backdrop, então removê-la ao abrir não esconde nada — só
   * reflui o conteúdo a cada abre/fecha, porque a barra ocupa espaço no fluxo.
   * Ela só sai de cena quando a sidebar está ACOPLADA e dividindo a largura,
   * onde seria repetição do que já está à vista.
   */
  readonly showOpenBar = computed(() => this.isCompact() || !this.sidenavOpened());

  // Estado inicial pelo breakpoint atual: no compacto a sidebar nasce fechada,
  // senão cobre a tela inteira ao carregar.
  readonly sidenavOpened = signal(!this.breakpoints.isMatched(COMPACT));

  private wasCompact: boolean | null = null;

  constructor() {
    effect(() => {
      const compact = this.isCompact();
      // Só age na TRANSIÇÃO de breakpoint. Reagir a toda execução faria o effect
      // sobrescrever o toggle manual — a intenção do usuário venceria só até o
      // próximo flush.
      if (this.wasCompact !== null && this.wasCompact !== compact) {
        this.sidenavOpened.set(!compact);
      }
      this.wasCompact = compact;
    });
  }


  /** Rótulo do estado ATUAL, não da próxima ação: com três estados, "Modo
   *  escuro" seria ambíguo (é o atual ou o que vem a seguir?). */
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

  /** No modo gaveta, navegar deve fechar — senão o conteúdo fica coberto. */
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
