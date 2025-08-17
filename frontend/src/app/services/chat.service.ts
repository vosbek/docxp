import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';
import { environment } from '../../environments/environment';
import { StrandsAgentsService, AgentType } from './strands-agents.service';

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
  private readonly baseUrl = environment.apiUrl || 'http://localhost:8000';
  private conversationContext = new BehaviorSubject<ConversationContext>({});
  
  public context$ = this.conversationContext.asObservable();

  constructor(
    private http: HttpClient,
    private strandsService: StrandsAgentsService
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
      
      // Fallback to simulated response for development
      return this.simulateResponse(message);
    } catch (error) {
      console.error('Chat service error:', error);
      // Fallback to simulation if all other methods fail
      return this.simulateResponse(message);
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
   * Simulate AI response for development/demo purposes
   * This will be replaced with actual API calls once backend is implemented
   */
  private async simulateResponse(message: string): Promise<ChatResponse> {
    // Simulate API delay
    await this.delay(1500 + Math.random() * 1000);

    const lowerMessage = message.toLowerCase();

    // Pattern-based responses for demonstration
    if (lowerMessage.includes('authentication') || lowerMessage.includes('auth')) {
      return {
        content: `🔐 **Authentication Analysis Results**

I found **6 repositories** using legacy authentication systems:

### Legacy Authentication Implementations:
1. **ClaimProcessor** - Uses custom AuthFilter.java (Struts-based)
2. **CustomerPortal** - LoginAction.java with session management
3. **PaymentGateway** - SecurityInterceptor.java (CORBA integration)
4. **UserManagement** - Legacy LDAP connector
5. **BillingService** - Token-based auth (deprecated)
6. **ReportingAPI** - Basic HTTP auth

### Migration Recommendations:
• **Priority 1**: Modernize to OAuth 2.0/OIDC
• **Priority 2**: Implement JWT tokens for stateless auth
• **Priority 3**: Consolidate to single identity provider

Would you like me to analyze the migration impact for any specific repository?`,
        metadata: {
          analysisType: 'cross-repo',
          fileReferences: [
            'ClaimProcessor/src/main/java/auth/AuthFilter.java',
            'CustomerPortal/src/actions/LoginAction.java',
            'PaymentGateway/src/security/SecurityInterceptor.java'
          ]
        }
      };
    }

    if (lowerMessage.includes('oracle') || lowerMessage.includes('database') || lowerMessage.includes('table')) {
      return {
        content: `🗄️ **Oracle Database Usage Analysis**

Found **CUSTOMER_ACCOUNTS** table usage across **8 repositories**:

### Database Dependencies:
1. **ClaimProcessor** → 15 queries (read/write)
2. **CustomerPortal** → 8 queries (mostly read)
3. **BillingService** → 12 queries (complex joins)
4. **UserManagement** → 6 queries (user profile data)
5. **ReportingAPI** → 22 queries (analytics)

### Schema Analysis:
\`\`\`sql
-- Most frequently accessed columns:
CUSTOMER_ID (PRIMARY KEY)
EMAIL_ADDRESS
ACCOUNT_STATUS
CREATED_DATE
LAST_LOGIN_DATE
\`\`\`

### Migration Strategy:
• **Phase 1**: Extract to microservice with REST API
• **Phase 2**: Migrate to PostgreSQL/MongoDB
• **Phase 3**: Implement event-driven updates

**⚠️ High Risk**: BillingService has complex stored procedures that need careful migration planning.`,
        metadata: {
          analysisType: 'cross-repo',
          repositoryName: 'Multiple repositories',
          fileReferences: [
            'ClaimProcessor/src/main/java/dao/CustomerDAO.java',
            'BillingService/src/main/java/billing/CustomerBillingDAO.java'
          ]
        }
      };
    }

    if (lowerMessage.includes('struts') || lowerMessage.includes('action')) {
      return {
        content: `⚡ **Struts Actions Analysis**

Found **47 Struts actions** across **4 repositories**:

### Payment Processing Actions:
• **PaymentAction.java** - Handles credit card processing
• **RefundAction.java** - Processes refunds and chargebacks  
• **BillingCycleAction.java** - Monthly billing automation
• **InvoiceAction.java** - Invoice generation and delivery

### Migration Complexity:
🟢 **Low**: Simple form processing (12 actions)
🟡 **Medium**: Business logic integration (23 actions)  
🔴 **High**: Complex workflows with multiple dependencies (12 actions)

### Modernization Path:
1. **Extract business logic** to service layer
2. **Convert to REST endpoints** (Spring Boot)
3. **Implement async processing** where applicable
4. **Add proper error handling** and validation

Would you like me to generate detailed migration plans for the high-complexity actions?`,
        metadata: {
          analysisType: 'single-repo',
          fileReferences: [
            'PaymentGateway/src/actions/PaymentAction.java',
            'BillingService/src/actions/RefundAction.java'
          ]
        }
      };
    }

    if (lowerMessage.includes('migration') || lowerMessage.includes('modernization') || lowerMessage.includes('plan')) {
      return {
        content: `🚀 **Enterprise Migration Strategy**

Based on analysis of your **100+ repositories**, here's the recommended migration approach:

### 🎯 Phase 1: Foundation (Months 1-3)
- **Containerize** core services (Docker + Kubernetes)
- **Implement** API gateway pattern
- **Establish** CI/CD pipelines
- **Set up** monitoring and logging

### 🔄 Phase 2: Core Services (Months 4-8)
- **Migrate** authentication to OAuth 2.0
- **Extract** database layer to microservices
- **Convert** critical Struts actions to REST APIs
- **Modernize** CORBA interfaces to gRPC

### ⚡ Phase 3: Optimization (Months 9-12)
- **Implement** event-driven architecture
- **Add** caching layers (Redis)
- **Optimize** database queries
- **Scale** horizontally with load balancing

### 📊 Risk Assessment:
• **High Risk**: 12 repositories with complex CORBA dependencies
• **Medium Risk**: 34 repositories with Oracle stored procedures
• **Low Risk**: 54 repositories with standard CRUD operations

**Estimated Timeline**: 12-15 months
**Team Required**: 8-10 developers + 2 architects
**Budget**: $2.5M - $3.2M

Would you like me to dive deeper into any specific phase?`,
        metadata: {
          analysisType: 'migration-analysis'
        }
      };
    }

    if (lowerMessage.includes('corba')) {
      return {
        content: `🔗 **CORBA Interfaces Analysis**

Identified **23 CORBA interfaces** that need modernization:

### Critical CORBA Dependencies:
1. **AccountService.idl** → Used by 8 repositories
2. **PaymentProcessor.idl** → Financial transactions
3. **CustomerLookup.idl** → User data retrieval
4. **ReportGenerator.idl** → Business intelligence

### Modernization Strategy:
• **Replace with gRPC** for high-performance inter-service communication
• **Convert to REST APIs** for web-facing services
• **Implement message queues** for async operations

### Implementation Plan:
1. **Map CORBA → gRPC** service definitions
2. **Create compatibility layer** during transition
3. **Gradual cutover** with feature flags
4. **Remove legacy CORBA** infrastructure

**Timeline**: 6-8 months with parallel development approach.`,
        metadata: {
          analysisType: 'cross-repo',
          fileReferences: [
            'CoreServices/idl/AccountService.idl',
            'PaymentGateway/idl/PaymentProcessor.idl'
          ]
        }
      };
    }

    // Default response for unrecognized patterns
    return {
      content: `I understand you're asking about: **"${message}"**

I can help you analyze your legacy codebase in several ways:

### 🔍 **Available Analysis Types:**
• **Repository Structure** - Understand dependencies and architecture
• **Technology Stack** - Identify legacy components that need modernization  
• **Migration Planning** - Get step-by-step modernization roadmaps
• **Cross-Repository Impact** - See how changes affect multiple systems
• **Code Pattern Detection** - Find similar implementations across repos

### 💡 **Try asking:**
• "Which repositories use the CustomerService?"
• "Show me all Oracle stored procedures"
• "What's the migration risk for the payment system?"
• "Find all deprecated APIs across repositories"

What specific aspect of your codebase would you like me to analyze?`,
      metadata: {
        analysisType: 'single-repo'
      }
    };
  }

  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
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