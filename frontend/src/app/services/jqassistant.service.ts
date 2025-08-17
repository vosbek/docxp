import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';
import { map, catchError } from 'rxjs/operators';
import { environment } from '../../environments/environment';

export interface ArchitecturalAnalysisRequest {
  repository_path: string;
  repository_id: string;
  commit_hash: string;
  indexing_job_id?: string;
  custom_layers?: ArchitecturalLayer[];
  custom_constraints?: string[];
  include_test_code?: boolean;
}

export interface ArchitecturalLayer {
  name: string;
  pattern: string;
  description: string;
  allowed_dependencies: string[];
  forbidden_dependencies: string[];
  severity_level: string;
}

export interface AnalysisJobStatus {
  job_id: string;
  status: string;
  repository_id: string;
  repository_path: string;
  commit_hash: string;
  progress: {
    total_packages: number;
    total_classes: number;
    total_methods: number;
    total_dependencies: number;
    cyclic_dependencies_count: number;
    architectural_violations_count: number;
  };
  quality_scores: {
    overall_quality_score: number;
    layer_compliance_score: number;
    architectural_debt_score: number;
  };
  timing: {
    created_at: string;
    started_at: string;
    completed_at: string;
    analysis_duration_seconds: number;
  };
  neo4j_stats: {
    nodes_created: number;
    relationships_created: number;
  };
  configuration: any;
  linked_indexing_job?: string;
  error_message?: string;
}

export interface PackageDependency {
  source_package: string;
  target_package: string;
  dependency_type: string;
  weight: number;
  files_involved: string[];
  is_cyclic: boolean;
  violation_type?: string;
}

export interface ArchitecturalViolation {
  violation_type: string;
  severity: string;
  source_element: string;
  target_element: string;
  constraint_violated: string;
  description: string;
  fix_suggestion?: string;
  file_path?: string;
  line_number?: number;
}

export interface DesignPattern {
  pattern_name: string;
  pattern_type: string;
  confidence: number;
  participants: string[];
  description: string;
  benefits: string[];
  location: string;
}

export interface DeadCodeElement {
  element_type: string;
  element_name: string;
  file_path: string;
  line_number?: number;
  reason: string;
  potential_impact: string;
  removal_suggestion: string;
}

export interface DependencyGraph {
  nodes: DependencyNode[];
  edges: DependencyEdge[];
  metadata: any;
}

export interface DependencyNode {
  id: string;
  label: string;
  type: string;
  layer?: string;
  metrics?: any;
}

export interface DependencyEdge {
  source: string;
  target: string;
  weight: number;
  type: string;
  is_cyclic?: boolean;
}

export interface ArchitecturalInsight {
  insight_type: string;
  category: string;
  priority: string;
  title: string;
  description: string;
  recommendation?: string;
  evidence?: any;
  affected_elements?: string[];
  business_impact?: string;
  technical_impact?: string;
  estimated_effort?: string;
  is_acknowledged?: boolean;
}

export interface CodeMetrics {
  complexity_metrics: any;
  coupling_metrics: any;
  size_metrics: any;
  quality_scores: any;
}

export interface RepositoryHealthScore {
  status: string;
  health_score?: number;
  health_grade?: string;
  health_factors?: any;
  analysis_date?: string;
  analysis_job_id?: string;
  recommendations?: string[];
}

@Injectable({
  providedIn: 'root'
})
export class JQAssistantService {
  private apiUrl = `${environment.apiUrl}/jqassistant`;
  private httpOptions = {
    headers: new HttpHeaders({
      'Content-Type': 'application/json'
    })
  };

  // Observable subjects for real-time updates
  private analysisStatusSubject = new BehaviorSubject<AnalysisJobStatus | null>(null);
  public analysisStatus$ = this.analysisStatusSubject.asObservable();

  private dependencyGraphSubject = new BehaviorSubject<DependencyGraph | null>(null);
  public dependencyGraph$ = this.dependencyGraphSubject.asObservable();

