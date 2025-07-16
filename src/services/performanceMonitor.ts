/**
 * Performance Monitoring Service - Task 3.2 Performance Optimization
 * Monitors application performance metrics and provides insights
 */

interface PerformanceMetric {
  name: string;
  value: number;
  timestamp: number;
  tags?: Record<string, string>;
}

interface NavigationTiming {
  domContentLoaded: number;
  firstPaint: number;
  firstContentfulPaint: number;
  largestContentfulPaint: number;
  firstInputDelay?: number;
  cumulativeLayoutShift?: number;
}

interface APIPerformance {
  endpoint: string;
  method: string;
  duration: number;
  status: number;
  timestamp: number;
  size?: number;
  cached?: boolean;
}

class PerformanceMonitor {
  private metrics: PerformanceMetric[] = [];
  private apiMetrics: APIPerformance[] = [];
  private navigationTiming: NavigationTiming | null = null;
  private observer: PerformanceObserver | null = null;

  constructor() {
    this.initializePerformanceObserver();
    this.captureNavigationTiming();
    this.startPeriodicReporting();
  }

  /**
   * Initialize Performance Observer for Core Web Vitals
   */
  private initializePerformanceObserver(): void {
    if (typeof window === "undefined" || !("PerformanceObserver" in window)) {
      return;
    }

    try {
      // Observe paint entries
      this.observer = new PerformanceObserver((list) => {
        list.getEntries().forEach((entry) => {
          this.recordMetric(entry.name, entry.startTime, {
            entryType: entry.entryType,
          });
        });
      });

      // Start observing
      this.observer.observe({ entryTypes: ["paint", "navigation", "measure"] });

      // Observe LCP (Largest Contentful Paint)
      if ("PerformanceObserver" in window) {
        const lcpObserver = new PerformanceObserver((list) => {
          list.getEntries().forEach((entry: any) => {
            this.recordMetric("largest-contentful-paint", entry.startTime);
          });
        });
        lcpObserver.observe({ entryTypes: ["largest-contentful-paint"] });

        // Observe FID (First Input Delay)
        const fidObserver = new PerformanceObserver((list) => {
          list.getEntries().forEach((entry: any) => {
            this.recordMetric(
              "first-input-delay",
              entry.processingStart - entry.startTime,
            );
          });
        });
        fidObserver.observe({ entryTypes: ["first-input"] });

        // Observe CLS (Cumulative Layout Shift)
        const clsObserver = new PerformanceObserver((list) => {
          list.getEntries().forEach((entry: any) => {
            if (!entry.hadRecentInput) {
              this.recordMetric("cumulative-layout-shift", entry.value);
            }
          });
        });
        clsObserver.observe({ entryTypes: ["layout-shift"] });
      }
    } catch (error) {
      console.warn("Performance Observer not supported:", error);
    }
  }

  /**
   * Capture navigation timing metrics
   */
  private captureNavigationTiming(): void {
    if (typeof window === "undefined" || !window.performance) {
      return;
    }

    // Wait for page to load before capturing timing
    window.addEventListener("load", () => {
      setTimeout(() => {
        const navigation = performance.getEntriesByType(
          "navigation",
        )[0] as PerformanceNavigationTiming;
        if (navigation) {
          this.navigationTiming = {
            domContentLoaded:
              navigation.domContentLoadedEventEnd -
              navigation.domContentLoadedEventStart,
            firstPaint: 0, // Will be updated by observer
            firstContentfulPaint: 0, // Will be updated by observer
            largestContentfulPaint: 0, // Will be updated by observer
          };

          // Record navigation metrics
          this.recordMetric(
            "navigation-time",
            navigation.loadEventEnd - navigation.fetchStart,
          );
          this.recordMetric(
            "dom-content-loaded",
            this.navigationTiming.domContentLoaded,
          );
          this.recordMetric(
            "dns-lookup",
            navigation.domainLookupEnd - navigation.domainLookupStart,
          );
          this.recordMetric(
            "server-response",
            navigation.responseEnd - navigation.requestStart,
          );
        }
      }, 100);
    });
  }

  /**
   * Record a performance metric
   */
  recordMetric(
    name: string,
    value: number,
    tags?: Record<string, string>,
  ): void {
    const metric: PerformanceMetric = {
      name,
      value,
      timestamp: Date.now(),
      tags,
    };

    this.metrics.push(metric);

    // Keep only last 1000 metrics to prevent memory leaks
    if (this.metrics.length > 1000) {
      this.metrics = this.metrics.slice(-1000);
    }

    console.log(`📊 Performance metric: ${name} = ${value.toFixed(2)}ms`, tags);
  }

  /**
   * Record API performance
   */
  recordAPICall(
    endpoint: string,
    method: string,
    duration: number,
    status: number,
    options?: {
      size?: number;
      cached?: boolean;
    },
  ): void {
    const apiMetric: APIPerformance = {
      endpoint,
      method,
      duration,
      status,
      timestamp: Date.now(),
      size: options?.size,
      cached: options?.cached,
    };

    this.apiMetrics.push(apiMetric);

    // Keep only last 500 API metrics
    if (this.apiMetrics.length > 500) {
      this.apiMetrics = this.apiMetrics.slice(-500);
    }

    const cacheStatus = options?.cached ? "(cached)" : "";
    console.log(
      `🌐 API call: ${method} ${endpoint} - ${duration.toFixed(2)}ms ${cacheStatus}`,
    );
  }

