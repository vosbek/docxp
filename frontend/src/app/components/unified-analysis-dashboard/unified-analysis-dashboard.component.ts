import { Component, OnInit, OnDestroy, Input, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, ActivatedRoute } from '@angular/router';
import { Subject, BehaviorSubject, combineLatest } from 'rxjs';
import { takeUntil, map, startWith } from 'rxjs/operators';

// PrimeNG Imports
import { CardModule } from 'primeng/card';
import { ButtonModule } from 'primeng/button';
import { TabViewModule } from 'primeng/tabview';
import { TreeModule } from 'primeng/tree';
import { TreeNode } from 'primeng/api';
import { TableModule } from 'primeng/table';
import { TagModule } from 'primeng/tag';
import { ProgressBarModule } from 'primeng/progressbar';
import { ToastModule } from 'primeng/toast';
import { MessageService } from 'primeng/api';
import { SplitterModule } from 'primeng/splitter';
import { PanelModule } from 'primeng/panel';
import { TimelineModule } from 'primeng/timeline';
import { BadgeModule } from 'primeng/badge';
import { MenuModule } from 'primeng/menu';
import { InputTextModule } from 'primeng/inputtext';
import { DropdownModule } from 'primeng/dropdown';
import { MultiSelectModule } from 'primeng/multiselect';

// Services
import { ApiService, JobStatus } from '../../services/api.service';
import { JQAssistantService, AnalysisJobStatus, ArchitecturalInsight, ArchitecturalViolation, DependencyGraph, RepositoryHealthScore } from '../../services/jqassistant.service';
import { ChatService } from '../../services/chat.service';
import { V1SearchService, SearchResponse } from '../../services/v1-search.service';

// Components
import { DiagramViewerComponent, DiagramData } from '../diagram-viewer/diagram-viewer.component';
// import { DependencyGraphComponent } from '../dependency-graph/dependency-graph.component';

/**
 * Unified Analysis Dashboard - Comprehensive Post-Indexing Information Display
 * 
 * This component provides a coordinated view of all analysis results including:
 * - Code structure and architecture
 * - Business rules and knowledge tracing
 * - Data flows and dependencies
 * - Cross-system relationships
 * - Legacy process documentation
 * - Technical debt and migration insights
 */

interface UnifiedAnalysisData {
  jobStatus: JobStatus | null;
  architecturalAnalysis: AnalysisJobStatus | null;
  diagrams: DiagramData[];
  dependencyGraph: DependencyGraph | null;
  architecturalInsights: ArchitecturalInsight[];
  violations: ArchitecturalViolation[];
  healthScore: RepositoryHealthScore | null;
  businessRuleTraces: BusinessRuleTrace[];
  dataFlowMappings: DataFlowMapping[];
  crossSystemRelationships: CrossSystemRelationship[];
  migrationReadiness: MigrationReadinessAssessment | null;
}

interface BusinessRuleTrace {
  id: string;
  ruleName: string;
  businessDescription: string;
  technicalImplementation: TechnicalImplementation[];
  dataElements: string[];
  relatedProcesses: string[];
  complianceRequirements: string[];
  lastUpdated: Date;
  confidence: number;
}

interface TechnicalImplementation {
  type: 'class' | 'method' | 'config' | 'database' | 'service';
  location: string;
  description: string;
  complexity: 'low' | 'medium' | 'high';
  dependencies: string[];
}

interface DataFlowMapping {
  id: string;
  flowName: string;
  sourceSystem: string;
  targetSystem: string;
  dataElements: DataElement[];
  transformations: DataTransformation[];
  businessPurpose: string;
  technicalPath: TechnicalPath[];
  riskLevel: 'low' | 'medium' | 'high';
}

interface DataElement {
  name: string;
  type: string;
  source: string;
  target: string;
  transformation?: string;
  validation?: string;
}

interface DataTransformation {
  step: number;
  description: string;
  location: string;
  complexity: 'low' | 'medium' | 'high';
}

