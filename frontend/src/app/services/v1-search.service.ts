import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { map, catchError, retry } from 'rxjs/operators';
import { environment } from '../../environments/environment';

// V1 Hybrid Search Interfaces
export interface HybridSearchRequest {
  query: string;
  repo_filters?: string[];
  commit_filters?: string[];
  file_types?: string[];
  max_results?: number;
  bm25_boost?: number;
  knn_boost?: number;
}

export interface SearchCitation {
  path: string;
  start: number;
  end: number;
  commit: string;
  tool: string;
  model: string;
  search_type: string;
  confidence: number;
}

export interface SearchResult {
  id: string;
  content: string;
  citation: SearchCitation;
  metadata: {
    repo_id: string;
    language: string;
    kind: string;
    content_hash: string;
    indexed_at: string;
  };
  scores: {
    rrf_score: number;
    bm25_rank?: number;
    knn_rank?: number;
    original_score: number;
  };
  highlight: any;
  search_context: {
    search_id: string;
    timestamp: string;
    fusion_params: {
      k: number;
      bm25_weight: number;
      knn_weight: number;
    };
  };
}

export interface SearchResponse {
  success: boolean;
  data: {
    search_id: string;
    query: string;
    results: SearchResult[];
    total_results: number;
    performance: {
      total_time_ms: number;
      meets_slo: boolean;
      target_p50_ms: number;
      target_p95_ms: number;
    };
    fusion_details: {
      bm25_results: number;
      knn_results: number;
      rrf_k: number;
      bm25_weight: number;
      knn_weight: number;
    };
    filters_applied: {
      repositories?: string[];
      commits?: string[];
      file_types?: string[];
    };
  };
}

export interface GoldenQuestionRequest {
  question: string;
  expected_repos?: string[];
  max_results?: number;
}

export interface DemoQuestion {
  id: string;
  question: string;
  description: string;
  expected_files: string[];
  category: string;
}

export interface HealthStatus {
  success: boolean;
  status: 'healthy' | 'unhealthy';
  data?: {
    opensearch: {
      status: string;
      cluster_name: string;
    };
    bedrock: {
      embedding_dimension: number;
      model: string;
    };
    configuration: {
      rrf_k: number;
      bm25_weight: number;
      knn_weight: number;
      target_p50_ms: number;
      target_p95_ms: number;
    };
  };
  error?: string;
}

@Injectable({
  providedIn: 'root'
})
export class V1SearchService {
  private readonly apiUrl = `${environment.apiUrl}/api`;

  constructor(private http: HttpClient) {}

  /**
   * Perform RRF hybrid search combining BM25 and k-NN
   */
  hybridSearch(request: HybridSearchRequest): Observable<SearchResponse> {
    this.logRequest('Hybrid Search', request);
    
    return this.http.post<SearchResponse>(`${this.apiUrl}/v1/search/hybrid`, request)
      .pipe(
        retry(1),
        map(response => {
          this.logResponse('Hybrid Search', response);
          return response;
        }),
        catchError(error => this.handleError('Hybrid Search', error))
      );
  }

  /**
   * Search within a specific repository
   */
  repositorySearch(query: string, repoId: string, maxResults: number = 10): Observable<SearchResponse> {
    const request = { query, repo_id: repoId, max_results: maxResults };
    this.logRequest('Repository Search', request);
    
    return this.http.post<SearchResponse>(`${this.apiUrl}/v1/search/repository`, request)
      .pipe(
        retry(1),
        map(response => {
          this.logResponse('Repository Search', response);
          return response;
        }),
        catchError(error => this.handleError('Repository Search', error))
      );
  }

  /**
   * Search within a specific commit
   */
  commitSearch(query: string, commitHash: string, maxResults: number = 10): Observable<SearchResponse> {
    const request = { query, commit_hash: commitHash, max_results: maxResults };
    this.logRequest('Commit Search', request);
    
    return this.http.post<SearchResponse>(`${this.apiUrl}/v1/search/commit`, request)
      .pipe(
        retry(1),
        map(response => {
          this.logResponse('Commit Search', response);
          return response;
        }),
        catchError(error => this.handleError('Commit Search', error))
      );
  }

  /**
   * Golden questions search for demo scenarios
   */
  goldenQuestionSearch(request: GoldenQuestionRequest): Observable<SearchResponse> {
    this.logRequest('Golden Question Search', request);
    
    return this.http.post<SearchResponse>(`${this.apiUrl}/v1/search/golden-questions`, request)
      .pipe(
        retry(1),
        map(response => {
          this.logResponse('Golden Question Search', response);
          return response;
        }),
        catchError(error => this.handleError('Golden Question Search', error))
      );
  }

  /**
   * Quick search for simple queries
   */
  quickSearch(
    query: string, 
    repos?: string, 
    types?: string, 
    limit: number = 10
  ): Observable<SearchResponse> {
    const params: any = { q: query, limit };
    if (repos) params.repos = repos;
    if (types) params.types = types;
    
    this.logRequest('Quick Search', params);
    
    return this.http.get<SearchResponse>(`${this.apiUrl}/v1/search/quick-search`, { params })
      .pipe(
        retry(1),
        map(response => {
          this.logResponse('Quick Search', response);
          return response;
        }),
        catchError(error => this.handleError('Quick Search', error))
      );
  }

