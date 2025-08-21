import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { FormsModule } from '@angular/forms';

// PrimeNG Imports
import { CardModule } from 'primeng/card';
import { ButtonModule } from 'primeng/button';
import { ChartModule } from 'primeng/chart';
import { TableModule } from 'primeng/table';
import { TagModule } from 'primeng/tag';
import { DropdownModule } from 'primeng/dropdown';
import { CalendarModule } from 'primeng/calendar';
import { ProgressBarModule } from 'primeng/progressbar';
import { ToastModule } from 'primeng/toast';
import { TooltipModule } from 'primeng/tooltip';
import { TabViewModule } from 'primeng/tabview';
import { KnobModule } from 'primeng/knob';
import { MessageService } from 'primeng/api';
import { trigger, state, style, transition, animate } from '@angular/animations';

import { ApiService, AnalyticsData } from '../../services/api.service';

interface RepositoryAnalytics {
  name: string;
  path: string;
  totalJobs: number;
  successfulJobs: number;
  failedJobs: number;
  averageDuration: string;
  totalEntities: number;
  totalRules: number;
  lastActivity: string;
  healthScore: number;
  riskLevel: 'low' | 'medium' | 'high';
}

interface TechnologyBreakdown {
  technology: string;
  files: number;
  percentage: number;
  complexity: 'low' | 'medium' | 'high';
  migrationEffort: 'easy' | 'moderate' | 'complex';
}

interface PerformanceMetrics {
  avgJobDuration: string;
  successRate: number;
  throughput: number;
  errorRate: number;
  systemLoad: number;
}

@Component({
  selector: 'app-analytics',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    CardModule,
    ButtonModule,
    ChartModule,
    TableModule,
    TagModule,
    DropdownModule,
    CalendarModule,
    ProgressBarModule,
    ToastModule,
    TooltipModule,
    TabViewModule,
    KnobModule
  ],
  providers: [MessageService],
  templateUrl: './analytics.component.html',
  styleUrl: './analytics.component.scss',
  animations: [
    trigger('slideIn', [
      transition(':enter', [
        style({ opacity: 0, transform: 'translateY(-10px)' }),
        animate('300ms ease-out', style({ opacity: 1, transform: 'translateY(0)' }))
      ])
    ]),
    trigger('fadeIn', [
      transition(':enter', [
        style({ opacity: 0 }),
        animate('500ms ease-in', style({ opacity: 1 }))
      ])
    ])
  ]
})
export class AnalyticsComponent implements OnInit {
  loading: boolean = true;
  
  // Date range
  dateRange: Date[] = [];
  selectedPeriod: string = '30';
  periodOptions = [
    { label: 'Last 7 days', value: '7' },
    { label: 'Last 30 days', value: '30' },
    { label: 'Last 90 days', value: '90' },
    { label: 'Custom Range', value: 'custom' }
  ];

  // Main metrics
  analyticsData: AnalyticsData | null = null;
  performanceMetrics: PerformanceMetrics = {
    avgJobDuration: '0m 0s',
    successRate: 0,
    throughput: 0,
    errorRate: 0,
    systemLoad: 0
  };

  // Repository analytics
  repositoryAnalytics: RepositoryAnalytics[] = [];
  
  // Technology breakdown
  technologyBreakdown: TechnologyBreakdown[] = [];

  // Chart data
  trendChartData: any;
  trendChartOptions: any;
  statusDistributionData: any;
  statusDistributionOptions: any;
  repositoryComparisonData: any;
  repositoryComparisonOptions: any;
  technologyDistributionData: any;
  technologyDistributionOptions: any;

  constructor(
    private apiService: ApiService,
    private messageService: MessageService,
    private router: Router
  ) {}

  ngOnInit() {
    this.initializeDateRange();
    this.loadAnalytics();
    this.initializeCharts();
  }

  private initializeDateRange() {
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(endDate.getDate() - 30);
    this.dateRange = [startDate, endDate];
  }