  /**
   * Measure execution time of a function
   */
  async measureAsync<T>(name: string, fn: () => Promise<T>): Promise<T> {
    const startTime = performance.now();
    try {
      const result = await fn();
      const duration = performance.now() - startTime;
      this.recordMetric(name, duration);
      return result;
    } catch (error) {
      const duration = performance.now() - startTime;
      this.recordMetric(`${name}-error`, duration, { error: "true" });
      throw error;
    }
  }

  /**
   * Measure execution time of a synchronous function
   */
  measure<T>(name: string, fn: () => T): T {
    const startTime = performance.now();
    try {
      const result = fn();
      const duration = performance.now() - startTime;
      this.recordMetric(name, duration);
      return result;
    } catch (error) {
      const duration = performance.now() - startTime;
      this.recordMetric(`${name}-error`, duration, { error: "true" });
      throw error;
    }
  }

  /**
   * Get performance summary
   */
  getPerformanceSummary() {
    const now = Date.now();
    const last5Minutes = now - 5 * 60 * 1000;

    // Filter recent metrics
    const recentMetrics = this.metrics.filter(
      (m) => m.timestamp >= last5Minutes,
    );
    const recentAPIMetrics = this.apiMetrics.filter(
      (m) => m.timestamp >= last5Minutes,
    );

    // Calculate averages
    const avgMetrics: Record<
      string,
      { avg: number; count: number; min: number; max: number }
    > = {};

    recentMetrics.forEach((metric) => {
      if (!avgMetrics[metric.name]) {
        avgMetrics[metric.name] = {
          avg: 0,
          count: 0,
          min: Infinity,
          max: -Infinity,
        };
      }
      avgMetrics[metric.name].count++;
      avgMetrics[metric.name].avg += metric.value;
      avgMetrics[metric.name].min = Math.min(
        avgMetrics[metric.name].min,
        metric.value,
      );
      avgMetrics[metric.name].max = Math.max(
        avgMetrics[metric.name].max,
        metric.value,
      );
    });

    // Finalize averages
    Object.keys(avgMetrics).forEach((key) => {
      avgMetrics[key].avg /= avgMetrics[key].count;
    });

    // API metrics summary
    const apiSummary = {
      totalCalls: recentAPIMetrics.length,
      averageResponseTime:
        recentAPIMetrics.length > 0
          ? recentAPIMetrics.reduce((sum, m) => sum + m.duration, 0) /
            recentAPIMetrics.length
          : 0,
      cacheHitRate:
        recentAPIMetrics.length > 0
          ? recentAPIMetrics.filter((m) => m.cached).length /
            recentAPIMetrics.length
          : 0,
      errorRate:
        recentAPIMetrics.length > 0
          ? recentAPIMetrics.filter((m) => m.status >= 400).length /
            recentAPIMetrics.length
          : 0,
    };

    return {
      navigationTiming: this.navigationTiming,
      metrics: avgMetrics,
      apiMetrics: apiSummary,
      totalMetrics: this.metrics.length,
      totalAPICalls: this.apiMetrics.length,
    };
  }

  /**
   * Get Core Web Vitals
   */
  getCoreWebVitals() {
    const vitals = {
      lcp: null as number | null, // Largest Contentful Paint
      fid: null as number | null, // First Input Delay
      cls: null as number | null, // Cumulative Layout Shift
      fcp: null as number | null, // First Contentful Paint
    };

    this.metrics.forEach((metric) => {
      switch (metric.name) {
        case "largest-contentful-paint":
          vitals.lcp = metric.value;
          break;
        case "first-input-delay":
          vitals.fid = metric.value;
          break;
        case "cumulative-layout-shift":
          vitals.cls = (vitals.cls || 0) + metric.value;
          break;
        case "first-contentful-paint":
          vitals.fcp = metric.value;
          break;
      }
    });

    return vitals;
  }

  /**
   * Start periodic performance reporting
   */
  private startPeriodicReporting(): void {
    setInterval(
      () => {
        const summary = this.getPerformanceSummary();
        const vitals = this.getCoreWebVitals();

        console.log("📊 Performance Summary (last 5 minutes):", {
          apiCalls: summary.apiMetrics.totalCalls,
          avgResponseTime:
            summary.apiMetrics.averageResponseTime.toFixed(2) + "ms",
          cacheHitRate:
            (summary.apiMetrics.cacheHitRate * 100).toFixed(1) + "%",
          errorRate: (summary.apiMetrics.errorRate * 100).toFixed(1) + "%",
          coreWebVitals: vitals,
        });
      },
      5 * 60 * 1000,
    ); // Report every 5 minutes
  }

  /**
   * Export performance data
   */
  exportData() {
    return {
      metrics: this.metrics,
      apiMetrics: this.apiMetrics,
      navigationTiming: this.navigationTiming,
      summary: this.getPerformanceSummary(),
      coreWebVitals: this.getCoreWebVitals(),
      exportedAt: new Date().toISOString(),
    };
  }

  /**
   * Clear all performance data
   */
  clear(): void {
    this.metrics = [];
    this.apiMetrics = [];
    this.navigationTiming = null;
  }
}

// Create singleton instance
export const performanceMonitor = new PerformanceMonitor();

// Export types for external use
export type { PerformanceMetric, NavigationTiming, APIPerformance };

export default PerformanceMonitor;
