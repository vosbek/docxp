import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';
import { environment } from '../../environments/environment';
import { StrandsAgentsService, AgentType } from './strands-agents.service';
import { LoggingService } from './logging.service';

export interface ChatResponse {
  content: string;
  metadata?: {
    repositoryName?: string;
    fileReferences?: string[];
    codeSnippets?: any[];
    analysisType?: 'single-repo' | 'cross-repo' | 'migration-analysis' | 'semantic-search' | 'strands-agent' | 'strands-agent-continuation';
    semanticContext?: {
      similar_patterns_found?: number;
      context_sources?: Array<{
        file: string;
        similarity: number;
        type: string;
      }>;
    };
    // Strands agent specific metadata
    agent_type?: string;
    confidence?: number;
    session_id?: string;
    suggested_actions?: string[];
    followup_questions?: string[];
    reasoning?: string;
    tool_calls?: any[];
    conversation_length?: number;
  };
}

export interface SemanticSearchResult {
  id: string;
  content: string;
  metadata: any;
  similarity_score: number;
  collection: string;
}

export interface ConversationContext {
  repositoryIds?: string[];
  analysisMode?: 'quick' | 'detailed' | 'migration-focused';
  previousQueries?: string[];
}

@Injectable({
  providedIn: 'root'
})
export class ChatService {
  private readonly baseUrl = environment.apiUrl;
  private conversationContext = new BehaviorSubject<ConversationContext>({});
  
  public context$ = this.conversationContext.asObservable();

  constructor(
    private http: HttpClient,
    private strandsService: StrandsAgentsService,
    private logger: LoggingService
  ) {}

  /**
   * Send a message to the AI assistant
   */
  async sendMessage(message: string, context?: ConversationContext): Promise<ChatResponse> {
    try {
      // Check if Strands Agents is available for enhanced conversational AI
      if (this.strandsService.isAvailable()) {
        return this.sendStrandsMessage(message, context);
      }
      
      // Try semantic search for enhanced responses
      const semanticResults = await this.performSemanticSearch(message);
      
      if (semanticResults && semanticResults.length > 0) {
        return this.generateSemanticResponse(message, semanticResults);
      }
      
      // No fallback - throw error if no service available
      throw new Error('No AI service available. Please ensure Strands Agents or Semantic Search services are running.');
    } catch (error) {
      console.error('Chat service error:', error);
      // Re-throw error without fallback
      throw error;
    }
  }

  /**
   * Send message using Strands Agents for enhanced conversational AI
   */
  private async sendStrandsMessage(message: string, context?: ConversationContext): Promise<ChatResponse> {
    try {
      // Determine the best agent for the query
      const agentType = this.strandsService.suggestAgentForQuery(message);
      
      // Create conversation request
      const request = this.strandsService.createConversationRequest(
        message,
        agentType,
        context?.repositoryIds,
        context?.analysisMode ? { analysis_mode: context.analysisMode } : undefined
      );
      
      // Start conversation with the appropriate agent
      const agentResponse = await this.strandsService.startConversation(request).toPromise();
      
      if (agentResponse) {
        // Track the conversation
        if (agentResponse.metadata && agentResponse.metadata['session_id']) {
          this.strandsService.addActiveConversation(agentResponse.metadata['session_id']);
        }
        
        // Convert to ChatResponse format
        return {
          content: agentResponse.content,
          metadata: {
            analysisType: 'strands-agent',
            agent_type: agentResponse.agent_type,
            confidence: agentResponse.confidence,
            session_id: agentResponse.metadata ? agentResponse.metadata['session_id'] : undefined,
            suggested_actions: agentResponse.suggested_actions,
            followup_questions: agentResponse.followup_questions,
            reasoning: agentResponse.reasoning,
            tool_calls: agentResponse.tool_calls
          }
        };
      }
      
      throw new Error('No response from Strands agent');
      
    } catch (error) {
      console.warn('Strands agent response failed:', error);
      throw error;
    }
  }

  /**
   * Perform semantic search across code entities and business rules
   */
  async performSemanticSearch(query: string): Promise<SemanticSearchResult[]> {
    try {
      const response = await this.http.post<{success: boolean, data: any}>(`${this.baseUrl}/api/semantic/search`, {
        query: query,
        collections: ['code_entities', 'business_rules', 'documentation'],
        max_results: 10
      }).toPromise();

      if (response?.success && response.data?.top_results) {
        return response.data.top_results;
      }
      
      return [];
    } catch (error) {
      console.warn('Semantic search not available, falling back to simulation:', error);
      return [];
    }
  }