  /**
   * Get predefined demo questions
   */
  getDemoQuestions(): Observable<{ success: boolean; data: { demo_questions: DemoQuestion[] } }> {
    this.logRequest('Get Demo Questions', {});
    
    return this.http.get<{ success: boolean; data: { demo_questions: DemoQuestion[] } }>(`${this.apiUrl}/v1/search/demo-questions`)
      .pipe(
        retry(1),
        map(response => {
          this.logResponse('Get Demo Questions', response);
          return response;
        }),
        catchError(error => this.handleError('Get Demo Questions', error))
      );
  }

  /**
   * Check V1 search system health
   */
  getSearchHealth(): Observable<HealthStatus> {
    this.logRequest('Search Health Check', {});
    
    return this.http.get<HealthStatus>(`${this.apiUrl}/v1/search/health`)
      .pipe(
        retry(1),
        map(response => {
          this.logResponse('Search Health Check', response);
          return response;
        }),
        catchError(error => this.handleError('Search Health Check', error))
      );
  }

  /**
   * Get search performance metrics
   */
  getSearchMetrics(): Observable<any> {
    this.logRequest('Search Metrics', {});
    
    return this.http.get<any>(`${this.apiUrl}/v1/search/metrics`)
      .pipe(
        retry(1),
        map(response => {
          this.logResponse('Search Metrics', response);
          return response;
        }),
        catchError(error => this.handleError('Search Metrics', error))
      );
  }

  /**
   * Helper method to build hybrid search request with common patterns
   */
  buildSearchRequest(
    query: string,
    options: {
      repositories?: string[];
      fileTypes?: string[];
      maxResults?: number;
      preferText?: boolean; // Boost BM25 for code searching
      preferSemantic?: boolean; // Boost k-NN for concept searching
    } = {}
  ): HybridSearchRequest {
    const request: HybridSearchRequest = {
      query,
      max_results: options.maxResults || 20
    };

    if (options.repositories?.length) {
      request.repo_filters = options.repositories;
    }

    if (options.fileTypes?.length) {
      request.file_types = options.fileTypes;
    }

    // Adjust fusion weights based on search type
    if (options.preferText) {
      request.bm25_boost = 1.5;
      request.knn_boost = 0.8;
    } else if (options.preferSemantic) {
      request.bm25_boost = 0.8;
      request.knn_boost = 1.5;
    }

    return request;
  }

  /**
   * Format citation for display
   */
  formatCitation(citation: SearchCitation): string {
    const filename = citation.path.split('/').pop() || citation.path;
    const lines = citation.start === citation.end ? 
      `L${citation.start}` : 
      `L${citation.start}-${citation.end}`;
    
    return `${filename}:${lines} (${citation.commit.substring(0, 8)})`;
  }

  /**
   * Extract code snippet from search result
   */
  getCodeSnippet(result: SearchResult, maxLength: number = 300): string {
    if (!result.content) return '';
    
    let snippet = result.content.trim();
    if (snippet.length > maxLength) {
      snippet = snippet.substring(0, maxLength) + '...';
    }
    
    return snippet;
  }

  /**
   * Determine if search performance meets SLOs
   */
  evaluatePerformance(response: SearchResponse): {
    status: 'excellent' | 'good' | 'acceptable' | 'poor';
    message: string;
  } {
    const { performance } = response.data;
    const timeMs = performance.total_time_ms;
    
    if (timeMs <= performance.target_p50_ms) {
      return { status: 'excellent', message: `Fast search (${timeMs.toFixed(0)}ms)` };
    } else if (timeMs <= performance.target_p95_ms) {
      return { status: 'good', message: `Good performance (${timeMs.toFixed(0)}ms)` };
    } else if (timeMs <= performance.target_p95_ms * 1.5) {
      return { status: 'acceptable', message: `Slower than target (${timeMs.toFixed(0)}ms)` };
    } else {
      return { status: 'poor', message: `Performance issue (${timeMs.toFixed(0)}ms)` };
    }
  }

  /**
   * Log request for debugging
   */
  private logRequest(operation: string, request: any): void {
    if (!environment.production) {
      console.log(`[V1Search] ${operation} Request:`, request);
    }
  }

  /**
   * Log response for debugging
   */
  private logResponse(operation: string, response: any): void {
    if (!environment.production) {
      console.log(`[V1Search] ${operation} Response:`, response);
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
        console.error(`[V1Search] ${operation} Error:`, {
          status: error.status,
          statusText: error.statusText,
          url: error.url,
          error: error.error
        });
      }
    }

    // Log error for user feedback
    console.error(`[V1Search] ${operation} failed: ${errorMessage}`);
    
    return throwError(() => new Error(`${operation} failed: ${errorMessage}`));
  }
}