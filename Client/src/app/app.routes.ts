import { Routes } from '@angular/router';

import { authGuard } from './guards/auth.guard';

export const routes: Routes = [
  {
    path: '',
    redirectTo: 'portfolio',
    pathMatch: 'full',
  },
  {
    path: 'login',
    loadComponent: () => import('./pages/login/login').then((m) => m.Login),
    data: { public: true },
  },
  {
    path: 'portfolio',
    loadComponent: () =>
      import('./pages/portfolio/portfolio').then((m) => m.Portfolio),
    canActivate: [authGuard],
  },
  {
    path: 'startup/:id',
    loadComponent: () =>
      import('./pages/startups/startup-detail/startup-detail').then((m) => m.StartupDetail),
    canActivate: [authGuard],
  },
  {
    path: 'dealflow',
    loadComponent: () =>
      import('./pages/dealflow/dealflow').then((m) => m.Dealflow),
    canActivate: [authGuard],
  },
  {
    path: 'users',
    loadComponent: () => import('./pages/users/users').then((m) => m.Users),
    canActivate: [authGuard],
  },
  {
    path: 'monthly-indicator/:token',
    loadComponent: () => import('./pages/report/report-form'),
    data: { public: true },
  },
];
