import { Component, OnInit, OnDestroy, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup } from '@angular/forms';
import { Subject, takeUntil, debounceTime, distinctUntilChanged, switchMap } from 'rxjs';
import { MatTabsModule } from '@angular/material/tabs';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatBadgeModule } from '@angular/material/badge';
import { MatDividerModule } from '@angular/material/divider';
import { 
  V1SearchService, 
  SearchResponse, 
  SearchResult 
} from '../../services/v1-search.service';

interface CodeFlowRelation {
  type: 'calls' | 'forwards_to' | 'injects' | 'implements' | 'renders';
  source: string;
  target: string;
  confidence: number;
  line_number: number;
}

interface EnhancedSearchResult extends SearchResult {
  codeFlow?: CodeFlowRelation[];
  generatedQuestions?: string[];
  codeContext?: {
    beforeLines: string[];
    afterLines: string[];
    relatedFiles: string[];
  };
  citationInteractive?: boolean;
}

interface AIGeneratedQuestion {
  question: string;
  confidence: number;
  reasoning: string;
  category: 'architecture' | 'implementation' | 'dependencies' | 'patterns';
}

@Component({
  selector: 'app-enhanced-answer-panel',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatTabsModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    MatIconModule,
    MatCardModule,
    MatChipsModule,
    MatProgressSpinnerModule,
    MatTooltipModule,
    MatExpansionModule,
    MatBadgeModule,
    MatDividerModule
  ],
  templateUrl: './enhanced-answer-panel.component.html',
  styleUrls: ['./enhanced-answer-panel.component.scss']
})
export class EnhancedAnswerPanelComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();
  
  @Input() searchResponse: SearchResponse | null = null;
  @Input() isSearching = false;
  @Output() questionSelected = new EventEmitter<string>();
  @Output() citationClicked = new EventEmitter<SearchResult>();
  @Output() codeFlowRequested = new EventEmitter<SearchResult>();

  enhancedResults: EnhancedSearchResult[] = [];
  generatedQuestions: AIGeneratedQuestion[] = [];
  selectedResult: EnhancedSearchResult | null = null;
  showCodeFlow = false;
  
  expandedResults = new Set<string>();
  bookmarkedResults = new Set<string>();
  
  questionForm: FormGroup;
  isGeneratingQuestions = false;

  constructor(
    private fb: FormBuilder,
    private searchService: V1SearchService
  ) {
    this.questionForm = this.fb.group({
      customQuestion: ['']
    });
  }

  ngOnInit(): void {
    this.setupQuestionGeneration();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  ngOnChanges(): void {
    if (this.searchResponse?.data?.results) {
      this.enhanceSearchResults();
      this.generateFollowUpQuestions();
    }
  }

  /**
   * Setup automatic question generation based on search results
   */
  private setupQuestionGeneration(): void {
    this.questionForm.get('customQuestion')?.valueChanges
      .pipe(
        debounceTime(1000),
        distinctUntilChanged(),
        takeUntil(this.destroy$)
      )
      .subscribe(question => {
        if (question && question.trim().length > 10) {
          this.generateContextualQuestions(question);
        }
      });
  }

  /**
   * Enhance search results with code flow analysis and context
   */
  private enhanceSearchResults(): void {
    if (!this.searchResponse?.data?.results) return;

    this.enhancedResults = this.searchResponse.data.results.map(result => {
      return {
        ...result,
        codeFlow: this.generateCodeFlowRelations(result),
        codeContext: this.extractCodeContext(result),
        citationInteractive: this.shouldMakeCitationInteractive(result),
        generatedQuestions: []
      };
    });
  }

  /**
   * Generate code flow relations using the tracers we built
   */
  private generateCodeFlowRelations(result: SearchResult): CodeFlowRelation[] {
    const relations: CodeFlowRelation[] = [];
    
    // Analyze file type and generate appropriate relations
    const filePath = result.citation.path;
    const fileExt = filePath.split('.').pop()?.toLowerCase();
    
    switch (fileExt) {
      case 'jsp':
        // JSP → Struts action relationships
        relations.push({
          type: 'forwards_to',
          source: filePath,
          target: 'inferred_action',
          confidence: 0.8,
          line_number: result.citation.start
        });
        break;
        
      case 'java':
        if (filePath.includes('Action')) {
          // Struts action → JSP relationships
          relations.push({
            type: 'renders',
            source: filePath,
            target: 'inferred_jsp',
            confidence: 0.7,
            line_number: result.citation.start
          });
        }
        break;
        
      case 'ts':
        if (result.content.includes('@Component')) {
          // Angular component → service relationships
          relations.push({
            type: 'injects',
            source: filePath,
            target: 'inferred_service',
            confidence: 0.9,
            line_number: result.citation.start
          });
        }
        break;
        
      case 'idl':
        // CORBA interface relationships
        relations.push({
          type: 'implements',
          source: filePath,
          target: 'corba_implementation',
          confidence: 0.6,
          line_number: result.citation.start
        });
        break;
    }
    
    return relations;
  }

  /**
   * Extract surrounding code context for better understanding
   */
  private extractCodeContext(result: SearchResult): any {
    // This would typically make an API call to get surrounding lines
    // For now, we'll simulate the context
    return {
      beforeLines: ['// Context before the match', '// ...'],
      afterLines: ['// Context after the match', '// ...'],
      relatedFiles: this.inferRelatedFiles(result)
    };
  }

  /**
   * Infer related files based on code flow analysis
   */
  private inferRelatedFiles(result: SearchResult): string[] {
    const filePath = result.citation.path;
    const relatedFiles: string[] = [];
    
    // Extract potential related files from content
    const content = result.content;
    
    // Look for import statements
    const importMatches = content.match(/import\s+.*?from\s+['"]([^'"]+)['"]/g);
    if (importMatches) {
      importMatches.forEach(match => {
        const pathMatch = match.match(/['"]([^'"]+)['"]/);
        if (pathMatch) {
          relatedFiles.push(pathMatch[1]);
        }
      });
    }
    
    // Look for JSP forward declarations
    const forwardMatches = content.match(/forward\s*=\s*['"]([^'"]+)['"]/g);
    if (forwardMatches) {
      forwardMatches.forEach(match => {
        const pathMatch = match.match(/['"]([^'"]+)['"]/);
        if (pathMatch) {
          relatedFiles.push(pathMatch[1] + '.jsp');
        }
      });
    }
    
    return relatedFiles;
  }

  /**
   * Determine if citation should be interactive
   */
  private shouldMakeCitationInteractive(result: SearchResult): boolean {
    // Make citations interactive for certain file types
    const supportedExts = ['java', 'jsp', 'ts', 'js', 'py'];
    const fileExt = result.citation.path.split('.').pop()?.toLowerCase();
    return supportedExts.includes(fileExt || '');
  }

  /**
   * Generate AI-powered follow-up questions based on search results
   */
  private generateFollowUpQuestions(): void {
    if (!this.searchResponse?.data?.results.length) return;

    this.isGeneratingQuestions = true;
    this.generatedQuestions = [];

    // Analyze search results to generate contextual questions
    const results = this.searchResponse.data.results;
    const query = this.searchResponse.data.query;
    
    // Generate questions based on result patterns
    setTimeout(() => {
      this.generatedQuestions = this.analyzeResultsForQuestions(results, query);
      this.isGeneratingQuestions = false;
    }, 1500); // Simulate AI processing time
  }

  /**
   * Analyze search results to generate intelligent follow-up questions
   */
  private analyzeResultsForQuestions(results: SearchResult[], originalQuery: string): AIGeneratedQuestion[] {
    const questions: AIGeneratedQuestion[] = [];
    
    // Analyze file types in results
    const fileTypes = new Set(results.map(r => r.citation.path.split('.').pop()?.toLowerCase()));
    
    // Architecture questions
    if (fileTypes.has('jsp') && fileTypes.has('java')) {
      questions.push({
        question: "How do JSP pages interact with Java action classes in this codebase?",
        confidence: 0.9,
        reasoning: "Found both JSP and Java files, suggesting MVC pattern",
        category: 'architecture'
      });
    }
    
    if (fileTypes.has('ts') && originalQuery.toLowerCase().includes('component')) {
      questions.push({
        question: "What services does this Angular component depend on?",
        confidence: 0.85,
        reasoning: "Angular component search suggests dependency analysis need",
        category: 'dependencies'
      });
    }
    
    // Implementation questions
    const hasErrorHandling = results.some(r => 
      r.content.toLowerCase().includes('try') || 
      r.content.toLowerCase().includes('catch') ||
      r.content.toLowerCase().includes('exception')
    );
    
    if (hasErrorHandling) {
      questions.push({
        question: "What error handling patterns are used in this implementation?",
        confidence: 0.8,
        reasoning: "Found error handling code in results",
        category: 'implementation'
      });
    }
    
    // Pattern questions
    const hasDatabase = results.some(r => 
      r.content.toLowerCase().includes('sql') ||
      r.content.toLowerCase().includes('database') ||
      r.content.toLowerCase().includes('query')
    );
    
    if (hasDatabase) {
      questions.push({
        question: "What database interaction patterns are being used?",
        confidence: 0.75,
        reasoning: "Database-related code found in search results",
        category: 'patterns'
      });
    }
    
    // Modernization questions based on legacy technologies
    if (fileTypes.has('jsp') || fileTypes.has('idl')) {
      questions.push({
        question: "How could this legacy code be modernized to use current best practices?",
        confidence: 0.7,
        reasoning: "Legacy technologies detected",
        category: 'architecture'
      });
    }
    
    return questions.slice(0, 6); // Limit to 6 questions
  }

  /**
   * Generate contextual questions based on user input
   */
  private generateContextualQuestions(userQuestion: string): void {
    // This would typically call an AI service
    // For now, generate based on keywords
    
    const contextualQuestions: AIGeneratedQuestion[] = [];
    
    if (userQuestion.toLowerCase().includes('how')) {
      contextualQuestions.push({
        question: `What are the implementation details behind: "${userQuestion}"?`,
        confidence: 0.8,
        reasoning: "How-question suggests need for implementation details",
        category: 'implementation'
      });
    }
    
    if (userQuestion.toLowerCase().includes('what')) {
      contextualQuestions.push({
        question: `What are the dependencies and relationships for: "${userQuestion}"?`,
        confidence: 0.75,
        reasoning: "What-question suggests need for relationship analysis",
        category: 'dependencies'
      });
    }
    
    // Add to existing questions
    this.generatedQuestions = [...this.generatedQuestions, ...contextualQuestions];
  }

  /**
   * Toggle result expansion
   */
  toggleResultExpansion(resultId: string): void {
    if (this.expandedResults.has(resultId)) {
      this.expandedResults.delete(resultId);
    } else {
      this.expandedResults.add(resultId);
    }
  }

  /**
   * Check if result is expanded
   */
  isResultExpanded(resultId: string): boolean {
    return this.expandedResults.has(resultId);
  }

  /**
   * Toggle bookmark for result
   */
  toggleBookmark(resultId: string): void {
    if (this.bookmarkedResults.has(resultId)) {
      this.bookmarkedResults.delete(resultId);
    } else {
      this.bookmarkedResults.add(resultId);
    }
  }

  /**
   * Check if result is bookmarked
   */
  isBookmarked(resultId: string): boolean {
    return this.bookmarkedResults.has(resultId);
  }

  /**
   * Handle generated question selection
   */
  selectGeneratedQuestion(question: AIGeneratedQuestion): void {
    this.questionSelected.emit(question.question);
  }

  /**
   * Handle citation click for interactive citations
   */
  onCitationClick(result: EnhancedSearchResult): void {
    if (result.citationInteractive) {
      this.citationClicked.emit(result);
    }
  }

  /**
   * Request code flow visualization
   */
  requestCodeFlow(result: EnhancedSearchResult): void {
    this.codeFlowRequested.emit(result);
    this.selectedResult = result;
    this.showCodeFlow = true;
  }

  /**
   * Get icon for file type
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
      case 'idl': return 'api';
      default: return 'insert_drive_file';
    }
  }

  /**
   * Get icon for code flow relation type
   */
  getFlowIcon(type: string): string {
    switch (type) {
      case 'calls': return 'call';
      case 'forwards_to': return 'arrow_forward';
      case 'injects': return 'input';
      case 'implements': return 'extension';
      case 'renders': return 'visibility';
      default: return 'link';
    }
  }

  /**
   * Get color class for question category
   */
  getQuestionCategoryClass(category: string): string {
    switch (category) {
      case 'architecture': return 'category-architecture';
      case 'implementation': return 'category-implementation';
      case 'dependencies': return 'category-dependencies';
      case 'patterns': return 'category-patterns';
      default: return 'category-default';
    }
  }

  /**
   * Format citation with enhanced display
   */
  formatEnhancedCitation(result: EnhancedSearchResult): string {
    const citation = this.searchService.formatCitation(result.citation);
    const relatedCount = result.codeContext?.relatedFiles?.length || 0;
    return relatedCount > 0 ? `${citation} (+${relatedCount} related)` : citation;
  }

  /**
   * Get confidence indicator class
   */
  getConfidenceClass(confidence: number): string {
    if (confidence >= 0.8) return 'confidence-high';
    if (confidence >= 0.6) return 'confidence-medium';
    return 'confidence-low';
  }

  /**
   * Submit custom question
   */
  submitCustomQuestion(): void {
    const question = this.questionForm.get('customQuestion')?.value;
    if (question?.trim()) {
      this.questionSelected.emit(question.trim());
      this.questionForm.reset();
    }
  }

  /**
   * Track by function for performance
   */
  trackByResultId(index: number, result: EnhancedSearchResult): string {
    return result.id;
  }

  /**
   * Track by function for questions
   */
  trackByQuestionText(index: number, question: AIGeneratedQuestion): string {
    return question.question;
  }
}