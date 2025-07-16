/**
 * Frontend Performance Monitor
 * Tracks page load times, API response times, and user interactions
 */

interface PerformanceMetric {
  name: string;
  value: number;
  timestamp: number;
  type: 'navigation' | 'resource' | 'measure' | 'api' | 'user';
  metadata?: Record<string, any>;
}

interface APIMetric {
  endpoint: string;
  method: string;
  duration: number;
  status: number;
  timestamp: number;
  size?: number;
}

class PerformanceMonitor {
  private metrics: PerformanceMetric[] = [];
  private apiMetrics: APIMetric[] = [];
  private reportingInterval: number;
  private batchSize: number = 50;
  private apiEndpoint: string;

  constructor(reportingInterval: number = 30000) {
    this.reportingInterval = reportingInterval;
    this.apiEndpoint = '/api/analytics/performance';
    
    this.initializeObservers();
    this.startPeriodicReporting();
  }

  private initializeObservers(): void {
    // Performance Observer for navigation and resource timing
    if ('PerformanceObserver' in window) {
      const observer = new PerformanceObserver((list) => {
        list.getEntries().forEach((entry) => {
          this.collectPerformanceEntry(entry);
        });
      });

      observer.observe({ 
        entryTypes: ['navigation', 'resource', 'measure', 'paint'] 
      });
    }

    // Web Vitals monitoring
    this.monitorCoreWebVitals();
    
    // API request monitoring
    this.interceptFetchRequests();
  }

  private collectPerformanceEntry(entry: PerformanceEntry): void {
    const metric: PerformanceMetric = {
      name: entry.name,
      value: entry.duration || (entry as any).value || 0,
      timestamp: Date.now(),
      type: this.getMetricType(entry.entryType),
      metadata: {
        entryType: entry.entryType,
        startTime: entry.startTime
      }
    };

    // Add specific metadata based on entry type
    if (entry.entryType === 'navigation') {
      const navEntry = entry as PerformanceNavigationTiming;
      metric.metadata = {
        ...metric.metadata,
        domContentLoaded: navEntry.domContentLoadedEventEnd - navEntry.domContentLoadedEventStart,
        loadComplete: navEntry.loadEventEnd - navEntry.loadEventStart,
        firstByte: navEntry.responseStart - navEntry.requestStart,
        domInteractive: navEntry.domInteractive - navEntry.fetchStart
      };
    }

    if (entry.entryType === 'resource') {
      const resourceEntry = entry as PerformanceResourceTiming;
      metric.metadata = {
        ...metric.metadata,
        transferSize: resourceEntry.transferSize,
        encodedBodySize: resourceEntry.encodedBodySize,
        decodedBodySize: resourceEntry.decodedBodySize,
        initiatorType: resourceEntry.initiatorType
      };
    }

    this.metrics.push(metric);
    this.checkAndReport();
  }

  private getMetricType(entryType: string): PerformanceMetric['type'] {
    switch (entryType) {
      case 'navigation':
        return 'navigation';
      case 'resource':
        return 'resource';
      case 'measure':
        return 'measure';
      default:
        return 'measure';
    }
  }

  private monitorCoreWebVitals(): void {
    // First Contentful Paint (FCP)
    const observer = new PerformanceObserver((list) => {
      list.getEntries().forEach((entry) => {
        if (entry.name === 'first-contentful-paint') {
          this.addMetric('FCP', entry.startTime, 'navigation', {
            description: 'First Contentful Paint'
          });
        }
      });
    });
    
    if (PerformanceObserver.supportedEntryTypes.includes('paint')) {
      observer.observe({ entryTypes: ['paint'] });
    }

    // Largest Contentful Paint (LCP)
    if ('LargestContentfulPaint' in window) {
      const lcpObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        const lastEntry = entries[entries.length - 1];
        this.addMetric('LCP', lastEntry.startTime, 'navigation', {
          description: 'Largest Contentful Paint',
          element: (lastEntry as any).element?.tagName
        });
      });
      
