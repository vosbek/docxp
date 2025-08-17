import { Component, OnInit, OnDestroy, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Subject, takeUntil, finalize } from 'rxjs';
import { MatTabsModule } from '@angular/material/tabs';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatSelectModule } from '@angular/material/select';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatTableModule } from '@angular/material/table';
import { MatSortModule } from '@angular/material/sort';
import { MatPaginatorModule } from '@angular/material/paginator';
import { MatBadgeModule } from '@angular/material/badge';
import { MatMenuModule } from '@angular/material/menu';
import { 
  SemgrepService,
  SemgrepAnalysisResult,
  SemgrepFinding,
  SecuritySummary,
  SemgrepValidation,
  AnalyzeRepositoryRequest
} from '../../services/semgrep.service';

interface FindingGroup {
  category: string;
  findings: SemgrepFinding[];
  count: number;
  criticalCount: number;
}

interface SecurityMetric {
  label: string;
  value: number;
  total: number;
  percentage: number;
  status: 'good' | 'warning' | 'critical';
}

@Component({
  selector: 'app-semgrep-analysis',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatTabsModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    MatIconModule,
    MatSelectModule,
    MatCardModule,
    MatChipsModule,
    MatProgressSpinnerModule,
    MatProgressBarModule,
    MatTooltipModule,
    MatExpansionModule,
    MatTableModule,
    MatSortModule,
    MatPaginatorModule,
    MatBadgeModule,
    MatMenuModule
  ],
  templateUrl: './semgrep-analysis.component.html',
  styleUrls: ['./semgrep-analysis.component.scss']
})
export class SemgrepAnalysisComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();
  
  @Input() repoId?: string;
  @Input() commitHash?: string;
  @Input() repoPath?: string;

  // Forms
  analysisForm: FormGroup;
  
  // State
  isAnalyzing = false;
  analysisProgress = 0;
  currentAnalysis: SemgrepAnalysisResult | null = null;
  securitySummary: SecuritySummary | null = null;
  semgrepHealth: SemgrepValidation | null = null;
  
  // Display data
  findingGroups: FindingGroup[] = [];
  securityMetrics: SecurityMetric[] = [];
  selectedSeverityFilter = 'ALL';
  selectedCategoryFilter = 'ALL';
  
  // Table configuration
  displayedColumns = ['severity', 'category', 'rule_id', 'message', 'file_path', 'line', 'actions'];
  filteredFindings: SemgrepFinding[] = [];
  
  // Available options
  severityOptions = [
    { value: 'ALL', label: 'All Severities' },
    { value: 'ERROR', label: 'Critical Issues' },
    { value: 'WARNING', label: 'Warnings' },
    { value: 'INFO', label: 'Info' }
  ];
  
  categoryOptions = [
    { value: 'ALL', label: 'All Categories' },
    { value: 'security', label: 'Security' },
    { value: 'performance', label: 'Performance' },
    { value: 'correctness', label: 'Correctness' },
    { value: 'maintainability', label: 'Maintainability' },
    { value: 'code-quality', label: 'Code Quality' }
  ];

  constructor(
    private fb: FormBuilder,
    private semgrepService: SemgrepService
  ) {
    this.analysisForm = this.fb.group({
      repoPath: ['', [Validators.required]],
      repoId: ['', [Validators.required]],
      commitHash: ['', [Validators.required]],
      ruleSets: [['security', 'quality']],
      customRules: [[]]
    });
  }

  ngOnInit(): void {
    this.checkSemgrepHealth();
    this.initializeForm();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  /**
   * Initialize form with input values
   */
  private initializeForm(): void {
    if (this.repoId || this.commitHash || this.repoPath) {
      this.analysisForm.patchValue({
        repoId: this.repoId || '',
        commitHash: this.commitHash || '',
        repoPath: this.repoPath || ''
      });
    }
  }

  /**
   * Check Semgrep installation status
   */
  checkSemgrepHealth(): void {
    this.semgrepService.getHealth()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (health) => {
          this.semgrepHealth = health;
          if (!health.semgrep_installed) {
            console.warn('Semgrep not installed or not configured properly');
          }
        },
        error: (error) => {
          console.error('Semgrep health check failed:', error);
        }
      });
  }

  /**
   * Start repository analysis
   */
  analyzeRepository(): void {
    if (this.analysisForm.invalid) {
      this.markFormGroupTouched();
      return;
    }

    const formValue = this.analysisForm.value;
    const request: AnalyzeRepositoryRequest = {
      repo_path: formValue.repoPath,
      repo_id: formValue.repoId,
      commit_hash: formValue.commitHash,
      rule_sets: formValue.ruleSets,
      custom_rules: formValue.customRules
    };

    this.isAnalyzing = true;
    this.analysisProgress = 0;
    this.currentAnalysis = null;
    this.securitySummary = null;

    // Simulate progress
    const progressInterval = setInterval(() => {
      this.analysisProgress += 10;
      if (this.analysisProgress >= 90) {
        clearInterval(progressInterval);
      }
    }, 500);

    this.semgrepService.analyzeRepository(request)
      .pipe(
        takeUntil(this.destroy$),
        finalize(() => {
          this.isAnalyzing = false;
          clearInterval(progressInterval);
          this.analysisProgress = 100;
        })
      )
      .subscribe({
        next: (analysis) => {
          this.currentAnalysis = analysis;
          this.processAnalysisResults();
          this.loadSecuritySummary();
        },
        error: (error) => {
          console.error('Repository analysis failed:', error);
          // Handle error appropriately
        }
      });
  }

  /**
   * Process analysis results for display
   */
  private processAnalysisResults(): void {
    if (!this.currentAnalysis) return;

    // Group findings by category
    this.findingGroups = this.groupFindingsByCategory(this.currentAnalysis.findings);
    
    // Generate security metrics
    this.securityMetrics = this.generateSecurityMetrics(this.currentAnalysis);
    
    // Initialize filtered findings
    this.applyFilters();
  }

  /**
   * Group findings by category
   */
  private groupFindingsByCategory(findings: SemgrepFinding[]): FindingGroup[] {
    const groups = new Map<string, SemgrepFinding[]>();
    
    findings.forEach(finding => {
      if (!groups.has(finding.category)) {
        groups.set(finding.category, []);
      }
      groups.get(finding.category)!.push(finding);
    });
    
    return Array.from(groups.entries()).map(([category, categoryFindings]) => ({
      category,
      findings: categoryFindings,
      count: categoryFindings.length,
      criticalCount: categoryFindings.filter(f => f.severity === 'ERROR').length
    }));
  }

  /**
   * Generate security metrics
   */
  private generateSecurityMetrics(analysis: SemgrepAnalysisResult): SecurityMetric[] {
    const total = analysis.total_findings;
    
    return [
      {
        label: 'Critical Issues',
        value: analysis.findings_by_severity['ERROR'] || 0,
        total,
        percentage: total > 0 ? ((analysis.findings_by_severity['ERROR'] || 0) / total) * 100 : 0,
        status: (analysis.findings_by_severity['ERROR'] || 0) > 0 ? 'critical' : 'good'
      },
      {
        label: 'Security Issues',
        value: analysis.critical_security_issues,
        total,
        percentage: total > 0 ? (analysis.critical_security_issues / total) * 100 : 0,
        status: analysis.critical_security_issues > 0 ? 'critical' : 'good'
      },
      {
        label: 'Performance Issues',
        value: analysis.performance_issues,
        total,
        percentage: total > 0 ? (analysis.performance_issues / total) * 100 : 0,
        status: analysis.performance_issues > 5 ? 'warning' : 'good'
      },
      {
        label: 'Maintainability Score',
        value: analysis.maintainability_score,
        total: 100,
        percentage: analysis.maintainability_score,
        status: analysis.maintainability_score >= 80 ? 'good' : 
                analysis.maintainability_score >= 60 ? 'warning' : 'critical'
      }
    ];
  }

  /**
   * Load security summary
   */
  private loadSecuritySummary(): void {
    if (!this.currentAnalysis) return;

    this.semgrepService.getSecuritySummary(this.currentAnalysis.repo_id, this.currentAnalysis.commit_hash)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (summary) => {
          this.securitySummary = summary;
        },
        error: (error) => {
          console.error('Security summary loading failed:', error);
        }
      });
  }

  /**
   * Apply severity and category filters
   */
  applyFilters(): void {
    if (!this.currentAnalysis) {
      this.filteredFindings = [];
      return;
    }

    let filtered = this.currentAnalysis.findings;

    // Apply severity filter
    if (this.selectedSeverityFilter !== 'ALL') {
      filtered = filtered.filter(f => f.severity === this.selectedSeverityFilter);
    }

    // Apply category filter
    if (this.selectedCategoryFilter !== 'ALL') {
      filtered = filtered.filter(f => f.category === this.selectedCategoryFilter);
    }

    this.filteredFindings = filtered;
  }

  /**
   * Handle severity filter change
   */
  onSeverityFilterChange(severity: string): void {
    this.selectedSeverityFilter = severity;
    this.applyFilters();
  }

  /**
   * Handle category filter change
   */
  onCategoryFilterChange(category: string): void {
    this.selectedCategoryFilter = category;
    this.applyFilters();
  }

  /**
   * Get severity icon
   */
  getSeverityIcon(severity: string): string {
    return this.semgrepService.getSeverityIcon(severity);
  }

  /**
   * Get severity color class
   */
  getSeverityColorClass(severity: string): string {
    return this.semgrepService.getSeverityColorClass(severity);
  }

  /**
   * Get category icon
   */
  getCategoryIcon(category: string): string {
    return this.semgrepService.getCategoryIcon(category);
  }

  /**
   * Get category color class
   */
  getCategoryColorClass(category: string): string {
    return this.semgrepService.getCategoryColorClass(category);
  }

  /**
   * Get confidence icon
   */
  getConfidenceIcon(confidence: string): string {
    return this.semgrepService.getConfidenceIcon(confidence);
  }

  /**
   * Get risk level color
   */
  getRiskLevelColor(riskLevel: string): string {
    return this.semgrepService.getRiskLevelColor(riskLevel);
  }

  /**
   * Get OWASP category name
   */
  getOwaspCategoryName(category: string): string {
    return this.semgrepService.getOwaspCategoryName(category);
  }

  /**
   * Get metric status color
   */
  getMetricStatusColor(status: string): string {
    switch (status) {
      case 'good': return '#4caf50';
      case 'warning': return '#ff9800';
      case 'critical': return '#f44336';
      default: return '#757575';
    }
  }

  /**
   * Check if finding is high priority
   */
  isHighPriorityFinding(finding: SemgrepFinding): boolean {
    return this.semgrepService.isHighPriorityFinding(finding);
  }

  /**
   * Export findings to CSV
   */
  exportFindings(): void {
    if (!this.currentAnalysis) return;
    
    const filename = `semgrep-analysis-${this.currentAnalysis.repo_id}-${Date.now()}.csv`;
    this.semgrepService.downloadFindingsCSV(this.filteredFindings, filename);
  }

  /**
   * View finding details
   */
  viewFindingDetails(finding: SemgrepFinding): void {
    // This would open a detailed view or navigate to the file
    console.log('Viewing finding details:', finding);
  }

  /**
   * Apply suggested fix
   */
  applySuggestedFix(finding: SemgrepFinding): void {
    if (finding.fix_suggestion) {
      // This would integrate with an editor or provide fix guidance
      console.log('Applying fix for:', finding.rule_id, finding.fix_suggestion);
    }
  }

  /**
   * Mark form group as touched
   */
  private markFormGroupTouched(): void {
    Object.keys(this.analysisForm.controls).forEach(key => {
      this.analysisForm.get(key)?.markAsTouched();
    });
  }

  /**
   * Check if form field has error
   */
  hasFieldError(fieldName: string): boolean {
    const field = this.analysisForm.get(fieldName);
    return !!(field && field.invalid && (field.dirty || field.touched));
  }

  /**
   * Get field error message
   */
  getFieldError(fieldName: string): string {
    const field = this.analysisForm.get(fieldName);
    if (!field || !field.errors) return '';

    if (field.errors['required']) return `${fieldName} is required`;
    return 'Invalid input';
  }

  /**
   * Track by function for ngFor
   */
  trackByFindingId(index: number, finding: SemgrepFinding): string {
    return `${finding.rule_id}_${finding.file_path}_${finding.start_line}`;
  }
}