import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { FormsModule } from '@angular/forms';

// PrimeNG Imports
import { CardModule } from 'primeng/card';
import { ButtonModule } from 'primeng/button';
import { TableModule } from 'primeng/table';
import { TagModule } from 'primeng/tag';
import { InputTextModule } from 'primeng/inputtext';
import { CalendarModule } from 'primeng/calendar';
import { DropdownModule } from 'primeng/dropdown';
import { ProgressBarModule } from 'primeng/progressbar';
import { ToastModule } from 'primeng/toast';
import { TooltipModule } from 'primeng/tooltip';
import { ChartModule } from 'primeng/chart';
import { TimelineModule } from 'primeng/timeline';
import { DialogModule } from 'primeng/dialog';
import { MessageService } from 'primeng/api';
import { trigger, state, style, transition, animate } from '@angular/animations';

import { ApiService, JobStatus } from '../../services/api.service';
import { Subscription, interval } from 'rxjs';

interface JobHistoryItem {
  id: string;
  repository: string;
  repositoryPath: string;
  status: 'success' | 'processing' | 'failed' | 'pending' | 'completed';
  startTime: string;
  endTime?: string;
  duration: string;
  entitiesCount: number;
  businessRulesCount: number;
  filesProcessed: number;
  outputSize: string;
  hasOutput: boolean;
}

interface FilterOptions {
  status: string;
  repository: string;
  dateFrom?: Date;
  dateTo?: Date;
}

@Component({
  selector: 'app-documentation-history',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    CardModule,
    ButtonModule,
    TableModule,
    TagModule,
    InputTextModule,
    CalendarModule,
    DropdownModule,
    ProgressBarModule,
    ToastModule,
    TooltipModule,
    ChartModule,
    TimelineModule,
    DialogModule
  ],
  providers: [MessageService],
  templateUrl: './documentation-history.component.html',
  styleUrl: './documentation-history.component.scss',
  animations: [
    trigger('slideIn', [
      transition(':enter', [
        style({ opacity: 0, transform: 'translateY(-10px)' }),
        animate('300ms ease-out', style({ opacity: 1, transform: 'translateY(0)' }))
      ])
    ])
  ]
})
export class DocumentationHistoryComponent implements OnInit, OnDestroy {
  jobs: JobHistoryItem[] = [];
  filteredJobs: JobHistoryItem[] = [];
  loading: boolean = true;
  totalRecords: number = 0;
  
  // Filters
  filters: FilterOptions = {
    status: 'all',
    repository: 'all'
  };
  
  statusOptions = [
    { label: 'All Status', value: 'all' },
    { label: 'Completed', value: 'completed' },
    { label: 'Success', value: 'success' },
    { label: 'Processing', value: 'processing' },
    { label: 'Failed', value: 'failed' },
    { label: 'Pending', value: 'pending' }
  ];
  
  repositoryOptions: any[] = [
    { label: 'All Repositories', value: 'all' }
  ];

  // Pagination
  first: number = 0;
  rows: number = 20;
  
  // Statistics
  statistics = {
    total: 0,
    completed: 0,
    failed: 0,
    processing: 0,
    avgDuration: '0m 0s',
    totalEntities: 0,
    totalRules: 0
  };

  // Chart data
  chartData: any;
  chartOptions: any;
  
  // Timeline data
  recentActivity: any[] = [];

  // Detail dialog
  showJobDetail: boolean = false;
  selectedJob: JobHistoryItem | null = null;

  private refreshSubscription: Subscription | null = null;

  constructor(
    private apiService: ApiService,
    private messageService: MessageService,
    private router: Router
  ) {}

  ngOnInit() {
    this.loadJobs();
    this.initializeChart();
    this.startAutoRefresh();
  }

  ngOnDestroy() {
    if (this.refreshSubscription) {
      this.refreshSubscription.unsubscribe();
    }
  }

  loadJobs() {
    this.loading = true;
    
    this.apiService.listJobs(this.first, this.rows).subscribe({
      next: (jobs: any[]) => {
        this.jobs = jobs.map(job => ({
          id: job.job_id,
          repository: job.repository_path.split('/').pop() || 'Unknown',
          repositoryPath: job.repository_path,
          status: this.mapJobStatus(job.status),
          startTime: job.created_at,
          endTime: job.completed_at,
          duration: this.calculateDuration(job.created_at, job.completed_at),
          entitiesCount: job.entities_count || 0,
          businessRulesCount: job.business_rules_count || 0,
          filesProcessed: job.files_processed || 0,
          outputSize: this.formatFileSize((job.files_processed || 0) * 1024),
          hasOutput: job.status === 'completed' || job.status === 'success'
        }));
        
        this.totalRecords = jobs.length; // In a real app, this would come from the API
        this.updateRepositoryOptions();
        this.applyFilters();
        this.calculateStatistics();
        this.updateChartData();
        this.updateRecentActivity();
        this.loading = false;
      },
      error: (error) => {
        console.error('Error loading jobs:', error);
        this.messageService.add({
          severity: 'error',
          summary: 'Load Error',
          detail: 'Failed to load job history'
        });
        this.loading = false;
      }
    });
  }

