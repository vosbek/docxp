import { Component, OnInit, ViewChild, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, ActivatedRoute } from '@angular/router';

// PrimeNG Imports
import { CardModule } from 'primeng/card';
import { ButtonModule } from 'primeng/button';
import { StepsModule } from 'primeng/steps';
import { InputTextModule } from 'primeng/inputtext';
import { DropdownModule } from 'primeng/dropdown';
import { CheckboxModule } from 'primeng/checkbox';
import { ChipsModule } from 'primeng/chips';
import { ProgressBarModule } from 'primeng/progressbar';
import { MessageModule } from 'primeng/message';
import { ToastModule } from 'primeng/toast';
import { DialogModule } from 'primeng/dialog';
import { TableModule } from 'primeng/table';
import { TooltipModule } from 'primeng/tooltip';
import { MenuItem, MessageService } from 'primeng/api';

import { ApiService, DocumentationRequest, RepositoryInfo, JobStatus } from '../../services/api.service';
import { interval, Subscription } from 'rxjs';
import { takeWhile } from 'rxjs/operators';

interface FocusAreas {
  [key: string]: boolean;
  classes: boolean;
  functions: boolean;
  apis: boolean;
  database: boolean;
  security: boolean;
  config: boolean;
}

interface StepData {
  repository?: RepositoryInfo;
  configuration?: Partial<DocumentationRequest>;
  jobStatus?: JobStatus;
}

@Component({
  selector: 'app-generation-wizard',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    CardModule,
    ButtonModule,
    StepsModule,
    InputTextModule,
    DropdownModule,
    CheckboxModule,
    ChipsModule,
    ProgressBarModule,
    MessageModule,
    ToastModule,
    DialogModule,
    TableModule,
    TooltipModule
  ],
  providers: [MessageService],
  templateUrl: './generation-wizard.component.html',
  styleUrl: './generation-wizard.component.scss'
})
export class GenerationWizardComponent implements OnInit, OnDestroy {
  steps: MenuItem[] = [];
  activeIndex: number = 0;
  
  // Step 1: Repository Selection
  repositoryPath: string = '';
  validatingRepo: boolean = false;
  repositoryInfo?: RepositoryInfo;
  repositoryValid: boolean = false;
  
  // Step 2: Configuration
  depths = [
    { label: 'Minimal - Basic structure only', value: 'minimal' },
    { label: 'Standard - Recommended for most projects', value: 'standard' },
    { label: 'Comprehensive - Detailed analysis', value: 'comprehensive' },
    { label: 'Exhaustive - Complete documentation', value: 'exhaustive' }
  ];
  
  selectedDepth: string = 'standard';
  includeDiagrams: boolean = true;
  includeBusinessRules: boolean = true;
  includeApiDocs: boolean = true;
  incrementalUpdate: boolean = false;
  
  focusAreas: FocusAreas = {
    classes: true,
    functions: true,
    apis: true,
    database: true,
    security: true,
    config: true
  };
  
  keywords: string[] = [];
  excludePatterns: string[] = ['node_modules', '.git', '__pycache__', 'dist', 'build'];
  
  // Step 3: Review
  estimatedTime: string = '';
  estimatedSize: string = '';
  
  // Step 4: Generation
  generating: boolean = false;
  generationProgress: number = 0;
  currentStatus: string = '';
  jobId?: string;
  pollingSubscription?: Subscription;
  
  // Step 5: Results
  generationComplete: boolean = false;
  generationResult?: JobStatus;
  outputPath?: string;
  
  constructor(
    private apiService: ApiService,
    private messageService: MessageService,
    private router: Router,
    private route: ActivatedRoute
  ) {}
  
  ngOnInit() {
    this.initializeSteps();
    
    // Check if repository path was passed as query param
    this.route.queryParams.subscribe(params => {
      if (params['repo']) {
        this.repositoryPath = params['repo'];
        this.validateRepository();
      }
    });
  }
  
  initializeSteps() {
    this.steps = [
      { label: 'Repository', icon: 'pi pi-folder' },
      { label: 'Configuration', icon: 'pi pi-cog' },
      { label: 'Review', icon: 'pi pi-check-square' },
      { label: 'Generation', icon: 'pi pi-bolt' },
      { label: 'Results', icon: 'pi pi-flag-fill' }
    ];
  }
  
