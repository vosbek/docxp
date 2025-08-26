import { Component, OnInit, OnDestroy, ViewChild, ElementRef } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MatTabChangeEvent } from '@angular/material/tabs';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Subject, interval, takeUntil, switchMap } from 'rxjs';
import { 
  JQAssistantService, 
  AnalysisJobStatus, 
  ArchitecturalAnalysisRequest,
  DependencyGraph,
  ArchitecturalViolation,
  ArchitecturalInsight,
  CodeMetrics,
  RepositoryHealthScore
} from '../../services/jqassistant.service';

@Component({
  selector: 'app-architecture-analysis',
  templateUrl: './architecture-analysis.component.html',
  styleUrls: ['./architecture-analysis.component.scss']
})
export class ArchitectureAnalysisComponent implements OnInit, OnDestroy {
  @ViewChild('dependencyGraphContainer', { static: false }) dependencyGraphContainer!: ElementRef;

  // Form and UI state
  analysisForm: FormGroup;
  selectedTabIndex = 0;
  isAnalyzing = false;
  showAdvancedOptions = false;

  // Analysis data
  currentJobId: string | null = null;
  analysisStatus: AnalysisJobStatus | null = null;
  dependencyGraph: DependencyGraph | null = null;
  violations: ArchitecturalViolation[] = [];
  insights: ArchitecturalInsight[] = [];
  codeMetrics: CodeMetrics | null = null;
  repositoryHealth: RepositoryHealthScore | null = null;

  // UI state
  violationFilters = {
    severity: '',
    type: '',
    resolved: null as boolean | null
  };

  insightFilters = {
    type: '',
    category: '',
    priority: '',
    acknowledged: null as boolean | null
  };

  // Chart data
  qualityChartData: any[] = [];
  violationChartData: any[] = [];
  dependencyChartData: any[] = [];

  // Recent jobs for quick access
  recentJobs: any[] = [];

  private destroy$ = new Subject<void>();

  constructor(
    private fb: FormBuilder,
    private jqassistantService: JQAssistantService,
    private snackBar: MatSnackBar
  ) {
    this.analysisForm = this.createAnalysisForm();
  }

