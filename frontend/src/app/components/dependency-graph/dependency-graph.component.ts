import { Component, OnInit, OnDestroy, Input, ViewChild, ElementRef, AfterViewInit } from '@angular/core';
import { Subject, takeUntil } from 'rxjs';
import { MatSnackBar } from '@angular/material/snack-bar';
import { 
  JQAssistantService, 
  DependencyGraph, 
  DependencyNode, 
  DependencyEdge 
} from '../../services/jqassistant.service';

// Interface for graph layout and visualization
interface GraphConfig {
  showCycles: boolean;
  showWeights: boolean;
  packageFilter: string;
  layoutAlgorithm: 'force' | 'hierarchical' | 'circular';
  nodeSize: 'uniform' | 'weighted';
  edgeThickness: 'uniform' | 'weighted';
  highlightCycles: boolean;
  groupByLayer: boolean;
}

interface GraphLayoutNode extends DependencyNode {
  x?: number;
  y?: number;
  fx?: number;
  fy?: number;
  vx?: number;
  vy?: number;
  group?: string;
  size?: number;
  highlighted?: boolean;
}

interface GraphLayoutEdge extends DependencyEdge {
  highlighted?: boolean;
  curved?: boolean;
}

@Component({
  selector: 'app-dependency-graph',
  templateUrl: './dependency-graph.component.html',
  styleUrls: ['./dependency-graph.component.scss']
})
export class DependencyGraphComponent implements OnInit, OnDestroy, AfterViewInit {
  @Input() jobId: string | null = null;
  @Input() height: number = 600;
  @Input() width: number = 800;
  
  @ViewChild('graphContainer', { static: true }) graphContainer!: ElementRef;
  @ViewChild('minimap', { static: false }) minimap!: ElementRef;

  // Graph data and configuration
  dependencyGraph: DependencyGraph | null = null;
  processedNodes: GraphLayoutNode[] = [];
  processedEdges: GraphLayoutEdge[] = [];
  
  config: GraphConfig = {
    showCycles: true,
    showWeights: true,
    packageFilter: '',
    layoutAlgorithm: 'force',
    nodeSize: 'weighted',
    edgeThickness: 'weighted',
    highlightCycles: true,
    groupByLayer: true
  };

  // UI state
  isLoading = false;
  selectedNode: GraphLayoutNode | null = null;
  selectedEdge: GraphLayoutEdge | null = null;
  zoomLevel = 1;
  showMinimap = true;
  showLegend = true;
  showNodeLabels = true;
  
  // Graph statistics
  stats = {
    totalNodes: 0,
    totalEdges: 0,
    cyclicEdges: 0,
    maxWeight: 0,
    layers: [] as string[],
    stronglyConnectedComponents: 0
  };

  // Simulation and rendering
  private simulation: any;
  private svg: any;
  private g: any;
  private zoom: any;
  private destroy$ = new Subject<void>();

  constructor(
    private jqassistantService: JQAssistantService,
    private snackBar: MatSnackBar
  ) {}

  ngOnInit(): void {
    this.loadDependencyGraph();
  }

  ngAfterViewInit(): void {
    this.initializeVisualization();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
    if (this.simulation) {
      this.simulation.stop();
    }
  }

  async loadDependencyGraph(): Promise<void> {
    if (!this.jobId) return;

    this.isLoading = true;
    try {
      this.dependencyGraph = await this.jqassistantService.getDependencyGraph(
        this.jobId,
        'json',
        this.config.showCycles,
        this.config.packageFilter || undefined
      ).toPromise();

      this.processGraphData();
      this.calculateStatistics();
      this.renderGraph();

    } catch (error) {
      console.error('Failed to load dependency graph:', error);
      this.snackBar.open('Failed to load dependency graph', 'Close', {
        duration: 5000,
        panelClass: ['error-snackbar']
      });
    } finally {
      this.isLoading = false;
    }
  }

