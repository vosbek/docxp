import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { CardModule } from 'primeng/card';
import { ButtonModule } from 'primeng/button';
import { ChartModule } from 'primeng/chart';
import { TableModule } from 'primeng/table';
import { TagModule } from 'primeng/tag';
import { ProgressBarModule } from 'primeng/progressbar';
import { TabViewModule } from 'primeng/tabview';
import { TimelineModule } from 'primeng/timeline';
import { ToastModule } from 'primeng/toast';
import { MessageService } from 'primeng/api';
import { trigger, state, style, transition, animate } from '@angular/animations';

import { ApiService, AnalyticsData, JobStatus } from '../../services/api.service';

interface RecentJob {
  id: string;
  repository: string;
  status: 'success' | 'processing' | 'failed' | 'pending' | 'completed';
  entities: number;
  rules: number;
  time: string;
  duration: string;
}

interface MetricCard {
  title: string;
  value: string | number;
  change: number;
  icon: string;
  color: string;
  trend: 'up' | 'down';
}

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    CardModule,
    ButtonModule,
    ChartModule,
    TableModule,
    TagModule,
    ProgressBarModule,
    TabViewModule,
    TimelineModule,
    ToastModule
  ],
  providers: [MessageService],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.scss',
  animations: [
    trigger('cardAnimation', [
      transition(':enter', [
        style({ opacity: 0, transform: 'translateY(20px)' }),
        animate('0.5s ease-out', style({ opacity: 1, transform: 'translateY(0)' }))
      ])
    ])
  ]
})
export class DashboardComponent implements OnInit {
  metrics: MetricCard[] = [];
  recentJobs: RecentJob[] = [];
  chartData: any;
  chartOptions: any;
  activityData: any;
  loading: boolean = true;
  
  constructor(
    private apiService: ApiService,
    private messageService: MessageService,
    private router: Router
  ) {}
  
  ngOnInit() {
    this.loadMetrics();
    this.loadRecentJobs();
    this.initializeCharts();
    this.startHealthMonitoring();
  }
  
