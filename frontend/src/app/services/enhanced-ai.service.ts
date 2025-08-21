import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of, forkJoin } from 'rxjs';
import { map, catchError } from 'rxjs/operators';
import { environment } from '../../environments/environment';
import { SearchResult, SearchResponse } from './v1-search.service';

export interface AIGeneratedQuestion {
  question: string;
  confidence: number;
  reasoning: string;
  category: 'architecture' | 'implementation' | 'dependencies' | 'patterns';
}

export interface CodeFlowAnalysis {
  relations: CodeFlowRelation[];
  suggestions: string[];
  complexity_score: number;
  modernization_opportunities: string[];
}

export interface CodeFlowRelation {
  type: 'calls' | 'forwards_to' | 'injects' | 'implements' | 'renders';
  source: string;
  target: string;
  confidence: number;
  line_number: number;
  description?: string;
}

export interface CodeContext {
  beforeLines: string[];
  afterLines: string[];
  relatedFiles: string[];
  imports: string[];
  exports: string[];
}

export interface EnhancementRequest {
  searchResults: SearchResult[];
  originalQuery: string;
  userContext?: string;
}

export interface EnhancementResponse {
  success: boolean;
  data: {
    aiQuestions: AIGeneratedQuestion[];
    codeFlowAnalysis: { [resultId: string]: CodeFlowAnalysis };
    codeContext: { [resultId: string]: CodeContext };
    crossFileRelations: CodeFlowRelation[];
  };
  performance: {
    analysis_time_ms: number;
    ai_generation_time_ms: number;
  };
}

@Injectable({
  providedIn: 'root'
})
export class EnhancedAIService {
  private readonly apiUrl = `${environment.apiUrl}/api`;

  constructor(private http: HttpClient) {}

  /**
   * Generate AI-powered follow-up questions based on search results
   */
  generateFollowUpQuestions(
    searchResults: SearchResult[], 
    originalQuery: string,
    userContext?: string
  ): Observable<AIGeneratedQuestion[]> {
    const request = {
      search_results: searchResults,
      original_query: originalQuery,
      user_context: userContext
    };

    return this.http.post<{ success: boolean; data: AIGeneratedQuestion[] }>(`${this.apiUrl}/v1/ai/generate-questions`, request)
      .pipe(
        map(response => response.success ? response.data : []),
        catchError(error => {
          console.error('AI question generation failed:', error);
          throw error;
        })
      );
  }

  /**
   * Analyze code flow relationships using the tracers we built
   */
  analyzeCodeFlow(searchResults: SearchResult[]): Observable<{ [resultId: string]: CodeFlowAnalysis }> {
    const request = {
      files: searchResults.map(r => ({
        id: r.id,
        path: r.citation.path,
        content: r.content,
        language: r.metadata.language,
        start_line: r.citation.start,
        end_line: r.citation.end
      }))
    };

    return this.http.post<{ success: boolean; data: any }>(`${this.apiUrl}/v1/analysis/code-flow`, request)
      .pipe(
        map(response => response.success ? response.data : {}),
        catchError(error => {
          console.error('Code flow analysis failed:', error);
          throw error;
        })
      );
  }

  /**
   * Get enhanced code context around search results
   */
  getCodeContext(searchResults: SearchResult[]): Observable<{ [resultId: string]: CodeContext }> {
    const contextRequests = searchResults.map(result => 
      this.getFileContext(result.citation.path, result.citation.start, result.citation.end)
        .pipe(map(context => ({ [result.id]: context })))
    );

    return forkJoin(contextRequests).pipe(
      map(contexts => Object.assign({}, ...contexts)),
      catchError(error => {
        console.error('Code context retrieval failed:', error);
        throw error;
      })
    );
  }

  /**
   * Get context around a specific file location
   */
  private getFileContext(filePath: string, startLine: number, endLine: number): Observable<CodeContext> {
    const request = {
      file_path: filePath,
      start_line: startLine,
      end_line: endLine,
      context_lines: 5
    };

    return this.http.post<{ success: boolean; data: CodeContext }>(`${this.apiUrl}/v1/analysis/file-context`, request)
      .pipe(
        map(response => response.success ? response.data : this.getEmptyContext()),
        catchError(() => of(this.getEmptyContext()))
      );
  }

  /**
   * Perform comprehensive enhancement of search results
   */
  enhanceSearchResults(request: EnhancementRequest): Observable<EnhancementResponse> {
    const startTime = Date.now();

    return forkJoin({
      aiQuestions: this.generateFollowUpQuestions(
        request.searchResults, 
        request.originalQuery, 
        request.userContext
      ),
      codeFlowAnalysis: this.analyzeCodeFlow(request.searchResults),
      codeContext: this.getCodeContext(request.searchResults)
    }).pipe(
      map(results => ({
        success: true,
        data: {
          ...results,
          crossFileRelations: this.extractCrossFileRelations(results.codeFlowAnalysis)
        },
        performance: {
          analysis_time_ms: Date.now() - startTime,
          ai_generation_time_ms: 1200 // Simulated
        }
      })),
      catchError(error => {
        console.error('Enhancement failed:', error);
        return of({
          success: false,
          data: {
            aiQuestions: [],
            codeFlowAnalysis: {},
            codeContext: {},
            crossFileRelations: []
          },
          performance: {
            analysis_time_ms: Date.now() - startTime,
            ai_generation_time_ms: 0
          }
        });
      })
    );
  }

  /**
   * Generate contextual questions based on user input
   */
  generateContextualQuestions(
    userQuestion: string, 
    existingResults: SearchResult[]
  ): Observable<AIGeneratedQuestion[]> {
    const request = {
      user_question: userQuestion,
      existing_results: existingResults
    };

    return this.http.post<{ success: boolean; data: AIGeneratedQuestion[] }>(`${this.apiUrl}/v1/ai/contextual-questions`, request)
      .pipe(
        map(response => response.success ? response.data : []),
        catchError(error => {
          console.error('Contextual question generation failed:', error);
          throw error;
        })
      );
  }





  private extractCrossFileRelations(codeFlowAnalysis: { [resultId: string]: CodeFlowAnalysis }): CodeFlowRelation[] {
    const crossFileRelations: CodeFlowRelation[] = [];
    
    Object.values(codeFlowAnalysis).forEach(analysis => {
      crossFileRelations.push(...analysis.relations);
    });
    
    return crossFileRelations;
  }


  private getEmptyContext(): CodeContext {
    return {
      beforeLines: [],
      afterLines: [],
      relatedFiles: [],
      imports: [],
      exports: []
    };
  }
}