      if (PerformanceObserver.supportedEntryTypes.includes('largest-contentful-paint')) {
        lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });
      }
    }

    // Cumulative Layout Shift (CLS)
    let clsValue = 0;
    const clsObserver = new PerformanceObserver((list) => {
      list.getEntries().forEach((entry: any) => {
        if (!entry.hadRecentInput) {
          clsValue += entry.value;
        }
      });
      
      this.addMetric('CLS', clsValue, 'navigation', {
        description: 'Cumulative Layout Shift'
      });
    });
    
    if (PerformanceObserver.supportedEntryTypes.includes('layout-shift')) {
      clsObserver.observe({ entryTypes: ['layout-shift'] });
    }
  }

  private interceptFetchRequests(): void {
    const originalFetch = window.fetch;
    
    window.fetch = async (...args) => {
      const startTime = performance.now();
      const url = typeof args[0] === 'string' ? args[0] : (args[0] as Request).url;
      const method = args[1]?.method || 'GET';
      
      try {
        const response = await originalFetch(...args);
        const endTime = performance.now();
        const duration = endTime - startTime;
        
        // Only track API calls, not static assets
        if (url.includes('/api/')) {
          const apiMetric: APIMetric = {
            endpoint: this.sanitizeEndpoint(url),
            method,
            duration,
            status: response.status,
            timestamp: Date.now(),
            size: response.headers.get('content-length') ? 
              parseInt(response.headers.get('content-length') || '0') : undefined
          };
          
          this.apiMetrics.push(apiMetric);
          
          // Add as performance metric too
          this.addMetric(`API_${method}_${response.status}`, duration, 'api', {
            endpoint: apiMetric.endpoint,
            status: response.status
          });
        }
        
        return response;
      } catch (error) {
        const endTime = performance.now();
        const duration = endTime - startTime;
        
        if (url.includes('/api/')) {
          const apiMetric: APIMetric = {
            endpoint: this.sanitizeEndpoint(url),
            method,
            duration,
            status: 0,
            timestamp: Date.now()
          };
          
          this.apiMetrics.push(apiMetric);
          
          this.addMetric(`API_${method}_ERROR`, duration, 'api', {
            endpoint: apiMetric.endpoint,
            error: error instanceof Error ? error.message : 'Unknown error'
          });
        }
        
        throw error;
      }
    };
  }

  private sanitizeEndpoint(url: string): string {
    // Remove query parameters and dynamic IDs for grouping
    return url
      .replace(/\?.*$/, '') // Remove query params
      .replace(/\/\d+/g, '/:id') // Replace numeric IDs
      .replace(/\/[a-f0-9-]{36}/g, '/:uuid') // Replace UUIDs
      .replace(/^https?:\/\/[^/]+/, ''); // Remove domain
  }

  public addMetric(name: string, value: number, type: PerformanceMetric['type'], metadata?: Record<string, any>): void {
    this.metrics.push({
      name,
      value,
      timestamp: Date.now(),
      type,
      metadata
    });
    
    this.checkAndReport();
  }

  public trackUserAction(action: string, duration?: number, metadata?: Record<string, any>): void {
    this.addMetric(`user_action_${action}`, duration || 0, 'user', metadata);
  }

  private checkAndReport(): void {
    if (this.metrics.length >= this.batchSize) {
      this.reportMetrics();
    }
  }

  private startPeriodicReporting(): void {
    setInterval(() => {
      if (this.metrics.length > 0 || this.apiMetrics.length > 0) {
        this.reportMetrics();
      }
    }, this.reportingInterval);
  }

  private async reportMetrics(): Promise<void> {
    if (this.metrics.length === 0 && this.apiMetrics.length === 0) return;

    const payload = {
      metrics: [...this.metrics],
      apiMetrics: [...this.apiMetrics],
      userAgent: navigator.userAgent,
      timestamp: Date.now(),
      url: window.location.href
    };

    // Clear metrics
    this.metrics = [];
    this.apiMetrics = [];

    try {
      await fetch(this.apiEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });
    } catch (error) {
      console.warn('Failed to report performance metrics:', error);
      // In case of failure, we could store metrics locally and retry
    }
  }

  public getPerformanceSummary(): {
    pageLoad: number;
    apiResponseTime: number;
    errorRate: number;
    totalMetrics: number;
  } {
    const navigationMetrics = this.metrics.filter(m => m.type === 'navigation');
    const apiMetrics = this.apiMetrics;
    const errorCount = apiMetrics.filter(m => m.status >= 400).length;

    return {
      pageLoad: navigationMetrics.length > 0 ? 
        navigationMetrics.reduce((sum, m) => sum + m.value, 0) / navigationMetrics.length : 0,
      apiResponseTime: apiMetrics.length > 0 ? 
        apiMetrics.reduce((sum, m) => sum + m.duration, 0) / apiMetrics.length : 0,
      errorRate: apiMetrics.length > 0 ? errorCount / apiMetrics.length : 0,
      totalMetrics: this.metrics.length + this.apiMetrics.length
    };
  }
}

// Export singleton instance
export const performanceMonitor = new PerformanceMonitor();

// Export class for testing
export { PerformanceMonitor };
export type { PerformanceMetric, APIMetric };