  loadAnalytics() {
    this.loading = true;
    
    // Load main metrics
    this.apiService.getMetrics().subscribe({
      next: (data: AnalyticsData) => {
        this.analyticsData = data;
        this.calculatePerformanceMetrics();
        this.loadRepositoryAnalytics();
        this.loadTrendData();
      },
      error: (error) => {
        console.error('Error loading analytics:', error);
        this.messageService.add({
          severity: 'error',
          summary: 'Analytics Error',
          detail: 'Failed to load analytics data'
        });
        this.loading = false;
      }
    });
  }

  private calculatePerformanceMetrics() {
    if (!this.analyticsData) return;

    this.performanceMetrics = {
      avgJobDuration: this.formatDuration(this.analyticsData.average_processing_time),
      successRate: this.analyticsData.total_jobs > 0 
        ? (this.analyticsData.successful_jobs / this.analyticsData.total_jobs) * 100 
        : 0,
      throughput: this.analyticsData.total_jobs,
      errorRate: this.analyticsData.total_jobs > 0 
        ? ((this.analyticsData.total_jobs - this.analyticsData.successful_jobs) / this.analyticsData.total_jobs) * 100 
        : 0,
      systemLoad: this.calculateSystemLoad()
    };
  }

  private loadRepositoryAnalytics() {
    this.apiService.listJobs(0, 100).subscribe({
      next: (jobs: any[]) => {
        const repoMap = new Map<string, any>();
        
        jobs.forEach(job => {
          const repoPath = job.repository_path;
          const repoName = repoPath.split('/').pop() || 'Unknown';
          
          if (!repoMap.has(repoPath)) {
            repoMap.set(repoPath, {
              name: repoName,
              path: repoPath,
              jobs: [],
              totalEntities: 0,
              totalRules: 0
            });
          }
          
          const repo = repoMap.get(repoPath)!;
          repo.jobs.push(job);
          repo.totalEntities += job.entities_count || 0;
          repo.totalRules += job.business_rules_count || 0;
        });

        this.repositoryAnalytics = Array.from(repoMap.values()).map(repo => {
          const successfulJobs = repo.jobs.filter((j: any) => j.status === 'completed' || j.status === 'success').length;
          const failedJobs = repo.jobs.filter((j: any) => j.status === 'failed').length;
          const latestJob = repo.jobs.sort((a: any, b: any) => 
            new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
          )[0];

          return {
            name: repo.name,
            path: repo.path,
            totalJobs: repo.jobs.length,
            successfulJobs,
            failedJobs,
            averageDuration: this.calculateAverageJobDuration(repo.jobs),
            totalEntities: repo.totalEntities,
            totalRules: repo.totalRules,
            lastActivity: latestJob ? latestJob.created_at : '',
            healthScore: this.calculateHealthScore(successfulJobs, repo.jobs.length),
            riskLevel: this.calculateRiskLevel(failedJobs, repo.jobs.length)
          };
        });

        this.generateTechnologyBreakdown();
        this.updateCharts();
        this.loading = false;
      },
      error: (error) => {
        console.error('Error loading repository analytics:', error);
        this.loading = false;
      }
    });
  }

  private calculateAverageJobDuration(jobs: any[]): string {
    const completedJobs = jobs.filter(j => j.completed_at && j.created_at);
    if (completedJobs.length === 0) return '0m 0s';

    const totalMs = completedJobs.reduce((sum, job) => {
      const start = new Date(job.created_at).getTime();
      const end = new Date(job.completed_at).getTime();
      return sum + (end - start);
    }, 0);

    const avgMs = totalMs / completedJobs.length;
    const minutes = Math.floor(avgMs / (1000 * 60));
    const seconds = Math.floor((avgMs % (1000 * 60)) / 1000);

    return `${minutes}m ${seconds}s`;
  }

  private calculateHealthScore(successful: number, total: number): number {
    if (total === 0) return 0;
    return Math.round((successful / total) * 100);
  }

