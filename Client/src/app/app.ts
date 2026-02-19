import { Component, inject, OnInit, signal } from '@angular/core';
import { NavigationEnd, Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { filter } from 'rxjs/operators';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatListModule } from '@angular/material/list';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';

import { AuthService } from './services/auth.service';

@Component({
  selector: 'app-root',
  imports: [
    RouterOutlet,
    RouterLink,
    RouterLinkActive,
    MatSidenavModule,
    MatListModule,
    MatIconModule,
    MatButtonModule,
  ],
  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class App implements OnInit {
  private readonly router = inject(Router);
  private readonly authService = inject(AuthService);

  readonly sidenavOpened = signal(true);
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

  toggleSidenav(): void {
    this.sidenavOpened.update(opened => !opened);
  }

  logout(): void {
    this.authService.logout();
    this.router.navigate(['/login']);
  }
}