  private processGraphData(): void {
    if (!this.dependencyGraph) return;

    // Process nodes
    this.processedNodes = this.dependencyGraph.nodes.map((node, index) => ({
      ...node,
      group: node.layer || 'unknown',
      size: this.calculateNodeSize(node),
      highlighted: false
    }));

    // Process edges
    this.processedEdges = this.dependencyGraph.edges.map(edge => ({
      ...edge,
      highlighted: false,
      curved: this.shouldCurveEdge(edge)
    }));

    // Apply filters
    this.applyFilters();
  }

  private calculateNodeSize(node: DependencyNode): number {
    if (this.config.nodeSize === 'uniform') {
      return 10;
    }
    
    // Calculate size based on in-degree and out-degree
    const inDegree = this.dependencyGraph?.edges.filter(e => e.target === node.id).length || 0;
    const outDegree = this.dependencyGraph?.edges.filter(e => e.source === node.id).length || 0;
    const totalDegree = inDegree + outDegree;
    
    return Math.max(8, Math.min(25, 8 + totalDegree * 2));
  }

  private shouldCurveEdge(edge: DependencyEdge): boolean {
    // Curve edges that create visual overlaps or are part of cycles
    return edge.is_cyclic || false;
  }

  private calculateStatistics(): void {
    if (!this.dependencyGraph) return;

    this.stats = {
      totalNodes: this.processedNodes.length,
      totalEdges: this.processedEdges.length,
      cyclicEdges: this.processedEdges.filter(e => e.is_cyclic).length,
      maxWeight: Math.max(...this.processedEdges.map(e => e.weight)),
      layers: [...new Set(this.processedNodes.map(n => n.group))].filter(Boolean),
      stronglyConnectedComponents: this.calculateSCCs()
    };
  }

  private calculateSCCs(): number {
    // Simplified SCC calculation for visualization
    // In a real implementation, you'd use Tarjan's or Kosaraju's algorithm
    return Math.ceil(this.stats.cyclicEdges / 3);
  }

  private applyFilters(): void {
    if (this.config.packageFilter) {
      const filterRegex = new RegExp(this.config.packageFilter, 'i');
      this.processedNodes = this.processedNodes.filter(node => 
        filterRegex.test(node.id) || filterRegex.test(node.label)
      );
      
      const nodeIds = new Set(this.processedNodes.map(n => n.id));
      this.processedEdges = this.processedEdges.filter(edge =>
        nodeIds.has(edge.source) && nodeIds.has(edge.target)
      );
    }

    if (!this.config.showCycles) {
      this.processedEdges = this.processedEdges.filter(edge => !edge.is_cyclic);
    }
  }

  private initializeVisualization(): void {
    const container = this.graphContainer.nativeElement;
    
    // Clear any existing content
    container.innerHTML = '';
    
    // Create SVG
    this.svg = d3.select(container)
      .append('svg')
      .attr('width', this.width)
      .attr('height', this.height)
      .style('border', '1px solid #ccc');

    // Add zoom behavior
    this.zoom = d3.zoom()
      .scaleExtent([0.1, 10])
      .on('zoom', (event) => {
        this.g.attr('transform', event.transform);
        this.zoomLevel = event.transform.k;
      });

    this.svg.call(this.zoom);

    // Create main group
    this.g = this.svg.append('g');

    // Add defs for markers and patterns
    this.addSVGDefinitions();
  }

  private addSVGDefinitions(): void {
    const defs = this.svg.append('defs');

    // Arrow markers for directed edges
    defs.append('marker')
      .attr('id', 'arrowhead')
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 15)
      .attr('refY', 0)
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,-5L10,0L0,5')
      .attr('fill', '#666');

