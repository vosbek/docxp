import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { Subject, takeUntil } from 'rxjs';
import { ApiService } from '../../services/api.service';
import { MarkdownPipe } from '../../shared/pipes/markdown.pipe';

export interface WikiNode {
  id: string;
  title: string;
  type: 'system' | 'component' | 'process' | 'data' | 'rule' | 'document';
  content: string;
  relationships: WikiRelationship[];
  metadata: {
    lastModified: Date;
    author: string;
    tags: string[];
    criticality: 'low' | 'medium' | 'high' | 'critical';
    migrationStatus: 'legacy' | 'modernizing' | 'modern' | 'deprecated';
  };
  children?: WikiNode[];
  parentId?: string;
}

export interface WikiRelationship {
  id: string;
  targetNodeId: string;
  type: 'depends_on' | 'connects_to' | 'implements' | 'extends' | 'uses' | 'references';
  strength: number; // 0-1, how strong the relationship is
  description: string;
}

export interface WikiSearchResult {
  node: WikiNode;
  relevanceScore: number;
  matchType: 'title' | 'content' | 'tag' | 'relationship';
  snippet: string;
}

@Component({
  selector: 'app-deep-wiki',
  standalone: true,
  imports: [CommonModule, FormsModule, MarkdownPipe],
  templateUrl: './deep-wiki.component.html',
  styleUrls: ['./deep-wiki.component.scss']
})
export class DeepWikiComponent implements OnInit, OnDestroy {
  // Navigation state
  currentNode: WikiNode | null = null;
  breadcrumbs: WikiNode[] = [];
  
  // Tree navigation
  rootNodes: WikiNode[] = [];
  expandedNodes: Set<string> = new Set();
  
  // Search functionality
  searchQuery = '';
  searchResults: WikiSearchResult[] = [];
  isSearching = false;
  
  // Relationship visualization
  showRelationshipMap = false;
  selectedRelationshipTypes: Set<string> = new Set(['depends_on', 'connects_to', 'implements']);
  
  // Filters and views
  selectedNodeTypes: Set<string> = new Set(['system', 'component', 'process', 'data', 'rule', 'document']);
  selectedCriticality: Set<string> = new Set(['medium', 'high', 'critical']);
  selectedMigrationStatus: Set<string> = new Set(['legacy', 'modernizing']);
  
  // Content editing
  isEditing = false;
  editingContent = '';
  
  private destroy$ = new Subject<void>();

  constructor(
    private apiService: ApiService,
    private router: Router
  ) {}

  ngOnInit() {
    this.loadWikiStructure();
    this.initializeDefaultView();
  }