  // Step 1: Repository Methods
  async validateRepository() {
    if (!this.repositoryPath) {
      this.messageService.add({
        severity: 'error',
        summary: 'Error',
        detail: 'Please enter a repository path'
      });
      return;
    }
    
    this.validatingRepo = true;
    this.repositoryValid = false;
    
    this.apiService.validateRepository(this.repositoryPath).subscribe({
      next: (info) => {
        this.repositoryInfo = info;
        this.repositoryValid = true;
        this.validatingRepo = false;
        
        this.messageService.add({
          severity: 'success',
          summary: 'Valid Repository',
          detail: `Found ${info.total_files} files in ${Object.keys(info.languages).length} languages`
        });
        
        // Auto-advance to next step
        setTimeout(() => this.nextStep(), 1500);
      },
      error: (error) => {
        this.validatingRepo = false;
        this.messageService.add({
          severity: 'error',
          summary: 'Invalid Repository',
          detail: error.error?.detail || 'Repository path not found or inaccessible'
        });
      }
    });
  }
  
  browseRepository() {
    // In a real app, this would open a file browser dialog
    // For now, we'll just show a message
    this.messageService.add({
      severity: 'info',
      summary: 'Browse',
      detail: 'File browser integration coming soon. Please enter path manually.'
    });
  }
  
  // Step 2: Configuration Methods
  onDepthChange() {
    this.updateEstimates();
  }
  
  updateEstimates() {
    if (!this.repositoryInfo) return;
    
    const baseTime = this.repositoryInfo.total_files * 0.1; // 0.1 minutes per file
    const depthMultiplier: { [key: string]: number } = {
      'minimal': 0.5,
      'standard': 1,
      'comprehensive': 1.5,
      'exhaustive': 2
    };
    
    const multiplier = depthMultiplier[this.selectedDepth] || 1;
    const estimatedMinutes = Math.ceil(baseTime * multiplier);
    
    this.estimatedTime = estimatedMinutes < 60 
      ? `${estimatedMinutes} minutes`
      : `${Math.ceil(estimatedMinutes / 60)} hours`;
    
    const estimatedMB = Math.ceil(this.repositoryInfo.total_files * 0.05 * multiplier);
    this.estimatedSize = `~${estimatedMB} MB`;
  }
  
  // Step 3: Review Methods
  getConfigurationSummary(): any[] {
    return [
      { setting: 'Repository', value: this.repositoryPath },
      { setting: 'Documentation Depth', value: this.selectedDepth },
      { setting: 'Include Diagrams', value: this.includeDiagrams ? 'Yes' : 'No' },
      { setting: 'Extract Business Rules', value: this.includeBusinessRules ? 'Yes' : 'No' },
      { setting: 'Generate API Docs', value: this.includeApiDocs ? 'Yes' : 'No' },
      { setting: 'Incremental Update', value: this.incrementalUpdate ? 'Yes' : 'No' },
      { setting: 'Keywords', value: this.keywords.length > 0 ? this.keywords.join(', ') : 'None' },
      { setting: 'Estimated Time', value: this.estimatedTime },
      { setting: 'Estimated Size', value: this.estimatedSize }
    ];
  }
  
  // Step 4: Generation Methods
  startGeneration() {
    const request: DocumentationRequest = {
      repository_path: this.repositoryPath,
      output_path: './output',
      depth: this.selectedDepth as any,
      include_diagrams: this.includeDiagrams,
      include_business_rules: this.includeBusinessRules,
      include_api_docs: this.includeApiDocs,
      incremental_update: this.incrementalUpdate,
      focus_classes: this.focusAreas.classes,
      focus_functions: this.focusAreas.functions,
      focus_apis: this.focusAreas.apis,
      focus_database: this.focusAreas.database,
      focus_security: this.focusAreas.security,
      focus_config: this.focusAreas.config,
      keywords: this.keywords,
      exclude_patterns: this.excludePatterns
    };
    
    this.generating = true;
    this.generationProgress = 0;
    this.currentStatus = 'Starting documentation generation...';
    
    this.apiService.generateDocumentation(request).subscribe({
      next: (response) => {
        this.jobId = response.job_id;
        this.currentStatus = 'Job created, processing...';
        this.startPollingJobStatus();
        
        this.messageService.add({
          severity: 'info',
          summary: 'Generation Started',
          detail: 'Documentation generation is in progress'
        });
      },
      error: (error) => {
        this.generating = false;
        this.messageService.add({
          severity: 'error',
          summary: 'Generation Failed',
          detail: error.error?.detail || 'Failed to start documentation generation'
        });
      }
    });
  }
  
