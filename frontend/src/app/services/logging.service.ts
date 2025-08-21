import { Injectable } from '@angular/core';
import { environment } from '../../environments/environment';

export interface LogEntry {
  timestamp: Date;
  level: 'DEBUG' | 'INFO' | 'WARN' | 'ERROR';
  category: string;
  message: string;
  data?: any;
  userId?: string;
  sessionId: string;
}

@Injectable({
  providedIn: 'root'
})
export class LoggingService {
  private sessionId: string;
  private userId?: string;
  private logs: LogEntry[] = [];
  private maxLogEntries = 1000;

  constructor() {
    this.sessionId = this.generateSessionId();
    this.initializeLogging();
  }

  private generateSessionId(): string {
    return 'session_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
  }

  private initializeLogging(): void {
    // Capture console errors
    const originalError = console.error;
    console.error = (...args: any[]) => {
      this.error('Console', args.join(' '), { originalArgs: args });
      originalError.apply(console, args);
    };

    // Capture unhandled promise rejections
    window.addEventListener('unhandledrejection', (event) => {
      this.error('UnhandledPromise', `Unhandled promise rejection: ${event.reason}`, {
        promise: event.promise,
        reason: event.reason
      });
    });

    // Capture JavaScript errors
    window.addEventListener('error', (event) => {
      this.error('JavaScriptError', `${event.message} at ${event.filename}:${event.lineno}`, {
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
        error: event.error
      });
    });

    this.info('Logging', 'Logging service initialized', { sessionId: this.sessionId });
  }

  setUserId(userId: string): void {
    this.userId = userId;
    this.info('Logging', 'User ID set', { userId });
  }

  debug(category: string, message: string, data?: any): void {
    this.log('DEBUG', category, message, data);
  }

  info(category: string, message: string, data?: any): void {
    this.log('INFO', category, message, data);
  }

  warn(category: string, message: string, data?: any): void {
    this.log('WARN', category, message, data);
  }

  error(category: string, message: string, data?: any): void {
    this.log('ERROR', category, message, data);
  }

  private log(level: LogEntry['level'], category: string, message: string, data?: any): void {
    const entry: LogEntry = {
      timestamp: new Date(),
      level,
      category,
      message,
      data,
      userId: this.userId,
      sessionId: this.sessionId
    };

    this.logs.push(entry);

    // Limit log entries to prevent memory issues
    if (this.logs.length > this.maxLogEntries) {
      this.logs = this.logs.slice(-this.maxLogEntries);
    }

    // Console output in development
    if (!environment.production) {
      const timestamp = entry.timestamp.toISOString();
      const logMessage = `[${timestamp}] [${level}] [${category}] ${message}`;
      
      switch (level) {
        case 'DEBUG':
          console.debug(logMessage, data);
          break;
        case 'INFO':
          console.info(logMessage, data);
          break;
        case 'WARN':
          console.warn(logMessage, data);
          break;
        case 'ERROR':
          console.error(logMessage, data);
          break;
      }
    }

    // Send critical errors to backend for monitoring
    if (level === 'ERROR') {
      this.sendLogToBackend(entry);
    }
  }

  private async sendLogToBackend(entry: LogEntry): Promise<void> {
    try {
      // Only send errors to backend to avoid spam
      await fetch(`${environment.apiUrl}/logging/error`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(entry)
      });
    } catch (error) {
      // Fail silently for logging errors to avoid infinite loops
      console.warn('Failed to send log to backend:', error);
    }
  }

  // API call logging helper
  logApiCall(method: string, url: string, duration: number, status: number, error?: any): void {
    const level = error ? 'ERROR' : status >= 400 ? 'WARN' : 'INFO';
    this.log(level, 'API', `${method} ${url} - ${status} (${duration}ms)`, {
      method,
      url,
      duration,
      status,
      error
    });
  }

  // User action logging
  logUserAction(action: string, component: string, data?: any): void {
    this.info('UserAction', `${component}: ${action}`, data);
  }

  // Navigation logging
  logNavigation(from: string, to: string, data?: any): void {
    this.info('Navigation', `${from} -> ${to}`, data);
  }

  // Performance logging
  logPerformance(operation: string, duration: number, data?: any): void {
    const level = duration > 5000 ? 'WARN' : 'INFO';
    this.log(level, 'Performance', `${operation} took ${duration}ms`, data);
  }

  // AWS operations logging
  logAwsOperation(operation: string, success: boolean, data?: any): void {
    const level = success ? 'INFO' : 'ERROR';
    this.log(level, 'AWS', `${operation} ${success ? 'succeeded' : 'failed'}`, data);
  }

  // Search operations logging
  logSearchOperation(query: string, resultCount: number, duration: number, searchType: string): void {
    this.info('Search', `${searchType} search: "${query}" returned ${resultCount} results (${duration}ms)`, {
      query,
      resultCount,
      duration,
      searchType
    });
  }

  // Chat operations logging
  logChatInteraction(message: string, responseType: 'success' | 'error', duration: number): void {
    this.info('Chat', `Message processed via ${responseType} service (${duration}ms)`, {
      messageLength: message.length,
      responseType,
      duration
    });
  }

  // Service availability logging
  logServiceStatus(serviceName: string, available: boolean, responseTime?: number): void {
    const level = available ? 'INFO' : 'WARN';
    this.log(level, 'ServiceStatus', `${serviceName} is ${available ? 'available' : 'unavailable'}`, {
      serviceName,
      available,
      responseTime
    });
  }

  // Export logs for debugging
  exportLogs(): LogEntry[] {
    return [...this.logs];
  }

  // Clear logs
  clearLogs(): void {
    this.logs = [];
    this.info('Logging', 'Logs cleared');
  }

  // Get logs by category or level
  getFilteredLogs(filters: { category?: string; level?: LogEntry['level']; since?: Date }): LogEntry[] {
    return this.logs.filter(log => {
      if (filters.category && log.category !== filters.category) return false;
      if (filters.level && log.level !== filters.level) return false;
      if (filters.since && log.timestamp < filters.since) return false;
      return true;
    });
  }

  // Get recent errors for debugging
  getRecentErrors(minutes: number = 30): LogEntry[] {
    const since = new Date(Date.now() - minutes * 60 * 1000);
    return this.getFilteredLogs({ level: 'ERROR', since });
  }
}