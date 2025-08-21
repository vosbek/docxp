import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';
import { environment } from '../../environments/environment';

export interface AgentResponse {
  content: string;
  agent_type: string;
  confidence: number;
  reasoning?: string;
  suggested_actions: string[];
  tool_calls: any[];
  followup_questions: string[];
  metadata: Record<string, any>;
}

export interface ConversationContext {
  repository_ids?: string[];
  user_preferences?: Record<string, any>;
  demo_mode?: boolean;
}

export interface StartConversationRequest {
  message: string;
  agent_type: string;
  context?: ConversationContext;
}

export interface ContinueConversationRequest {
  message: string;
  agent_type?: string;
}

export interface ConversationHistory {
  session_id: string;
  repository_ids: string[];
  current_agent?: string;
  conversation_history: ConversationExchange[];
  created_at: string;
  last_activity: string;
  total_exchanges: number;
}

export interface ConversationExchange {
  timestamp: string;
  user_message: string;
  agent_response: string;
  agent_type: string;
}

export interface AgentInfo {
  name: string;
  available: boolean;
  description: string;
  capabilities: string[];
}

export interface AgentCapabilities {
  primary_focus: string;
  tools: string[];
  expertise_areas: string[];
  deliverables: string[];
}

export interface DetailedAgentInfo extends AgentInfo {
  detailed_capabilities: AgentCapabilities;
  availability: {
    service_available: boolean;
    agent_ready: boolean;
  };
}

export type AgentType = 
  | 'migration_expert' 
  | 'code_analyzer' 
  | 'architecture_advisor' 
  | 'business_analyst' 
  | 'technical_writer';

@Injectable({
  providedIn: 'root'
})
export class StrandsAgentsService {
  private readonly baseUrl = environment.apiUrl;
  
  private activeConversationsSubject = new BehaviorSubject<string[]>([]);
  private agentHealthSubject = new BehaviorSubject<any>(null);
  
  public activeConversations$ = this.activeConversationsSubject.asObservable();
  public agentHealth$ = this.agentHealthSubject.asObservable();

  constructor(private http: HttpClient) {
    this.checkAgentHealth();
  }

  /**
   * Start a new conversation with a specialized agent
   */
  startConversation(request: StartConversationRequest): Observable<AgentResponse> {
    return this.http.post<AgentResponse>(`${this.baseUrl}/api/strands/agents/start`, request);
  }

  /**
   * Continue an existing conversation
   */
  continueConversation(sessionId: string, request: ContinueConversationRequest): Observable<AgentResponse> {
    return this.http.post<AgentResponse>(
      `${this.baseUrl}/api/strands/agents/continue/${sessionId}`, 
      request
    );
  }

  /**
   * Get conversation history for a session
   */
  getConversationHistory(sessionId: string): Observable<ConversationHistory> {
    return this.http.get<ConversationHistory>(`${this.baseUrl}/api/strands/agents/conversation/${sessionId}`);
  }

  /**
   * End a conversation session
   */
  endConversation(sessionId: string): Observable<any> {
    return this.http.delete(`${this.baseUrl}/api/strands/agents/conversation/${sessionId}`);
  }

  /**
   * Get available agents and their basic information
   */
  getAvailableAgents(): Observable<Record<string, AgentInfo>> {
    return this.http.get<Record<string, AgentInfo>>(`${this.baseUrl}/api/strands/agents/available`);
  }

  /**
   * Get detailed capabilities for a specific agent
   */
  getAgentCapabilities(agentType: AgentType): Observable<{
    success: boolean;
    agent_type: string;
    basic_info: AgentInfo;
    detailed_capabilities: AgentCapabilities;
    availability: {
      service_available: boolean;
      agent_ready: boolean;
    };
  }> {
    return this.http.get<any>(`${this.baseUrl}/api/strands/agents/capabilities/${agentType}`);
  }

