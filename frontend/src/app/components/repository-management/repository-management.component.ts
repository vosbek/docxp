import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';

// PrimeNG Imports
import { CardModule } from 'primeng/card';
import { ButtonModule } from 'primeng/button';
import { TableModule } from 'primeng/table';
import { TagModule } from 'primeng/tag';
import { InputTextModule } from 'primeng/inputtext';
import { DialogModule } from 'primeng/dialog';
import { ProgressBarModule } from 'primeng/progressbar';
import { ToastModule } from 'primeng/toast';
import { TooltipModule } from 'primeng/tooltip';
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { MessageService, ConfirmationService } from 'primeng/api';
import { trigger, state, style, transition, animate } from '@angular/animations';

import { ApiService, RepositoryInfo } from '../../services/api.service';

interface RepositoryStatus {
  path: string;
  name: string;
  status: 'synced' | 'syncing' | 'error' | 'not_synced';
  lastSync: string;
  filesCount: number;
  size: string;
  lastJobId?: string;
  lastJobStatus?: string;
  health: 'healthy' | 'warning' | 'error';
}

@Component({
  selector: 'app-repository-management',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    CardModule,
    ButtonModule,
    TableModule,
    TagModule,
    InputTextModule,
    DialogModule,
    ProgressBarModule,
    ToastModule,
    TooltipModule,
    ConfirmDialogModule
  ],
  providers: [MessageService, ConfirmationService],
  templateUrl: './repository-management.component.html',
  styleUrl: './repository-management.component.scss',
  animations: [
    trigger('slideIn', [
      transition(':enter', [
        style({ opacity: 0, transform: 'translateX(-20px)' }),
        animate('300ms ease-out', style({ opacity: 1, transform: 'translateX(0)' }))
      ])
    ])
  ]
})
export class RepositoryManagementComponent implements OnInit {
  repositories: RepositoryStatus[] = [];
  loading: boolean = true;
  showAddDialog: boolean = false;
  newRepositoryPath: string = '';
  addingRepository: boolean = false;
  
  // Statistics
  totalRepositories: number = 0;
  syncedRepositories: number = 0;
  healthyRepositories: number = 0;

  constructor(
    private apiService: ApiService,
    private messageService: MessageService,
    private confirmationService: ConfirmationService,
    private router: Router
  ) {}

  ngOnInit() {
    this.loadRepositories();
    this.startPeriodicRefresh();
  }

  loadRepositories() {
    this.loading = true;
    
    // Since we don't have a dedicated repository list endpoint, 
    // we'll simulate this with job data and repository discovery
    this.apiService.listJobs(0, 50).subscribe({
      next: (jobs: any[]) => {
        // Extract unique repositories from jobs
        const repoMap = new Map<string, RepositoryStatus>();
        
        jobs.forEach(job => {
          const repoPath = job.repository_path;
          const repoName = repoPath.split('/').pop() || 'Unknown';
          
          if (!repoMap.has(repoPath)) {
            repoMap.set(repoPath, {
              path: repoPath,
              name: repoName,
              status: this.getRepositoryStatus(job.status),
              lastSync: job.created_at,
              filesCount: job.files_processed || 0,
              size: this.formatFileSize(job.files_processed * 1024), // Estimate
              lastJobId: job.job_id,
              lastJobStatus: job.status,
              health: this.getRepositoryHealth(job.status)
            });
          } else {
            // Update with latest job data if more recent
            const existing = repoMap.get(repoPath)!;
            if (new Date(job.created_at) > new Date(existing.lastSync)) {
              existing.lastSync = job.created_at;
              existing.lastJobId = job.job_id;
              existing.lastJobStatus = job.status;
              existing.status = this.getRepositoryStatus(job.status);
              existing.health = this.getRepositoryHealth(job.status);
            }
          }
        });
        
        this.repositories = Array.from(repoMap.values()).sort((a, b) => 
          new Date(b.lastSync).getTime() - new Date(a.lastSync).getTime()
        );
        
        this.updateStatistics();
        this.loading = false;
      },
      error: (error) => {
        console.error('Error loading repositories:', error);
        this.messageService.add({
          severity: 'error',
          summary: 'Load Error',
          detail: 'Failed to load repository data'
        });
        this.loading = false;
      }
    });
  }

  private getRepositoryStatus(jobStatus: string): 'synced' | 'syncing' | 'error' | 'not_synced' {
    switch (jobStatus) {
      case 'completed':
      case 'success':
        return 'synced';
      case 'processing':
      case 'pending':
        return 'syncing';
      case 'failed':
        return 'error';
      default:
        return 'not_synced';
    }
  }

  private getRepositoryHealth(jobStatus: string): 'healthy' | 'warning' | 'error' {
    switch (jobStatus) {
      case 'completed':
      case 'success':
        return 'healthy';
      case 'processing':
      case 'pending':
        return 'warning';
      case 'failed':
        return 'error';
      default:
        return 'warning';
    }
  }

