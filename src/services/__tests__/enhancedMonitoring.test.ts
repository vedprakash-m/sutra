import EnhancedMonitoring from "../enhancedMonitoring";

// Mock console methods
const mockConsoleLog = jest.spyOn(console, "log").mockImplementation();
const mockConsoleWarn = jest.spyOn(console, "warn").mockImplementation();
const mockConsoleError = jest.spyOn(console, "error").mockImplementation();
const mockConsoleDebug = jest.spyOn(console, "debug").mockImplementation();

// Mock performance.now for consistent testing
const mockPerformanceNow = jest.spyOn(performance, "now");

describe("EnhancedMonitoring", () => {
  let service: EnhancedMonitoring;

  beforeEach(() => {
    service = EnhancedMonitoring.getInstance();
    jest.clearAllMocks();
    mockPerformanceNow.mockReturnValue(100);
  });

  afterAll(() => {
    mockConsoleLog.mockRestore();
    mockConsoleWarn.mockRestore();
    mockConsoleError.mockRestore();
    mockConsoleDebug.mockRestore();
    mockPerformanceNow.mockRestore();
  });

  describe("Singleton Pattern", () => {
    it("should return the same instance", () => {
      const instance1 = EnhancedMonitoring.getInstance();
      const instance2 = EnhancedMonitoring.getInstance();
      expect(instance1).toBe(instance2);
    });
  });

  describe("trackUserActivity", () => {
    it("should track user activity and log the correct message", () => {
      const activity = {
        userId: "user123",
        activity: "login",
        timestamp: new Date(),
        metadata: { source: "web" },
      };

      service.trackUserActivity(activity);

      expect(mockConsoleLog).toHaveBeenCalledWith(
        "👤 User activity tracked:",
        activity,
      );
      expect(mockConsoleDebug).toHaveBeenCalledWith(
        "📊 Storing user activity:",
        activity,
      );
    });

    it("should handle errors during activity tracking", () => {
      const invalidActivity = {
        userId: "user123",
        activity: "login",
        timestamp: new Date(),
      };

      // Mock the storeUserActivity method to throw an error
      const originalStoreUserActivity = service["storeUserActivity"];
      service["storeUserActivity"] = jest.fn().mockImplementation(() => {
        throw new Error("Storage error");
      });

      service.trackUserActivity(invalidActivity);

      expect(mockConsoleError).toHaveBeenCalledWith(
        "Failed to track user activity:",
        expect.any(Error),
      );

      // Restore original method
      service["storeUserActivity"] = originalStoreUserActivity;
    });
  });

  describe("trackComponentPerformance", () => {
    it("should track component performance successfully", () => {
      const performance = {
        component: "PromptBuilder",
        loadTime: 150,
        timestamp: new Date(),
      };

      service.trackComponentPerformance(performance);

      expect(mockConsoleLog).toHaveBeenCalledWith(
        "⚡ Component performance tracked:",
        performance,
      );
      expect(mockConsoleDebug).toHaveBeenCalledWith(
        "⚡ Storing component performance:",
        performance,
      );
    });

    it("should handle errors during performance tracking", () => {
      const performance = {
        component: "PromptBuilder",
        loadTime: 150,
        timestamp: new Date(),
      };

      // Mock the storeComponentPerformance method to throw an error
      const originalMethod = service["storeComponentPerformance"];
      service["storeComponentPerformance"] = jest
        .fn()
        .mockImplementation(() => {
          throw new Error("Performance tracking error");
        });

      service.trackComponentPerformance(performance);

      expect(mockConsoleError).toHaveBeenCalledWith(
        "Failed to track component performance:",
        expect.any(Error),
      );

      // Restore original method
      service["storeComponentPerformance"] = originalMethod;
    });
  });

  describe("getDashboardMetrics", () => {
    it("should return dashboard metrics", async () => {
      const result = await service.getDashboardMetrics();

      expect(result).toEqual({
        responseTime: 245,
        errorRate: 0.03,
        activeUsers: 127,
        systemHealth: 98.5,
      });
    });
  });

  describe("trackUserJourney", () => {
    it("should track complete user journey with valid data", () => {
      const userId = "user123";
      const journey = {
        duration: 1800,
        prompts: ["prompt1", "prompt2", "prompt3"],
        features: ["collections", "prompt-builder", "llm-compare"],
        iterations: 5,
      };

      // Mock performance timing
      mockPerformanceNow.mockReturnValueOnce(0).mockReturnValueOnce(50);

      service.trackUserJourney(userId, journey);

      expect(mockConsoleLog).toHaveBeenCalledWith(
        `📊 User journey tracked for ${userId}:`,
        expect.objectContaining({
          sessionDuration: 1800,
          promptsExecuted: 3,
          featuresUsed: ["collections", "prompt-builder", "llm-compare"],
          iterationCount: 5,
          lastActivity: expect.any(Date),
        }),
      );

      expect(mockConsoleDebug).toHaveBeenCalledWith(
        expect.stringContaining("⏱️ Operation trackUserJourney took"),
      );
    });

    it("should handle empty journey data", () => {
      const userId = "user456";
      const journey = {};

      service.trackUserJourney(userId, journey);

      expect(mockConsoleLog).toHaveBeenCalledWith(
        `📊 User journey tracked for ${userId}:`,
        expect.objectContaining({
          sessionDuration: 0,
          promptsExecuted: 0,
          featuresUsed: [],
          iterationCount: 0,
        }),
      );
    });

    it("should handle errors during journey tracking", () => {
      const userId = "user789";
      const journey = { duration: 1000 };

      // Mock storeUserMetrics to throw error
      const originalMethod = service["storeUserMetrics"];
      service["storeUserMetrics"] = jest.fn().mockImplementation(() => {
        throw new Error("Storage error");
      });

      service.trackUserJourney(userId, journey);

      expect(mockConsoleError).toHaveBeenCalledWith(
        "Failed to track user journey:",
        expect.any(Error),
      );

      // Restore original method
      service["storeUserMetrics"] = originalMethod;
    });
  });

  describe("measurePromptEffectiveness", () => {
    it("should measure prompt effectiveness with complete metrics", () => {
      const promptId = "prompt123";
      const metrics = {
        successRate: 0.85,
        responseTime: 1200,
        userRating: 4.5,
        cost: 0.05,
      };

      // Mock performance timing
      mockPerformanceNow.mockReturnValueOnce(0).mockReturnValueOnce(25);

      service.measurePromptEffectiveness(promptId, metrics);

      expect(mockConsoleLog).toHaveBeenCalledWith(
        `🎯 Prompt effectiveness measured for ${promptId}:`,
        expect.objectContaining({
          successRate: 0.85,
          averageResponseTime: 1200,
          userRating: 4.5,
          modelEffectiveness: expect.any(Number),
          costEfficiency: expect.any(Number),
        }),
      );
    });

    it("should handle minimal metrics data", () => {
      const promptId = "prompt456";
      const metrics = {};

      service.measurePromptEffectiveness(promptId, metrics);

      expect(mockConsoleLog).toHaveBeenCalledWith(
        `🎯 Prompt effectiveness measured for ${promptId}:`,
        expect.objectContaining({
          successRate: 0,
          averageResponseTime: 0,
          userRating: undefined,
          modelEffectiveness: expect.any(Number),
          costEfficiency: expect.any(Number),
        }),
      );
    });

    it("should handle errors during effectiveness measurement", () => {
      const promptId = "prompt789";
      const metrics = { successRate: 0.9 };

      // Mock calculateModelEffectiveness to throw error
      const originalMethod = service["calculateModelEffectiveness"];
      service["calculateModelEffectiveness"] = jest
        .fn()
        .mockImplementation(() => {
          throw new Error("Calculation error");
        });

      service.measurePromptEffectiveness(promptId, metrics);

      expect(mockConsoleError).toHaveBeenCalledWith(
        "Failed to measure prompt effectiveness:",
        expect.any(Error),
      );

      // Restore original method
      service["calculateModelEffectiveness"] = originalMethod;
    });
  });

  describe("monitorSystemPerformance", () => {
    it("should monitor system performance with complete metrics", () => {
      const component = "API Gateway";
      const metrics = {
        responseTime: 500,
        errorRate: 0.02,
        resourceUsage: 0.65,
        cacheHitRatio: 0.85,
        activeConnections: 150,
      };

      // Mock performance timing
      mockPerformanceNow.mockReturnValueOnce(0).mockReturnValueOnce(30);

      service.monitorSystemPerformance(component, metrics);

      expect(mockConsoleLog).toHaveBeenCalledWith(
        `⚡ System performance monitored for ${component}:`,
        expect.objectContaining({
          apiResponseTime: 500,
          errorRate: 0.02,
          resourceUtilization: 0.65,
          cacheHitRatio: 0.85,
          activeConnections: 150,
        }),
      );
    });

    it("should trigger high response time alert", () => {
      const component = "Slow API";
      const metrics = {
        responseTime: 3000, // Above 2000ms threshold
        errorRate: 0.01,
        resourceUsage: 0.5,
      };

      service.monitorSystemPerformance(component, metrics);

      expect(mockConsoleWarn).toHaveBeenCalledWith(
        "🚨 System alerts:",
        expect.arrayContaining([
          expect.objectContaining({
            type: "performance",
            severity: "high",
            message: "High API response time: 3000ms",
            component: "Slow API",
          }),
        ]),
      );
    });

    it("should trigger high error rate alert", () => {
      const component = "Error-prone Service";
      const metrics = {
        responseTime: 500,
        errorRate: 0.08, // Above 5% threshold
        resourceUsage: 0.4,
      };

      service.monitorSystemPerformance(component, metrics);

      expect(mockConsoleWarn).toHaveBeenCalledWith(
        "🚨 System alerts:",
        expect.arrayContaining([
          expect.objectContaining({
            type: "error",
            severity: "critical",
            message: "High error rate: 8.00%",
            component: "Error-prone Service",
          }),
        ]),
      );
    });

    it("should trigger high resource utilization alert", () => {
      const component = "Heavy Service";
      const metrics = {
        responseTime: 500,
        errorRate: 0.01,
        resourceUsage: 0.9, // Above 85% threshold
      };

      service.monitorSystemPerformance(component, metrics);

      expect(mockConsoleWarn).toHaveBeenCalledWith(
        "🚨 System alerts:",
        expect.arrayContaining([
          expect.objectContaining({
            type: "resource",
            severity: "warning",
            message: "High resource utilization: 90.00%",
            component: "Heavy Service",
          }),
        ]),
      );
    });

    it("should not trigger alerts for normal metrics", () => {
      const component = "Healthy Service";
      const metrics = {
        responseTime: 300,
        errorRate: 0.02,
        resourceUsage: 0.6,
      };

      service.monitorSystemPerformance(component, metrics);

      expect(mockConsoleWarn).not.toHaveBeenCalledWith(
        "🚨 System alerts:",
        expect.any(Array),
      );
    });

    it("should handle errors during system monitoring", () => {
      const component = "Test Service";
      const metrics = { responseTime: 500 };

      // Mock checkSystemAlerts to throw error
      const originalMethod = service["checkSystemAlerts"];
      service["checkSystemAlerts"] = jest.fn().mockImplementation(() => {
        throw new Error("Alert checking error");
      });

      service.monitorSystemPerformance(component, metrics);

      expect(mockConsoleError).toHaveBeenCalledWith(
        "Failed to monitor system performance:",
        expect.any(Error),
      );

      // Restore original method
      service["checkSystemAlerts"] = originalMethod;
    });
  });

  describe("generateBusinessInsights", () => {
    it("should generate business insights and return insights object", () => {
      const result = service.generateBusinessInsights();

      expect(result).toEqual({
        userGrowth: expect.any(Number),
        featureUsage: expect.any(Object),
        costOptimization: expect.any(Number),
        qualityTrends: expect.any(Array),
        recommendations: expect.any(Array),
      });

      expect(mockConsoleLog).toHaveBeenCalledWith(
        "📈 Business insights generated:",
        result,
      );
    });
  });

  describe("Model Effectiveness Calculation", () => {
    it("should calculate model effectiveness with high quality metrics", () => {
      const metrics = {
        successRate: 0.9,
        responseTime: 1000,
        userRating: 5,
        cost: 0.02,
      };

      const effectiveness = service["calculateModelEffectiveness"](metrics);

      expect(effectiveness).toBeGreaterThan(0.9);
      expect(effectiveness).toBeLessThanOrEqual(1);
    });

    it("should calculate model effectiveness with poor metrics", () => {
      const metrics = {
        successRate: 0.3,
        responseTime: 8000,
        userRating: 1,
        cost: 0.1,
      };

      const effectiveness = service["calculateModelEffectiveness"](metrics);

      expect(effectiveness).toBeLessThan(0.5);
      expect(effectiveness).toBeGreaterThanOrEqual(0);
    });

    it("should handle missing metrics gracefully", () => {
      const metrics = {};

      const effectiveness = service["calculateModelEffectiveness"](metrics);

      expect(effectiveness).toBeDefined();
      expect(typeof effectiveness).toBe("number");
    });
  });

  describe("Cost Efficiency Calculation", () => {
    it("should calculate cost efficiency with good performance and low cost", () => {
      const metrics = {
        successRate: 0.85,
        cost: 0.01,
      };

      const efficiency = service["calculateCostEfficiency"](metrics);

      expect(efficiency).toBe(1); // Capped at 1 due to Math.min
    });

    it("should calculate cost efficiency with poor performance and high cost", () => {
      const metrics = {
        successRate: 0.2,
        cost: 100, // Very high cost relative to success rate
      };

      const efficiency = service["calculateCostEfficiency"](metrics);

      expect(efficiency).toBeLessThan(1);
      expect(efficiency).toBeGreaterThan(0);
      expect(efficiency).toBe(0.2); // (0.2 / 100) * 100 = 0.2
    });

    it("should return 1 when cost is zero", () => {
      const metrics = {
        successRate: 0.8,
        cost: 0,
      };

      const efficiency = service["calculateCostEfficiency"](metrics);

      expect(efficiency).toBe(1);
    });

    it("should handle undefined values", () => {
      const metrics = {};

      const efficiency = service["calculateCostEfficiency"](metrics);

      expect(efficiency).toBe(1); // When cost is 0 (undefined)
    });
  });

  describe("Private Helper Methods", () => {
    it("should store user metrics with debug log", () => {
      const userId = "user123";
      const metrics = {
        sessionDuration: 1800,
        promptsExecuted: 5,
        featuresUsed: ["prompts", "collections"],
        iterationCount: 3,
        lastActivity: new Date(),
      };

      service["storeUserMetrics"](userId, metrics);

      expect(mockConsoleDebug).toHaveBeenCalledWith(
        `📊 Storing user metrics for ${userId}:`,
        metrics,
      );
    });

    it("should store prompt metrics with debug log", () => {
      const promptId = "prompt123";
      const metrics = {
        successRate: 0.9,
        averageResponseTime: 1500,
        userRating: 4.5,
        modelEffectiveness: 0.85,
        costEfficiency: 0.9,
      };

      service["storePromptMetrics"](promptId, metrics);

      expect(mockConsoleDebug).toHaveBeenCalledWith(
        `🎯 Storing prompt metrics for ${promptId}:`,
        metrics,
      );
    });

    it("should track performance with debug log", () => {
      const operation = "testOperation";
      const duration = 123.45;

      service["trackPerformance"](operation, duration);

      expect(mockConsoleDebug).toHaveBeenCalledWith(
        `⏱️ Operation ${operation} took ${duration.toFixed(2)}ms`,
      );
    });

    it("should update real-time dashboard with debug log", () => {
      const userId = "user123";
      const metrics = {
        sessionDuration: 1000,
        promptsExecuted: 2,
        featuresUsed: ["dashboard"],
        iterationCount: 1,
        lastActivity: new Date(),
      };

      service["updateRealTimeDashboard"](userId, metrics);

      expect(mockConsoleDebug).toHaveBeenCalledWith(
        `📈 Updating dashboard for user ${userId}:`,
        metrics,
      );
    });
  });
});