interface TechnicalPath {
  sequence: number;
  component: string;
  operation: string;
  input: string;
  output: string;
}

interface CrossSystemRelationship {
  id: string;
  relationshipType: 'api_call' | 'data_sharing' | 'event_publishing' | 'batch_processing' | 'shared_database';
  sourceSystem: string;
  targetSystem: string;
  interface: string;
  dataContract: any;
  frequency: string;
  businessCriticality: 'low' | 'medium' | 'high' | 'critical';
  migrationComplexity: 'low' | 'medium' | 'high';
}

interface MigrationReadinessAssessment {
  overallScore: number;
  readinessGrade: 'A' | 'B' | 'C' | 'D' | 'F';
  categories: {
    codeQuality: number;
    architecture: number;
    dependencies: number;
    testCoverage: number;
    documentation: number;
    businessAlignment: number;
  };
  blockers: MigrationBlocker[];
  recommendations: MigrationRecommendation[];
  estimatedEffort: {
    timeline: string;
    resources: number;
    risk: 'low' | 'medium' | 'high';
  };
}

interface MigrationBlocker {
  category: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  description: string;
  impact: string;
  resolution: string;
  estimatedEffort: string;
}

interface MigrationRecommendation {
  priority: number;
  category: string;
  recommendation: string;
  rationale: string;
  expectedBenefit: string;
  implementation: string;
}

interface ContextualView {
  id: string;
  name: string;
  description: string;
  focusArea: 'architecture' | 'business' | 'data' | 'migration' | 'quality';
  components: string[];
}

@Component({
  selector: 'app-unified-analysis-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    CardModule,
    ButtonModule,
    TabViewModule,
    TreeModule,
    TableModule,
    TagModule,
    ProgressBarModule,
    ToastModule,
    SplitterModule,
    PanelModule,
    TimelineModule,
    BadgeModule,
    MenuModule,
    InputTextModule,
    DropdownModule,
    MultiSelectModule,
    DiagramViewerComponent
    // DependencyGraphComponent
  ],
  providers: [MessageService],
  templateUrl: './unified-analysis-dashboard.component.html',
  styleUrls: ['./unified-analysis-dashboard.component.scss']
})
export class UnifiedAnalysisDashboardComponent implements OnInit, OnDestroy {
  @Input() jobId: string = '';
  @ViewChild('dashboardContainer') dashboardContainer!: ElementRef;

  private destroy$ = new Subject<void>();
  
  // Data subjects for reactive updates
  private analysisDataSubject = new BehaviorSubject<UnifiedAnalysisData>({
    jobStatus: null,
    architecturalAnalysis: null,
    diagrams: [],
    dependencyGraph: null,
    architecturalInsights: [],
    violations: [],
    healthScore: null,
    businessRuleTraces: [],
    dataFlowMappings: [],
    crossSystemRelationships: [],
    migrationReadiness: null
  });

  public analysisData$ = this.analysisDataSubject.asObservable();
  
  // UI State
  loading = true;
  selectedView: ContextualView | null = null;
  activeTabIndex = 0;
  searchQuery = '';
  selectedFocusAreas: string[] = [];
  
  // Contextual Views Configuration
  contextualViews: ContextualView[] = [
    {
      id: 'architect_overview',
      name: 'Architect Overview',
      description: 'High-level system architecture and key relationships',
      focusArea: 'architecture',
      components: ['dependency_graph', 'architectural_insights', 'health_score', 'violations_summary']
    },
    {
      id: 'business_knowledge',
      name: 'Business Knowledge Tracing',
      description: 'Business rules mapped to technical implementation',
      focusArea: 'business',
      components: ['business_rules', 'compliance_mapping', 'process_flows', 'stakeholder_map']
    },
    {
      id: 'data_lineage',
      name: 'Data Flow Analysis',
      description: 'Data movement and transformation across systems',
      focusArea: 'data',
      components: ['data_flows', 'transformation_mapping', 'data_quality', 'integration_points']
    },
    {
      id: 'migration_readiness',
      name: 'Migration Assessment',
      description: 'Modernization readiness and pathway analysis',
      focusArea: 'migration',
      components: ['readiness_score', 'blockers', 'recommendations', 'effort_estimation']
    },
    {
      id: 'quality_insights',
      name: 'Quality & Technical Debt',
      description: 'Code quality metrics and improvement opportunities',
      focusArea: 'quality',
      components: ['code_metrics', 'tech_debt', 'pattern_analysis', 'improvement_recommendations']
    }
  ];

