import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject, interval } from 'rxjs';
import { switchMap, takeWhile, catchError } from 'rxjs/operators';
import { environment } from '../../environments/environment';

export interface RepositorySource {
  id: string;
  name: string;
  source_type: 'git' | 'zip' | 'tar' | 'directory';
  source_path: string;
  branch?: string;
  priority?: number;
  processing_options?: Record<string, any>;
  metadata?: Record<string, any>;
}

export interface ProcessingStatus {
  repository_id: string;
  status: 'pending' | 'downloading' | 'extracting' | 'analyzing' | 'indexing' | 'completed' | 'failed' | 'cancelled';
  start_time: string;
  end_time?: string;
  entities_extracted: number;
  business_rules_found: number;
  files_processed: number;
  errors: string[];
  warnings: string[];
  processing_stats: Record<string, any>;
}

export interface BatchStatus {
  active_jobs: number;
  completed_jobs: number;
  failed_jobs: number;
  total_processed: number;
  current_jobs: string[];
}

export interface BatchProcessingRequest {
  repositories: RepositorySource[];
  batch_options?: Record<string, any>;
}

@Injectable({
  providedIn: 'root'
})
export class RepositoryProcessingService {
  private readonly baseUrl = environment.apiUrl || 'http://localhost:8000';
  
  private batchStatusSubject = new BehaviorSubject<BatchStatus | null>(null);
  private repositoryStatusMap = new Map<string, BehaviorSubject<ProcessingStatus | null>>();
  
  public batchStatus$ = this.batchStatusSubject.asObservable();

  constructor(private http: HttpClient) {}

  /**
   * Start batch processing of multiple repositories
   */
  startBatchProcessing(request: BatchProcessingRequest): Observable<any> {
    return this.http.post(`${this.baseUrl}/api/repositories/processing/batch`, request);
  }

  /**
   * Start processing a single repository
   */
  startSingleRepositoryProcessing(repository: RepositorySource): Observable<any> {
    return this.http.post(`${this.baseUrl}/api/repositories/processing/single`, repository);
  }

  /**
   * Get processing status for a specific repository
   */
  getRepositoryStatus(repositoryId: string): Observable<ProcessingStatus> {
    return this.http.get<ProcessingStatus>(`${this.baseUrl}/api/repositories/processing/status/${repositoryId}`);
  }

  /**
   * Get overall batch processing status
   */
  getBatchStatus(): Observable<BatchStatus> {
    return this.http.get<BatchStatus>(`${this.baseUrl}/api/repositories/processing/batch-status`);
  }

  /**
   * Cancel processing for a specific repository
   */
  cancelRepositoryProcessing(repositoryId: string): Observable<any> {
    return this.http.post(`${this.baseUrl}/api/repositories/processing/cancel/${repositoryId}`, {});
  }

  /**
   * Get processing history with optional filtering
   */
  getProcessingHistory(limit: number = 50, statusFilter?: string): Observable<any> {
    let url = `${this.baseUrl}/api/repositories/processing/history?limit=${limit}`;
    if (statusFilter) {
      url += `&status_filter=${statusFilter}`;
    }
    return this.http.get(url);
  }

  /**
   * Get supported source types and their requirements
   */
  getSupportedSourceTypes(): Observable<any> {
    return this.http.get(`${this.baseUrl}/api/repositories/processing/supported-sources`);
  }

  /**
   * Health check for repository processing service
   */
  getProcessingHealth(): Observable<any> {
    return this.http.get(`${this.baseUrl}/api/repositories/processing/health`);
  }

  /**
   * Start monitoring repository status with automatic polling
   */
  monitorRepositoryStatus(repositoryId: string): Observable<ProcessingStatus | null> {
    if (!this.repositoryStatusMap.has(repositoryId)) {
      const statusSubject = new BehaviorSubject<ProcessingStatus | null>(null);
      this.repositoryStatusMap.set(repositoryId, statusSubject);
      
      // Start polling for status updates
      interval(2000) // Poll every 2 seconds
        .pipe(
          switchMap(() => this.getRepositoryStatus(repositoryId)),
          takeWhile(status => 
            status && !['completed', 'failed', 'cancelled'].includes(status.status), 
            true // Include the final status
          ),
          catchError(error => {
            console.warn(`Failed to get status for repository ${repositoryId}:`, error);
            return [];
          })
        )
        .subscribe(
          status => statusSubject.next(status),
          error => {
            console.error(`Repository status monitoring error for ${repositoryId}:`, error);
            statusSubject.next(null);
          }
        );
    }
    
    return this.repositoryStatusMap.get(repositoryId)!.asObservable();
  }

  /**
   * Start monitoring batch status with automatic polling
   */
  monitorBatchStatus(): void {
    interval(3000) // Poll every 3 seconds
      .pipe(
        switchMap(() => this.getBatchStatus()),
        catchError(error => {
          console.warn('Failed to get batch status:', error);
          return [];
        })
      )
      .subscribe(
        status => this.batchStatusSubject.next(status),
        error => {
          console.error('Batch status monitoring error:', error);
        }
      );
  }