  private mapJobStatus(status: string): 'success' | 'processing' | 'failed' | 'pending' | 'completed' {
    const statusMap: { [key: string]: 'success' | 'processing' | 'failed' | 'pending' | 'completed' } = {
      'completed': 'success',
      'processing': 'processing',
      'failed': 'failed',
      'pending': 'pending',
      'success': 'success'
    };
    return statusMap[status] || 'pending';
  }

  private calculateDuration(start: string, end?: string): string {
    if (!end) return 'In progress';
    
    const startDate = new Date(start);
    const endDate = new Date(end);
    const diff = endDate.getTime() - startDate.getTime();
    
    const minutes = Math.floor(diff / (1000 * 60));
    const seconds = Math.floor((diff % (1000 * 60)) / 1000);
    
    return `${minutes}m ${seconds}s`;
  }

  private formatFileSize(bytes: number): string {
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    if (bytes === 0) return '0 Bytes';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  }

  private updateRepositoryOptions() {
    const uniqueRepos = [...new Set(this.jobs.map(job => job.repository))];
    this.repositoryOptions = [
      { label: 'All Repositories', value: 'all' },
      ...uniqueRepos.map(repo => ({ label: repo, value: repo }))
    ];
  }

  applyFilters() {
    this.filteredJobs = this.jobs.filter(job => {
      // Status filter
      if (this.filters.status !== 'all' && job.status !== this.filters.status) {
        return false;
      }
      
      // Repository filter
      if (this.filters.repository !== 'all' && job.repository !== this.filters.repository) {
        return false;
      }
      
      // Date filter
      const jobDate = new Date(job.startTime);
      if (this.filters.dateFrom && jobDate < this.filters.dateFrom) {
        return false;
      }
      if (this.filters.dateTo && jobDate > this.filters.dateTo) {
        return false;
      }
      
      return true;
    });
  }

  onFilterChange() {
    this.applyFilters();
    this.calculateStatistics();
  }

  clearFilters() {
    this.filters = {
      status: 'all',
      repository: 'all'
    };
    this.applyFilters();
    this.calculateStatistics();
  }

  private calculateStatistics() {
    const jobs = this.filteredJobs;
    
    this.statistics = {
      total: jobs.length,
      completed: jobs.filter(j => j.status === 'success' || j.status === 'completed').length,
      failed: jobs.filter(j => j.status === 'failed').length,
      processing: jobs.filter(j => j.status === 'processing').length,
      avgDuration: this.calculateAverageDuration(jobs),
      totalEntities: jobs.reduce((sum, job) => sum + job.entitiesCount, 0),
      totalRules: jobs.reduce((sum, job) => sum + job.businessRulesCount, 0)
    };
  }

  private calculateAverageDuration(jobs: JobHistoryItem[]): string {
    const completedJobs = jobs.filter(j => j.endTime && j.status === 'success');
    if (completedJobs.length === 0) return '0m 0s';
    
    const totalMs = completedJobs.reduce((sum, job) => {
      const start = new Date(job.startTime).getTime();
      const end = new Date(job.endTime!).getTime();
      return sum + (end - start);
    }, 0);
    
    const avgMs = totalMs / completedJobs.length;
    const minutes = Math.floor(avgMs / (1000 * 60));
    const seconds = Math.floor((avgMs % (1000 * 60)) / 1000);
    
    return `${minutes}m ${seconds}s`;
  }