  ngOnInit(): void {
    this.loadRecentJobs();
    this.checkJQAssistantHealth();
    
    // Subscribe to analysis status updates
    this.jqassistantService.analysisStatus$
      .pipe(takeUntil(this.destroy$))
      .subscribe(status => {
        if (status) {
          this.analysisStatus = status;
          this.updateChartsFromStatus(status);
        }
      });

    // Subscribe to dependency graph updates
    this.jqassistantService.dependencyGraph$
      .pipe(takeUntil(this.destroy$))
      .subscribe(graph => {
        if (graph) {
          this.dependencyGraph = graph;
          this.renderDependencyGraph();
        }
      });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private createAnalysisForm(): FormGroup {
    return this.fb.group({
      repositoryPath: ['', [Validators.required]],
      repositoryId: ['', [Validators.required]],
      commitHash: ['HEAD', [Validators.required]],
      indexingJobId: [''],
      includeTestCode: [false],
      customLayers: [[]],
      customConstraints: [[]]
    });
  }

  async checkJQAssistantHealth(): Promise<void> {
    try {
      const health = await this.jqassistantService.checkHealth().toPromise();
      if (!health.jqassistant_installed) {
        this.snackBar.open('jQAssistant is not properly installed', 'Close', {
          duration: 5000,
          panelClass: ['error-snackbar']
        });
      }
    } catch (error) {
      console.error('Health check failed:', error);
      this.snackBar.open('Failed to check jQAssistant health', 'Close', {
        duration: 5000,
        panelClass: ['error-snackbar']
      });
    }
  }

  async startAnalysis(): Promise<void> {
    if (this.analysisForm.invalid) {
      this.snackBar.open('Please fill in all required fields', 'Close', {
        duration: 3000,
        panelClass: ['warning-snackbar']
      });
      return;
    }

    this.isAnalyzing = true;
    const formValue = this.analysisForm.value;

    const request: ArchitecturalAnalysisRequest = {
      repository_path: formValue.repositoryPath,
      repository_id: formValue.repositoryId,
      commit_hash: formValue.commitHash,
      indexing_job_id: formValue.indexingJobId || undefined,
      include_test_code: formValue.includeTestCode,
      custom_layers: formValue.customLayers.length > 0 ? formValue.customLayers : undefined,
      custom_constraints: formValue.customConstraints.length > 0 ? formValue.customConstraints : undefined
    };

    try {
      const response = await this.jqassistantService.analyzeRepository(request).toPromise();
      this.currentJobId = response.job_id;
      
      this.snackBar.open('Analysis started successfully', 'Close', {
        duration: 3000,
        panelClass: ['success-snackbar']
      });

      // Start polling for status updates
      this.pollAnalysisStatus();

    } catch (error) {
      console.error('Analysis start failed:', error);
      this.snackBar.open('Failed to start analysis', 'Close', {
        duration: 5000,
        panelClass: ['error-snackbar']
      });
      this.isAnalyzing = false;
    }
  }

  private pollAnalysisStatus(): void {
    if (!this.currentJobId) return;

    this.jqassistantService.pollAnalysisStatus(this.currentJobId)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (status) => {
          this.analysisStatus = status;
          if (status.status === 'completed') {
            this.isAnalyzing = false;
            this.loadAnalysisResults();
            this.snackBar.open('Analysis completed successfully', 'Close', {
              duration: 3000,
              panelClass: ['success-snackbar']
            });
          } else if (status.status === 'failed') {
            this.isAnalyzing = false;
            this.snackBar.open(`Analysis failed: ${status.error_message}`, 'Close', {
              duration: 5000,
              panelClass: ['error-snackbar']
            });
          }
        },
        error: (error) => {
          console.error('Status polling failed:', error);
          this.isAnalyzing = false;
        }
      });
  }

  private async loadAnalysisResults(): Promise<void> {
    if (!this.currentJobId) return;

    try {
      // Load detailed results in parallel
      const [
        dependencyGraph,
        violations,
        insights,
        metrics
      ] = await Promise.all([
        this.jqassistantService.getDependencyGraph(this.currentJobId).toPromise(),
        this.jqassistantService.getViolations(this.currentJobId).toPromise(),
        this.jqassistantService.getInsights(this.currentJobId).toPromise(),
        this.jqassistantService.getMetrics(this.currentJobId).toPromise()
      ]);

      this.dependencyGraph = dependencyGraph;
      this.violations = violations.violations || [];
      this.insights = insights.insights || [];
      this.codeMetrics = metrics;

      // Load repository health score
      if (this.analysisForm.value.repositoryPath) {
        this.repositoryHealth = await this.jqassistantService
          .getRepositoryHealth(this.analysisForm.value.repositoryPath).toPromise();
      }

      this.updateCharts();
      this.renderDependencyGraph();

    } catch (error) {
      console.error('Failed to load analysis results:', error);
      this.snackBar.open('Failed to load analysis results', 'Close', {
        duration: 5000,
        panelClass: ['error-snackbar']
      });
    }
  }

  onTabChange(event: MatTabChangeEvent): void {
    this.selectedTabIndex = event.index;
    
    // Trigger specific tab initialization
    switch (event.index) {
      case 1: // Dependency Graph
        setTimeout(() => this.renderDependencyGraph(), 100);
        break;
      case 2: // Violations
        this.applyViolationFilters();
        break;
      case 3: // Insights
        this.applyInsightFilters();
        break;
      case 4: // Metrics
        this.updateMetricsCharts();
        break;
    }
  }

  private updateChartsFromStatus(status: AnalysisJobStatus): void {
    // Update quality score chart
    this.qualityChartData = [
      {
        name: 'Overall Quality',
        value: status.quality_scores.overall_quality_score
      },
      {
        name: 'Layer Compliance',
        value: status.quality_scores.layer_compliance_score
      },
      {
        name: 'Architectural Debt',
        value: 100 - status.quality_scores.architectural_debt_score
      }
    ];

    // Update progress metrics
    this.dependencyChartData = [
      {
        name: 'Packages',
        value: status.progress.total_packages
      },
      {
        name: 'Classes',
        value: status.progress.total_classes
      },
      {
        name: 'Methods',
        value: status.progress.total_methods
      },
      {
        name: 'Dependencies',
        value: status.progress.total_dependencies
      }
    ];
  }

  private updateCharts(): void {
    if (this.violations.length > 0) {
      // Group violations by severity
      const severityCount = this.violations.reduce((acc, violation) => {
        acc[violation.severity] = (acc[violation.severity] || 0) + 1;
        return acc;
      }, {} as { [key: string]: number });

      this.violationChartData = Object.entries(severityCount).map(([severity, count]) => ({
        name: severity,
        value: count
      }));
    }
  }

  private updateMetricsCharts(): void {
    if (!this.codeMetrics) return;
    
    // This would create charts for complexity, coupling, etc.
    // Implementation depends on charting library used
  }

  applyViolationFilters(): void {
    // Filter violations based on current filter settings
    // Implementation would filter this.violations array
  }

  applyInsightFilters(): void {
    // Filter insights based on current filter settings
    // Implementation would filter this.insights array
  }

  private renderDependencyGraph(): void {
    if (!this.dependencyGraph || !this.dependencyGraphContainer) return;

    // Implementation would use D3.js, Cytoscape.js, or similar
    // to render the dependency graph visualization
    
    const container = this.dependencyGraphContainer.nativeElement;
    container.innerHTML = '<p>Dependency graph visualization would be rendered here</p>';
    
    // Example pseudo-code for graph rendering:
    // const graph = new DependencyGraphRenderer(container);
    // graph.render(this.dependencyGraph);
  }

  async loadRecentJobs(): Promise<void> {
    try {
      const response = await this.jqassistantService.getRecentJobs(5).toPromise();
      this.recentJobs = response.jobs || [];
    } catch (error) {
      console.error('Failed to load recent jobs:', error);
    }
  }

  loadJob(jobId: string): void {
    this.currentJobId = jobId;
    this.jqassistantService.getAnalysisStatus(jobId)
      .subscribe({
        next: (status) => {
          this.analysisStatus = status;
          if (status.status === 'completed') {
            this.loadAnalysisResults();
          }
        },
        error: (error) => {
          console.error('Failed to load job:', error);
          this.snackBar.open('Failed to load analysis job', 'Close', {
            duration: 3000,
            panelClass: ['error-snackbar']
          });
        }
      });
  }

  getProgressPercentage(): number {
    if (!this.analysisStatus) return 0;
    
    switch (this.analysisStatus.status) {
      case 'completed': return 100;
      case 'failed': return 0;
      case 'running': return 50; // Estimate
      default: return 0;
    }
  }

  getQualityScoreColor(score: number): string {
    return this.jqassistantService.getQualityScoreColor(score);
  }

  getSeverityColor(severity: string): string {
    return this.jqassistantService.getSeverityColor(severity);
  }

  acknowledgeInsight(insight: ArchitecturalInsight): void {
    // Implementation would call API to acknowledge insight
    insight.is_acknowledged = true;
    this.snackBar.open('Insight acknowledged', 'Close', {
      duration: 2000,
      panelClass: ['success-snackbar']
    });
  }

  markViolationResolved(violation: ArchitecturalViolation): void {
    // Implementation would call API to mark violation as resolved
    this.snackBar.open('Violation marked as resolved', 'Close', {
      duration: 2000,
      panelClass: ['success-snackbar']
    });
  }

  exportResults(): void {
    if (!this.analysisStatus) return;

    const exportData = {
      analysis_status: this.analysisStatus,
      violations: this.violations,
      insights: this.insights,
      metrics: this.codeMetrics,
      dependency_graph: this.dependencyGraph,
      repository_health: this.repositoryHealth
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `architecture-analysis-${this.analysisStatus.repository_id}-${Date.now()}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  }

  toggleAdvancedOptions(): void {
    this.showAdvancedOptions = !this.showAdvancedOptions;
  }

  addCustomLayer(): void {
    const customLayers = this.analysisForm.get('customLayers')?.value || [];
    customLayers.push({
      name: '',
      pattern: '',
      description: '',
      allowed_dependencies: [],
      forbidden_dependencies: [],
      severity_level: 'HIGH'
    });
    this.analysisForm.patchValue({ customLayers });
  }

  removeCustomLayer(index: number): void {
    const customLayers = this.analysisForm.get('customLayers')?.value || [];
    customLayers.splice(index, 1);
    this.analysisForm.patchValue({ customLayers });
  }

  addCustomConstraint(): void {
    const customConstraints = this.analysisForm.get('customConstraints')?.value || [];
    customConstraints.push('');
    this.analysisForm.patchValue({ customConstraints });
  }

  removeCustomConstraint(index: number): void {
    const customConstraints = this.analysisForm.get('customConstraints')?.value || [];
    customConstraints.splice(index, 1);
    this.analysisForm.patchValue({ customConstraints });
  }
}