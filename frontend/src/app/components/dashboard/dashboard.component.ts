import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { CardModule } from 'primeng/card';
import { ButtonModule } from 'primeng/button';
import { ChartModule } from 'primeng/chart';
import { TableModule } from 'primeng/table';
import { TagModule } from 'primeng/tag';
import { ProgressBarModule } from 'primeng/progressbar';
import { TabViewModule } from 'primeng/tabview';
import { TimelineModule } from 'primeng/timeline';
import { trigger, state, style, transition, animate } from '@angular/animations';

interface RecentJob {
  id: string;
  repository: string;
  status: 'success' | 'processing' | 'failed';
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
    TimelineModule
  ],
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
  
  ngOnInit() {
    this.loadMetrics();
    this.loadRecentJobs();
    this.initializeCharts();
  }

  loadMetrics() {
    this.metrics = [
      {
        title: 'Total Documentations',
        value: '1,284',
        change: 12.5,
        icon: 'pi pi-file',
        color: 'primary',
        trend: 'up'
      },
      {
        title: 'Active Repositories',
        value: '47',
        change: 8.3,
        icon: 'pi pi-folder',
        color: 'success',
        trend: 'up'
      },
      {
        title: 'Business Rules',
        value: '3,462',
        change: -2.1,
        icon: 'pi pi-shield',
        color: 'warning',
        trend: 'down'
      },
      {
        title: 'Success Rate',
        value: '98.5%',
        change: 0.8,
        icon: 'pi pi-chart-line',
        color: 'info',
        trend: 'up'
      }
    ];
  }

  loadRecentJobs() {
    this.recentJobs = [
      {
        id: 'JOB-001',
        repository: 'payment-service',
        status: 'success',
        entities: 142,
        rules: 23,
        time: '2 hours ago',
        duration: '4m 32s'
      },
      {
        id: 'JOB-002',
        repository: 'customer-portal',
        status: 'processing',
        entities: 89,
        rules: 15,
        time: '3 hours ago',
        duration: '2m 15s'
      },
      {
        id: 'JOB-003',
        repository: 'legacy-claims',
        status: 'success',
        entities: 234,
        rules: 41,
        time: '5 hours ago',
        duration: '8m 12s'
      },
      {
        id: 'JOB-004',
        repository: 'underwriting-engine',
        status: 'failed',
        entities: 0,
        rules: 0,
        time: '6 hours ago',
        duration: '0m 45s'
      }
    ];
  }

  initializeCharts() {
    const documentStyle = getComputedStyle(document.documentElement);
    
    // Line chart for documentation trend
    this.chartData = {
      labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul'],
      datasets: [
        {
          label: 'Documentations Generated',
          data: [65, 59, 80, 81, 96, 105, 120],
          fill: false,
          borderColor: '#667eea',
          tension: 0.4,
          backgroundColor: 'rgba(102, 126, 234, 0.2)'
        },
        {
          label: 'Business Rules Extracted',
          data: [28, 48, 40, 59, 66, 77, 90],
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
  }

  getStatusSeverity(status: string): string {
    switch(status) {
      case 'success': return 'success';
      case 'processing': return 'warning';
      case 'failed': return 'danger';
      default: return 'info';
    }
  }

  formatDuration(duration: string): string {
    return duration;
  }
}