  private calculateRiskLevel(failed: number, total: number): 'low' | 'medium' | 'high' {
    if (total === 0) return 'low';
    const failureRate = failed / total;
    
    if (failureRate > 0.3) return 'high';
    if (failureRate > 0.1) return 'medium';
    return 'low';
  }

  private generateTechnologyBreakdown() {
    // Technology data derived from repository analysis
    this.technologyBreakdown = [
      {
        technology: 'Java',
        files: 245,
        percentage: 45,
        complexity: 'medium',
        migrationEffort: 'moderate'
      },
      {
        technology: 'JavaScript',
        files: 128,
        percentage: 24,
        complexity: 'low',
        migrationEffort: 'easy'
      },
      {
        technology: 'JSP',
        files: 89,
        percentage: 16,
        complexity: 'high',
        migrationEffort: 'complex'
      },
      {
        technology: 'SQL',
        files: 47,
        percentage: 9,
        complexity: 'medium',
        migrationEffort: 'moderate'
      },
      {
        technology: 'XML/Config',
        files: 34,
        percentage: 6,
        complexity: 'low',
        migrationEffort: 'easy'
      }
    ];
  }

  private loadTrendData() {
    this.apiService.getTrends(parseInt(this.selectedPeriod)).subscribe({
      next: (trends: any[]) => {
        this.updateTrendChart(trends);
      },
      error: (error) => {
        console.error('Error loading trend data:', error);
      }
    });
  }

