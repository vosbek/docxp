import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { map, catchError, retry } from 'rxjs/operators';
import { environment } from '../../environments/environment';

// Semgrep Analysis Interfaces
export interface SemgrepFinding {
  rule_id: string;
  severity: 'ERROR' | 'WARNING' | 'INFO';
  category: 'security' | 'performance' | 'correctness' | 'maintainability' | 'code-quality';
  message: string;
  file_path: string;
  start_line: number;
  end_line: number;
  code_snippet: string;
  confidence: 'HIGH' | 'MEDIUM' | 'LOW';
  cwe_ids: string[];
  owasp_categories: string[];
  fix_suggestion?: string;
}

export interface SemgrepAnalysisResult {
  repo_id: string;
  commit_hash: string;
  total_findings: number;
  findings_by_severity: { [key: string]: number };
  findings_by_category: { [key: string]: number };
  critical_security_issues: number;
  performance_issues: number;
  maintainability_score: number;
  analysis_duration_seconds: number;
  findings: SemgrepFinding[];
}

export interface SecuritySummary {
  total_security_findings: number;
  critical_vulnerabilities: number;
  risk_score: number;
  risk_level: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'MINIMAL';
  remediation_priority: RemediationPriority[];
}

export interface RemediationPriority {
  rule_id: string;
  total_occurrences: number;
  critical_occurrences: number;
  priority_score: number;
  category: string;
  fix_suggestion?: string;
  affected_files: string[];
}

export interface SemgrepValidation {
  semgrep_installed: boolean;
  version?: string;
  rules_available: boolean;
  custom_rules_ready: boolean;
  errors: string[];
}

export interface AnalyzeRepositoryRequest {
  repo_path: string;
  repo_id: string;
  commit_hash: string;
  rule_sets?: string[];
  custom_rules?: string[];
}

export interface AnalyzeFileRequest {
  file_path: string;
  content?: string;
}

@Injectable({
  providedIn: 'root'
})
export class SemgrepService {
  private readonly apiUrl = environment.production ? 
    'http://localhost:8000/api' : 
    'http://localhost:8000/api';

  constructor(private http: HttpClient) {}

  /**
   * Check Semgrep installation and configuration status
   */
  getHealth(): Observable<SemgrepValidation> {
    this.logRequest('Semgrep Health Check', {});
    
    return this.http.get<SemgrepValidation>(`${this.apiUrl}/v1/semgrep/health`)
      .pipe(
        retry(1),
        map(response => {
          this.logResponse('Semgrep Health Check', response);
          return response;
        }),
        catchError(error => this.handleError('Semgrep Health Check', error))
      );
  }

  /**
   * Analyze entire repository with Semgrep
   */
  analyzeRepository(request: AnalyzeRepositoryRequest): Observable<SemgrepAnalysisResult> {
    this.logRequest('Repository Analysis', request);
    
    return this.http.post<SemgrepAnalysisResult>(`${this.apiUrl}/v1/semgrep/analyze/repository`, request)
      .pipe(
        retry(1),
        map(response => {
          this.logResponse('Repository Analysis', response);
          return response;
        }),
        catchError(error => this.handleError('Repository Analysis', error))
      );
  }

  /**
   * Analyze single file with Semgrep
   */
  analyzeFile(request: AnalyzeFileRequest): Observable<SemgrepFinding[]> {
    this.logRequest('File Analysis', request);
    
    return this.http.post<SemgrepFinding[]>(`${this.apiUrl}/v1/semgrep/analyze/file`, request)
      .pipe(
        retry(1),
        map(response => {
          this.logResponse('File Analysis', response);
          return response;
        }),
        catchError(error => this.handleError('File Analysis', error))
      );
  }

  /**
   * Get security summary for repository
   */
  getSecuritySummary(repoId: string, commitHash?: string): Observable<SecuritySummary> {
    const params = commitHash ? { commit_hash: commitHash } : {};
    this.logRequest('Security Summary', { repoId, ...params });
    
    return this.http.get<SecuritySummary>(`${this.apiUrl}/v1/semgrep/security/summary/${repoId}`, { params })
      .pipe(
        retry(1),
        map(response => {
          this.logResponse('Security Summary', response);
          return response;
        }),
        catchError(error => this.handleError('Security Summary', error))
      );
  }

