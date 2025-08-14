import { bootstrapApplication } from '@angular/platform-browser';
import { provideRouter, Routes } from '@angular/router';
import { provideHttpClient } from '@angular/common/http';
import { provideAnimations } from '@angular/platform-browser/animations';
import { AppComponent } from './app/app.component';

const routes: Routes = [
  { path: '', redirectTo: '/dashboard', pathMatch: 'full' },
  { 
    path: 'dashboard', 
    loadComponent: () => import('./app/components/dashboard/dashboard.component').then(m => m.DashboardComponent) 
  },
  { 
    path: 'generate', 
    loadComponent: () => import('./app/components/generation-wizard/generation-wizard.component').then(m => m.GenerationWizardComponent) 
  },
  { 
    path: 'repositories', 
    loadComponent: () => import('./app/components/dashboard/dashboard.component').then(m => m.DashboardComponent) 
  },
  { 
    path: 'history', 
    loadComponent: () => import('./app/components/dashboard/dashboard.component').then(m => m.DashboardComponent) 
  },
  { 
    path: 'analytics', 
    loadComponent: () => import('./app/components/dashboard/dashboard.component').then(m => m.DashboardComponent) 
  },
  { 
    path: 'settings', 
    loadComponent: () => import('./app/components/dashboard/dashboard.component').then(m => m.DashboardComponent) 
  },
  { 
    path: 'jobs/:id', 
    loadComponent: () => import('./app/components/job-details/job-details.component').then(m => m.JobDetailsComponent) 
  },
  { 
    path: 'documentation/:id', 
    loadComponent: () => import('./app/components/dashboard/dashboard.component').then(m => m.DashboardComponent) 
  },
  { path: '**', redirectTo: '/dashboard' }
];

bootstrapApplication(AppComponent, {
  providers: [
    provideRouter(routes),
    provideHttpClient(),
    provideAnimations()
  ]
}).catch(err => console.error(err));