    // Arrow marker for cyclic edges
    defs.append('marker')
      .attr('id', 'arrowhead-cyclic')
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 15)
      .attr('refY', 0)
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,-5L10,0L0,5')
      .attr('fill', '#f44336');

    // Patterns for different node types
    const patterns = ['controller', 'service', 'repository', 'entity'];
    patterns.forEach((pattern, index) => {
      const patternDef = defs.append('pattern')
        .attr('id', `pattern-${pattern}`)
        .attr('patternUnits', 'userSpaceOnUse')
        .attr('width', 20)
        .attr('height', 20);
      
      patternDef.append('rect')
        .attr('width', 20)
        .attr('height', 20)
        .attr('fill', this.getLayerColor(pattern));
      
      patternDef.append('circle')
        .attr('cx', 10)
        .attr('cy', 10)
        .attr('r', 3)
        .attr('fill', 'white')
        .attr('opacity', 0.7);
    });
  }

  private renderGraph(): void {
    if (!this.processedNodes.length) return;

    // Create force simulation
    this.simulation = d3.forceSimulation(this.processedNodes)
      .force('link', d3.forceLink(this.processedEdges).id((d: any) => d.id).distance(80))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(this.width / 2, this.height / 2))
      .force('collision', d3.forceCollide().radius((d: any) => d.size + 5));

    // Apply layout-specific forces
    this.applyLayoutForces();

    // Render edges
    this.renderEdges();

    // Render nodes
    this.renderNodes();

    // Add labels if enabled
    if (this.showNodeLabels) {
      this.renderLabels();
    }

    // Start simulation
    this.simulation.on('tick', () => this.updatePositions());
  }

  private applyLayoutForces(): void {
    switch (this.config.layoutAlgorithm) {
      case 'hierarchical':
        this.simulation
          .force('y', d3.forceY().y((d: any) => this.getHierarchicalY(d)).strength(0.3));
        break;
      
      case 'circular':
        this.simulation
          .force('radial', d3.forceRadial(150, this.width / 2, this.height / 2).strength(0.3));
        break;
      
      default: // force
        // Default force layout already configured
        break;
    }

    if (this.config.groupByLayer) {
      this.simulation
        .force('cluster', this.forceCluster().strength(0.2));
    }
  }

  private getHierarchicalY(node: GraphLayoutNode): number {
    const layerOrder = ['entity', 'repository', 'service', 'controller'];
    const layerIndex = layerOrder.indexOf(node.layer || 'unknown');
    return layerIndex >= 0 ? (layerIndex + 1) * (this.height / (layerOrder.length + 1)) : this.height / 2;
  }

  private forceCluster() {
    const strength = 0.2;
    const nodes = this.processedNodes;

    function force(alpha: number) {
      for (let i = 0, n = nodes.length; i < n; ++i) {
        const node = nodes[i];
        const cluster = nodes.find(n => n.group === node.group);
        if (cluster === node) continue;
        
        let x = node.x! - cluster!.x!;
        let y = node.y! - cluster!.y!;
        let l = Math.sqrt(x * x + y * y);
        let r = node.size! + cluster!.size!;
        
        if (l !== r) {
          l = (l - r) / l * alpha * strength;
          node.x! -= x *= l;
          node.y! -= y *= l;
          cluster!.x! += x;
          cluster!.y! += y;
        }
      }
    }

    return force;
  }

  private renderEdges(): void {
    const edges = this.g.selectAll('.edge')
      .data(this.processedEdges)
      .enter()
      .append('line')
      .attr('class', 'edge')
      .attr('stroke', (d: GraphLayoutEdge) => d.is_cyclic ? '#f44336' : '#666')
      .attr('stroke-width', (d: GraphLayoutEdge) => 
        this.config.edgeThickness === 'weighted' ? Math.max(1, d.weight / 2) : 2
      )
      .attr('marker-end', (d: GraphLayoutEdge) => 
        d.is_cyclic ? 'url(#arrowhead-cyclic)' : 'url(#arrowhead)'
      )
      .style('opacity', 0.6)
      .on('click', (event, d) => this.onEdgeClick(d))
      .on('mouseover', (event, d) => this.onEdgeHover(d, true))
      .on('mouseout', (event, d) => this.onEdgeHover(d, false));

    // Add weight labels for edges if enabled
    if (this.config.showWeights) {
      this.g.selectAll('.edge-label')
        .data(this.processedEdges.filter(e => e.weight > 1))
        .enter()
        .append('text')
        .attr('class', 'edge-label')
        .attr('text-anchor', 'middle')
        .attr('dy', -2)
        .attr('font-size', '10px')
        .attr('fill', '#333')
        .text((d: GraphLayoutEdge) => d.weight);
    }
  }

  private renderNodes(): void {
    const nodes = this.g.selectAll('.node')
      .data(this.processedNodes)
      .enter()
      .append('circle')
      .attr('class', 'node')
      .attr('r', (d: GraphLayoutNode) => d.size)
      .attr('fill', (d: GraphLayoutNode) => this.getNodeColor(d))
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .style('cursor', 'pointer')
      .on('click', (event, d) => this.onNodeClick(d))
      .on('mouseover', (event, d) => this.onNodeHover(d, true))
      .on('mouseout', (event, d) => this.onNodeHover(d, false))
      .call(this.createDragBehavior());
  }

  private renderLabels(): void {
    this.g.selectAll('.label')
      .data(this.processedNodes)
      .enter()
      .append('text')
      .attr('class', 'label')
      .attr('text-anchor', 'middle')
      .attr('dy', (d: GraphLayoutNode) => d.size! + 15)
      .attr('font-size', '10px')
      .attr('fill', '#333')
      .text((d: GraphLayoutNode) => this.getShortLabel(d.label))
      .style('pointer-events', 'none');
  }

  private getShortLabel(label: string): string {
    const parts = label.split('.');
    return parts.length > 1 ? parts[parts.length - 1] : label;
  }

  private updatePositions(): void {
    this.g.selectAll('.edge')
      .attr('x1', (d: any) => d.source.x)
      .attr('y1', (d: any) => d.source.y)
      .attr('x2', (d: any) => d.target.x)
      .attr('y2', (d: any) => d.target.y);

    this.g.selectAll('.edge-label')
      .attr('x', (d: any) => (d.source.x + d.target.x) / 2)
      .attr('y', (d: any) => (d.source.y + d.target.y) / 2);

    this.g.selectAll('.node')
      .attr('cx', (d: any) => d.x)
      .attr('cy', (d: any) => d.y);

    this.g.selectAll('.label')
      .attr('x', (d: any) => d.x)
      .attr('y', (d: any) => d.y);
  }

  private createDragBehavior(): any {
    return d3.drag()
      .on('start', (event, d: any) => {
        if (!event.active) this.simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
      })
      .on('drag', (event, d: any) => {
        d.fx = event.x;
        d.fy = event.y;
      })
      .on('end', (event, d: any) => {
        if (!event.active) this.simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
      });
  }

  private getNodeColor(node: GraphLayoutNode): string {
    if (node.highlighted) return '#ff9800';
    return this.getLayerColor(node.layer || 'unknown');
  }

  private getLayerColor(layer: string): string {
    const colors: { [key: string]: string } = {
      'controller': '#f44336',
      'service': '#2196f3',
      'repository': '#4caf50',
      'entity': '#9c27b0',
      'dto': '#ff9800',
      'unknown': '#9e9e9e'
    };
    return colors[layer.toLowerCase()] || colors['unknown'];
  }

  onNodeClick(node: GraphLayoutNode): void {
    this.selectedNode = node;
    this.highlightConnectedElements(node);
  }

  onEdgeClick(edge: GraphLayoutEdge): void {
    this.selectedEdge = edge;
  }

  onNodeHover(node: GraphLayoutNode, isEntering: boolean): void {
    if (isEntering) {
      this.showNodeTooltip(node);
    } else {
      this.hideTooltip();
    }
  }

  onEdgeHover(edge: GraphLayoutEdge, isEntering: boolean): void {
    if (isEntering) {
      this.showEdgeTooltip(edge);
    } else {
      this.hideTooltip();
    }
  }

  private highlightConnectedElements(node: GraphLayoutNode): void {
    // Reset all highlights
    this.processedNodes.forEach(n => n.highlighted = false);
    this.processedEdges.forEach(e => e.highlighted = false);

    // Highlight selected node
    node.highlighted = true;

    // Highlight connected edges and nodes
    this.processedEdges.forEach(edge => {
      if (edge.source === node.id || edge.target === node.id) {
        edge.highlighted = true;
        
        // Highlight connected nodes
        const connectedNodeId = edge.source === node.id ? edge.target : edge.source;
        const connectedNode = this.processedNodes.find(n => n.id === connectedNodeId);
        if (connectedNode) {
          connectedNode.highlighted = true;
        }
      }
    });

    this.updateHighlights();
  }

  private updateHighlights(): void {
    this.g.selectAll('.node')
      .attr('stroke', (d: GraphLayoutNode) => d.highlighted ? '#ff9800' : '#fff')
      .attr('stroke-width', (d: GraphLayoutNode) => d.highlighted ? 3 : 2);

    this.g.selectAll('.edge')
      .style('opacity', (d: GraphLayoutEdge) => d.highlighted ? 1 : 0.3)
      .attr('stroke-width', (d: GraphLayoutEdge) => {
        const baseWidth = this.config.edgeThickness === 'weighted' ? Math.max(1, d.weight / 2) : 2;
        return d.highlighted ? baseWidth * 2 : baseWidth;
      });
  }

  private showNodeTooltip(node: GraphLayoutNode): void {
    // Implementation would show a tooltip with node details
  }

  private showEdgeTooltip(edge: GraphLayoutEdge): void {
    // Implementation would show a tooltip with edge details
  }

  private hideTooltip(): void {
    // Implementation would hide tooltips
  }

  onConfigChange(): void {
    this.processGraphData();
    this.calculateStatistics();
    this.renderGraph();
  }

  resetZoom(): void {
    this.svg.transition().duration(750).call(
      this.zoom.transform,
      d3.zoomIdentity
    );
  }

  fitToView(): void {
    const bounds = this.g.node().getBBox();
    const parent = this.g.node().parentElement;
    const fullWidth = parent.clientWidth || parent.parentNode.clientWidth;
    const fullHeight = parent.clientHeight || parent.parentNode.clientHeight;
    const width = bounds.width;
    const height = bounds.height;
    const midX = bounds.x + width / 2;
    const midY = bounds.y + height / 2;
    
    if (width === 0 || height === 0) return;
    
    const scale = 0.9 / Math.max(width / fullWidth, height / fullHeight);
    const translate = [fullWidth / 2 - scale * midX, fullHeight / 2 - scale * midY];
    
    this.svg.transition().duration(750).call(
      this.zoom.transform,
      d3.zoomIdentity.translate(translate[0], translate[1]).scale(scale)
    );
  }

  exportGraph(format: 'svg' | 'png' = 'svg'): void {
    if (format === 'svg') {
      const svgString = new XMLSerializer().serializeToString(this.svg.node());
      const blob = new Blob([svgString], { type: 'image/svg+xml' });
      this.downloadBlob(blob, 'dependency-graph.svg');
    } else {
      // Implementation for PNG export would go here
      this.snackBar.open('PNG export not yet implemented', 'Close', {
        duration: 3000
      });
    }
  }

  private downloadBlob(blob: Blob, filename: string): void {
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  }

  clearSelection(): void {
    this.selectedNode = null;
    this.selectedEdge = null;
    this.processedNodes.forEach(n => n.highlighted = false);
    this.processedEdges.forEach(e => e.highlighted = false);
    this.updateHighlights();
  }
}