  /**
   * Get findings filtered by category
   */
  getFindingsByCategory(
    repoId: string, 
    category: string, 
    severity?: string, 
    limit: number = 50
  ): Observable<any> {
    const params: any = { category, limit };
    if (severity) params.severity = severity;
    
    this.logRequest('Findings by Category', { repoId, ...params });
    
    return this.http.get<any>(`${this.apiUrl}/v1/semgrep/findings/by-category/${repoId}`, { params })
      .pipe(
        retry(1),
        map(response => {
          this.logResponse('Findings by Category', response);
          return response;
        }),
        catchError(error => this.handleError('Findings by Category', error))
      );
  }

  /**
   * Get available rules and rule sets
   */
  getAvailableRules(): Observable<any> {
    this.logRequest('Available Rules', {});
    
    return this.http.get<any>(`${this.apiUrl}/v1/semgrep/rules/available`)
      .pipe(
        retry(1),
        map(response => {
          this.logResponse('Available Rules', response);
          return response;
        }),
        catchError(error => this.handleError('Available Rules', error))
      );
  }

  /**
   * Get analysis dashboard data
   */
  getAnalysisDashboard(repoId: string): Observable<any> {
    this.logRequest('Analysis Dashboard', { repoId });
    
    return this.http.get<any>(`${this.apiUrl}/v1/semgrep/stats/dashboard/${repoId}`)
      .pipe(
        retry(1),
        map(response => {
          this.logResponse('Analysis Dashboard', response);
          return response;
        }),
        catchError(error => this.handleError('Analysis Dashboard', error))
      );
  }

  /**
   * Validate custom rules
   */
  validateCustomRules(rulesPath: string): Observable<any> {
    this.logRequest('Validate Custom Rules', { rulesPath });
    
    return this.http.post<any>(`${this.apiUrl}/v1/semgrep/rules/validate`, { rules_path: rulesPath })
      .pipe(
        retry(1),
        map(response => {
          this.logResponse('Validate Custom Rules', response);
          return response;
        }),
        catchError(error => this.handleError('Validate Custom Rules', error))
      );
  }

  /**
   * Get severity icon for display
   */
  getSeverityIcon(severity: string): string {
    switch (severity) {
      case 'ERROR': return 'error';
      case 'WARNING': return 'warning';
      case 'INFO': return 'info';
      default: return 'help';
    }
  }

  /**
   * Get severity color class
   */
  getSeverityColorClass(severity: string): string {
    switch (severity) {
      case 'ERROR': return 'severity-error';
      case 'WARNING': return 'severity-warning';
      case 'INFO': return 'severity-info';
      default: return 'severity-default';
    }
  }

  /**
   * Get category icon for display
   */
  getCategoryIcon(category: string): string {
    switch (category) {
      case 'security': return 'security';
      case 'performance': return 'speed';
      case 'correctness': return 'bug_report';
      case 'maintainability': return 'build';
      case 'code-quality': return 'code';
      default: return 'help';
    }
  }

  /**
   * Get category color class
   */
  getCategoryColorClass(category: string): string {
    switch (category) {
      case 'security': return 'category-security';
      case 'performance': return 'category-performance';
      case 'correctness': return 'category-correctness';
      case 'maintainability': return 'category-maintainability';
      case 'code-quality': return 'category-quality';
      default: return 'category-default';
    }
  }

  /**
   * Get confidence icon
   */
  getConfidenceIcon(confidence: string): string {
    switch (confidence) {
      case 'HIGH': return 'verified';
      case 'MEDIUM': return 'help';
      case 'LOW': return 'help_outline';
      default: return 'help';
    }
  }

  /**
   * Get risk level color
   */
  getRiskLevelColor(riskLevel: string): string {
    switch (riskLevel) {
      case 'CRITICAL': return '#d32f2f';
      case 'HIGH': return '#f57c00';
      case 'MEDIUM': return '#fbc02d';
      case 'LOW': return '#388e3c';
      case 'MINIMAL': return '#1976d2';
      default: return '#757575';
    }
  }

