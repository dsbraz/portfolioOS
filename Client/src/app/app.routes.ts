import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    redirectTo: 'portfolio-monitoring',
    pathMatch: 'full',
  },
  {
    path: 'portfolio-monitoring',
    loadComponent: () =>
      import('./pages/portfolio-monitoring/portfolio-monitoring').then((m) => m.PortfolioMonitoring),
  },
  {
    path: 'startup/:id',
    loadComponent: () =>
      import('./pages/startups/startup-detail/startup-detail').then((m) => m.StartupDetail),
  },
  {
    path: 'dealflow',
    loadComponent: () =>
      import('./pages/dealflow/dealflow').then((m) => m.Dealflow),
  },
  {
    path: 'report/:token',
    loadComponent: () => import('./pages/report/report-form'),
    data: { public: true },
  },
];