  constructor(private http: HttpClient) {}

  /**
   * Check jQAssistant health and installation status
   */
  checkHealth(): Observable<any> {
    return this.http.get(`${this.apiUrl}/health`);
  }

  /**
   * Start architectural analysis for a repository
   */
  analyzeRepository(request: ArchitecturalAnalysisRequest): Observable<any> {
    return this.http.post(`${this.apiUrl}/analyze/repository`, request, this.httpOptions);
  }

  /**
   * Get analysis job status
   */
  getAnalysisStatus(jobId: string): Observable<AnalysisJobStatus> {
    return this.http.get<AnalysisJobStatus>(`${this.apiUrl}/analyze/status/${jobId}`)
      .pipe(
        map(status => {
          this.analysisStatusSubject.next(status);
          return status;
        })
      );
  }

  /**
   * Get detailed analysis results
   */
  getAnalysisResults(
    jobId: string,
    options: {
      includeDependencies?: boolean;
      includeViolations?: boolean;
      includePatterns?: boolean;
      includeDeadCode?: boolean;
      limitResults?: number;
    } = {}
  ): Observable<any> {
    const params = new URLSearchParams();
    if (options.includeDependencies !== undefined) {
      params.append('include_dependencies', options.includeDependencies.toString());
    }
    if (options.includeViolations !== undefined) {
      params.append('include_violations', options.includeViolations.toString());
    }
    if (options.includePatterns !== undefined) {
      params.append('include_patterns', options.includePatterns.toString());
    }
    if (options.includeDeadCode !== undefined) {
      params.append('include_dead_code', options.includeDeadCode.toString());
    }
    if (options.limitResults !== undefined) {
      params.append('limit_results', options.limitResults.toString());
    }

    return this.http.get(`${this.apiUrl}/analyze/results/${jobId}?${params.toString()}`);
  }

  /**
   * Get dependency graph for visualization
   */
  getDependencyGraph(
    jobId: string,
    format: string = 'json',
    includeCycles: boolean = true,
    packageFilter?: string
  ): Observable<DependencyGraph> {
    const params = new URLSearchParams();
    params.append('format', format);
    params.append('include_cycles', includeCycles.toString());
    if (packageFilter) {
      params.append('package_filter', packageFilter);
    }

    return this.http.get<DependencyGraph>(`${this.apiUrl}/dependencies/graph/${jobId}?${params.toString()}`)
      .pipe(
        map(graph => {
          this.dependencyGraphSubject.next(graph);
          return graph;
        })
      );
  }

  /**
   * Get architectural violations
   */
  getViolations(
    jobId: string,
    violationType?: string,
    severity?: string,
    resolved?: boolean,
    limit: number = 50
  ): Observable<any> {
    const params = new URLSearchParams();
    if (violationType) params.append('violation_type', violationType);
    if (severity) params.append('severity', severity);
    if (resolved !== undefined) params.append('resolved', resolved.toString());
    params.append('limit', limit.toString());

    return this.http.get(`${this.apiUrl}/violations/${jobId}?${params.toString()}`);
  }

  /**
   * Get code metrics
   */
  getMetrics(
    jobId: string,
    scopeType: string = 'REPOSITORY',
    scopeName?: string
  ): Observable<CodeMetrics> {
    const params = new URLSearchParams();
    params.append('scope_type', scopeType);
    if (scopeName) params.append('scope_name', scopeName);

    return this.http.get<CodeMetrics>(`${this.apiUrl}/metrics/${jobId}?${params.toString()}`);
  }

  /**
   * Get design patterns
   */
  getDesignPatterns(
    jobId: string,
    patternType?: string,
    confidenceThreshold: number = 0.5
  ): Observable<any> {
    const params = new URLSearchParams();
    if (patternType) params.append('pattern_type', patternType);
    params.append('confidence_threshold', confidenceThreshold.toString());

    return this.http.get(`${this.apiUrl}/patterns/${jobId}?${params.toString()}`);
  }

