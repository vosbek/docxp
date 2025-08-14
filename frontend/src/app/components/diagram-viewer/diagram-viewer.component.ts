import { Component, Input, OnInit, OnDestroy, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ButtonModule } from 'primeng/button';
import { DropdownModule } from 'primeng/dropdown';
import { TooltipModule } from 'primeng/tooltip';
import { MessageService } from 'primeng/api';
import mermaid from 'mermaid';

// Enterprise-grade type definitions for diagram data
export type DiagramType = 
  | 'class' 
  | 'flow' 
  | 'migration_architecture' 
  | 'migration_risk_matrix' 
  | 'data_flow' 
  | 'technology_integration' 
  | 'legacy_architecture';

export interface DiagramData {
  readonly id: string;
  readonly name: string;
  readonly type: DiagramType;
  readonly content: string;
  readonly description?: string;
}

export interface DiagramOption {
  readonly label: string;
  readonly value: DiagramData;
  readonly icon: string;
}

export interface ExportFormat {
  readonly format: 'png' | 'svg' | 'pdf';
  readonly mimeType: string;
  readonly extension: string;
}

@Component({
  selector: 'app-diagram-viewer',
  standalone: true,
  imports: [CommonModule, FormsModule, ButtonModule, DropdownModule, TooltipModule],
  templateUrl: './diagram-viewer.component.html',
  styleUrl: './diagram-viewer.component.scss'
})
export class DiagramViewerComponent implements OnInit, OnDestroy {
  @Input() diagrams: DiagramData[] = [];
  @Input() initialDiagram?: string;
  @ViewChild('diagramContainer', { static: true }) diagramContainer!: ElementRef;

  selectedDiagram: DiagramData | null = null;
  diagramOptions: DiagramOption[] = [];
  isLoading = false;
  zoomLevel = 1;
  private mermaidInitialized = false;

  constructor(private messageService: MessageService) {}

  ngOnInit() {
    this.initializeMermaid();
    this.setupDiagramOptions();
    
    // Set initial diagram
    if (this.initialDiagram) {
      const initial = this.diagrams.find(d => d.id === this.initialDiagram);
      if (initial) {
        this.selectedDiagram = initial;
      }
    }
    
    // Default to first diagram if no initial diagram specified
    if (!this.selectedDiagram && this.diagrams.length > 0) {
      this.selectedDiagram = this.diagrams[0];
    }
    
    if (this.selectedDiagram) {
      this.renderDiagram();
    }
  }

  ngOnDestroy() {
    // Clean up any event listeners or subscriptions
  }

  private initializeMermaid() {
    if (!this.mermaidInitialized) {
      mermaid.initialize({
        startOnLoad: true,
        theme: 'default',
        securityLevel: 'strict', // Changed from 'loose' to 'strict' for enterprise security
        fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
        fontSize: 14,
        // Enhanced security configuration for enterprise deployment
        dompurifyConfig: {
          USE_PROFILES: { html: true },
          FORBID_TAGS: ['script', 'object', 'embed', 'link'],
          FORBID_ATTR: ['onclick', 'onmouseover', 'onload', 'onerror']
        },
        sequence: {
          actorMargin: 50,
          width: 150,
          height: 65,
          boxMargin: 10,
          boxTextMargin: 5,
          noteMargin: 10,
          messageMargin: 35
        },
        flowchart: {
          nodeSpacing: 50,
          rankSpacing: 50,
          curve: 'basis',
          padding: 10
        },
        gantt: {
          numberSectionStyles: 4,
          axisFormat: '%Y-%m-%d'
        }
      });
      this.mermaidInitialized = true;
    }
  }

  private setupDiagramOptions() {
    this.diagramOptions = this.diagrams.map(diagram => ({
      label: this.getDiagramDisplayName(diagram.type, diagram.name),
      value: diagram,
      icon: this.getDiagramIcon(diagram.type)
    }));
  }

  private getDiagramDisplayName(type: DiagramType, name: string): string {
    const displayNames: Record<DiagramType, string> = {
      'class': '📊 Class Diagram',
      'flow': '🔄 Flow Diagram', 
      'migration_architecture': '🏗️ Migration Architecture',
      'migration_risk_matrix': '⚠️ Risk Assessment Matrix',
      'data_flow': '📊 Data Flow Diagram',
      'technology_integration': '🔗 Technology Integration Map',
      'legacy_architecture': '🏛️ Legacy Architecture'
    };
    return displayNames[type] || name;
  }

  private getDiagramIcon(type: DiagramType): string {
    const icons: Record<DiagramType, string> = {
      'class': 'pi pi-sitemap',
      'flow': 'pi pi-share-alt',
      'migration_architecture': 'pi pi-building',
      'migration_risk_matrix': 'pi pi-exclamation-triangle',
      'data_flow': 'pi pi-arrows-h', 
      'technology_integration': 'pi pi-link',
      'legacy_architecture': 'pi pi-server'
    };
    return icons[type] || 'pi pi-chart-bar';
  }

