import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Subject, takeUntil, debounceTime, distinctUntilChanged } from 'rxjs';
import { MatTabsModule } from '@angular/material/tabs';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatSelectModule } from '@angular/material/select';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatTooltipModule } from '@angular/material/tooltip';
import { 
  V1SearchService, 
  SearchResponse, 
  SearchResult, 
  DemoQuestion,
  HealthStatus 
} from '../../services/v1-search.service';

interface SearchTab {
  id: string;
  label: string;
  icon: string;
}

@Component({
  selector: 'app-v1-search',
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
    MatCheckboxModule,
    MatExpansionModule,
    MatCardModule,
    MatChipsModule,
    MatProgressSpinnerModule,
    MatTooltipModule
  ],
  templateUrl: './v1-search.component.html',
  styleUrls: ['./v1-search.component.scss']
})
export class V1SearchComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();
  
  searchForm: FormGroup;
  searchResults: SearchResult[] = [];
  searchResponse: SearchResponse | null = null;
  demoQuestions: DemoQuestion[] = [];
  healthStatus: HealthStatus | null = null;
  
  isSearching = false;
  searchError: string | null = null;
  selectedTabIndex = 0;
  
  tabs: SearchTab[] = [
    { id: 'hybrid', label: 'Hybrid Search', icon: 'search' },
    { id: 'golden', label: 'Golden Questions', icon: 'quiz' },
    { id: 'quick', label: 'Quick Search', icon: 'flash_on' }
  ];

  fileTypeOptions = [
    { value: 'java', label: 'Java (.java)' },
    { value: 'jsp', label: 'JSP (.jsp)' },
    { value: 'sql', label: 'SQL (.sql)' },
    { value: 'xml', label: 'XML (.xml)' },
    { value: 'js', label: 'JavaScript (.js)' },
    { value: 'ts', label: 'TypeScript (.ts)' },
    { value: 'py', label: 'Python (.py)' },
    { value: 'html', label: 'HTML (.html)' }
  ];

  constructor(
    private fb: FormBuilder,
    private searchService: V1SearchService
  ) {
    this.searchForm = this.fb.group({
      query: ['', [Validators.required, Validators.minLength(2)]],
      fileTypes: [[]],
      repositories: [[]],
      maxResults: [20, [Validators.min(1), Validators.max(100)]],
      preferText: [false],
      preferSemantic: [false]
    });
  }

  ngOnInit(): void {
    this.checkSystemHealth();
    this.loadDemoQuestions();
    this.setupSearchDebounce();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  /**
   * Setup debounced search for quick mode
   */
  private setupSearchDebounce(): void {
    this.searchForm.get('query')?.valueChanges
      .pipe(
        debounceTime(500),
        distinctUntilChanged(),
        takeUntil(this.destroy$)
      )
      .subscribe(query => {
        if (this.selectedTabIndex === 2 && query && query.length >= 2) {
          this.performQuickSearch(query);
        }
      });
  }

  /**
   * Check V1 search system health
   */
  checkSystemHealth(): void {
    this.searchService.getSearchHealth()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (health) => {
          this.healthStatus = health;
          if (!health.success) {
            console.warn('V1 Search system health check failed:', health.error);
          }
        },
        error: (error) => {
          console.error('Health check failed:', error);
          this.healthStatus = {
            success: false,
            status: 'unhealthy',
            error: 'Cannot connect to V1 backend'
          };
        }
      });
  }

  /**
   * Load demo questions for golden questions tab
   */
  loadDemoQuestions(): void {
    this.searchService.getDemoQuestions()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (response) => {
          if (response.success) {
            this.demoQuestions = response.data.demo_questions;
          }
        },
        error: (error) => {
          console.error('Failed to load demo questions:', error);
        }
      });
  }

  /**
   * Perform hybrid search
   */
  performSearch(): void {
    if (this.searchForm.invalid) {
      this.markFormGroupTouched();
      return;
    }

    const formValue = this.searchForm.value;
    this.isSearching = true;
    this.searchError = null;

    const searchRequest = this.searchService.buildSearchRequest(
      formValue.query,
      {
        fileTypes: formValue.fileTypes.length > 0 ? formValue.fileTypes : undefined,
        repositories: formValue.repositories.length > 0 ? formValue.repositories : undefined,
        maxResults: formValue.maxResults,
        preferText: formValue.preferText,
        preferSemantic: formValue.preferSemantic
      }
    );

    this.searchService.hybridSearch(searchRequest)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (response) => {
          this.handleSearchResponse(response);
        },
        error: (error) => {
          this.handleSearchError(error);
        },
        complete: () => {
          this.isSearching = false;
        }
      });
  }

  /**
   * Perform quick search (for auto-search as user types)
   */
  performQuickSearch(query: string): void {
    this.isSearching = true;
    this.searchError = null;

    this.searchService.quickSearch(query, undefined, undefined, 10)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (response) => {
          this.handleSearchResponse(response);
        },
        error: (error) => {
          this.handleSearchError(error);
        },
        complete: () => {
          this.isSearching = false;
        }
      });
  }

  /**
   * Perform golden question search
   */
  performGoldenQuestionSearch(question: string): void {
    this.isSearching = true;
    this.searchError = null;

    this.searchService.goldenQuestionSearch({ question, max_results: 3 })
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (response) => {
          this.handleSearchResponse(response);
        },
        error: (error) => {
          this.handleSearchError(error);
        },
        complete: () => {
          this.isSearching = false;
        }
      });
  }

  /**
   * Handle successful search response
   */
  private handleSearchResponse(response: SearchResponse): void {
    if (response.success) {
      this.searchResponse = response;
      this.searchResults = response.data.results;
      
      // Log performance for monitoring
      const performance = this.searchService.evaluatePerformance(response);
      console.log(`Search performance: ${performance.status} - ${performance.message}`);
      
    } else {
      this.searchError = 'Search failed: Invalid response';
    }
  }

  /**
   * Handle search error
   */
  private handleSearchError(error: any): void {
    this.searchError = error.message || 'An unexpected error occurred';
    this.searchResults = [];
    this.searchResponse = null;
  }

  /**
   * Tab selection handler
   */
  selectTab(tabIndex: number): void {
    this.selectedTabIndex = tabIndex;
    this.clearResults();
  }

  /**
   * Clear search results
   */
  clearResults(): void {
    this.searchResults = [];
    this.searchResponse = null;
    this.searchError = null;
  }

  /**
   * Mark all form controls as touched to show validation errors
   */
  private markFormGroupTouched(): void {
    Object.keys(this.searchForm.controls).forEach(key => {
      this.searchForm.get(key)?.markAsTouched();
    });
  }

  /**
   * Get formatted citation for display
   */
  formatCitation(result: SearchResult): string {
    return this.searchService.formatCitation(result.citation);
  }

  /**
   * Get code snippet for display
   */
  getCodeSnippet(result: SearchResult): string {
    return this.searchService.getCodeSnippet(result, 200);
  }

  /**
   * Get performance status class for styling
   */
  getPerformanceClass(): string {
    if (!this.searchResponse) return '';
    
    const performance = this.searchService.evaluatePerformance(this.searchResponse);
    return `performance-${performance.status}`;
  }

  /**
   * Get health status class for styling
   */
  getHealthStatusClass(): string {
    if (!this.healthStatus) return 'health-unknown';
    return this.healthStatus.success ? 'health-healthy' : 'health-unhealthy';
  }

  /**
   * Format search time for display
   */
  formatSearchTime(): string {
    if (!this.searchResponse) return '';
    return `${this.searchResponse.data.performance.total_time_ms.toFixed(0)}ms`;
  }

  /**
   * Get RRF fusion details for display
   */
  getFusionDetails(): string {
    if (!this.searchResponse) return '';
    
    const { fusion_details } = this.searchResponse.data;
    return `BM25: ${fusion_details.bm25_results}, k-NN: ${fusion_details.knn_results}, k=${fusion_details.rrf_k}`;
  }

  /**
   * Check if form field has error
   */
  hasFieldError(fieldName: string): boolean {
    const field = this.searchForm.get(fieldName);
    return !!(field && field.invalid && (field.dirty || field.touched));
  }

  /**
   * Get field error message
   */
  getFieldError(fieldName: string): string {
    const field = this.searchForm.get(fieldName);
    if (!field || !field.errors) return '';

    if (field.errors['required']) return `${fieldName} is required`;
    if (field.errors['minlength']) return `${fieldName} is too short`;
    if (field.errors['min']) return `${fieldName} must be at least ${field.errors['min'].min}`;
    if (field.errors['max']) return `${fieldName} must be at most ${field.errors['max'].max}`;

    return 'Invalid input';
  }

  /**
   * Track by function for ngFor performance
   */
  trackByResultId(index: number, result: SearchResult): string {
    return result.id;
  }

  /**
   * Get file icon based on file extension
   */
  getFileIcon(path: string): string {
    const ext = path.split('.').pop()?.toLowerCase();
    switch (ext) {
      case 'java': return 'code';
      case 'jsp': return 'web';
      case 'sql': return 'storage';
      case 'xml': return 'description';
      case 'js': case 'ts': return 'javascript';
      case 'html': return 'html';
      case 'css': case 'scss': return 'style';
      case 'py': return 'code';
      default: return 'insert_drive_file';
    }
  }

  /**
   * Copy citation to clipboard
   */
  copyCitation(result: SearchResult): void {
    const citation = this.formatCitation(result);
    navigator.clipboard.writeText(citation).then(() => {
      // Could add a snackbar notification here
      console.log('Citation copied to clipboard:', citation);
    }).catch(err => {
      console.error('Failed to copy citation:', err);
    });
  }
}