  /**
   * Get dead code elements
   */
  getDeadCode(
    jobId: string,
    elementType?: string,
    potentialImpact?: string,
    verifiedOnly: boolean = false
  ): Observable<any> {
    const params = new URLSearchParams();
    if (elementType) params.append('element_type', elementType);
    if (potentialImpact) params.append('potential_impact', potentialImpact);
    params.append('verified_only', verifiedOnly.toString());

    return this.http.get(`${this.apiUrl}/dead-code/${jobId}?${params.toString()}`);
  }

  /**
   * Get architectural insights
   */
  getInsights(
    jobId: string,
    insightType?: string,
    category?: string,
    priority?: string,
    acknowledged?: boolean
  ): Observable<any> {
    const params = new URLSearchParams();
    if (insightType) params.append('insight_type', insightType);
    if (category) params.append('category', category);
    if (priority) params.append('priority', priority);
    if (acknowledged !== undefined) params.append('acknowledged', acknowledged.toString());

    return this.http.get(`${this.apiUrl}/insights/${jobId}?${params.toString()}`);
  }

  /**
   * Get architecture dashboard
   */
  getArchitectureDashboard(repositoryId: string, timeRange: string = '30d'): Observable<any> {
    const params = new URLSearchParams();
    params.append('time_range', timeRange);

    return this.http.get(`${this.apiUrl}/dashboard/${repositoryId}?${params.toString()}`);
  }

  /**
   * List recent analysis jobs
   */
  getRecentJobs(limit: number = 10): Observable<any> {
    const params = new URLSearchParams();
    params.append('limit', limit.toString());

    return this.http.get(`${this.apiUrl}/jobs/recent?${params.toString()}`);
  }

  /**
   * Validate architectural layers
   */
  validateLayers(layers: ArchitecturalLayer[]): Observable<any> {
    return this.http.post(`${this.apiUrl}/layers/validate`, layers, this.httpOptions);
  }

  /**
   * Get default architectural layers
   */
  getDefaultLayers(): Observable<any> {
    return this.http.get(`${this.apiUrl}/config/default-layers`);
  }

  /**
   * Get repository health score
   */
  getRepositoryHealth(repositoryPath: string): Observable<RepositoryHealthScore> {
    // This would be implemented via the enhanced V1 indexing service
    return this.http.get<RepositoryHealthScore>(`${environment.apiUrl}/v1-indexing/health-score`, {
      params: { repository_path: repositoryPath }
    });
  }

  /**
   * Poll analysis status until completion
   */
  pollAnalysisStatus(jobId: string, interval: number = 5000): Observable<AnalysisJobStatus> {
    return new Observable(observer => {
      const poll = () => {
        this.getAnalysisStatus(jobId).subscribe({
          next: (status) => {
            observer.next(status);
            if (status.status === 'completed' || status.status === 'failed') {
              observer.complete();
            } else {
              setTimeout(poll, interval);
            }
          },
          error: (error) => {
            observer.error(error);
          }
        });
      };
      poll();
    });
  }

  /**
   * Calculate quality score color
   */
  getQualityScoreColor(score: number): string {
    if (score >= 90) return '#4caf50'; // Green
    if (score >= 80) return '#8bc34a'; // Light green
    if (score >= 70) return '#ffeb3b'; // Yellow
    if (score >= 60) return '#ff9800'; // Orange
    return '#f44336'; // Red
  }

  /**
   * Get severity color
   */
  getSeverityColor(severity: string): string {
    switch (severity.toLowerCase()) {
      case 'critical': return '#f44336';
      case 'high': return '#ff9800';
      case 'medium': return '#ffeb3b';
      case 'low': return '#4caf50';
      default: return '#9e9e9e';
    }
  }

  /**
   * Format architectural layer name
   */
  formatLayerName(layer: string): string {
    return layer.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase());
  }

  /**
   * Clear cached data
   */
  clearCache(): void {
    this.analysisStatusSubject.next(null);
    this.dependencyGraphSubject.next(null);
  }
}