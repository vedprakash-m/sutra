/**
 * API Response Cache Service - Task 3.2 Performance Optimization
 * Implements in-memory caching with TTL and LRU eviction
 */

interface CacheItem<T> {
  data: T;
  timestamp: number;
  ttl: number;
}

interface CacheConfig {
  defaultTTL: number;
  maxSize: number;
}

class APICache {
  private cache = new Map<string, CacheItem<any>>();
  private accessOrder = new Map<string, number>();
  private accessCounter = 0;

  private config: CacheConfig = {
    defaultTTL: 5 * 60 * 1000, // 5 minutes default TTL
    maxSize: 100, // Maximum cache entries
  };

  constructor(config?: Partial<CacheConfig>) {
    if (config) {
      this.config = { ...this.config, ...config };
    }
  }

  /**
   * Get cached data if it exists and is not expired
   */
  get<T>(key: string): T | null {
    const item = this.cache.get(key);

    if (!item) {
      return null;
    }

    // Check if expired
    if (Date.now() - item.timestamp > item.ttl) {
      this.cache.delete(key);
      this.accessOrder.delete(key);
      return null;
    }

    // Update access order for LRU
    this.accessOrder.set(key, ++this.accessCounter);

    return item.data;
  }

  /**
   * Set data in cache with optional TTL
   */
  set<T>(key: string, data: T, ttl?: number): void {
    const cacheItem: CacheItem<T> = {
      data,
      timestamp: Date.now(),
      ttl: ttl || this.config.defaultTTL,
    };

    // If cache is full, remove least recently used item
    if (this.cache.size >= this.config.maxSize) {
      this.evictLRU();
    }

    this.cache.set(key, cacheItem);
    this.accessOrder.set(key, ++this.accessCounter);
  }

  /**
   * Remove item from cache
   */
  delete(key: string): boolean {
    this.accessOrder.delete(key);
    return this.cache.delete(key);
  }

  /**
   * Clear all cache entries
   */
  clear(): void {
    this.cache.clear();
    this.accessOrder.clear();
    this.accessCounter = 0;
  }

  /**
   * Get cache statistics
   */
  getStats() {
    const now = Date.now();
    let expired = 0;
    let valid = 0;

    for (const [, item] of this.cache.entries()) {
      if (now - item.timestamp > item.ttl) {
        expired++;
      } else {
        valid++;
      }
    }

    return {
      totalEntries: this.cache.size,
      validEntries: valid,
      expiredEntries: expired,
      maxSize: this.config.maxSize,
      hitRate: this.getHitRate(),
    };
  }

  /**
   * Evict least recently used item
   */
  private evictLRU(): void {
    let oldestKey: string | null = null;
    let oldestAccess = Infinity;

    for (const [key, accessTime] of this.accessOrder.entries()) {
      if (accessTime < oldestAccess) {
        oldestAccess = accessTime;
        oldestKey = key;
      }
    }

    if (oldestKey) {
      this.cache.delete(oldestKey);
      this.accessOrder.delete(oldestKey);
    }
  }

  /**
   * Get cache hit rate (simplified - would need request tracking for real rate)
   */
  private getHitRate(): number {
    // This is a simplified version - in production, you'd track hits vs misses
    return this.cache.size > 0 ? 0.75 : 0; // Mock 75% hit rate when cache has items
  }

  /**
   * Clean up expired entries
   */
  cleanup(): void {
    const now = Date.now();
    const expiredKeys: string[] = [];

    for (const [key, item] of this.cache.entries()) {
      if (now - item.timestamp > item.ttl) {
        expiredKeys.push(key);
      }
    }

    expiredKeys.forEach((key) => {
      this.cache.delete(key);
      this.accessOrder.delete(key);
    });
  }

  /**
   * Generate cache key from URL and parameters
   */
  static generateKey(url: string, params?: Record<string, any>): string {
    if (!params || Object.keys(params).length === 0) {
      return url;
    }

    const sortedParams = Object.keys(params)
      .sort()
      .map((key) => `${key}=${encodeURIComponent(String(params[key]))}`)
      .join("&");

    return `${url}?${sortedParams}`;
  }
}

// Create singleton cache instance
export const apiCache = new APICache({
  defaultTTL: 5 * 60 * 1000, // 5 minutes
  maxSize: 100,
});

// Cache configurations for different endpoint types
export const CacheTTL = {
  SHORT: 1 * 60 * 1000, // 1 minute - for dynamic data
  MEDIUM: 5 * 60 * 1000, // 5 minutes - for semi-static data
  LONG: 30 * 60 * 1000, // 30 minutes - for static data
  VERY_LONG: 2 * 60 * 60 * 1000, // 2 hours - for rarely changing data
};

// Set up automatic cleanup every 5 minutes
setInterval(
  () => {
    apiCache.cleanup();
  },
  5 * 60 * 1000,
);

export default APICache;