  private formatFileSize(bytes: number): string {
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    if (bytes === 0) return '0 Bytes';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  }

  private updateStatistics() {
    this.totalRepositories = this.repositories.length;
    this.syncedRepositories = this.repositories.filter(r => r.status === 'synced').length;
    this.healthyRepositories = this.repositories.filter(r => r.health === 'healthy').length;
  }

  // Actions
  showAddRepositoryDialog() {
    this.showAddDialog = true;
    this.newRepositoryPath = '';
  }

  addRepository() {
    if (!this.newRepositoryPath.trim()) {
      this.messageService.add({
        severity: 'warn',
        summary: 'Invalid Input',
        detail: 'Please enter a valid repository path'
      });
      return;
    }

    this.addingRepository = true;
    
    this.apiService.syncRepository(this.newRepositoryPath).subscribe({
      next: (response) => {
        this.messageService.add({
          severity: 'success',
          summary: 'Repository Added',
          detail: 'Repository sync initiated successfully'
        });
        this.showAddDialog = false;
        this.newRepositoryPath = '';
        this.addingRepository = false;
        
        // Refresh the list after a short delay
        setTimeout(() => this.loadRepositories(), 1000);
      },
      error: (error) => {
        this.messageService.add({
          severity: 'error',
          summary: 'Sync Failed',
          detail: error.error?.detail || 'Failed to sync repository'
        });
        this.addingRepository = false;
      }
    });
  }

  syncRepository(repo: RepositoryStatus) {
    this.messageService.add({
      severity: 'info',
      summary: 'Syncing',
      detail: `Starting sync for ${repo.name}...`
    });

    repo.status = 'syncing';
    
    this.apiService.syncRepository(repo.path).subscribe({
      next: (response) => {
        this.messageService.add({
          severity: 'success',
          summary: 'Sync Started',
          detail: `Repository ${repo.name} sync initiated`
        });
        
        // Refresh data after sync
        setTimeout(() => this.loadRepositories(), 2000);
      },
      error: (error) => {
        repo.status = 'error';
        this.messageService.add({
          severity: 'error',
          summary: 'Sync Failed',
          detail: error.error?.detail || 'Failed to sync repository'
        });
      }
    });
  }

  generateDocumentation(repo: RepositoryStatus) {
    this.router.navigate(['/generate'], { 
      queryParams: { 
        repo: repo.path,
        name: repo.name 
      } 
    });
  }

  viewLastJob(repo: RepositoryStatus) {
    if (repo.lastJobId) {
      this.router.navigate(['/jobs', repo.lastJobId]);
    }
  }

  confirmRemoveRepository(repo: RepositoryStatus) {
    this.confirmationService.confirm({
      message: `Are you sure you want to remove repository "${repo.name}" from tracking?`,
      header: 'Remove Repository',
      icon: 'pi pi-exclamation-triangle',
      accept: () => {
        this.removeRepository(repo);
      }
    });
  }

  private removeRepository(repo: RepositoryStatus) {
    // Since there's no dedicated remove endpoint, we'll just hide it from the UI
    // In a real implementation, this would call an API to remove the repository
    this.repositories = this.repositories.filter(r => r.path !== repo.path);
    this.updateStatistics();
    
    this.messageService.add({
      severity: 'info',
      summary: 'Repository Removed',
      detail: `${repo.name} has been removed from tracking`
    });
  }

  // Utility methods
  getStatusSeverity(status: string): "success" | "secondary" | "info" | "warning" | "danger" | "contrast" | undefined {
    const severityMap: { [key: string]: "success" | "secondary" | "info" | "warning" | "danger" | "contrast" } = {
      'synced': 'success',
      'syncing': 'warning',
      'error': 'danger',
      'not_synced': 'secondary'
    };
    return severityMap[status] || 'secondary';
  }

  getHealthSeverity(health: string): "success" | "secondary" | "info" | "warning" | "danger" | "contrast" | undefined {
    const severityMap: { [key: string]: "success" | "secondary" | "info" | "warning" | "danger" | "contrast" } = {
      'healthy': 'success',
      'warning': 'warning',
      'error': 'danger'
    };
    return severityMap[health] || 'secondary';
  }

  getRelativeTime(timestamp: string): string {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const hours = Math.floor(diff / (1000 * 60 * 60));
    
    if (hours < 1) {
      const minutes = Math.floor(diff / (1000 * 60));
      return `${minutes} min ago`;
    } else if (hours < 24) {
      return `${hours}h ago`;
    } else {
      const days = Math.floor(hours / 24);
      return `${days}d ago`;
    }
  }

  private startPeriodicRefresh() {
    // Refresh repository status every 30 seconds
    setInterval(() => {
      if (!this.loading) {
        this.loadRepositories();
      }
    }, 30000);
  }

  // Navigation helpers
  navigateToAnalytics() {
    this.router.navigate(['/analytics']);
  }

  navigateToHistory() {
    this.router.navigate(['/history']);
  }
}