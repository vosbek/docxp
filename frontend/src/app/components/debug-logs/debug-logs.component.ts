import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { LoggingService, LogEntry } from '../../services/logging.service';
import { Subscription, interval } from 'rxjs';

@Component({
  selector: 'app-debug-logs',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="debug-logs-container">
      <div class="debug-header">
        <h3>Debug Logs</h3>
        <div class="debug-controls">
          <select [(ngModel)]="selectedLevel" (change)="filterLogs()" class="level-filter">
            <option value="">All Levels</option>
            <option value="ERROR">Errors Only</option>
            <option value="WARN">Warnings+</option>
            <option value="INFO">Info+</option>
            <option value="DEBUG">Debug+</option>
          </select>
          
          <select [(ngModel)]="selectedCategory" (change)="filterLogs()" class="category-filter">
            <option value="">All Categories</option>
            <option *ngFor="let cat of categories" [value]="cat">{{cat}}</option>
          </select>
          
          <button (click)="clearLogs()" class="clear-btn">Clear</button>
          <button (click)="toggleAutoRefresh()" class="refresh-btn">
            {{ autoRefresh ? 'Stop' : 'Start' }} Auto-refresh
          </button>
          <button (click)="exportLogs()" class="export-btn">Export</button>
        </div>
      </div>
      
      <div class="logs-container">
        <div class="log-stats">
          <span class="stat error-count">Errors: {{errorCount}}</span>
          <span class="stat warn-count">Warnings: {{warnCount}}</span>
          <span class="stat info-count">Info: {{infoCount}}</span>
          <span class="stat debug-count">Debug: {{debugCount}}</span>
          <span class="stat total-count">Total: {{filteredLogs.length}}</span>
        </div>
        
        <div class="logs-list">
          <div 
            *ngFor="let log of filteredLogs | slice:0:maxDisplayedLogs; trackBy: trackByLogEntry"
            class="log-entry"
            [class.log-error]="log.level === 'ERROR'"
            [class.log-warn]="log.level === 'WARN'"
            [class.log-info]="log.level === 'INFO'"
            [class.log-debug]="log.level === 'DEBUG'"
          >
            <div class="log-main">
              <span class="log-timestamp">{{formatTime(log.timestamp)}}</span>
              <span class="log-level">{{log.level}}</span>
              <span class="log-category">{{log.category}}</span>
              <span class="log-message">{{log.message}}</span>
            </div>
            <div *ngIf="log.data && showDetails" class="log-data">
              <pre>{{formatData(log.data)}}</pre>
            </div>
          </div>
          
          <div *ngIf="filteredLogs.length > maxDisplayedLogs" class="more-logs">
            <button (click)="loadMoreLogs()" class="load-more-btn">
              Load More ({{filteredLogs.length - maxDisplayedLogs}} remaining)
            </button>
          </div>
          
          <div *ngIf="filteredLogs.length === 0" class="no-logs">
            No logs found matching current filters.
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .debug-logs-container {
      background: #1e1e1e;
      color: #d4d4d4;
      font-family: 'Courier New', monospace;
      height: 100%;
      display: flex;
      flex-direction: column;
    }
    
    .debug-header {
      padding: 1rem;
      border-bottom: 1px solid #333;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    
    .debug-header h3 {
      margin: 0;
      color: #569cd6;
    }
    
    .debug-controls {
      display: flex;
      gap: 0.5rem;
      align-items: center;
    }
    
    .level-filter, .category-filter {
      background: #2d2d30;
      color: #d4d4d4;
      border: 1px solid #3c3c3c;
      padding: 0.25rem 0.5rem;
      border-radius: 4px;
    }
    
    .clear-btn, .refresh-btn, .export-btn, .load-more-btn {
      background: #0e639c;
      color: white;
      border: none;
      padding: 0.25rem 0.5rem;
      border-radius: 4px;
      cursor: pointer;
      font-size: 0.8rem;
    }
    
    .clear-btn:hover, .refresh-btn:hover, .export-btn:hover, .load-more-btn:hover {
      background: #1177bb;
    }
    
    .logs-container {
      flex: 1;
      overflow: hidden;
      display: flex;
      flex-direction: column;
    }
    
    .log-stats {
      padding: 0.5rem 1rem;
      background: #252526;
      border-bottom: 1px solid #333;
      display: flex;
      gap: 1rem;
    }
    
    .stat {
      font-size: 0.8rem;
      padding: 0.2rem 0.4rem;
      border-radius: 3px;
    }
    
    .error-count { background: #3c1e1e; color: #f48771; }
    .warn-count { background: #3c3c1e; color: #dcdcaa; }
    .info-count { background: #1e3c3c; color: #9cdcfe; }
    .debug-count { background: #2d2d30; color: #808080; }
    .total-count { background: #1e1e3c; color: #c586c0; }
    
    .logs-list {
      flex: 1;
      overflow-y: auto;
      padding: 0.5rem;
    }
    
    .log-entry {
      margin-bottom: 0.25rem;
      padding: 0.5rem;
      border-radius: 4px;
      background: #2d2d30;
      border-left: 3px solid #666;
    }
    
    .log-error { border-left-color: #f48771; background: #3c1e1e; }
    .log-warn { border-left-color: #dcdcaa; background: #3c3c1e; }
    .log-info { border-left-color: #9cdcfe; background: #1e3c3c; }
    .log-debug { border-left-color: #808080; }
    
    .log-main {
      display: flex;
      gap: 0.5rem;
      align-items: center;
      font-size: 0.8rem;
    }
    
    .log-timestamp {
      color: #808080;
      min-width: 60px;
    }
    
    .log-level {
      font-weight: bold;
      min-width: 50px;
      text-align: center;
      padding: 0.1rem 0.3rem;
      border-radius: 3px;
      font-size: 0.7rem;
    }
    
    .log-error .log-level { background: #f48771; color: #000; }
    .log-warn .log-level { background: #dcdcaa; color: #000; }
    .log-info .log-level { background: #9cdcfe; color: #000; }
    .log-debug .log-level { background: #808080; color: #fff; }
    
    .log-category {
      color: #569cd6;
      min-width: 80px;
      font-weight: bold;
    }
    
    .log-message {
      flex: 1;
      word-break: break-word;
    }
    
    .log-data {
      margin-top: 0.5rem;
      padding: 0.5rem;
      background: #1e1e1e;
      border-radius: 3px;
      border: 1px solid #333;
    }
    
    .log-data pre {
      margin: 0;
      font-size: 0.7rem;
      color: #ce9178;
      white-space: pre-wrap;
      word-break: break-all;
    }
    
    .more-logs {
      text-align: center;
      padding: 1rem;
    }
    
    .no-logs {
      text-align: center;
      color: #808080;
      padding: 2rem;
    }
  `]
})
export class DebugLogsComponent implements OnInit, OnDestroy {
  logs: LogEntry[] = [];
  filteredLogs: LogEntry[] = [];
  categories: string[] = [];
  
  selectedLevel: string = '';
  selectedCategory: string = '';
  showDetails: boolean = false;
  autoRefresh: boolean = true;
  maxDisplayedLogs: number = 100;
  
  errorCount: number = 0;
  warnCount: number = 0;
  infoCount: number = 0;
  debugCount: number = 0;
  
  private refreshSubscription?: Subscription;

  constructor(private loggingService: LoggingService) {}

  ngOnInit(): void {
    this.refreshLogs();
    this.startAutoRefresh();
  }

  ngOnDestroy(): void {
    this.stopAutoRefresh();
  }

  refreshLogs(): void {
    this.logs = this.loggingService.exportLogs();
    this.updateCategories();
    this.filterLogs();
    this.updateCounts();
  }

  filterLogs(): void {
    this.filteredLogs = this.logs.filter(log => {
      if (this.selectedLevel) {
        const levelOrder = ['DEBUG', 'INFO', 'WARN', 'ERROR'];
        const selectedIndex = levelOrder.indexOf(this.selectedLevel);
        const logIndex = levelOrder.indexOf(log.level);
        if (logIndex < selectedIndex) return false;
      }
      
      if (this.selectedCategory && log.category !== this.selectedCategory) {
        return false;
      }
      
      return true;
    }).reverse(); // Show newest first
  }

  updateCategories(): void {
    this.categories = [...new Set(this.logs.map(log => log.category))].sort();
  }

  updateCounts(): void {
    this.errorCount = this.filteredLogs.filter(log => log.level === 'ERROR').length;
    this.warnCount = this.filteredLogs.filter(log => log.level === 'WARN').length;
    this.infoCount = this.filteredLogs.filter(log => log.level === 'INFO').length;
    this.debugCount = this.filteredLogs.filter(log => log.level === 'DEBUG').length;
  }

  clearLogs(): void {
    this.loggingService.clearLogs();
    this.refreshLogs();
  }

  toggleAutoRefresh(): void {
    this.autoRefresh = !this.autoRefresh;
    if (this.autoRefresh) {
      this.startAutoRefresh();
    } else {
      this.stopAutoRefresh();
    }
  }

  startAutoRefresh(): void {
    this.stopAutoRefresh();
    if (this.autoRefresh) {
      this.refreshSubscription = interval(2000).subscribe(() => {
        this.refreshLogs();
      });
    }
  }

  stopAutoRefresh(): void {
    if (this.refreshSubscription) {
      this.refreshSubscription.unsubscribe();
      this.refreshSubscription = undefined;
    }
  }

  loadMoreLogs(): void {
    this.maxDisplayedLogs += 100;
  }

  exportLogs(): void {
    const dataStr = JSON.stringify(this.filteredLogs, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `docxp-logs-${new Date().toISOString().slice(0, 19)}.json`;
    link.click();
    URL.revokeObjectURL(url);
  }

  formatTime(timestamp: Date): string {
    return timestamp.toLocaleTimeString();
  }

  formatData(data: any): string {
    if (!data) return '';
    try {
      return JSON.stringify(data, null, 2);
    } catch {
      return String(data);
    }
  }

  trackByLogEntry(index: number, log: LogEntry): string {
    return `${log.timestamp.getTime()}-${log.category}-${log.message}`;
  }
}