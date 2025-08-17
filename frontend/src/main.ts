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
    path: 'chat', 
    loadComponent: () => import('./app/components/chat/chat-interface.component').then(m => m.ChatInterfaceComponent) 
  },
  { 
    path: 'v1-search', 
    loadComponent: () => import('./app/components/v1-search/v1-search.component').then(m => m.V1SearchComponent) 
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