  onDiagramSelectionChange(event: any) {
    this.selectedDiagram = event.value;
    if (this.selectedDiagram) {
      this.renderDiagram();
    }
  }

  async renderDiagram() {
    if (!this.selectedDiagram || !this.diagramContainer) {
      return;
    }

    this.isLoading = true;

    try {
      // Clear previous content
      const container = this.diagramContainer.nativeElement;
      container.innerHTML = '';

      // Generate unique ID for this render
      const diagramId = `diagram-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
      
      // Create diagram element
      const diagramDiv = document.createElement('div');
      diagramDiv.id = diagramId;
      diagramDiv.className = 'mermaid-diagram';
      container.appendChild(diagramDiv);

      // Render the diagram
      const { svg } = await mermaid.render(diagramId + '-svg', this.selectedDiagram.content);
      diagramDiv.innerHTML = svg;

      // Add interactivity
      this.addInteractivity(diagramDiv);

      this.messageService.add({
        severity: 'success',
        summary: 'Diagram Loaded',
        detail: `${this.getDiagramDisplayName(this.selectedDiagram.type, this.selectedDiagram.name)} rendered successfully`,
        life: 3000
      });

    } catch (error) {
      console.error('Error rendering diagram:', error);
      this.messageService.add({
        severity: 'error',
        summary: 'Diagram Error',
        detail: 'Failed to render diagram. Please check the diagram syntax.',
        life: 5000
      });
      
      // Show error fallback
      this.showErrorFallback();
    } finally {
      this.isLoading = false;
    }
  }

  private addInteractivity(diagramElement: HTMLElement) {
    // Add zoom controls
    diagramElement.style.transform = `scale(${this.zoomLevel})`;
    diagramElement.style.transformOrigin = 'top left';
    
    // Add click handlers for nodes (future enhancement)
    const nodes = diagramElement.querySelectorAll('[id*="node"]');
    nodes.forEach(node => {
      node.addEventListener('click', (event) => {
        this.onNodeClick(event, node);
      });
    });

    // Add hover tooltips (future enhancement)
    const elements = diagramElement.querySelectorAll('g[class*="node"], rect, circle');
    elements.forEach(element => {
      element.addEventListener('mouseenter', (event) => {
        this.showElementTooltip(event, element);
      });
      element.addEventListener('mouseleave', () => {
        this.hideElementTooltip();
      });
    });
  }

  private onNodeClick(event: Event, node: Element) {
    event.preventDefault();
    console.log('Node clicked:', node);
    // TODO: Implement navigation to source code
    // This could emit an event to parent component or navigate to code view
  }

  private showElementTooltip(event: Event, element: Element) {
    // TODO: Implement tooltip showing component details like complexity, risk, etc.
    console.log('Element hovered:', element);
  }

  private hideElementTooltip() {
    // TODO: Hide tooltip
  }

  private showErrorFallback() {
    const container = this.diagramContainer.nativeElement;
    container.innerHTML = `
      <div class="diagram-error">
        <i class="pi pi-exclamation-triangle error-icon"></i>
        <h3>Diagram Rendering Error</h3>
        <p>Unable to render the selected diagram. Please try selecting a different diagram.</p>
        <button class="p-button p-button-outlined p-button-sm" onclick="location.reload()">
          <i class="pi pi-refresh"></i> Refresh
        </button>
      </div>
    `;
  }

  // Zoom controls
  zoomIn() {
    this.zoomLevel = Math.min(this.zoomLevel + 0.25, 3);
    this.applyZoom();
  }

  zoomOut() {
    this.zoomLevel = Math.max(this.zoomLevel - 0.25, 0.25);
    this.applyZoom();
  }

  resetZoom() {
    this.zoomLevel = 1;
    this.applyZoom();
  }

  private applyZoom() {
    if (this.diagramContainer) {
      const diagram = this.diagramContainer.nativeElement.querySelector('.mermaid-diagram');
      if (diagram) {
        diagram.style.transform = `scale(${this.zoomLevel})`;
      }
    }
  }

  // Enterprise-grade export functionality with proper error handling
  async exportDiagram(format: ExportFormat['format']): Promise<void> {
    if (!this.selectedDiagram) {
      this.showErrorMessage('Export Failed', 'No diagram selected for export');
      return;
    }

    const exportFormats: Record<ExportFormat['format'], ExportFormat> = {
      'svg': { format: 'svg', mimeType: 'image/svg+xml', extension: 'svg' },
      'png': { format: 'png', mimeType: 'image/png', extension: 'png' },
      'pdf': { format: 'pdf', mimeType: 'application/pdf', extension: 'pdf' }
    };

    const selectedFormat = exportFormats[format];
    if (!selectedFormat) {
      this.showErrorMessage('Export Failed', `Unsupported export format: ${format}`);
      return;
    }

    try {
      const diagramElement = this.diagramContainer.nativeElement.querySelector('svg') as SVGElement;
      if (!diagramElement) {
        throw new Error('No diagram element found for export');
      }

      const sanitizedName = this.sanitizeFileName(this.selectedDiagram.name);
      const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
      const filename = `${sanitizedName}_${this.selectedDiagram.type}_${timestamp}.${selectedFormat.extension}`;

      switch (format) {
        case 'svg':
          await this.downloadSVG(diagramElement, filename);
          break;
        case 'png':
          await this.downloadPNG(diagramElement, filename);
          break;
        case 'pdf':
          await this.downloadPDF(diagramElement, filename);
          break;
        default:
          throw new Error(`Unsupported format: ${format}`);
      }

      this.showSuccessMessage('Export Successful', `Diagram exported as ${format.toUpperCase()}: ${filename}`);

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      console.error('Export error:', error);
      this.showErrorMessage('Export Failed', `Failed to export diagram: ${errorMessage}`);
    }
  }

  private sanitizeFileName(name: string): string {
    return name.replace(/[^a-z0-9]/gi, '_').toLowerCase();
  }

  private showSuccessMessage(summary: string, detail: string): void {
    this.messageService.add({
      severity: 'success',
      summary,
      detail,
      life: 3000
    });
  }

  private showErrorMessage(summary: string, detail: string): void {
    this.messageService.add({
      severity: 'error',
      summary,
      detail,
      life: 5000
    });
  }

  private async downloadSVG(svgElement: SVGElement, filename: string): Promise<void> {
    try {
      const svgData = new XMLSerializer().serializeToString(svgElement);
      const blob = new Blob([svgData], { type: 'image/svg+xml' });
      this.downloadBlob(blob, filename);
    } catch (error) {
      throw new Error(`SVG export failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  private async downloadPNG(svgElement: SVGElement, filename: string): Promise<void> {
    try {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      if (!ctx) {
        throw new Error('Canvas 2D context not available in this browser');
      }

      const img = new Image();
      const svgData = new XMLSerializer().serializeToString(svgElement);
      
      // Ensure SVG has proper dimensions
      const svgRect = svgElement.getBoundingClientRect();
      if (svgRect.width === 0 || svgRect.height === 0) {
        throw new Error('SVG element has no dimensions for PNG conversion');
      }

      const svg64 = btoa(unescape(encodeURIComponent(svgData)));
      const b64Start = 'data:image/svg+xml;base64,';

      return new Promise<void>((resolve, reject) => {
        const timeout = setTimeout(() => {
          reject(new Error('PNG conversion timeout - image loading took too long'));
        }, 10000); // 10-second timeout

        img.onload = () => {
          clearTimeout(timeout);
          try {
            canvas.width = img.naturalWidth || svgRect.width;
            canvas.height = img.naturalHeight || svgRect.height;
            
            // Set white background for better contrast
            ctx.fillStyle = 'white';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            
            ctx.drawImage(img, 0, 0);
            
            canvas.toBlob(blob => {
              if (blob) {
                this.downloadBlob(blob, filename);
                resolve();
              } else {
                reject(new Error('Failed to create PNG blob from canvas'));
              }
            }, 'image/png', 1.0);
          } catch (drawError) {
            reject(new Error(`Canvas drawing failed: ${drawError instanceof Error ? drawError.message : 'Unknown error'}`));
          }
        };
        
        img.onerror = () => {
          clearTimeout(timeout);
          reject(new Error('Failed to load SVG as image for PNG conversion'));
        };
        
        img.src = b64Start + svg64;
      });
    } catch (error) {
      throw new Error(`PNG export failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  private async downloadPDF(svgElement: SVGElement, filename: string): Promise<void> {
    try {
      // For enterprise-grade PDF export, we would typically use a library like jsPDF
      // For now, we'll fallback to PNG export with a clear message
      const pngFilename = filename.replace('.pdf', '.png');
      this.showSuccessMessage('PDF Export Note', 'PDF export is currently implemented as high-quality PNG. Enterprise PDF support coming soon.');
      await this.downloadPNG(svgElement, pngFilename);
    } catch (error) {
      throw new Error(`PDF export failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  private downloadBlob(blob: Blob, filename: string) {
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }

  // Utility methods
  get hasMultipleDiagrams(): boolean {
    return this.diagrams.length > 1;
  }

  get currentDiagramInfo(): string {
    if (!this.selectedDiagram) return '';
    return `${this.getDiagramDisplayName(this.selectedDiagram.type, this.selectedDiagram.name)}`;
  }
}