  // Focus area options for filtering
  focusAreaOptions = [
    { label: 'Architecture', value: 'architecture' },
    { label: 'Business Logic', value: 'business' },
    { label: 'Data Flows', value: 'data' },
    { label: 'Migration', value: 'migration' },
    { label: 'Quality', value: 'quality' }
  ];

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private apiService: ApiService,
    private jqAssistantService: JQAssistantService,
    private chatService: ChatService,
    private searchService: V1SearchService,
    private messageService: MessageService
  ) {}

  ngOnInit() {
    this.route.params.subscribe(params => {
      this.jobId = params['id'];
      if (this.jobId) {
        this.initializeDashboard();
      }
    });

    // Set default view
    this.selectedView = this.contextualViews[0];
  }

  ngOnDestroy() {
    this.destroy$.next();
    this.destroy$.complete();
  }

  /**
   * Initialize the comprehensive dashboard by loading all related data
   */
  private async initializeDashboard() {
    this.loading = true;
    
    try {
      await this.loadAllAnalysisData();
      this.setupReactiveDataUpdates();
      this.initializeContextualViews();
    } catch (error) {
      console.error('Failed to initialize unified dashboard:', error);
      this.messageService.add({
        severity: 'error',
        summary: 'Dashboard Error',
        detail: 'Failed to load comprehensive analysis data'
      });
    } finally {
      this.loading = false;
    }
  }

  /**
   * Load all analysis data from multiple sources
   */
  private async loadAllAnalysisData() {
    const promises = [
      this.loadJobStatus(),
      this.loadArchitecturalAnalysis(),
      this.loadDiagrams(),
      this.loadDependencyGraph(),
      this.loadBusinessRuleTraces(),
      this.loadDataFlowMappings(),
      this.loadCrossSystemRelationships(),
      this.loadMigrationReadiness()
    ];

    await Promise.allSettled(promises);
  }

  private async loadJobStatus() {
    try {
      const jobStatus = await this.apiService.getJobStatus(this.jobId).toPromise();
      this.updateAnalysisData({ jobStatus });
    } catch (error) {
      console.error('Failed to load job status:', error);
    }
  }

  private async loadArchitecturalAnalysis() {
    try {
      // Check if architectural analysis exists for this job
      const analysis = await this.jqAssistantService.getAnalysisStatus(this.jobId).toPromise();
      // const insights = await this.jqAssistantService.getArchitecturalInsights(this.jobId).toPromise();
      // const violations = await this.jqAssistantService.getArchitecturalViolations(this.jobId).toPromise();
      const insights: any[] = [];
      const violations: any[] = [];
      const healthScore = await this.jqAssistantService.getRepositoryHealth(this.jobId).toPromise();
      
      this.updateAnalysisData({ 
        architecturalAnalysis: analysis,
        architecturalInsights: insights,
        violations: violations,
        healthScore: healthScore
      });
    } catch (error) {
      console.error('Failed to load architectural analysis:', error);
    }
  }

  private async loadDiagrams() {
    try {
      const response = await this.apiService.getJobDiagrams(this.jobId).toPromise();
      const diagrams = response.diagrams.map(d => ({
        id: d.id,
        name: d.name,
        type: d.type as any,
        content: d.content,
        description: d.description
      }));
      
      this.updateAnalysisData({ diagrams });
    } catch (error) {
      console.error('Failed to load diagrams:', error);
    }
  }

  private async loadDependencyGraph() {
    try {
      const dependencyGraph = await this.jqAssistantService.getDependencyGraph(this.jobId).toPromise();
      this.updateAnalysisData({ dependencyGraph });
    } catch (error) {
      console.error('Failed to load dependency graph:', error);
    }
  }

  private async loadBusinessRuleTraces() {
    try {
      // This would be a new API endpoint to trace business rules to code
      // const businessRuleTraces = await this.apiService.getBusinessRuleTraces(this.jobId).toPromise();
      const businessRuleTraces: any[] = [];
      this.updateAnalysisData({ businessRuleTraces });
    } catch (error) {
      console.error('Failed to load business rule traces:', error);
      // For now, provide mock data structure
      this.updateAnalysisData({ businessRuleTraces: [] });
    }
  }

  private async loadDataFlowMappings() {
    try {
      // This would be a new API endpoint for data flow analysis
      // const dataFlowMappings = await this.apiService.getDataFlowMappings(this.jobId).toPromise();
      const dataFlowMappings: any[] = [];
      this.updateAnalysisData({ dataFlowMappings });
    } catch (error) {
      console.error('Failed to load data flow mappings:', error);
      this.updateAnalysisData({ dataFlowMappings: [] });
    }
  }

  private async loadCrossSystemRelationships() {
    try {
      // This would be a new API endpoint for cross-system analysis
      // const crossSystemRelationships = await this.apiService.getCrossSystemRelationships(this.jobId).toPromise();
      const crossSystemRelationships: any[] = [];
      this.updateAnalysisData({ crossSystemRelationships });
    } catch (error) {
      console.error('Failed to load cross-system relationships:', error);
      this.updateAnalysisData({ crossSystemRelationships: [] });
    }
  }

  private async loadMigrationReadiness() {
    try {
      // This would be a new API endpoint for migration assessment
      // const migrationReadiness = await this.apiService.getMigrationReadiness(this.jobId).toPromise();
      const migrationReadiness: any = {};
      this.updateAnalysisData({ migrationReadiness });
    } catch (error) {
      console.error('Failed to load migration readiness:', error);
      this.updateAnalysisData({ migrationReadiness: null });
    }
  }

  private updateAnalysisData(partialData: Partial<UnifiedAnalysisData>) {
    const currentData = this.analysisDataSubject.value;
    this.analysisDataSubject.next({ ...currentData, ...partialData });
  }

  private setupReactiveDataUpdates() {
    // Setup reactive subscriptions for real-time updates
    this.jqAssistantService.analysisStatus$
      .pipe(takeUntil(this.destroy$))
      .subscribe(status => {
        if (status) {
          this.updateAnalysisData({ architecturalAnalysis: status });
        }
      });

    this.jqAssistantService.dependencyGraph$
      .pipe(takeUntil(this.destroy$))
      .subscribe(graph => {
        if (graph) {
          this.updateAnalysisData({ dependencyGraph: graph });
        }
      });
  }

  private initializeContextualViews() {
    // Setup contextual view configurations based on available data
    const data = this.analysisDataSubject.value;
    
    // Customize views based on what data is available
    this.contextualViews.forEach(view => {
      view.components = this.filterAvailableComponents(view.components, data);
    });
  }

  private filterAvailableComponents(components: string[], data: UnifiedAnalysisData): string[] {
    return components.filter(component => {
      switch (component) {
        case 'dependency_graph':
          return data.dependencyGraph !== null;
        case 'architectural_insights':
          return data.architecturalInsights.length > 0;
        case 'business_rules':
          return data.businessRuleTraces.length > 0;
        case 'data_flows':
          return data.dataFlowMappings.length > 0;
        case 'readiness_score':
          return data.migrationReadiness !== null;
        default:
          return true;
      }
    });
  }

  /**
   * Navigation and view management
   */
  selectContextualView(view: ContextualView) {
    this.selectedView = view;
    this.activeTabIndex = 0;
  }

  navigateToDetailView(viewType: string, itemId?: string) {
    switch (viewType) {
      case 'architecture_analysis':
        this.router.navigate(['/architecture-analysis', this.jobId]);
        break;
      case 'dependency_graph':
        this.router.navigate(['/dependency-graph', this.jobId]);
        break;
      case 'search':
        this.router.navigate(['/v1-search'], { 
          queryParams: { jobId: this.jobId, query: this.searchQuery } 
        });
        break;
      case 'chat':
        this.router.navigate(['/chat'], { 
          queryParams: { context: `job:${this.jobId}` } 
        });
        break;
    }
  }

  /**
   * Search and filtering
   */
  onSearchQueryChange() {
    // Implement real-time search across all data
    if (this.searchQuery.length > 2) {
      this.performUnifiedSearch();
    }
  }

  private async performUnifiedSearch() {
    try {
      const searchResponse = await this.searchService.quickSearch(
        this.searchQuery,
        this.jobId,
        this.selectedFocusAreas.join(','),
        10
      ).toPromise();
      
      // Update UI with search results
      this.highlightSearchResults(searchResponse);
    } catch (error) {
      console.error('Search failed:', error);
    }
  }

  private highlightSearchResults(searchResponse: SearchResponse) {
    // Implement search result highlighting across different views
    console.log('Search results:', searchResponse);
  }

  /**
   * AI-powered insights and recommendations
   */
  async getAIInsights(context: string): Promise<void> {
    try {
      const response = await this.chatService.sendMessage(
        `Analyze the ${context} data for job ${this.jobId} and provide actionable insights for architects.`,
        { repositoryIds: [this.jobId], analysisMode: 'detailed' }
      );
      
      this.messageService.add({
        severity: 'info',
        summary: 'AI Analysis',
        detail: 'AI insights generated successfully'
      });
      
      return response;
    } catch (error) {
      console.error('Failed to get AI insights:', error);
      this.messageService.add({
        severity: 'error',
        summary: 'AI Error',
        detail: 'Failed to generate AI insights'
      });
    }
  }

  /**
   * Export and documentation
   */
  exportAnalysisReport(format: 'pdf' | 'excel' | 'markdown') {
    // Implement comprehensive analysis export
    const data = this.analysisDataSubject.value;
    
    switch (format) {
      case 'pdf':
        this.exportToPDF(data);
        break;
      case 'excel':
        this.exportToExcel(data);
        break;
      case 'markdown':
        this.exportToMarkdown(data);
        break;
    }
  }

  private exportToPDF(data: UnifiedAnalysisData) {
    // Implementation for PDF export
    console.log('Exporting to PDF:', data);
  }

  private exportToExcel(data: UnifiedAnalysisData) {
    // Implementation for Excel export
    console.log('Exporting to Excel:', data);
  }

  private exportToMarkdown(data: UnifiedAnalysisData) {
    // Implementation for Markdown export
    console.log('Exporting to Markdown:', data);
  }

  /**
   * Utility methods
   */
  getHealthScoreColor(score: number): string {
    if (score >= 80) return 'success';
    if (score >= 60) return 'warning';
    return 'danger';
  }

  getSeverityColor(severity: string): string {
    switch (severity.toLowerCase()) {
      case 'critical': return 'danger';
      case 'high': return 'danger';
      case 'medium': return 'warning';
      case 'low': return 'info';
      default: return 'secondary';
    }
  }

  formatRelativeTime(date: Date): string {
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const hours = Math.floor(diff / (1000 * 60 * 60));
    
    if (hours < 1) {
      const minutes = Math.floor(diff / (1000 * 60));
      return `${minutes} minutes ago`;
    } else if (hours < 24) {
      return `${hours} hours ago`;
    } else {
      const days = Math.floor(hours / 24);
      return `${days} days ago`;
    }
  }
}