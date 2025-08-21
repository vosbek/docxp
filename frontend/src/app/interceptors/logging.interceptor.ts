import { Injectable } from '@angular/core';
import { HttpInterceptor, HttpRequest, HttpHandler, HttpEvent, HttpResponse, HttpErrorResponse } from '@angular/common/http';
import { Observable } from 'rxjs';
import { tap, finalize } from 'rxjs/operators';
import { LoggingService } from '../services/logging.service';

@Injectable()
export class LoggingInterceptor implements HttpInterceptor {
  constructor(private loggingService: LoggingService) {}

  intercept(req: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    const startTime = Date.now();
    
    // Log the outgoing request
    this.loggingService.debug('HTTP', `Starting ${req.method} ${req.url}`, {
      method: req.method,
      url: req.url,
      headers: this.sanitizeHeaders(req.headers),
      body: req.body
    });

    return next.handle(req).pipe(
      tap({
        next: (event) => {
          if (event instanceof HttpResponse) {
            const duration = Date.now() - startTime;
            this.loggingService.logApiCall(req.method, req.url, duration, event.status);
            
            // Log successful responses
            this.loggingService.debug('HTTP', `Completed ${req.method} ${req.url}`, {
              status: event.status,
              duration,
              responseSize: JSON.stringify(event.body).length
            });
          }
        },
        error: (error: HttpErrorResponse) => {
          const duration = Date.now() - startTime;
          this.loggingService.logApiCall(req.method, req.url, duration, error.status || 0, error);
          
          // Log detailed error information
          this.loggingService.error('HTTP', `Failed ${req.method} ${req.url}`, {
            status: error.status,
            statusText: error.statusText,
            duration,
            error: error.error,
            message: error.message,
            url: error.url
          });
        }
      }),
      finalize(() => {
        // Log that the request has completed (success or error)
        const duration = Date.now() - startTime;
        if (duration > 5000) {
          this.loggingService.warn('HTTP', `Slow request ${req.method} ${req.url} took ${duration}ms`, {
            method: req.method,
            url: req.url,
            duration
          });
        }
      })
    );
  }

  private sanitizeHeaders(headers: any): any {
    const sanitized: any = {};
    headers.keys().forEach((key: string) => {
      // Don't log sensitive headers
      if (key.toLowerCase().includes('authorization') || 
          key.toLowerCase().includes('token') ||
          key.toLowerCase().includes('key')) {
        sanitized[key] = '[REDACTED]';
      } else {
        sanitized[key] = headers.get(key);
      }
    });
    return sanitized;
  }
}