  /**
   * Stop monitoring a specific repository
   */
  stopRepositoryMonitoring(repositoryId: string): void {
    const statusSubject = this.repositoryStatusMap.get(repositoryId);
    if (statusSubject) {
      statusSubject.complete();
      this.repositoryStatusMap.delete(repositoryId);
    }
  }

  /**
   * Create a sample repository configuration for testing
   */
  createSampleRepositories(): RepositorySource[] {
    return [
      {
        id: 'sample-legacy-app',
        name: 'Sample Legacy Application',
        source_type: 'git',
        source_path: 'https://github.com/apache/struts.git',
        branch: 'master',
        priority: 1,
        processing_options: {
          deep_analysis: true,
          extract_business_rules: true,
          include_tests: true
        },
        metadata: {
          description: 'Apache Struts - Legacy Java web framework',
          migration_target: 'Spring Boot',
          team: 'migration-team'
        }
      },
      {
        id: 'sample-corba-service',
        name: 'Legacy CORBA Service',
        source_type: 'directory',
        source_path: '/path/to/corba/service',
        priority: 2,
        processing_options: {
          deep_analysis: true,
          extract_business_rules: true
        },
        metadata: {
          description: 'Legacy CORBA-based service',
          migration_target: 'gRPC/REST API',
          complexity: 'high'
        }
      }
    ];
  }

  /**
   * Validate repository configuration
   */
  validateRepositorySource(repository: RepositorySource): string[] {
    const errors: string[] = [];

    if (!repository.id || repository.id.trim() === '') {
      errors.push('Repository ID is required');
    }

    if (!repository.name || repository.name.trim() === '') {
      errors.push('Repository name is required');
    }

    if (!repository.source_type) {
      errors.push('Source type is required');
    } else if (!['git', 'zip', 'tar', 'directory'].includes(repository.source_type)) {
      errors.push('Invalid source type. Must be git, zip, tar, or directory');
    }

    if (!repository.source_path || repository.source_path.trim() === '') {
      errors.push('Source path is required');
    }

    if (repository.source_type === 'git') {
      // Basic URL validation for git repositories
      try {
        new URL(repository.source_path);
      } catch {
        if (!repository.source_path.includes('git@')) {
          errors.push('Git source path must be a valid URL or SSH path');
        }
      }
    }

    if (repository.priority && (repository.priority < 1 || repository.priority > 5)) {
      errors.push('Priority must be between 1 and 5');
    }

    return errors;
  }

  /**
   * Calculate estimated processing time based on repository characteristics
   */
  estimateProcessingTime(repository: RepositorySource): string {
    const baseTime = 60; // Base time in seconds
    let multiplier = 1;

    // Adjust based on source type
    switch (repository.source_type) {
      case 'git':
        multiplier *= 1.5; // Git cloning takes extra time
        break;
      case 'zip':
      case 'tar':
        multiplier *= 1.2; // Archive extraction
        break;
      case 'directory':
        multiplier *= 1.0; // Local directory is fastest
        break;
    }

    // Adjust based on processing options
    if (repository.processing_options?.deep_analysis) {
      multiplier *= 2.0;
    }
    if (repository.processing_options?.extract_business_rules) {
      multiplier *= 1.3;
    }

    const estimatedSeconds = baseTime * multiplier;
    
    if (estimatedSeconds < 120) {
      return `~${Math.round(estimatedSeconds)} seconds`;
    } else if (estimatedSeconds < 3600) {
      return `~${Math.round(estimatedSeconds / 60)} minutes`;
    } else {
      return `~${Math.round(estimatedSeconds / 3600)} hours`;
    }
  }

  /**
   * Get processing status description
   */
  getStatusDescription(status: string): string {
    switch (status) {
      case 'pending':
        return 'Waiting to start processing';
      case 'downloading':
        return 'Downloading repository content';
      case 'extracting':
        return 'Extracting and analyzing file structure';
      case 'analyzing':
        return 'Analyzing code entities and patterns';
      case 'indexing':
        return 'Indexing content into vector database';
      case 'completed':
        return 'Processing completed successfully';
      case 'failed':
        return 'Processing failed';
      case 'cancelled':
        return 'Processing was cancelled';
      default:
        return 'Unknown status';
    }
  }

  /**
   * Get status color for UI display
   */
  getStatusColor(status: string): string {
    switch (status) {
      case 'completed':
        return '#22c55e'; // Green
      case 'failed':
        return '#ef4444'; // Red
      case 'cancelled':
        return '#6b7280'; // Gray
      case 'pending':
        return '#f59e0b'; // Amber
      default:
        return '#3b82f6'; // Blue for processing states
    }
  }
}