  /**
   * Generate response based on semantic search results
   */
  private generateSemanticResponse(query: string, results: SemanticSearchResult[]): ChatResponse {
    const codeEntities = results.filter(r => r.collection === 'code_entities');
    const businessRules = results.filter(r => r.collection === 'business_rules');
    const documentation = results.filter(r => r.collection === 'documentation');

    let content = `🔍 **Semantic Analysis Results for: "${query}"**\n\n`;

    if (codeEntities.length > 0) {
      content += `### 📁 Related Code Entities (${codeEntities.length} found):\n`;
      codeEntities.slice(0, 3).forEach((entity, index) => {
        const meta = entity.metadata;
        content += `${index + 1}. **${meta.name || 'Unknown'}** (${meta.type || 'Unknown'})\n`;
        content += `   📄 File: \`${meta.file_path || 'Unknown'}\`\n`;
        content += `   🎯 Similarity: ${(entity.similarity_score * 100).toFixed(1)}%\n\n`;
      });
    }

    if (businessRules.length > 0) {
      content += `### 📋 Related Business Rules (${businessRules.length} found):\n`;
      businessRules.slice(0, 2).forEach((rule, index) => {
        const meta = rule.metadata;
        content += `${index + 1}. **${meta.description ? meta.description.substring(0, 100) + '...' : 'Business Rule'}\n`;
        content += `   🎯 Similarity: ${(rule.similarity_score * 100).toFixed(1)}%\n\n`;
      });
    }

    if (documentation.length > 0) {
      content += `### 📚 Related Documentation (${documentation.length} found):\n`;
      documentation.slice(0, 2).forEach((doc, index) => {
        content += `${index + 1}. Documentation match found\n`;
        content += `   🎯 Similarity: ${(doc.similarity_score * 100).toFixed(1)}%\n\n`;
      });
    }

    if (results.length === 0) {
      content += `No semantic matches found. This might be a new concept or the vector database may need more content indexed.\n\n`;
      content += `💡 **Suggestions:**\n`;
      content += `• Try more specific technical terms\n`;
      content += `• Ask about specific file names or class names\n`;
      content += `• Use technology-specific keywords (e.g., "Struts", "CORBA", "Oracle")\n`;
    }

    return {
      content,
      metadata: {
        analysisType: 'semantic-search',
        fileReferences: codeEntities.map(e => e.metadata.file_path).filter(Boolean),
        semanticContext: {
          similar_patterns_found: results.length,
          context_sources: results.slice(0, 5).map(r => ({
            file: r.metadata.file_path || r.metadata.name || 'Unknown',
            similarity: r.similarity_score,
            type: r.metadata.type || r.collection
          }))
        }
      }
    };
  }

  /**
   * Update conversation context (selected repositories, analysis mode, etc.)
   */
  updateContext(context: Partial<ConversationContext>) {
    const currentContext = this.conversationContext.value;
    this.conversationContext.next({ ...currentContext, ...context });
  }

  /**
   * Get current conversation context
   */
  getContext(): ConversationContext {
    return this.conversationContext.value;
  }

  /**
   * Clear conversation context
   */
  clearContext() {
    this.conversationContext.next({});
  }


  /**
   * Continue a Strands conversation with a specific session
   */
  async continueStrandsConversation(
    sessionId: string, 
    message: string, 
    agentType?: AgentType
  ): Promise<ChatResponse> {
    try {
      const request = {
        message,
        agent_type: agentType
      };
      
      const agentResponse = await this.strandsService.continueConversation(sessionId, request).toPromise();
      
      if (agentResponse) {
        return {
          content: agentResponse.content,
          metadata: {
            analysisType: 'strands-agent-continuation',
            agent_type: agentResponse.agent_type,
            confidence: agentResponse.confidence,
            session_id: sessionId,
            suggested_actions: agentResponse.suggested_actions,
            followup_questions: agentResponse.followup_questions,
            reasoning: agentResponse.reasoning,
            conversation_length: agentResponse.metadata ? agentResponse.metadata['conversation_length'] : undefined
          }
        };
      }
      
      throw new Error('No response from Strands agent continuation');
      
    } catch (error) {
      console.error('Strands conversation continuation failed:', error);
      throw error;
    }
  }

  /**
   * Get Strands service health and availability
   */
  async getStrandsHealth(): Promise<any> {
    return this.strandsService.checkAgentHealth().toPromise();
  }

  /**
   * Get available Strands agents
   */
  async getAvailableAgents(): Promise<any> {
    return this.strandsService.getAvailableAgents().toPromise();
  }

  /**
   * End a Strands conversation session
   */
  async endStrandsConversation(sessionId: string): Promise<void> {
    try {
      await this.strandsService.endConversation(sessionId).toPromise();
      this.strandsService.removeActiveConversation(sessionId);
    } catch (error) {
      console.error('Failed to end Strands conversation:', error);
    }
  }

  /**
   * Check if enhanced AI (Strands) is available
   */
  isEnhancedAIAvailable(): boolean {
    return this.strandsService.isAvailable();
  }

  /**
   * Get installation instructions for enhanced AI
   */
  getEnhancedAIInstructions(): string[] {
    return this.strandsService.getInstallationInstructions();
  }

  /**
   * Suggest the best agent type for a query
   */
  suggestAgentForQuery(query: string): AgentType {
    return this.strandsService.suggestAgentForQuery(query);
  }
}