  /**
   * Format analysis summary for display
   */
  formatAnalysisSummary(analysis: SemgrepAnalysisResult): string {
    const criticalCount = analysis.findings_by_severity['ERROR'] || 0;
    const warningCount = analysis.findings_by_severity['WARNING'] || 0;
    const infoCount = analysis.findings_by_severity['INFO'] || 0;
    
    return `${analysis.total_findings} findings: ${criticalCount} critical, ${warningCount} warnings, ${infoCount} info`;
  }

  /**
   * Get fix suggestion icon
   */
  getFixSuggestionIcon(): string {
    return 'lightbulb';
  }

  /**
   * Check if finding is high priority
   */
  isHighPriorityFinding(finding: SemgrepFinding): boolean {
    return (
      (finding.severity === 'ERROR' && finding.category === 'security') ||
      (finding.severity === 'ERROR' && finding.confidence === 'HIGH')
    );
  }

  /**
   * Get OWASP category display name
   */
  getOwaspCategoryName(category: string): string {
    const owaspNames: { [key: string]: string } = {
      'A01': 'Broken Access Control',
      'A02': 'Cryptographic Failures', 
      'A03': 'Injection',
      'A04': 'Insecure Design',
      'A05': 'Security Misconfiguration',
      'A06': 'Vulnerable Components',
      'A07': 'Authentication Failures',
      'A08': 'Software Integrity Failures',
      'A09': 'Logging Failures',
      'A10': 'Server-Side Request Forgery'
    };
    
    return owaspNames[category] || category;
  }

  /**
   * Get CWE display name
   */
  getCweDisplayName(cweId: string): string {
    // This could be expanded with a full CWE mapping
    return cweId.startsWith('CWE-') ? cweId : `CWE-${cweId}`;
  }

  /**
   * Export findings to CSV
   */
  exportFindingsToCSV(findings: SemgrepFinding[]): string {
    const headers = [
      'Rule ID', 'Severity', 'Category', 'Message', 'File Path', 
      'Start Line', 'End Line', 'Confidence', 'CWE IDs', 'OWASP Categories'
    ];
    
    const rows = findings.map(f => [
      f.rule_id,
      f.severity,
      f.category,
      f.message.replace(/"/g, '""'),
      f.file_path,
      f.start_line.toString(),
      f.end_line.toString(),
      f.confidence,
      f.cwe_ids.join(';'),
      f.owasp_categories.join(';')
    ]);
    
    const csvContent = [headers, ...rows]
      .map(row => row.map(cell => `"${cell}"`).join(','))
      .join('\n');
    
    return csvContent;
  }

  /**
   * Download findings as CSV file
   */
  downloadFindingsCSV(findings: SemgrepFinding[], filename: string = 'semgrep-findings.csv'): void {
    const csvContent = this.exportFindingsToCSV(findings);
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
    
    window.URL.revokeObjectURL(url);
  }

  /**
   * Log request for debugging
   */
  private logRequest(operation: string, request: any): void {
    if (!environment.production) {
      console.log(`[Semgrep] ${operation} Request:`, request);
    }
  }

  /**
   * Log response for debugging
   */
  private logResponse(operation: string, response: any): void {
    if (!environment.production) {
      console.log(`[Semgrep] ${operation} Response:`, response);
    }
  }

  /**
   * Handle HTTP errors with proper logging
   */
  private handleError(operation: string, error: HttpErrorResponse): Observable<never> {
    let errorMessage = 'An unexpected error occurred';
    
    if (error.error instanceof ErrorEvent) {
      // Client-side error
      errorMessage = `Client Error: ${error.error.message}`;
    } else {
      // Server-side error
      errorMessage = `Server Error (${error.status}): ${error.error?.detail || error.message}`;
      
      // Log specific error details for debugging
      if (!environment.production) {
        console.error(`[Semgrep] ${operation} Error:`, {
          status: error.status,
          statusText: error.statusText,
          url: error.url,
          error: error.error
        });
      }
    }

    // Log error for user feedback
    console.error(`[Semgrep] ${operation} failed: ${errorMessage}`);
    
    return throwError(() => new Error(`${operation} failed: ${errorMessage}`));
  }
}