  /**
   * Get all available agent types
   */
  getAgentTypes(): Observable<{
    success: boolean;
    agent_types: Array<{
      id: string;
      name: string;
      description: string;
    }>;
    total_agents: number;
  }> {
    return this.http.get<any>(`${this.baseUrl}/api/strands/agents/agent-types`);
  }

  /**
   * Health check for Strands Agents service
   */
  checkAgentHealth(): Observable<any> {
    const healthCheck = this.http.get(`${this.baseUrl}/api/strands/agents/health`);
    healthCheck.subscribe(
      health => this.agentHealthSubject.next(health),
      error => this.agentHealthSubject.next({ success: false, error: error.message })
    );
    return healthCheck;
  }

  /**
   * Run demo conversations with all agent types
   */
  runDemo(): Observable<any> {
    return this.http.post(`${this.baseUrl}/api/strands/agents/demo`, {});
  }

  /**
   * Perform bulk analysis using multiple agents
   */
  bulkAnalyze(repositoryIds: string[], analysisTypes: AgentType[]): Observable<any> {
    return this.http.post(`${this.baseUrl}/api/strands/agents/bulk-analyze`, {
      repository_ids: repositoryIds,
      analysis_types: analysisTypes
    });
  }

  /**
   * Helper method to get agent display name
   */
  getAgentDisplayName(agentType: AgentType): string {
    const displayNames: Record<AgentType, string> = {
      migration_expert: 'Migration Expert',
      code_analyzer: 'Code Analyzer',
      architecture_advisor: 'Architecture Advisor',
      business_analyst: 'Business Analyst',
      technical_writer: 'Technical Writer'
    };
    return displayNames[agentType] || agentType.replace('_', ' ');
  }

  /**
   * Helper method to get agent icon class
   */
  getAgentIcon(agentType: AgentType): string {
    const icons: Record<AgentType, string> = {
      migration_expert: 'fas fa-exchange-alt',
      code_analyzer: 'fas fa-search',
      architecture_advisor: 'fas fa-drafting-compass',
      business_analyst: 'fas fa-chart-line',
      technical_writer: 'fas fa-file-alt'
    };
    return icons[agentType] || 'fas fa-robot';
  }

  /**
   * Helper method to get agent color theme
   */
  getAgentColor(agentType: AgentType): string {
    const colors: Record<AgentType, string> = {
      migration_expert: '#3B82F6', // Blue
      code_analyzer: '#10B981', // Emerald
      architecture_advisor: '#8B5CF6', // Violet
      business_analyst: '#F59E0B', // Amber
      technical_writer: '#EF4444' // Red
    };
    return colors[agentType] || '#6B7280';
  }

  /**
   * Helper method to determine best agent for a query
   */
  suggestAgentForQuery(query: string): AgentType {
    const queryLower = query.toLowerCase();
    
    // Migration-related keywords
    if (queryLower.includes('migrat') || queryLower.includes('legacy') || 
        queryLower.includes('moderniz') || queryLower.includes('struts') ||
        queryLower.includes('corba') || queryLower.includes('upgrade')) {
      return 'migration_expert';
    }
    
    // Code analysis keywords
    if (queryLower.includes('code quality') || queryLower.includes('refactor') ||
        queryLower.includes('technical debt') || queryLower.includes('pattern') ||
        queryLower.includes('complexity')) {
      return 'code_analyzer';
    }
    
    // Architecture keywords
    if (queryLower.includes('architect') || queryLower.includes('scalab') ||
        queryLower.includes('microservice') || queryLower.includes('design') ||
        queryLower.includes('system')) {
      return 'architecture_advisor';
    }
    
    // Business analysis keywords
    if (queryLower.includes('business') || queryLower.includes('process') ||
        queryLower.includes('requirement') || queryLower.includes('impact') ||
        queryLower.includes('workflow')) {
      return 'business_analyst';
    }
    
    // Documentation keywords
    if (queryLower.includes('document') || queryLower.includes('guide') ||
        queryLower.includes('manual') || queryLower.includes('help') ||
        queryLower.includes('explain')) {
      return 'technical_writer';
    }
    
    // Default to migration expert for general queries
    return 'migration_expert';
  }

