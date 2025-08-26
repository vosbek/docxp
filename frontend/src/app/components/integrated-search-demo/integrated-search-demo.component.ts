import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Subject, takeUntil } from 'rxjs';
import { MatTabsModule } from '@angular/material/tabs';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatCardModule } from '@angular/material/card';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatChipsModule } from '@angular/material/chips';

// Import both components
import { V1SearchComponent } from '../v1-search/v1-search.component';
import { EnhancedAnswerPanelComponent } from '../enhanced-answer-panel/enhanced-answer-panel.component';

// Import services
import { V1SearchService, SearchResponse, SearchResult } from '../../services/v1-search.service';
import { EnhancedAIService, AIGeneratedQuestion } from '../../services/enhanced-ai.service';

@Component({
  selector: 'app-integrated-search-demo',
  standalone: true,
  imports: [
    CommonModule,
    MatTabsModule,
    MatButtonModule,
    MatIconModule,
    MatCardModule,
    MatProgressBarModule,
    MatChipsModule,
    V1SearchComponent,
    EnhancedAnswerPanelComponent
  ],
  templateUrl: './integrated-search-demo.component.html',
  styleUrls: ['./integrated-search-demo.component.scss']
})
export class IntegratedSearchDemoComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();
  
  // Search state
  currentSearchResponse: SearchResponse | null = null;
  isSearching = false;
  searchHistory: Array<{ query: string; timestamp: Date; resultCount: number }> = [];
  
  // Enhanced features state
  isEnhancing = false;
  enhancementProgress = 0;
  showEnhancedPanel = false;
  
  // Production mode - no demo functionality

  constructor(
    private searchService: V1SearchService,
    private aiService: EnhancedAIService
  ) {}

  ngOnInit(): void {
    // Initialize state
    this.loadSearchHistory();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  /**
   * Handle search completion from V1 search component
   */
  onSearchComplete(response: SearchResponse): void {
    this.currentSearchResponse = response;
    this.isSearching = false;
    
    // Update search history
    this.addToSearchHistory(response.data.query, response.data.results.length);
    
    // Automatically enhance results
    this.enhanceResults();
  }

  /**
   * Handle search start
   */
  onSearchStart(): void {
    this.isSearching = true;
    this.showEnhancedPanel = false;
    this.enhancementProgress = 0;
  }

  /**
   * Enhance search results with AI analysis
   */
  private enhanceResults(): void {
    if (!this.currentSearchResponse?.data?.results?.length) return;
    
    this.isEnhancing = true;
    this.enhancementProgress = 0;
    
    // Simulate enhancement progress
    const progressInterval = setInterval(() => {
      this.enhancementProgress += 15;
      if (this.enhancementProgress >= 100) {
        clearInterval(progressInterval);
        this.completeEnhancement();
      }
    }, 200);
  }

  /**
   * Complete enhancement process
   */
  private completeEnhancement(): void {
    this.isEnhancing = false;
    this.showEnhancedPanel = true;
  }

  /**
   * Handle AI question selection
   */
  onQuestionSelected(question: string): void {
    // Trigger new search with the AI-generated question
    this.performEnhancedSearch(question);
  }

  /**
   * Handle citation click for interactive exploration
   */
  onCitationClicked(result: SearchResult): void {
    // Open a detailed file view or code explorer
    console.log('Opening detailed view for:', result.citation);
    
    // TODO: Implement actual file view functionality
    // Placeholder: show file path info
    alert(`Opening detailed view for ${result.citation.path}:${result.citation.start}-${result.citation.end}`);
  }

  /**
   * Handle code flow visualization request
   */
  onCodeFlowRequested(result: SearchResult): void {
    // Open an interactive code flow diagram
    console.log('Showing code flow for:', result.citation);
    
    // TODO: Implement actual code flow visualization
    // Placeholder: show code flow info
    alert(`Visualizing code flow relationships for ${result.citation.path}`);
  }

  /**
   * Perform enhanced search with AI question
   */
  private performEnhancedSearch(question: string): void {
    // This would trigger a new search in the V1 component
    // For now, just simulate it
    console.log('Performing enhanced search for:', question);
  }

  /**
   * Add search to history
   */
  private addToSearchHistory(query: string, resultCount: number): void {
    this.searchHistory.unshift({
      query,
      timestamp: new Date(),
      resultCount
    });
    
    // Keep only last 10 searches
    if (this.searchHistory.length > 10) {
      this.searchHistory = this.searchHistory.slice(0, 10);
    }
    
    this.saveSearchHistory();
  }

  /**
   * Load search history from localStorage
   */
  private loadSearchHistory(): void {
    try {
      const stored = localStorage.getItem('docxp_search_history');
      if (stored) {
        this.searchHistory = JSON.parse(stored).map((item: any) => ({
          ...item,
          timestamp: new Date(item.timestamp)
        }));
      }
    } catch (error) {
      console.warn('Failed to load search history:', error);
      this.searchHistory = [];
    }
  }

  /**
   * Save search history to localStorage
   */
  private saveSearchHistory(): void {
    try {
      localStorage.setItem('docxp_search_history', JSON.stringify(this.searchHistory));
    } catch (error) {
      console.warn('Failed to save search history:', error);
    }
  }

  /**
   * Reset search interface
   */
  resetSearch(): void {
    this.currentSearchResponse = null;
    this.showEnhancedPanel = false;
    this.isEnhancing = false;
    this.enhancementProgress = 0;
  }

  /**
   * Format time for display
   */
  formatTime(date: Date): string {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  /**
   * Repeat previous search
   */
  repeatSearch(historyItem: any): void {
    // This would trigger the search again
    console.log('Repeating search:', historyItem.query);
  }

  /**
   * Clear search history
   */
  clearHistory(): void {
    this.searchHistory = [];
    this.saveSearchHistory();
  }

  /**
   * Get search result summary
   */
  getSearchSummary(): string {
    if (!this.currentSearchResponse) return '';
    
    const { data } = this.currentSearchResponse;
    const fileTypes = new Set(data.results.map(r => r.citation.path.split('.').pop()));
    const repos = new Set(data.results.map(r => r.metadata.repo_id));
    
    return `${data.results.length} results across ${repos.size} repositories, ${fileTypes.size} file types`;
  }

  /**
   * Get performance summary
   */
  getPerformanceSummary(): string {
    if (!this.currentSearchResponse) return '';
    
    const perf = this.currentSearchResponse.data.performance;
    const fusion = this.currentSearchResponse.data.fusion_details;
    
    return `${perf.total_time_ms.toFixed(0)}ms (BM25: ${fusion.bm25_results}, k-NN: ${fusion.knn_results})`;
  }
}