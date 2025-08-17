import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of, forkJoin } from 'rxjs';
import { map, catchError, delay } from 'rxjs/operators';
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
  private readonly apiUrl = environment.production ? 
    'http://localhost:8000/api' : 
    'http://localhost:8000/api';

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

    // For now, simulate AI generation with intelligent analysis
    // In production, this would call a real AI service
    return of(this.simulateAIQuestionGeneration(searchResults, originalQuery))
      .pipe(
        delay(1200), // Simulate AI processing time
        catchError(error => {
          console.error('AI question generation failed:', error);
          return of(this.getFallbackQuestions(searchResults, originalQuery));
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
          return of(this.simulateCodeFlowAnalysis(searchResults));
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
        return of(this.simulateCodeContext(searchResults));
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
            aiQuestions: this.getFallbackQuestions(request.searchResults, request.originalQuery),
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
    return of(this.analyzeUserQuestionForContext(userQuestion, existingResults))
      .pipe(delay(800)); // Simulate processing
  }

  /**
   * Simulate AI question generation with intelligent analysis
   */
  private simulateAIQuestionGeneration(
    results: SearchResult[], 
    originalQuery: string
  ): AIGeneratedQuestion[] {
    const questions: AIGeneratedQuestion[] = [];
    
    // Analyze file types and patterns
    const fileTypes = new Set(results.map(r => r.citation.path.split('.').pop()?.toLowerCase()));
    const languages = new Set(results.map(r => r.metadata.language));
    const hasMultipleRepos = new Set(results.map(r => r.metadata.repo_id)).size > 1;
    
    // Architecture questions
    if (fileTypes.has('jsp') && fileTypes.has('java')) {
      questions.push({
        question: "How does the MVC architecture flow from JSP views to Java controllers in this system?",
        confidence: 0.92,
        reasoning: "Found JSP and Java files indicating classic MVC pattern",
        category: 'architecture'
      });
    }
    
    if (fileTypes.has('ts') && originalQuery.toLowerCase().includes('component')) {
      questions.push({
        question: "What Angular services and dependencies does this component hierarchy require?",
        confidence: 0.88,
        reasoning: "Angular component query suggests dependency analysis need",
        category: 'dependencies'
      });
    }
    
    if (fileTypes.has('idl')) {
      questions.push({
        question: "How can these CORBA interfaces be modernized to RESTful APIs?",
        confidence: 0.75,
        reasoning: "CORBA IDL files suggest legacy system modernization opportunity",
        category: 'architecture'
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
        question: "What error handling and recovery patterns are implemented across these components?",
        confidence: 0.83,
        reasoning: "Multiple files show error handling implementations",
        category: 'implementation'
      });
    }
    
    // Pattern questions
    const hasAsync = results.some(r => 
      r.content.toLowerCase().includes('async') ||
      r.content.toLowerCase().includes('promise') ||
      r.content.toLowerCase().includes('observable')
    );
    
    if (hasAsync) {
      questions.push({
        question: "How are asynchronous operations coordinated and what concurrency patterns are used?",
        confidence: 0.78,
        reasoning: "Asynchronous code patterns detected",
        category: 'patterns'
      });
    }
    
    // Cross-repository questions
    if (hasMultipleRepos) {
      questions.push({
        question: "How do these components interact across different repositories and what integration challenges exist?",
        confidence: 0.81,
        reasoning: "Multiple repositories suggest distributed system architecture",
        category: 'dependencies'
      });
    }
    
    // Language-specific questions
    if (languages.has('Python') && languages.has('JavaScript')) {
      questions.push({
        question: "How is data exchanged between the Python backend and JavaScript frontend?",
        confidence: 0.85,
        reasoning: "Full-stack implementation with Python and JavaScript",
        category: 'implementation'
      });
    }
    
    return questions.slice(0, 6); // Limit to 6 high-quality questions
  }

  /**
   * Simulate code flow analysis
   */
  private simulateCodeFlowAnalysis(results: SearchResult[]): { [resultId: string]: CodeFlowAnalysis } {
    const analysis: { [resultId: string]: CodeFlowAnalysis } = {};
    
    results.forEach(result => {
      const filePath = result.citation.path;
      const fileExt = filePath.split('.').pop()?.toLowerCase();
      const relations: CodeFlowRelation[] = [];
      
      // Generate relations based on file type and content
      switch (fileExt) {
        case 'jsp':
          relations.push({
            type: 'forwards_to',
            source: filePath,
            target: this.inferActionFromJSP(result.content),
            confidence: 0.8,
            line_number: result.citation.start,
            description: 'JSP form submits to Struts action'
          });
          break;
          
        case 'java':
          if (filePath.includes('Action')) {
            relations.push({
              type: 'renders',
              source: filePath,
              target: this.inferJSPFromAction(result.content),
              confidence: 0.75,
              line_number: result.citation.start,
              description: 'Action forwards to JSP view'
            });
          }
          break;
          
        case 'ts':
          if (result.content.includes('@Component')) {
            relations.push({
              type: 'injects',
              source: filePath,
              target: this.inferServiceFromComponent(result.content),
              confidence: 0.9,
              line_number: result.citation.start,
              description: 'Component injects service dependency'
            });
          }
          break;
      }
      
      analysis[result.id] = {
        relations,
        suggestions: this.generateCodeSuggestions(result),
        complexity_score: this.calculateComplexityScore(result),
        modernization_opportunities: this.identifyModernizationOpportunities(result)
      };
    });
    
    return analysis;
  }

  /**
   * Simulate code context
   */
  private simulateCodeContext(results: SearchResult[]): { [resultId: string]: CodeContext } {
    const context: { [resultId: string]: CodeContext } = {};
    
    results.forEach(result => {
      context[result.id] = {
        beforeLines: ['// Context before the match', '// Additional setup code'],
        afterLines: ['// Context after the match', '// Cleanup or follow-up code'],
        relatedFiles: this.inferRelatedFiles(result),
        imports: this.extractImports(result.content),
        exports: this.extractExports(result.content)
      };
    });
    
    return context;
  }

  /**
   * Helper methods for content analysis
   */
  private inferActionFromJSP(content: string): string {
    const actionMatch = content.match(/action\s*=\s*['"]([^'"]+)['"]/);
    return actionMatch ? actionMatch[1] : 'unknown_action';
  }

  private inferJSPFromAction(content: string): string {
    const forwardMatch = content.match(/forward\s*=\s*['"]([^'"]+)['"]/);
    return forwardMatch ? forwardMatch[1] + '.jsp' : 'unknown_view.jsp';
  }

  private inferServiceFromComponent(content: string): string {
    const serviceMatch = content.match(/constructor\([^)]*(\w+Service)[^)]*/);
    return serviceMatch ? serviceMatch[1] : 'unknown_service';
  }

  private inferRelatedFiles(result: SearchResult): string[] {
    const relatedFiles: string[] = [];
    const content = result.content;
    
    // Extract import statements
    const importMatches = content.match(/import\s+.*?from\s+['"]([^'"]+)['"]/g);
    if (importMatches) {
      importMatches.forEach(match => {
        const pathMatch = match.match(/['"]([^'"]+)['"]/);
        if (pathMatch) {
          relatedFiles.push(pathMatch[1]);
        }
      });
    }
    
    return relatedFiles;
  }

  private extractImports(content: string): string[] {
    const imports: string[] = [];
    const importMatches = content.match(/import\s+[^;]+;/g);
    if (importMatches) {
      imports.push(...importMatches);
    }
    return imports;
  }

  private extractExports(content: string): string[] {
    const exports: string[] = [];
    const exportMatches = content.match(/export\s+[^;]+;/g);
    if (exportMatches) {
      exports.push(...exportMatches);
    }
    return exports;
  }

  private generateCodeSuggestions(result: SearchResult): string[] {
    const suggestions: string[] = [];
    
    if (result.content.includes('TODO')) {
      suggestions.push('Contains TODO items that need attention');
    }
    
    if (!result.content.includes('try') && result.content.includes('Exception')) {
      suggestions.push('Consider adding proper error handling');
    }
    
    return suggestions;
  }

  private calculateComplexityScore(result: SearchResult): number {
    let score = 1;
    score += (result.content.match(/if\s*\(/g) || []).length;
    score += (result.content.match(/for\s*\(/g) || []).length;
    score += (result.content.match(/while\s*\(/g) || []).length;
    return Math.min(score, 10);
  }

  private identifyModernizationOpportunities(result: SearchResult): string[] {
    const opportunities: string[] = [];
    
    if (result.citation.path.includes('.jsp')) {
      opportunities.push('Consider migrating JSP to modern template engine or SPA');
    }
    
    if (result.content.includes('CORBA')) {
      opportunities.push('Modernize CORBA interfaces to REST APIs');
    }
    
    return opportunities;
  }

  private extractCrossFileRelations(codeFlowAnalysis: { [resultId: string]: CodeFlowAnalysis }): CodeFlowRelation[] {
    const crossFileRelations: CodeFlowRelation[] = [];
    
    Object.values(codeFlowAnalysis).forEach(analysis => {
      crossFileRelations.push(...analysis.relations);
    });
    
    return crossFileRelations;
  }

  private analyzeUserQuestionForContext(
    userQuestion: string, 
    existingResults: SearchResult[]
  ): AIGeneratedQuestion[] {
    const contextualQuestions: AIGeneratedQuestion[] = [];
    
    if (userQuestion.toLowerCase().includes('how')) {
      contextualQuestions.push({
        question: `What are the step-by-step implementation details for: "${userQuestion}"?`,
        confidence: 0.85,
        reasoning: "How-question suggests need for detailed implementation walkthrough",
        category: 'implementation'
      });
    }
    
    if (userQuestion.toLowerCase().includes('what')) {
      contextualQuestions.push({
        question: `What dependencies and relationships are involved in: "${userQuestion}"?`,
        confidence: 0.8,
        reasoning: "What-question suggests need for comprehensive relationship analysis",
        category: 'dependencies'
      });
    }
    
    if (userQuestion.toLowerCase().includes('why')) {
      contextualQuestions.push({
        question: `What architectural decisions led to the approach in: "${userQuestion}"?`,
        confidence: 0.75,
        reasoning: "Why-question suggests need for architectural reasoning analysis",
        category: 'architecture'
      });
    }
    
    return contextualQuestions;
  }

  private getFallbackQuestions(results: SearchResult[], originalQuery: string): AIGeneratedQuestion[] {
    return [
      {
        question: "What are the main components and their responsibilities in this codebase?",
        confidence: 0.7,
        reasoning: "General architectural overview question",
        category: 'architecture'
      },
      {
        question: "How are errors handled and what recovery mechanisms exist?",
        confidence: 0.65,
        reasoning: "Important implementation detail",
        category: 'implementation'
      }
    ];
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