  ngOnDestroy() {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private loadWikiStructure() {
    // In a real implementation, this would load from the backend
    // For now, create a sample structure based on typical enterprise architecture
    this.rootNodes = this.createSampleWikiStructure();
  }

  private createSampleWikiStructure(): WikiNode[] {
    return [
      {
        id: 'enterprise-architecture',
        title: 'Enterprise Architecture',
        type: 'system',
        content: `# Enterprise Architecture Overview

Our enterprise architecture represents 15+ years of evolution across multiple business domains. This deep wiki documents the current state, relationships, and migration strategies for our complex legacy systems.

## Key Architectural Decisions
- **Service-Oriented Architecture** (SOA) with CORBA interfaces
- **Oracle-centric data layer** with 200+ tables
- **Multi-layered authentication** (LDAP, Custom, OAuth2)
- **Distributed processing** across 12 data centers

## Critical Migration Priorities
1. **Customer Management System** - High complexity, critical business impact
2. **Payment Processing** - Legacy Struts framework, PCI compliance requirements  
3. **Reporting Infrastructure** - Oracle-dependent, performance bottlenecks`,
        relationships: [
          {
            id: 'rel-1',
            targetNodeId: 'customer-management',
            type: 'connects_to',
            strength: 0.9,
            description: 'Primary customer data flow'
          },
          {
            id: 'rel-2', 
            targetNodeId: 'payment-processing',
            type: 'depends_on',
            strength: 0.8,
            description: 'Financial transaction processing'
          }
        ],
        metadata: {
          lastModified: new Date('2024-01-15'),
          author: 'Enterprise Architect',
          tags: ['architecture', 'overview', 'strategy'],
          criticality: 'critical',
          migrationStatus: 'modernizing'
        },
        children: [
          {
            id: 'customer-management',
            title: 'Customer Management System',
            type: 'system',
            content: `# Customer Management System

Legacy Java EE application managing 2.5M+ customer records with complex business rules and audit requirements.

## Current Technical Stack
- **Framework**: Java EE 6, Struts 1.3
- **Database**: Oracle 11g with 45 related tables
- **Authentication**: Custom LDAP integration
- **APIs**: SOAP-based with 200+ operations

## Business Rules Engine
- Customer lifecycle management
- Account hierarchy validation  
- Compliance audit trails
- Data retention policies (7-year requirement)

## Migration Challenges
- **Data Dependencies**: 12 downstream systems rely on customer data
- **Custom Business Logic**: 15,000+ lines of validation rules
- **Integration Points**: 45 external system connections
- **Audit Requirements**: Regulatory compliance for financial services`,
            relationships: [
              {
                id: 'rel-cm-1',
                targetNodeId: 'oracle-customer-schema',
                type: 'uses',
                strength: 1.0,
                description: 'Primary data storage'
              },
              {
                id: 'rel-cm-2',
                targetNodeId: 'ldap-authentication',
                type: 'depends_on',
                strength: 0.7,
                description: 'User authentication and authorization'
              }
            ],
            metadata: {
              lastModified: new Date('2024-01-10'),
              author: 'System Architect',
              tags: ['customer', 'legacy', 'java-ee', 'struts'],
              criticality: 'critical',
              migrationStatus: 'legacy'
            },
            parentId: 'enterprise-architecture'
          },
          {
            id: 'payment-processing',
            title: 'Payment Processing Engine',
            type: 'system',
            content: `# Payment Processing Engine

Mission-critical system handling $2B+ annual transaction volume with PCI DSS compliance requirements.

## Architecture Overview
- **Core Framework**: Struts 2.5 with custom interceptors
- **Security**: PCI DSS Level 1 compliant
- **Database**: Oracle with encrypted sensitive data
- **Integration**: 15 payment gateway connections

## Critical Business Processes
1. **Transaction Authorization** - Real-time fraud detection
2. **Settlement Processing** - Batch processing overnight
3. **Chargeback Management** - Complex dispute workflows
4. **Compliance Reporting** - Automated regulatory submissions

## Technical Debt Concerns
- **Legacy Framework**: Struts 2.5 (EOL approaching)
- **Monolithic Design**: Single deployment unit for all functions
- **Performance Issues**: Database bottlenecks during peak processing
- **Security Updates**: Manual patching process, security vulnerabilities`,
            relationships: [
              {
                id: 'rel-pp-1',
                targetNodeId: 'fraud-detection',
                type: 'implements',
                strength: 0.9,
                description: 'Real-time fraud analysis'
              },
              {
                id: 'rel-pp-2',
                targetNodeId: 'pci-compliance',
                type: 'implements',
                strength: 1.0,
                description: 'Security and compliance requirements'
              }
            ],
            metadata: {
              lastModified: new Date('2024-01-08'),
              author: 'Payment Team Lead',
              tags: ['payment', 'pci', 'struts', 'security'],
              criticality: 'critical',
              migrationStatus: 'legacy'
            },
            parentId: 'enterprise-architecture'
          }
        ]
      },
      {
        id: 'data-architecture',
        title: 'Data Architecture & Lineage',
        type: 'data',
        content: `# Data Architecture & Lineage

Comprehensive mapping of data flows, transformations, and dependencies across our enterprise systems.

## Oracle Schema Overview
- **Core Tables**: 200+ tables with complex relationships
- **Data Volume**: 50TB+ with 15-year retention requirements
- **Critical Entities**: Customer, Account, Transaction, Product, Compliance

## Data Flow Patterns
1. **Real-time Streams** - Customer interactions, payment processing
2. **Batch ETL** - Nightly data warehouse updates, reporting
3. **Event-driven Updates** - Account status changes, notifications
4. **Audit Trails** - Comprehensive logging for compliance

## Migration Considerations
- **Data Dependencies**: Cross-system references require coordinated migration
- **Performance Requirements**: Sub-second response times for customer lookups
- **Compliance**: Data residency, retention, and privacy requirements`,
        relationships: [],
        metadata: {
          lastModified: new Date('2024-01-12'),
          author: 'Data Architect',
          tags: ['data', 'oracle', 'etl', 'compliance'],
          criticality: 'high',
          migrationStatus: 'modernizing'
        },
        children: [
          {
            id: 'oracle-customer-schema',
            title: 'Oracle Customer Schema',
            type: 'data',
            content: `# Oracle Customer Schema

Core customer data model supporting multiple business domains with 45 interconnected tables.

## Primary Tables
- **CUSTOMERS** (2.5M records) - Core customer information
- **ACCOUNTS** (8.2M records) - Customer account relationships  
- **CUSTOMER_ADDRESSES** (5.1M records) - Address management with history
- **CUSTOMER_PREFERENCES** (12.8M records) - Personalization data
- **AUDIT_CUSTOMER_CHANGES** (45M records) - Complete change audit trail

## Complex Relationships
- Customer → Account (1:many) with hierarchy support
- Customer → Address (1:many) with temporal validity
- Account → Product (many:many) with configuration options
- Customer → Compliance (1:many) for regulatory requirements

## Performance Characteristics
- **Peak Read Load**: 15,000 queries/second during business hours
- **Write Volume**: 50,000 updates/day with audit trail generation
- **Index Strategy**: 125 indexes optimized for specific query patterns
- **Partitioning**: Monthly partitions on audit tables`,
            relationships: [
              {
                id: 'rel-ocs-1',
                targetNodeId: 'customer-management',
                type: 'uses',
                strength: 1.0,
                description: 'Primary application using this schema'
              }
            ],
            metadata: {
              lastModified: new Date('2024-01-07'),
              author: 'Database Administrator',
              tags: ['oracle', 'schema', 'customer', 'performance'],
              criticality: 'critical',
              migrationStatus: 'legacy'
            },
            parentId: 'data-architecture'
          }
        ]
      },
      {
        id: 'migration-strategy',
        title: 'Migration Strategy & Roadmap',
        type: 'document',
        content: `# Migration Strategy & Roadmap

Comprehensive 18-month plan for modernizing our legacy enterprise systems while maintaining business continuity.

## Strategic Objectives
1. **Reduce Technical Debt** - Eliminate EOL frameworks and libraries
2. **Improve Performance** - 50% reduction in response times
3. **Enhance Security** - Modern authentication and encryption
4. **Enable Scalability** - Cloud-native architecture patterns

## Migration Phases

### Phase 1: Foundation (Months 1-6)
- Establish CI/CD pipelines
- Containerize existing applications
- Implement API gateway pattern
- Set up monitoring and observability

### Phase 2: Core Systems (Months 7-12) 
- Migrate Customer Management to Spring Boot
- Modernize Payment Processing with microservices
- Implement event-driven architecture
- Database migration to PostgreSQL

### Phase 3: Integration (Months 13-18)
- Complete API standardization
- Implement real-time analytics
- Migrate remaining legacy components
- Full cloud deployment

## Risk Mitigation
- **Parallel Running** - New and old systems run simultaneously
- **Data Synchronization** - Bi-directional sync during transition
- **Rollback Plans** - Complete rollback capability at each phase
- **Performance Testing** - Continuous load testing throughout migration`,
        relationships: [
          {
            id: 'rel-ms-1',
            targetNodeId: 'enterprise-architecture',
            type: 'references',
            strength: 0.8,
            description: 'Migration target architecture'
          }
        ],
        metadata: {
          lastModified: new Date('2024-01-20'),
          author: 'Migration Program Manager',
          tags: ['migration', 'strategy', 'roadmap', 'planning'],
          criticality: 'high',
          migrationStatus: 'modernizing'
        }
      }
    ];
  }

  private initializeDefaultView() {
    // Start with enterprise architecture overview
    if (this.rootNodes.length > 0) {
      this.navigateToNode(this.rootNodes[0]);
    }
  }

  navigateToNode(node: WikiNode) {
    this.currentNode = node;
    this.updateBreadcrumbs(node);
    this.clearSearch();
  }

  private updateBreadcrumbs(node: WikiNode) {
    this.breadcrumbs = [];
    let current: WikiNode | undefined = node;
    
    while (current) {
      this.breadcrumbs.unshift(current);
      current = this.findParentNode(current.parentId);
    }
  }

  private findParentNode(parentId?: string): WikiNode | undefined {
    if (!parentId) return undefined;
    return this.findNodeById(parentId, this.rootNodes);
  }

  private findNodeById(id: string, nodes: WikiNode[]): WikiNode | undefined {
    for (const node of nodes) {
      if (node.id === id) return node;
      if (node.children) {
        const found = this.findNodeById(id, node.children);
        if (found) return found;
      }
    }
    return undefined;
  }

  toggleNodeExpansion(nodeId: string) {
    if (this.expandedNodes.has(nodeId)) {
      this.expandedNodes.delete(nodeId);
    } else {
      this.expandedNodes.add(nodeId);
    }
  }

  async performSearch() {
    if (!this.searchQuery.trim()) {
      this.clearSearch();
      return;
    }

    this.isSearching = true;
    this.searchResults = [];

    try {
      // Simulate search across all nodes
      const results = this.searchInNodes(this.searchQuery.toLowerCase(), this.rootNodes);
      this.searchResults = results.sort((a, b) => b.relevanceScore - a.relevanceScore);
    } catch (error) {
      console.error('Search error:', error);
    } finally {
      this.isSearching = false;
    }
  }

  private searchInNodes(query: string, nodes: WikiNode[]): WikiSearchResult[] {
    const results: WikiSearchResult[] = [];

    for (const node of nodes) {
      // Search in title
      if (node.title.toLowerCase().includes(query)) {
        results.push({
          node,
          relevanceScore: 0.9,
          matchType: 'title',
          snippet: node.title
        });
      }

      // Search in content
      const contentMatch = node.content.toLowerCase().indexOf(query);
      if (contentMatch !== -1) {
        const snippet = this.extractSnippet(node.content, contentMatch, query);
        results.push({
          node,
          relevanceScore: 0.7,
          matchType: 'content',
          snippet
        });
      }

      // Search in tags
      if (node.metadata.tags.some(tag => tag.toLowerCase().includes(query))) {
        results.push({
          node,
          relevanceScore: 0.6,
          matchType: 'tag',
          snippet: node.metadata.tags.join(', ')
        });
      }

      // Search in children
      if (node.children) {
        results.push(...this.searchInNodes(query, node.children));
      }
    }

    return results;
  }

  private extractSnippet(content: string, matchIndex: number, query: string): string {
    const snippetLength = 150;
    const start = Math.max(0, matchIndex - 50);
    const end = Math.min(content.length, start + snippetLength);
    
    let snippet = content.substring(start, end);
    if (start > 0) snippet = '...' + snippet;
    if (end < content.length) snippet = snippet + '...';
    
    // Highlight the query term
    const regex = new RegExp(`(${query})`, 'gi');
    snippet = snippet.replace(regex, '<mark>$1</mark>');
    
    return snippet;
  }

  clearSearch() {
    this.searchQuery = '';
    this.searchResults = [];
  }

  toggleRelationshipMap() {
    this.showRelationshipMap = !this.showRelationshipMap;
  }

  getFilteredNodes(): WikiNode[] {
    return this.rootNodes.filter(node => 
      this.selectedNodeTypes.has(node.type) &&
      this.selectedCriticality.has(node.metadata.criticality) &&
      this.selectedMigrationStatus.has(node.metadata.migrationStatus)
    );
  }

  getRelatedNodes(node: WikiNode): WikiNode[] {
    const relatedIds = node.relationships.map(rel => rel.targetNodeId);
    return relatedIds
      .map(id => this.findNodeById(id, this.rootNodes))
      .filter(n => n !== undefined) as WikiNode[];
  }

  getCriticalityColor(criticality: string): string {
    const colors = {
      'low': '#10b981',      // green
      'medium': '#f59e0b',   // amber  
      'high': '#ef4444',     // red
      'critical': '#dc2626'  // dark red
    };
    return colors[criticality as keyof typeof colors] || '#6b7280';
  }

  getMigrationStatusColor(status: string): string {
    const colors = {
      'legacy': '#ef4444',      // red
      'modernizing': '#f59e0b', // amber
      'modern': '#10b981',      // green
      'deprecated': '#6b7280'   // gray
    };
    return colors[status as keyof typeof colors] || '#6b7280';
  }

  startEditing() {
    if (this.currentNode) {
      this.isEditing = true;
      this.editingContent = this.currentNode.content;
    }
  }

  saveContent() {
    if (this.currentNode && this.editingContent) {
      this.currentNode.content = this.editingContent;
      this.currentNode.metadata.lastModified = new Date();
      this.isEditing = false;
      
      // In a real implementation, save to backend
      console.log('Saving content for node:', this.currentNode.id);
    }
  }

  cancelEditing() {
    this.isEditing = false;
    this.editingContent = '';
  }

  exportWikiStructure() {
    const data = {
      exportDate: new Date().toISOString(),
      structure: this.rootNodes
    };
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'deep-wiki-export.json';
    link.click();
    window.URL.revokeObjectURL(url);
  }
}