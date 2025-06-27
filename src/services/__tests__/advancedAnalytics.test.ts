/**
 * Tests for Advanced Analytics Service
 */

import AdvancedAnalytics from "../advancedAnalytics";

// Mock console methods to avoid noise in tests
const mockConsoleLog = jest.spyOn(console, "log").mockImplementation();
const mockConsoleError = jest.spyOn(console, "error").mockImplementation();

describe("AdvancedAnalytics", () => {
  let analytics: AdvancedAnalytics;

  beforeEach(() => {
    analytics = AdvancedAnalytics.getInstance();
    jest.clearAllMocks();
  });

  afterAll(() => {
    mockConsoleLog.mockRestore();
    mockConsoleError.mockRestore();
  });

  describe("Singleton Pattern", () => {
    it("should return the same instance", () => {
      const instance1 = AdvancedAnalytics.getInstance();
      const instance2 = AdvancedAnalytics.getInstance();
      expect(instance1).toBe(instance2);
    });
  });

  describe("analyzePromptPatterns", () => {
    it("should analyze user prompt patterns and return insights", async () => {
      const result = await analytics.analyzePromptPatterns("user123");

      expect(result).toHaveProperty("optimizationSuggestions");
      expect(result).toHaveProperty("qualityScore");
      expect(result).toHaveProperty("costEfficiency");
      expect(result).toHaveProperty("recommendedModels");
      expect(result).toHaveProperty("usagePatterns");

      expect(Array.isArray(result.optimizationSuggestions)).toBe(true);
      expect(typeof result.qualityScore).toBe("number");
      expect(typeof result.costEfficiency).toBe("number");
      expect(Array.isArray(result.recommendedModels)).toBe(true);
      expect(Array.isArray(result.usagePatterns)).toBe(true);

      expect(mockConsoleLog).toHaveBeenCalledWith(
        expect.stringContaining(
          "🧠 Prompt patterns analyzed for user user123:",
        ),
        result,
      );
    });

    it("should use cached results when available", async () => {
      // First call - should cache the result
      const result1 = await analytics.analyzePromptPatterns("user123");

      // Second call - should use cache
      const result2 = await analytics.analyzePromptPatterns("user123");

      expect(result1).toEqual(result2);
    });
  });

  describe("predictCostTrends", () => {
    it("should predict cost trends and return projection", async () => {
      const result = await analytics.predictCostTrends("entity123");

      expect(result).toHaveProperty("currentTrend");
      expect(result).toHaveProperty("projectedCost");
      expect(result).toHaveProperty("confidenceInterval");
      expect(result).toHaveProperty("recommendations");
      expect(result).toHaveProperty("breakdownByModel");

      expect(typeof result.currentTrend).toBe("number");
      expect(typeof result.projectedCost).toBe("number");
      expect(Array.isArray(result.confidenceInterval)).toBe(true);
      expect(result.confidenceInterval).toHaveLength(2);
      expect(Array.isArray(result.recommendations)).toBe(true);
      expect(typeof result.breakdownByModel).toBe("object");

      expect(mockConsoleLog).toHaveBeenCalledWith(
        expect.stringContaining("💰 Cost trends predicted for entity123:"),
        result,
      );
    });
  });

  describe("recommendOptimizations", () => {
    it("should provide optimization recommendations based on context", async () => {
      const context = {
        userId: "user123",
        timeframe: "30d",
        scope: "user" as const,
        filters: { model: "gpt-4" },
      };

      const result = await analytics.recommendOptimizations(context);

      expect(result).toHaveProperty("promptOptimizations");
      expect(result).toHaveProperty("modelRecommendations");
      expect(result).toHaveProperty("costSavings");
      expect(result).toHaveProperty("performanceImprovements");

      expect(Array.isArray(result.promptOptimizations)).toBe(true);
      expect(Array.isArray(result.modelRecommendations)).toBe(true);
      expect(Array.isArray(result.costSavings)).toBe(true);
      expect(Array.isArray(result.performanceImprovements)).toBe(true);

      expect(mockConsoleLog).toHaveBeenCalledWith(
        expect.stringContaining("🚀 Optimization recommendations generated:"),
        result,
      );
    });
  });

  describe("detectAnomalies", () => {
    it("should detect anomalies in analytics data", async () => {
      const userId = "user123";
      const timeframe = "7d";

      const result = await analytics.detectAnomalies(userId, timeframe);

      expect(Array.isArray(result)).toBe(true);
      // The detectAnomalies method should return an array of anomalies
      result.forEach((anomaly) => {
        expect(anomaly).toHaveProperty("timestamp");
        expect(anomaly).toHaveProperty("severity");
        expect(anomaly).toHaveProperty("description");
        expect(anomaly).toHaveProperty("recommendation");
      });

      expect(mockConsoleLog).toHaveBeenCalledWith(
        expect.stringContaining(`🔍 Anomalies detected for user ${userId}:`),
        result,
      );
    });
  });

  describe("generatePersonalizedRecommendations", () => {
    it("should generate personalized recommendations for a user", async () => {
      const userId = "user123";

      const result =
        await analytics.generatePersonalizedRecommendations(userId);

      expect(Array.isArray(result)).toBe(true);
      result.forEach((recommendation) => {
        expect(recommendation).toHaveProperty("type");
        expect(recommendation).toHaveProperty("title");
        expect(recommendation).toHaveProperty("description");
        expect(recommendation).toHaveProperty("priority");
        expect(recommendation).toHaveProperty("impact");
      });

      expect(mockConsoleLog).toHaveBeenCalledWith(
        expect.stringContaining(
          `👤 Personalized recommendations for user ${userId}:`,
        ),
        result,
      );
    });
  });

  describe("Private Helper Methods", () => {
    it("should handle optimization suggestions generation", () => {
      const suggestions = analytics["generateOptimizationSuggestions"]();

      expect(Array.isArray(suggestions)).toBe(true);
      suggestions.forEach((suggestion) => {
        expect(suggestion).toHaveProperty("type");
        expect(suggestion).toHaveProperty("description");
        expect(suggestion).toHaveProperty("impact");
        expect(suggestion).toHaveProperty("effort");
        expect(suggestion).toHaveProperty("priority");
      });
    });

    it("should calculate quality scores", () => {
      const patterns = { complexity: 0.5, effectiveness: 0.8 };
      const score = analytics["calculateQualityScore"](patterns);

      expect(typeof score).toBe("number");
      expect(score).toBeGreaterThanOrEqual(0);
      expect(score).toBeLessThanOrEqual(100);
    });

    it("should calculate cost efficiency", () => {
      const patterns = { averageCost: 10, averageQuality: 8 };
      const efficiency = analytics["calculateCostEfficiency"](patterns);

      expect(typeof efficiency).toBe("number");
      expect(efficiency).toBeGreaterThanOrEqual(0);
      expect(efficiency).toBeLessThanOrEqual(100);
    });

    it("should recommend models based on patterns", () => {
      const patterns = { complexity: 0.7, budget: "medium" };
      const models = analytics["recommendModels"](patterns);

      expect(Array.isArray(models)).toBe(true);
      expect(models.length).toBeGreaterThan(0);
      models.forEach((model) => {
        expect(typeof model).toBe("string");
      });
    });

    it("should analyze usage patterns", () => {
      const patterns = { frequency: 10, timeDistribution: {} };
      const usagePatterns = analytics["analyzeUsagePatterns"](patterns);

      expect(Array.isArray(usagePatterns)).toBe(true);
      usagePatterns.forEach((pattern) => {
        expect(pattern).toHaveProperty("pattern");
        expect(pattern).toHaveProperty("frequency");
        expect(pattern).toHaveProperty("trend");
      });
    });
  });
});