  /**
   * Create conversation request with smart defaults
   */
  createConversationRequest(
    message: string, 
    agentType?: AgentType,
    repositoryIds?: string[],
    userPreferences?: Record<string, any>
  ): StartConversationRequest {
    const selectedAgent = agentType || this.suggestAgentForQuery(message);
    
    return {
      message,
      agent_type: selectedAgent,
      context: {
        repository_ids: repositoryIds || [],
        user_preferences: userPreferences || {
          technical_depth: 'detailed',
          response_format: 'structured'
        }
      }
    };
  }

  /**
   * Format agent response for display
   */
  formatAgentResponse(response: AgentResponse): {
    content: string;
    actions: string[];
    questions: string[];
    confidence: string;
    agent: string;
  } {
    return {
      content: response.content,
      actions: response.suggested_actions || [],
      questions: response.followup_questions || [],
      confidence: `${Math.round(response.confidence * 100)}%`,
      agent: this.getAgentDisplayName(response.agent_type as AgentType)
    };
  }

  /**
   * Track active conversation sessions
   */
  addActiveConversation(sessionId: string): void {
    const current = this.activeConversationsSubject.value;
    if (!current.includes(sessionId)) {
      this.activeConversationsSubject.next([...current, sessionId]);
    }
  }

  /**
   * Remove conversation from active tracking
   */
  removeActiveConversation(sessionId: string): void {
    const current = this.activeConversationsSubject.value;
    this.activeConversationsSubject.next(current.filter(id => id !== sessionId));
  }

  /**
   * Check if Strands Agents is available
   */
  isAvailable(): boolean {
    const health = this.agentHealthSubject.value;
    return health && health.success && health.service_info?.service_available;
  }

  /**
   * Get installation instructions if not available
   */
  getInstallationInstructions(): string[] {
    return [
      'Install Strands Agents SDK:',
      'pip install strands-agents',
      '',
      'Or using conda:',
      'conda install -c conda-forge strands-agents',
      '',
      'Restart the backend service after installation.'
    ];
  }

  /**
   * Validate agent type
   */
  isValidAgentType(agentType: string): agentType is AgentType {
    const validTypes: AgentType[] = [
      'migration_expert',
      'code_analyzer', 
      'architecture_advisor',
      'business_analyst',
      'technical_writer'
    ];
    return validTypes.includes(agentType as AgentType);
  }

  /**
   * Get quick start prompts for each agent type
   */
  getQuickStartPrompts(agentType: AgentType): string[] {
    const prompts: Record<AgentType, string[]> = {
      migration_expert: [
        "Help me migrate our Struts application to Spring Boot",
        "What's the best approach for modernizing our CORBA services?",
        "Analyze the migration risks for our legacy Oracle database",
        "Create a migration roadmap for our monolithic application"
      ],
      code_analyzer: [
        "Analyze the code quality of our Java services",
        "Identify technical debt in our codebase",
        "Find performance bottlenecks in our application",
        "Review our code for security vulnerabilities"
      ],
      architecture_advisor: [
        "Design a scalable microservices architecture",
        "Recommend technologies for our cloud migration",
        "Help optimize our system for high availability",
        "Review our API design and integration patterns"
      ],
      business_analyst: [
        "Extract business rules from our legacy system",
        "Analyze the impact of our modernization project",
        "Map our current business processes",
        "Define requirements for our new system"
      ],
      technical_writer: [
        "Create migration documentation for our team",
        "Generate API documentation for our services",
        "Write user guides for our new system",
        "Develop training materials for the migration"
      ]
    };
    return prompts[agentType] || [];
  }
}