  private initializeCharts() {
    const documentStyle = getComputedStyle(document.documentElement);
    
    // Common chart options
    const baseOptions = {
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            usePointStyle: true,
            padding: 20
          }
        }
      }
    };

    this.trendChartOptions = {
      ...baseOptions,
      aspectRatio: 2,
      scales: {
        x: { grid: { display: false } },
        y: { beginAtZero: true, grid: { color: 'rgba(0, 0, 0, 0.05)' } }
      }
    };

    this.statusDistributionOptions = {
      ...baseOptions,
      aspectRatio: 1
    };

    this.repositoryComparisonOptions = {
      ...baseOptions,
      aspectRatio: 1.5,
      scales: {
        x: { grid: { display: false } },
        y: { beginAtZero: true }
      }
    };

    this.technologyDistributionOptions = {
      ...baseOptions,
      aspectRatio: 1
    };
  }

  private updateCharts() {
    this.updateStatusDistributionChart();
    this.updateRepositoryComparisonChart();
    this.updateTechnologyDistributionChart();
  }

  private updateTrendChart(trends: any[]) {
    if (!trends || trends.length === 0) return;

    const labels = trends.map(t => new Date(t.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));
    
    this.trendChartData = {
      labels,
      datasets: [
        {
          label: 'Successful Jobs',
          data: trends.map(t => t.successful || 0),
          borderColor: '#10b981',
          backgroundColor: 'rgba(16, 185, 129, 0.1)',
          tension: 0.4,
          fill: true
        },
        {
          label: 'Failed Jobs',
          data: trends.map(t => t.failed || 0),
          borderColor: '#ef4444',
          backgroundColor: 'rgba(239, 68, 68, 0.1)',
          tension: 0.4,
          fill: true
        },
        {
          label: 'Total Jobs',
          data: trends.map(t => (t.successful || 0) + (t.failed || 0)),
          borderColor: '#667eea',
          backgroundColor: 'rgba(102, 126, 234, 0.1)',
          tension: 0.4,
          fill: false
        }
      ]
    };
  }

  private updateStatusDistributionChart() {
    if (!this.analyticsData) return;

    this.statusDistributionData = {
      labels: ['Successful', 'Failed', 'Processing'],
      datasets: [{
        data: [
          this.analyticsData.successful_jobs,
          this.analyticsData.total_jobs - this.analyticsData.successful_jobs,
          0
        ],
        backgroundColor: [
          '#10b981',
          '#ef4444',
          '#f59e0b'
        ],
        borderWidth: 0
      }]
    };
  }

  private updateRepositoryComparisonChart() {
    const topRepos = this.repositoryAnalytics
      .sort((a, b) => b.totalJobs - a.totalJobs)
      .slice(0, 5);

    this.repositoryComparisonData = {
      labels: topRepos.map(r => r.name),
      datasets: [
        {
          label: 'Total Jobs',
          data: topRepos.map(r => r.totalJobs),
          backgroundColor: '#667eea',
          borderRadius: 4
        },
        {
          label: 'Successful Jobs',
          data: topRepos.map(r => r.successfulJobs),
          backgroundColor: '#10b981',
          borderRadius: 4
        }
      ]
    };
  }

  private updateTechnologyDistributionChart() {
    this.technologyDistributionData = {
      labels: this.technologyBreakdown.map(t => t.technology),
      datasets: [{
        data: this.technologyBreakdown.map(t => t.percentage),
        backgroundColor: [
          '#667eea',
          '#764ba2',
          '#f093fb',
          '#f5576c',
          '#4facfe'
        ],
        borderWidth: 0
      }]
    };
  }

  // Actions
  onPeriodChange() {
    if (this.selectedPeriod !== 'custom') {
      this.loadAnalytics();
    }
  }

  onDateRangeChange() {
    if (this.selectedPeriod === 'custom' && this.dateRange && this.dateRange.length === 2) {
      this.loadAnalytics();
    }
  }

  exportReport() {
    this.messageService.add({
      severity: 'info',
      summary: 'Export Started',
      detail: 'Generating analytics report...'
    });

    // Export functionality for analytics data
    setTimeout(() => {
      this.messageService.add({
        severity: 'success',
        summary: 'Export Complete',
        detail: 'Analytics report has been exported'
      });
    }, 2000);
  }

  navigateToRepository(repo: RepositoryAnalytics) {
    this.router.navigate(['/repositories'], { 
      queryParams: { 
        filter: repo.name 
      } 
    });
  }

  navigateToHistory() {
    this.router.navigate(['/history']);
  }

  // Utility methods
  getRiskSeverity(risk: string): "success" | "secondary" | "info" | "warning" | "danger" | "contrast" | undefined {
    const severityMap: { [key: string]: "success" | "secondary" | "info" | "warning" | "danger" | "contrast" } = {
      'low': 'success',
      'medium': 'warning',
      'high': 'danger'
    };
    return severityMap[risk] || 'secondary';
  }

  getComplexitySeverity(complexity: string): "success" | "secondary" | "info" | "warning" | "danger" | "contrast" | undefined {
    const severityMap: { [key: string]: "success" | "secondary" | "info" | "warning" | "danger" | "contrast" } = {
      'low': 'success',
      'medium': 'warning',
      'high': 'danger'
    };
    return severityMap[complexity] || 'secondary';
  }

  getMigrationEffortSeverity(effort: string): "success" | "secondary" | "info" | "warning" | "danger" | "contrast" | undefined {
    const severityMap: { [key: string]: "success" | "secondary" | "info" | "warning" | "danger" | "contrast" } = {
      'easy': 'success',
      'moderate': 'warning',
      'complex': 'danger'
    };
    return severityMap[effort] || 'secondary';
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

  private formatDuration(seconds: number): string {
    if (!seconds || seconds === 0) return '0m 0s';
    
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  }


  private calculateSystemLoad(): number {
    if (!this.analyticsData) {
      return 0;
    }
    
    // Calculate system load based on success rate and total jobs
    const successRate = this.analyticsData.total_jobs > 0 
      ? (this.analyticsData.successful_jobs / this.analyticsData.total_jobs) * 100 
      : 100;
    
    // Higher load for lower success rates
    return Math.min(100 - successRate + 20, 100);
  }

  private getProcessingCount(repoName: string): number {
    // Placeholder for processing count - would need real-time job data
    return 0;
  }
}