  loadMetrics() {
    this.apiService.getMetrics().subscribe({
      next: (data: AnalyticsData) => {
        this.metrics = [
          {
            title: 'Total Documentations',
            value: data.total_jobs.toString(),
            change: 12.5,
            icon: 'pi pi-file',
            color: 'primary',
            trend: 'up'
          },
          {
            title: 'Successful Jobs',
            value: data.successful_jobs.toString(),
            change: 8.3,
            icon: 'pi pi-check-circle',
            color: 'success',
            trend: 'up'
          },
          {
            title: 'Business Rules',
            value: data.total_business_rules.toString(),
            change: -2.1,
            icon: 'pi pi-shield',
            color: 'warning',
            trend: 'down'
          },
          {
            title: 'Success Rate',
            value: data.successful_jobs > 0 
              ? `${((data.successful_jobs / data.total_jobs) * 100).toFixed(1)}%`
              : '0%',
            change: 0.8,
            icon: 'pi pi-chart-line',
            color: 'info',
            trend: 'up'
          }
        ];
        this.loading = false;
      },
      error: (error) => {
        console.error('Error loading metrics:', error);
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to load metrics'
        });
        this.loadMockMetrics();
      }
    });
  }
  
  loadMockMetrics() {
    // Fallback to mock data if API fails
    this.metrics = [
      {
        title: 'Total Documentations',
        value: '0',
        change: 0,
        icon: 'pi pi-file',
        color: 'primary',
        trend: 'up'
      },
      {
        title: 'Active Repositories',
        value: '0',
        change: 0,
        icon: 'pi pi-folder',
        color: 'success',
        trend: 'up'
      },
      {
        title: 'Business Rules',
        value: '0',
        change: 0,
        icon: 'pi pi-shield',
        color: 'warning',
        trend: 'down'
      },
      {
        title: 'Success Rate',
        value: '0%',
        change: 0,
        icon: 'pi pi-chart-line',
        color: 'info',
        trend: 'up'
      }
    ];
    this.loading = false;
  }

  loadRecentJobs() {
    this.apiService.listJobs(0, 10).subscribe({
      next: (jobs: any[]) => {
        this.recentJobs = jobs.map(job => ({
          id: job.job_id,
          repository: job.repository_path.split('/').pop() || 'Unknown',
          status: this.mapJobStatus(job.status),
          entities: job.entities_count || 0,
          rules: job.business_rules_count || 0,
          time: this.getRelativeTime(job.created_at),
          duration: this.calculateDuration(job.created_at, job.completed_at)
        }));
      },
      error: (error) => {
        console.error('Error loading jobs:', error);
        this.recentJobs = [];
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
  
  private getRelativeTime(timestamp: string): string {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const hours = Math.floor(diff / (1000 * 60 * 60));
    
    if (hours < 1) {
      const minutes = Math.floor(diff / (1000 * 60));
      return `${minutes} minutes ago`;
    } else if (hours < 24) {
      return `${hours} hours ago`;
    } else {
      const days = Math.floor(hours / 24);
      return `${days} days ago`;
    }
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

  initializeCharts() {
    const documentStyle = getComputedStyle(document.documentElement);
    
    this.chartData = {
      labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul'],
      datasets: [
        {
          label: 'Documentations Generated',
          data: [0, 0, 0, 0, 0, 0, 0],
          fill: false,
          borderColor: '#667eea',
          tension: 0.4,
          backgroundColor: 'rgba(102, 126, 234, 0.2)'
        },
        {
          label: 'Business Rules Extracted',
          data: [0, 0, 0, 0, 0, 0, 0],
          fill: false,
          borderColor: '#764ba2',
          tension: 0.4,
          backgroundColor: 'rgba(118, 75, 162, 0.2)'
        }
      ]
    };

    this.chartOptions = {
      maintainAspectRatio: false,
      aspectRatio: 1.5,
      plugins: {
        legend: {
          display: true,
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
    
    // Load real chart data
    this.loadChartData();
  }
  
  loadChartData() {
    this.apiService.getTrends(30).subscribe({
      next: (trends: any[]) => {
        if (trends && trends.length > 0) {
          const labels = trends.map(t => t.date.substring(5)); // MM-DD format
          const docsData = trends.map(t => t.successful || 0);
          const rulesData = trends.map(t => t.rules || 0);
          
          this.chartData = {
            ...this.chartData,
            labels: labels.slice(-7), // Last 7 days
            datasets: [
              { ...this.chartData.datasets[0], data: docsData.slice(-7) },
              { ...this.chartData.datasets[1], data: rulesData.slice(-7) }
            ]
          };
        }
      },
      error: (error) => {
        console.error('Error loading trends:', error);
      }
    });
  }

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

  formatDuration(duration: string): string {
    return duration;
  }
  
  // Navigation methods
  navigateToGeneration() {
    this.router.navigate(['/generate']);
  }
  
  navigateToRepository(repoPath?: string) {
    if (repoPath) {
      this.router.navigate(['/generate'], { queryParams: { repo: repoPath } });
    } else {
      this.router.navigate(['/repositories']);
    }
  }
  
  viewJobDetails(job: RecentJob) {
    this.router.navigate(['/jobs', job.id]);
  }
  
  downloadDocumentation(job: RecentJob) {
    window.open(`http://localhost:8001/output/${job.id}/README.md`, '_blank');
  }
  
  // Quick action methods
  onNewDocumentation() {
    this.navigateToGeneration();
  }
  
  onSyncRepository() {
    this.messageService.add({
      severity: 'info',
      summary: 'Sync',
      detail: 'Repository sync feature coming soon'
    });
  }
  
  onConfiguration() {
    this.router.navigate(['/settings']);
  }
  
  onAnalytics() {
    this.router.navigate(['/analytics']);
  }
  
  onViewGuide() {
    window.open('/assets/guide.pdf', '_blank');
  }
}
  // Button click handlers with proper implementations
  onSyncRepository() {
    // Create a simple prompt for repository path
    const repoPath = prompt('Enter repository path to sync:');
    if (repoPath) {
      this.messageService.add({
        severity: 'info',
        summary: 'Syncing',
        detail: 'Starting repository sync...'
      });
      
      this.apiService.syncRepository(repoPath).subscribe({
        next: (response) => {
          this.messageService.add({
            severity: 'success',
            summary: 'Sync Started',
            detail: response.message || 'Repository sync has been initiated'
          });
          // Refresh jobs list
          this.loadRecentJobs();
        },
        error: (error) => {
          this.messageService.add({
            severity: 'error',
            summary: 'Sync Failed',
            detail: error.error?.detail || 'Failed to sync repository'
          });
        }
      });
    }
  }
  
  viewJobDetails(job: RecentJob) {
    // For now, show job details in a message
    // In production, this would navigate to a details page or open a modal
    this.messageService.add({
      severity: 'info',
      summary: 'Job Details',
      detail: `Job ${job.id}: ${job.repository} - Status: ${job.status}, Entities: ${job.entities}, Rules: ${job.rules}`
    });
    
    // Optional: Try to navigate to job details page if it exists
    this.router.navigate(['/jobs', job.id]).catch(() => {
      // If route doesn't exist, just show the message above
    });
  }
  
  downloadDocumentation(job: RecentJob) {
    if (job.status !== 'success' && job.status !== 'completed') {
      this.messageService.add({
        severity: 'warn',
        summary: 'Not Ready',
        detail: 'Documentation is still being generated'
      });
      return;
    }
    
    this.messageService.add({
      severity: 'info',
      summary: 'Downloading',
      detail: 'Preparing documentation download...'
    });
    
    this.apiService.downloadJobOutput(job.id).subscribe({
      next: (blob) => {
        // Create download link
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `documentation_${job.id}.zip`;
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
          detail: 'Failed to download documentation. It may not be ready yet.'
        });
      }
    });
  }
  
  onViewGuide() {
    // Create a simple guide or open documentation
    const guideUrl = '/assets/guide.pdf';
    const helpText = `
DocXP Quick Guide:

1. Generate Documentation:
   - Click "Generate Documentation" or "New Documentation"
   - Enter repository path
   - Select configuration options
   - Click Generate

2. View Results:
   - Check Recent Jobs table
   - Click eye icon to view details
   - Click download icon to get documentation

3. System Status:
   - Green indicators = healthy
   - Check health endpoint for details

For more help, visit the API docs at:
http://localhost:8001/docs
    `;
    
    // Try to open guide PDF if it exists
    fetch(guideUrl).then(response => {
      if (response.ok) {
        window.open(guideUrl, '_blank');
      } else {
        // Show help text in alert if no PDF
        alert(helpText);
      }
    }).catch(() => {
      alert(helpText);
    });
  }
  
  // Monitor system health periodically
  private startHealthMonitoring() {
    // Check health every 30 seconds
    setInterval(() => {
      this.apiService.getHealthStatus().subscribe({
        next: (health) => {
          // Update status indicators based on health
          if (health.status === 'unhealthy') {
            this.messageService.add({
              severity: 'error',
              summary: 'System Issue',
              detail: 'Some services are experiencing issues'
            });
          }
        },
        error: (error) => {
          // Silently log, don't spam user with errors
          console.error('Health check failed:', error);
        }
      });
    }, 30000);
  }