  startPollingJobStatus() {
    if (!this.jobId) return;
    
    this.pollingSubscription = interval(2000)
      .pipe(
        takeWhile(() => this.generating)
      )
      .subscribe(() => {
        if (!this.jobId) return;
        
        this.apiService.getJobStatus(this.jobId).subscribe({
          next: (status) => {
            this.updateGenerationProgress(status);
            
            if (status.status === 'completed' || status.status === 'failed') {
              this.generating = false;
              this.generationComplete = true;
              this.generationResult = status;
              
              if (status.status === 'completed') {
                this.outputPath = status.output_path;
                this.messageService.add({
                  severity: 'success',
                  summary: 'Generation Complete!',
                  detail: `Generated documentation for ${status.entities_count} entities and ${status.business_rules_count} business rules`
                });
                
                // Auto-advance to results
                setTimeout(() => this.nextStep(), 1000);
              } else {
                this.messageService.add({
                  severity: 'error',
                  summary: 'Generation Failed',
                  detail: status.error_message || 'Unknown error occurred'
                });
              }
              
              this.pollingSubscription?.unsubscribe();
            }
          },
          error: (error) => {
            console.error('Error polling job status:', error);
          }
        });
      });
  }
  
  updateGenerationProgress(status: JobStatus) {
    // Estimate progress based on status
    switch (status.status) {
      case 'pending':
        this.generationProgress = 10;
        this.currentStatus = 'Waiting in queue...';
        break;
      case 'processing':
        // Simulate progress based on time elapsed
        const elapsed = new Date().getTime() - new Date(status.created_at).getTime();
        const estimatedTotal = 60000; // 60 seconds estimate
        this.generationProgress = Math.min(90, Math.floor((elapsed / estimatedTotal) * 90));
        
        if (this.generationProgress < 30) {
          this.currentStatus = 'Analyzing repository structure...';
        } else if (this.generationProgress < 50) {
          this.currentStatus = 'Parsing code files...';
        } else if (this.generationProgress < 70) {
          this.currentStatus = 'Extracting business rules...';
        } else {
          this.currentStatus = 'Generating documentation...';
        }
        break;
      case 'completed':
        this.generationProgress = 100;
        this.currentStatus = 'Documentation generated successfully!';
        break;
      case 'failed':
        this.currentStatus = 'Generation failed';
        break;
    }
  }
  
  // Navigation Methods
  nextStep() {
    if (this.activeIndex < this.steps.length - 1) {
      // Validation before advancing
      if (this.activeIndex === 0 && !this.repositoryValid) {
        this.messageService.add({
          severity: 'warn',
          summary: 'Validation Required',
          detail: 'Please validate the repository before proceeding'
        });
        return;
      }
      
      if (this.activeIndex === 1) {
        this.updateEstimates();
      }
      
      if (this.activeIndex === 2) {
        // Auto-start generation when moving from review to generation
        this.activeIndex++;
        setTimeout(() => this.startGeneration(), 500);
        return;
      }
      
      this.activeIndex++;
    }
  }
  
  previousStep() {
    if (this.activeIndex > 0 && !this.generating) {
      this.activeIndex--;
    }
  }
  
  restart() {
    this.activeIndex = 0;
    this.repositoryPath = '';
    this.repositoryInfo = undefined;
    this.repositoryValid = false;
    this.selectedDepth = 'standard';
    this.keywords = [];
    this.generationComplete = false;
    this.generationResult = undefined;
    this.jobId = undefined;
  }
  
  viewDocumentation() {
    if (this.outputPath) {
      // In a real app, this would open the documentation viewer
      this.router.navigate(['/documentation', this.jobId]);
    }
  }
  
  downloadDocumentation() {
    if (this.outputPath) {
      // In a real app, this would trigger a download
      window.open(`http://localhost:8001/output/${this.jobId}/README.md`, '_blank');
    }
  }
  
  ngOnDestroy() {
    this.pollingSubscription?.unsubscribe();
  }
}
