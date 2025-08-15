import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable, BehaviorSubject, interval } from 'rxjs';
import { map, catchError, switchMap } from 'rxjs/operators';
import { environment } from '../../environments/environment';

export interface DocumentationRequest {
  repository_path: string;
  output_path?: string;
  depth: 'minimal' | 'standard' | 'comprehensive' | 'exhaustive';
  include_diagrams: boolean;
  include_business_rules: boolean;
  include_api_docs: boolean;
  incremental_update: boolean;
  focus_classes: boolean;
  focus_functions: boolean;
  focus_apis: boolean;
  focus_database: boolean;
  focus_security: boolean;
  focus_config: boolean;
  keywords?: string[];
  exclude_patterns?: string[];
}

export interface DocumentationResponse {
  job_id: string;
  status: string;
  message: string;
}

export interface JobStatus {
  job_id: string;
  status: string;
  repository_path?: string;
  created_at: Date;
  completed_at?: Date;
  entities_count: number;
  business_rules_count: number;
  files_processed: number;
  output_path?: string;
  error_message?: string;
  processing_time_seconds?: number;
}

export interface RepositoryInfo {
  path: string;
  name: string;
  total_files: number;
  total_lines: number;
  languages: { [key: string]: number };
  is_git: boolean;
  last_commit?: string;
  size_mb: number;
}

export interface AnalyticsData {
  total_jobs: number;
  successful_jobs: number;
  failed_jobs: number;
  average_processing_time: number;
  total_entities: number;
  total_business_rules: number;
  repositories_analyzed: number;
}

export interface DiagramData {
  id: string;
  name: string;
  type: string;
  content: string;
  description?: string;
}

export interface JobDiagramsResponse {
  job_id: string;
  repository_path: string;
  diagrams: DiagramData[];
}

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private apiUrl = 'http://localhost:8001/api';
  private activeJobs = new BehaviorSubject<JobStatus[]>([]);
  
  constructor(private http: HttpClient) {}
  
  // Documentation Generation
  generateDocumentation(request: DocumentationRequest): Observable<DocumentationResponse> {
    return this.http.post<DocumentationResponse>(
      `${this.apiUrl}/documentation/generate`,
      request
    );
  }
  
  getJobStatus(jobId: string): Observable<JobStatus> {
    return this.http.get<JobStatus>(
      `${this.apiUrl}/documentation/status/${jobId}`
    );
  }
  
  pollJobStatus(jobId: string, intervalMs: number = 2000): Observable<JobStatus> {
    return interval(intervalMs).pipe(
      switchMap(() => this.getJobStatus(jobId))
    );
  }
  
  listJobs(skip: number = 0, limit: number = 100): Observable<any[]> {
    return this.http.get<any[]>(
      `${this.apiUrl}/documentation/jobs?skip=${skip}&limit=${limit}`
    );
  }
  
  getJobDiagrams(jobId: string): Observable<JobDiagramsResponse> {
    return this.http.get<JobDiagramsResponse>(
      `${this.apiUrl}/documentation/jobs/${jobId}/diagrams`
    );
  }
  
  // Repository Management
  listRepositories(skip: number = 0, limit: number = 100): Observable<RepositoryInfo[]> {
    return this.http.get<RepositoryInfo[]>(
      `${this.apiUrl}/repositories?skip=${skip}&limit=${limit}`
    );
  }
  
  validateRepository(repoPath: string): Observable<RepositoryInfo> {
    return this.http.post<RepositoryInfo>(
      `${this.apiUrl}/repositories/validate`,
      null,
      { params: { repo_path: repoPath } }
    );
  }
  
  // Analytics
  getMetrics(): Observable<AnalyticsData> {
    return this.http.get<AnalyticsData>(`${this.apiUrl}/analytics/metrics`);
  }
  
  getTrends(days: number = 30): Observable<any[]> {
    return this.http.get<any[]>(
      `${this.apiUrl}/analytics/trends?days=${days}`
    );
  }
  
  getLanguageDistribution(): Observable<{ [key: string]: number }> {
    return this.http.get<{ [key: string]: number }>(
      `${this.apiUrl}/analytics/language-distribution`
    );
  }
  
  getPerformanceStats(): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/analytics/performance-stats`);
  }
  
  // Configuration
  listConfigTemplates(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/configuration/templates`);
  }
  
  createConfigTemplate(template: any): Observable<any> {
    return this.http.post<any>(
      `${this.apiUrl}/configuration/templates`,
      template
    );
  }
  
  getConfigTemplate(name: string): Observable<any> {
    return this.http.get<any>(
      `${this.apiUrl}/configuration/templates/${name}`
    );
  }
  
  deleteConfigTemplate(name: string): Observable<any> {
    return this.http.delete<any>(
      `${this.apiUrl}/configuration/templates/${name}`
    );
  }
  
  getDefaultConfig(): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/configuration/defaults`);
  }
  
  // Repository Sync
  syncRepository(repoPath: string): Observable<any> {
    return this.http.post<any>(
      `${this.apiUrl}/documentation/sync`,
      null,
      { params: { repo_path: repoPath } }
    );
  }
  
  // Download Documentation
  downloadJobOutput(jobId: string): Observable<Blob> {
    return this.http.get(
      `${this.apiUrl}/documentation/download/${jobId}`,
      { responseType: 'blob' }
    );
  }
  
  // Health Check
  getHealthStatus(): Observable<any> {
    return this.http.get<any>('http://localhost:8001/health/detailed');
  }
  
  // Active Jobs Management
  getActiveJobs(): Observable<JobStatus[]> {
    return this.activeJobs.asObservable();
  }
  
  addActiveJob(job: JobStatus): void {
    const current = this.activeJobs.value;
    this.activeJobs.next([...current, job]);
  }
  
  updateActiveJob(jobId: string, status: JobStatus): void {
    const current = this.activeJobs.value;
    const updated = current.map(job => 
      job.job_id === jobId ? status : job
    );
    this.activeJobs.next(updated);
  }
  
  removeActiveJob(jobId: string): void {
    const current = this.activeJobs.value;
    const filtered = current.filter(job => job.job_id !== jobId);
    this.activeJobs.next(filtered);
  }

  // AWS Configuration Methods
  getAWSStatus(): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/configuration/aws/status`);
  }

  testAWSCredentials(credentials: any): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/configuration/aws/test-credentials`, credentials);
  }

  configureAWS(config: any): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/configuration/aws/configure`, config);
  }

  getCurrentModelInfo(): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/configuration/aws/model-info`);
  }

  getAWSProfiles(): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/configuration/aws/profiles`);
  }
}
