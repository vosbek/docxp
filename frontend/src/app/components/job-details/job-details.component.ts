import { Component, OnInit, OnDestroy } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { CardModule } from 'primeng/card';
import { ButtonModule } from 'primeng/button';
import { ProgressBarModule } from 'primeng/progressbar';
import { TagModule } from 'primeng/tag';
import { ToastModule } from 'primeng/toast';
import { MessageService } from 'primeng/api';
import { Subscription } from 'rxjs';

import { ApiService, JobStatus } from '../../services/api.service';
import { DiagramViewerComponent, DiagramData } from '../diagram-viewer/diagram-viewer.component';

@Component({
  selector: 'app-job-details',
  standalone: true,
  imports: [
    CommonModule,
    CardModule,
    ButtonModule,
    ProgressBarModule,
    TagModule,
    ToastModule,
    DiagramViewerComponent
  ],
  providers: [MessageService],
  templateUrl: './job-details.component.html',
  styleUrl: './job-details.component.scss'
})
export class JobDetailsComponent implements OnInit, OnDestroy {
  jobId: string = '';
  job: JobStatus | null = null;
  diagrams: DiagramData[] = [];
  loading: boolean = true;
  loadingDiagrams: boolean = false;
  private subscriptions: Subscription[] = [];

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private apiService: ApiService,
    private messageService: MessageService
  ) {}

  ngOnInit() {
    this.route.params.subscribe(params => {
      this.jobId = params['id'];
      if (this.jobId) {
        this.loadJobDetails();
      }
    });
  }

  ngOnDestroy() {
    this.subscriptions.forEach(sub => sub.unsubscribe());
  }

  loadJobDetails() {
    this.loading = true;
    
    const statusSub = this.apiService.getJobStatus(this.jobId).subscribe({
      next: (job) => {
        this.job = job;
        this.loading = false;
        
        // If job is completed, load diagrams
        if (job.status === 'completed') {
          this.loadJobDiagrams();
        }
      },
      error: (error) => {
        console.error('Error loading job details:', error);
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to load job details'
        });
        this.loading = false;
      }
    });
    
    this.subscriptions.push(statusSub);
  }

  loadJobDiagrams() {
    this.loadingDiagrams = true;
    
    const diagramsSub = this.apiService.getJobDiagrams(this.jobId).subscribe({
      next: (response) => {
        // Convert API response to DiagramViewer format
        this.diagrams = response.diagrams.map(d => ({
          id: d.id,
          name: d.name,
          type: d.type as any, // Type conversion for compatibility
          content: d.content,
          description: d.description
        }));
        this.loadingDiagrams = false;
        
        if (this.diagrams.length > 0) {
          this.messageService.add({
            severity: 'success',
            summary: 'Diagrams Loaded',
            detail: `Found ${this.diagrams.length} generated diagrams`,
            life: 3000
          });
        }
      },
      error: (error) => {
        console.error('Error loading job diagrams:', error);
        this.loadingDiagrams = false;
        // Don't show error for diagrams as they might not exist for older jobs
      }
    });
    
    this.subscriptions.push(diagramsSub);
  }

  downloadDocumentation() {
    if (!this.job || this.job.status !== 'completed') {
      this.messageService.add({
        severity: 'warn',
        summary: 'Not Ready',
        detail: 'Documentation is not ready for download'
      });
      return;
    }
    
    this.messageService.add({
      severity: 'info',
      summary: 'Downloading',
      detail: 'Preparing documentation download...'
    });
    
    const downloadSub = this.apiService.downloadJobOutput(this.jobId).subscribe({
      next: (blob) => {
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `documentation_${this.jobId}.zip`;
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
    
    this.subscriptions.push(downloadSub);
  }

  goBack() {
    this.router.navigate(['/']);
  }

  refreshJob() {
    this.loadJobDetails();
  }

  getStatusSeverity(status: string): "success" | "secondary" | "info" | "warning" | "danger" | "contrast" | undefined {
    const severityMap: { [key: string]: "success" | "secondary" | "info" | "warning" | "danger" | "contrast" } = {
      'completed': 'success',
      'processing': 'warning',
      'pending': 'info',
      'failed': 'danger'
    };
    return severityMap[status] || 'secondary';
  }

  formatDuration(seconds: number): string {
    if (seconds < 60) {
      return `${seconds.toFixed(1)}s`;
    } else if (seconds < 3600) {
      const minutes = Math.floor(seconds / 60);
      const remainingSeconds = Math.floor(seconds % 60);
      return `${minutes}m ${remainingSeconds}s`;
    } else {
      const hours = Math.floor(seconds / 3600);
      const minutes = Math.floor((seconds % 3600) / 60);
      return `${hours}h ${minutes}m`;
    }
  }

  getRepositoryName(): string {
    if (!this.job?.repository_path) return 'Unknown';
    return this.job.repository_path.split('/').pop() || 'Unknown';
  }
}