  private initializeChart() {
    const documentStyle = getComputedStyle(document.documentElement);
    
    this.chartOptions = {
      maintainAspectRatio: false,
      aspectRatio: 0.8,
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            usePointStyle: true,
            padding: 20
          }
        }
      },
      scales: {
        x: {
          grid: {
            display: false
          }
        },
        y: {
          beginAtZero: true,
          grid: {
            color: 'rgba(0, 0, 0, 0.05)'
          }
        }
      }
    };
  }

  private updateChartData() {
    // Group jobs by date for the last 7 days
    const last7Days = Array.from({ length: 7 }, (_, i) => {
      const date = new Date();
      date.setDate(date.getDate() - (6 - i));
      return date.toISOString().split('T')[0];
    });

    const jobsByDate = last7Days.map(date => {
      const jobsOnDate = this.jobs.filter(job => 
        job.startTime.split('T')[0] === date
      );
      return {
        date,
        total: jobsOnDate.length,
        successful: jobsOnDate.filter(j => j.status === 'success').length,
        failed: jobsOnDate.filter(j => j.status === 'failed').length
      };
    });

    this.chartData = {
      labels: last7Days.map(date => new Date(date).toLocaleDateString('en-US', { weekday: 'short' })),
      datasets: [
        {
          label: 'Total Jobs',
          data: jobsByDate.map(d => d.total),
          borderColor: '#667eea',
          backgroundColor: 'rgba(102, 126, 234, 0.1)',
          tension: 0.4
        },
        {
          label: 'Successful',
          data: jobsByDate.map(d => d.successful),
          borderColor: '#10b981',
          backgroundColor: 'rgba(16, 185, 129, 0.1)',
          tension: 0.4
        },
        {
          label: 'Failed',
          data: jobsByDate.map(d => d.failed),
          borderColor: '#ef4444',
          backgroundColor: 'rgba(239, 68, 68, 0.1)',
          tension: 0.4
        }
      ]
    };
  }

  private updateRecentActivity() {
    this.recentActivity = this.jobs
      .slice(0, 5)
      .map(job => ({
        status: job.status,
        time: new Date(job.startTime).toLocaleString(),
        repository: job.repository,
        entities: job.entitiesCount,
        icon: this.getActivityIcon(job.status),
        color: this.getActivityColor(job.status),
        title: `${job.repository} Documentation`,
        subtitle: `${job.entitiesCount} entities, ${job.businessRulesCount} rules`
      }));
  }

  private getActivityIcon(status: string): string {
    const iconMap: { [key: string]: string } = {
      'success': 'pi-check-circle',
      'completed': 'pi-check-circle',
      'processing': 'pi-spin pi-spinner',
      'failed': 'pi-times-circle',
      'pending': 'pi-clock'
    };
    return iconMap[status] || 'pi-info-circle';
  }

  private getActivityColor(status: string): string {
    const colorMap: { [key: string]: string } = {
      'success': '#10b981',
      'completed': '#10b981',
      'processing': '#f59e0b',
      'failed': '#ef4444',
      'pending': '#6b7280'
    };
    return colorMap[status] || '#6b7280';
  }

  // Actions
  viewJobDetails(job: JobHistoryItem) {
    this.router.navigate(['/jobs', job.id]);
  }

  showJobDetailDialog(job: JobHistoryItem) {
    this.selectedJob = job;
    this.showJobDetail = true;
  }

  downloadDocumentation(job: JobHistoryItem) {
    if (!job.hasOutput) {
      this.messageService.add({
        severity: 'warn',
        summary: 'Not Available',
        detail: 'Documentation output is not available for this job'
      });
      return;
    }

    this.messageService.add({
      severity: 'info',
      summary: 'Downloading',
      detail: 'Preparing documentation download...'
    });

    this.apiService.downloadJobOutput(job.id).subscribe({
      next: (blob: any) => {
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `documentation_${job.repository}_${job.id}.zip`;
        link.click();
        window.URL.revokeObjectURL(url);

        this.messageService.add({
          severity: 'success',
          summary: 'Download Complete',
          detail: 'Documentation has been downloaded'
        });
      },
      error: (error) => {
        this.messageService.add({
          severity: 'error',
          summary: 'Download Failed',
          detail: 'Failed to download documentation'
        });
      }
    });
  }

  rerunJob(job: JobHistoryItem) {
    this.router.navigate(['/generate'], { 
      queryParams: { 
        repo: job.repositoryPath,
        name: job.repository,
        rerun: job.id
      } 
    });
  }

  // Utility methods
  getStatusSeverity(status: string): "success" | "secondary" | "info" | "warning" | "danger" | "contrast" | undefined {
    const severityMap: { [key: string]: "success" | "secondary" | "info" | "warning" | "danger" | "contrast" } = {
      'success': 'success',
      'completed': 'success',
      'processing': 'warning',
      'pending': 'info',
      'failed': 'danger'
    };
    return severityMap[status] || 'secondary';
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

  onPageChange(event: any) {
    this.first = event.first;
    this.rows = event.rows;
    this.loadJobs();
  }

  private startAutoRefresh() {
    // Refresh every 30 seconds for processing jobs
    this.refreshSubscription = interval(30000).subscribe(() => {
      const hasProcessingJobs = this.jobs.some(job => 
        job.status === 'processing' || job.status === 'pending'
      );
      
      if (hasProcessingJobs && !this.loading) {
        this.loadJobs();
      }
    });
  }
}