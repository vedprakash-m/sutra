import EnhancedMonitoring from "../enhancedMonitoring";

// Mock console methods
const mockConsoleLog = jest.spyOn(console, "log").mockImplementation();
const mockConsoleWarn = jest.spyOn(console, "warn").mockImplementation();
const mockConsoleError = jest.spyOn(console, "error").mockImplementation();

describe("EnhancedMonitoring", () => {
  let service: EnhancedMonitoring;

  beforeEach(() => {
    service = EnhancedMonitoring.getInstance();
    jest.clearAllMocks();
  });

  afterAll(() => {
    mockConsoleLog.mockRestore();
    mockConsoleWarn.mockRestore();
    mockConsoleError.mockRestore();
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
});
