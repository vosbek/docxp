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
import { TooltipModule } from 'primeng/tooltip';
import { MessageService } from 'primeng/api';
import { trigger, state, style, transition, animate } from '@angular/animations';

import { ApiService, AnalyticsData, JobStatus } from '../../services/api.service';
import { DiagramViewerComponent, DiagramData } from '../diagram-viewer/diagram-viewer.component';
import { environment } from '../../../environments/environment';

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
    ToastModule,
    TooltipModule,
    DiagramViewerComponent
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
  sampleDiagrams: DiagramData[] = [];
  
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
    this.loadSampleDiagrams();
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
          summary: 'Metrics Error',
          detail: 'Failed to load metrics. Please check your connection and try again.'
        });
        this.loading = false;
      }
    });
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
  
  // Quick action methods
  onNewDocumentation() {
    this.navigateToGeneration();
  }
  
  onConfiguration() {
    this.router.navigate(['/settings']);
  }
  
  onAnalytics() {
    this.router.navigate(['/analytics']);
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
${environment.apiUrl.replace('/api', '')}/docs
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
        next: (response: any) => {
          this.messageService.add({
            severity: 'success',
            summary: 'Sync Started',
            detail: response.message || 'Repository sync has been initiated'
          });
          // Refresh jobs list
          this.loadRecentJobs();
        },
        error: (error: any) => {
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
    // Navigate to job details page
    this.router.navigate(['/jobs', job.id]);
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
      next: (blob: any) => {
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
      error: (error: any) => {
        this.messageService.add({
          severity: 'error',
          summary: 'Download Failed',
          detail: 'Failed to download documentation. It may not be ready yet.'
        });
      }
    });
  }
  
  // Monitor system health periodically
  private startHealthMonitoring() {
    // Check health every 30 seconds
    setInterval(() => {
      this.apiService.getHealthStatus().subscribe({
        next: (health: any) => {
          // Update status indicators based on health
          if (health.status === 'unhealthy') {
            this.messageService.add({
              severity: 'error',
              summary: 'System Issue',
              detail: 'Some services are experiencing issues'
            });
          }
        },
        error: (error: any) => {
          // Silently log, don't spam user with errors
          console.error('Health check failed:', error);
        }
      });
    }, 30000);
  }

  // Sample diagram methods - used for dashboard preview only
  // Real diagrams are generated per job and viewed in job details
  loadSampleDiagrams() {
    // Sample enterprise migration diagrams for dashboard preview
    this.sampleDiagrams = [
      {
        id: 'migration_architecture',
        name: 'Migration Architecture',
        type: 'migration_architecture',
        description: 'Enterprise migration architecture showing current and target state',
        content: this.generateSampleMigrationArchitectureDiagram()
      },
      {
        id: 'migration_risk_matrix',
        name: 'Risk Assessment Matrix',
        type: 'migration_risk_matrix', 
        description: 'Component risk assessment for migration planning',
        content: this.generateSampleRiskMatrixDiagram()
      },
      {
        id: 'data_flow',
        name: 'Data Flow Diagram',
        type: 'data_flow',
        description: 'Data flow across technology boundaries',
        content: this.generateSampleDataFlowDiagram()
      },
      {
        id: 'technology_integration',
        name: 'Technology Integration Map',
        type: 'technology_integration',
        description: 'Cross-technology integration patterns and confidence scores',
        content: this.generateSampleTechnologyMapDiagram()
      }
    ];
  }


  private generateSampleMigrationArchitectureDiagram(): string {
    return `graph TB
    subgraph "Frontend Layer"
        ANG[🅰️ Angular Components]:::frontend
        JSP[📄 JSP Pages]:::frontend
    end

    subgraph "Business Logic Layer"
        JAVA[☕ Java Services]:::backend
        STRUTS[⚙️ Struts Actions]:::backend
    end

    subgraph "Data Layer"
        ORACLE[(🗄️ Oracle Database)]:::data
    end

    subgraph "Legacy Systems"
        CORBA[🏛️ CORBA Services]:::legacy
        MAINFRAME[💻 Mainframe]:::legacy
    end

    subgraph "Target Modern Architecture"
        REST_API[🔗 REST APIs]:::modern
        MICROSERVICES[⚡ Microservices]:::modern
        CLOUD_DB[(☁️ Cloud Database)]:::modern
    end

    %% Current flows
    ANG --> STRUTS
    JSP --> STRUTS
    STRUTS --> JAVA
    JAVA --> ORACLE
    JAVA --> CORBA

    %% Migration paths
    CORBA -.-> REST_API
    STRUTS -.-> MICROSERVICES
    ORACLE -.-> CLOUD_DB

    %% Styling
    classDef legacy fill:#ffcccc,stroke:#ff6666,stroke-width:2px
    classDef modern fill:#ccffcc,stroke:#66ff66,stroke-width:2px
    classDef frontend fill:#cce5ff,stroke:#0066cc,stroke-width:2px
    classDef backend fill:#ffffcc,stroke:#cccc00,stroke-width:2px
    classDef data fill:#ffccff,stroke:#cc00cc,stroke-width:2px`;
  }

  private generateSampleRiskMatrixDiagram(): string {
    return `graph LR
    subgraph "Critical Risk - Immediate Action Required"
        CR0["CORBA Interface\\n(Very High complexity)"]:::critical
        CR1["Legacy Authentication\\n(High complexity)"]:::critical
    end

    subgraph "High Risk - Plan Carefully"
        HR0["Database Layer\\n(High complexity)"]:::high
        HR1["Struts Actions\\n(Medium complexity)"]:::high
        HR2["Session Management\\n(High complexity)"]:::high
    end

    subgraph "Medium Risk - Standard Process"
        MR0["Business Logic\\n(Medium complexity)"]:::medium
        MR1["Data Validation\\n(Low complexity)"]:::medium
        MR2["Report Generation\\n(Medium complexity)"]:::medium
    end

    subgraph "Low Risk - Quick Wins"
        LR0["Static Resources\\n(Low complexity)"]:::low
        LR1["Configuration Files\\n(Low complexity)"]:::low
        LR2["Utility Classes\\n(Low complexity)"]:::low
    end

    %% Risk Level Styling
    classDef critical fill:#ffcccc,stroke:#cc0000,stroke-width:3px
    classDef high fill:#ffd9cc,stroke:#ff6600,stroke-width:2px
    classDef medium fill:#ffffcc,stroke:#cccc00,stroke-width:2px
    classDef low fill:#ccffcc,stroke:#00cc00,stroke-width:2px`;
  }

  private generateSampleDataFlowDiagram(): string {
    return `flowchart TD
    USER[👤 User]:::user

    subgraph "Frontend Data Entry"
        FORMS[📝 Forms & UI]:::frontend
        ANGULAR[🅰️ Angular Components]:::frontend
        JSP[📄 JSP Pages]:::frontend
    end

    subgraph "API & Integration Layer"
        REST[🔗 REST APIs]:::api
        STRUTS[⚙️ Struts Actions]:::api
        CORBA[🏛️ CORBA Services]:::legacy
    end

    subgraph "Business Logic"
        SERVICES[⚡ Java Services]:::backend
        PROCESSORS[🔄 Data Processors]:::backend
        VALIDATION[✅ Validation Logic]:::backend
    end

    subgraph "Data Persistence"
        DB[(🗄️ Oracle Database\\n47 tables)]:::database
        CACHE[(⚡ Redis Cache)]:::cache
        FILES[📁 File Storage]:::storage
    end

    %% User Interaction Flows
    USER --> FORMS
    USER --> ANGULAR
    USER --> JSP

    %% Frontend to API Flows
    FORMS --> REST
    ANGULAR --> REST
    JSP --> STRUTS

    %% API to Business Logic Flows
    REST --> SERVICES
    STRUTS --> SERVICES
    CORBA --> SERVICES

    %% Business Logic Processing
    SERVICES --> PROCESSORS
    PROCESSORS --> VALIDATION

    %% Data Persistence Flows
    VALIDATION --> DB
    SERVICES --> CACHE
    PROCESSORS --> FILES

    %% Styling
    classDef user fill:#e1f5fe,stroke:#0277bd,stroke-width:2px
    classDef frontend fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef api fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef backend fill:#e8f5e8,stroke:#388e3c,stroke-width:2px
    classDef database fill:#fce4ec,stroke:#c2185b,stroke-width:2px
    classDef legacy fill:#ffebee,stroke:#d32f2f,stroke-width:3px
    classDef cache fill:#fff8e1,stroke:#fbc02d,stroke-width:1px
    classDef storage fill:#e0f2f1,stroke:#00695c,stroke-width:1px`;
  }

  private generateSampleTechnologyMapDiagram(): string {
    return `graph TB
    subgraph "Frontend Technologies"
        ANG[🅰️ Angular\\n12 HTTP calls]:::frontend
        JSP[📄 JSP\\n8 forms]:::frontend
    end

    subgraph "API Integration Layer"
        REST[🔗 REST APIs\\n15 endpoints]:::api
        STRUTS[⚙️ Struts Actions\\n23 actions]:::api
    end

    subgraph "Backend Services"
        JAVA[☕ Java Services\\n34 services]:::backend
        CORBA[🏛️ CORBA\\n7 interfaces]:::legacy
    end

    subgraph "Migration Recommendations"
        REC[📋 Migration Complexity: Medium]:::recommendation
    end

    %% Integration Flows with Confidence Scores
    ANG ==> REST
    JSP --> STRUTS
    REST ==> JAVA
    STRUTS ==> JAVA
    JAVA -.-> CORBA

    %% Technology Integration Styling
    classDef frontend fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px
    classDef api fill:#fff3e0,stroke:#ff9800,stroke-width:2px
    classDef backend fill:#e8f5e8,stroke:#4caf50,stroke-width:2px
    classDef legacy fill:#ffebee,stroke:#f44336,stroke-width:3px
    classDef recommendation fill:#f3e5f5,stroke:#9c27b0,stroke-width:2px`;
  }
}
