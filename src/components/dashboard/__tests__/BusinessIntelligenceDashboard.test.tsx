import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BrowserRouter } from "react-router-dom";
import { BusinessIntelligenceDashboard } from "../BusinessIntelligenceDashboard";

// Mock the services
const mockGetDashboardMetrics = jest.fn().mockResolvedValue({});
const mockAnalyzePromptPatterns = jest.fn().mockResolvedValue({});
const mockPredictCostTrends = jest.fn().mockResolvedValue({});
const mockDetectAnomalies = jest.fn().mockResolvedValue({});
const mockGeneratePersonalizedRecommendations = jest.fn().mockResolvedValue({});

jest.mock("@/services/enhancedMonitoring", () => ({
  __esModule: true,
  default: {
    getInstance: () => ({
      getDashboardMetrics: mockGetDashboardMetrics,
    }),
  },
}));

jest.mock("@/services/advancedAnalytics", () => ({
  __esModule: true,
  default: {
    getInstance: () => ({
      analyzePromptPatterns: mockAnalyzePromptPatterns,
      predictCostTrends: mockPredictCostTrends,
      detectAnomalies: mockDetectAnomalies,
      generatePersonalizedRecommendations:
        mockGeneratePersonalizedRecommendations,
    }),
  },
}));

// Mock the useAuth hook
const mockUseAuth = jest.fn();
jest.mock("@/components/auth/AuthProvider", () => ({
  useAuth: () => mockUseAuth(),
}));

// Mock DOM methods for file operations
const mockClick = jest.fn();
const mockCreateObjectURL = jest.fn().mockReturnValue("mock-url");
const mockRevokeObjectURL = jest.fn();
const mockPrompt = jest.fn();
const mockAlert = jest.fn();
const mockLocalStorage = {
  setItem: jest.fn(),
  getItem: jest.fn(),
  removeItem: jest.fn(),
};

// Setup global mocks
Object.defineProperty(global, "URL", {
  value: {
    createObjectURL: mockCreateObjectURL,
    revokeObjectURL: mockRevokeObjectURL,
  },
  writable: true,
});

Object.defineProperty(global, "localStorage", {
  value: mockLocalStorage,
  writable: true,
});

Object.defineProperty(global, "prompt", {
  value: mockPrompt,
  writable: true,
});

Object.defineProperty(global, "alert", {
  value: mockAlert,
  writable: true,
});

const originalCreateElement = document.createElement;

beforeEach(() => {
  jest.clearAllMocks();

  // Set up default auth mock
  mockUseAuth.mockReturnValue({
    user: { id: "test-user", email: "test@example.com" },
    isAdmin: true,
    isLoading: false,
    token: "mock-token",
  });

  // Mock document.createElement to return a mock element
  document.createElement = jest.fn((tagName) => {
    const element = originalCreateElement.call(document, tagName);
    if (tagName === "a") {
      element.click = mockClick;
    }
    return element;
  });

  // Reset service mocks to resolve immediately
  mockGetDashboardMetrics.mockResolvedValue({});
  mockAnalyzePromptPatterns.mockResolvedValue({});
  mockPredictCostTrends.mockResolvedValue({});
  mockDetectAnomalies.mockResolvedValue({});
  mockGeneratePersonalizedRecommendations.mockResolvedValue({});
});

afterEach(() => {
  document.createElement = originalCreateElement;
});

const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <BrowserRouter>{children}</BrowserRouter>
);

describe("BusinessIntelligenceDashboard", () => {
  describe("Access Control", () => {
    it("should not render dashboard for non-admin users", () => {
      mockUseAuth.mockReturnValue({
        user: { id: "test-user", email: "test@example.com" },
        isAdmin: false,
        isLoading: false,
        token: "mock-token",
      });

      const { container } = render(
        <TestWrapper>
          <BusinessIntelligenceDashboard />
        </TestWrapper>,
      );

      expect(container).toBeEmptyDOMElement();
    });

    it("should render dashboard for admin users", async () => {
      render(
        <TestWrapper>
          <BusinessIntelligenceDashboard />
        </TestWrapper>,
      );

      // Should eventually render the dashboard
      await waitFor(
        () => {
          expect(
            screen.getByText("Business Intelligence Dashboard"),
          ).toBeInTheDocument();
        },
        { timeout: 15000 },
      );
    });
  });

  describe("Loading State", () => {
    it("should show loading skeleton initially", () => {
      render(
        <TestWrapper>
          <BusinessIntelligenceDashboard />
        </TestWrapper>,
      );

      // Check that loading state is displayed (skeleton with pulse animation)
      const skeletonElements = document.querySelectorAll(".animate-pulse");
      expect(skeletonElements.length).toBeGreaterThan(0);
    });
  });

  describe("Metrics Display", () => {
    it("should display metrics after loading", async () => {
      render(
        <TestWrapper>
          <BusinessIntelligenceDashboard />
        </TestWrapper>,
      );

      // Wait for metrics to load and check key elements
      await waitFor(
        () => {
          expect(screen.getByText("245ms")).toBeInTheDocument();
        },
        { timeout: 15000 },
      );

      expect(screen.getByText("Avg Response Time")).toBeInTheDocument();
      expect(screen.getByText("Error Rate")).toBeInTheDocument();
      expect(screen.getByText("Active Users")).toBeInTheDocument();
      expect(screen.getByText("Cost per Request")).toBeInTheDocument();
      expect(screen.getByText("System Health")).toBeInTheDocument();
      expect(screen.getByText("User Satisfaction")).toBeInTheDocument();
    });

    it("should display correct metric values", async () => {
      render(
        <TestWrapper>
          <BusinessIntelligenceDashboard />
        </TestWrapper>,
      );

      await waitFor(
        () => {
          expect(screen.getByText("245ms")).toBeInTheDocument();
          expect(screen.getByText("3.0%")).toBeInTheDocument();
          expect(screen.getByText("127")).toBeInTheDocument();
          expect(screen.getByText("$0.045")).toBeInTheDocument();
          expect(screen.getByText("98.5%")).toBeInTheDocument();
          expect(screen.getByText("4.7/5")).toBeInTheDocument();
        },
        { timeout: 15000 },
      );
    });

    it("should show live data indicator", async () => {
      render(
        <TestWrapper>
          <BusinessIntelligenceDashboard />
        </TestWrapper>,
      );

      await waitFor(
        () => {
          expect(screen.getByText("Live Data")).toBeInTheDocument();
        },
        { timeout: 15000 },
      );
    });
  });

  describe("Error Handling", () => {
    it("should handle service errors gracefully", async () => {
      const consoleSpy = jest
        .spyOn(console, "error")
        .mockImplementation(() => {});

      mockGetDashboardMetrics.mockRejectedValue(new Error("Service error"));
      mockAnalyzePromptPatterns.mockRejectedValue(new Error("Analytics error"));

      render(
        <TestWrapper>
          <BusinessIntelligenceDashboard />
        </TestWrapper>,
      );

      await waitFor(
        () => {
          expect(consoleSpy).toHaveBeenCalledWith(
            "Failed to load dashboard metrics:",
            expect.any(Error),
          );
        },
        { timeout: 15000 },
      );

      consoleSpy.mockRestore();
    });
  });

  describe("Button Interactions", () => {
    it("should render action buttons", async () => {
      render(
        <TestWrapper>
          <BusinessIntelligenceDashboard />
        </TestWrapper>,
      );

      await waitFor(
        () => {
          expect(screen.getByText("Generate Report")).toBeInTheDocument();
          expect(screen.getByText("Export Metrics")).toBeInTheDocument();
          expect(screen.getByText("Configure Alerts")).toBeInTheDocument();
        },
        { timeout: 15000 },
      );
    });

    it("should handle export metrics button click", async () => {
      render(
        <TestWrapper>
          <BusinessIntelligenceDashboard />
        </TestWrapper>,
      );

      await waitFor(
        () => {
          expect(screen.getByText("Export Metrics")).toBeInTheDocument();
        },
        { timeout: 15000 },
      );

      const exportButton = screen.getByText("Export Metrics");
      await userEvent.click(exportButton);

      // Should trigger file creation and download
      expect(mockCreateObjectURL).toHaveBeenCalled();
    });

    it("should handle alert configuration with valid JSON", async () => {
      const alertSpy = jest.spyOn(window, "alert").mockImplementation(() => {});
      const validConfig = {
        responseTime: 500,
        errorRate: 0.02,
        systemHealth: 97,
      };
      mockPrompt.mockReturnValue(JSON.stringify(validConfig));

      render(
        <TestWrapper>
          <BusinessIntelligenceDashboard />
        </TestWrapper>,
      );

      await waitFor(
        () => {
          expect(screen.getByText("Configure Alerts")).toBeInTheDocument();
        },
        { timeout: 15000 },
      );

      const alertButton = screen.getByText("Configure Alerts");
      await userEvent.click(alertButton);

      expect(mockPrompt).toHaveBeenCalled();
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
        "sutra-alert-config",
        JSON.stringify(validConfig),
      );
      expect(alertSpy).toHaveBeenCalledWith(
        "Alert configuration saved successfully!",
      );

      alertSpy.mockRestore();
    });

    it("should handle invalid JSON in alert configuration", async () => {
      const consoleSpy = jest
        .spyOn(console, "error")
        .mockImplementation(() => {});
      const alertSpy = jest.spyOn(window, "alert").mockImplementation(() => {});

      mockPrompt.mockReturnValue("invalid json");

      render(
        <TestWrapper>
          <BusinessIntelligenceDashboard />
        </TestWrapper>,
      );

      await waitFor(
        () => {
          expect(screen.getByText("Configure Alerts")).toBeInTheDocument();
        },
        { timeout: 15000 },
      );

      const alertButton = screen.getByText("Configure Alerts");
      await userEvent.click(alertButton);

      expect(consoleSpy).toHaveBeenCalledWith(
        "❌ Invalid JSON format:",
        expect.any(Error),
      );
      expect(alertSpy).toHaveBeenCalledWith(
        "Invalid JSON format. Please check your input.",
      );

      consoleSpy.mockRestore();
      alertSpy.mockRestore();
    });
  });

  describe("Component Features", () => {
    it("should render enhanced analytics section", async () => {
      render(
        <TestWrapper>
          <BusinessIntelligenceDashboard />
        </TestWrapper>,
      );

      await waitFor(
        () => {
          expect(
            screen.getByText("🚀 Enhanced Monitoring & Analytics (Phase 1)"),
          ).toBeInTheDocument();
        },
        { timeout: 15000 },
      );

      expect(screen.getByText("✅ Implemented Features")).toBeInTheDocument();
      expect(screen.getByText("🔄 Coming Next (Phase 2)")).toBeInTheDocument();
    });
  });

  describe("Service Integration", () => {
    it("should call services during initialization", async () => {
      render(
        <TestWrapper>
          <BusinessIntelligenceDashboard />
        </TestWrapper>,
      );

      await waitFor(
        () => {
          expect(mockGetDashboardMetrics).toHaveBeenCalled();
          expect(mockAnalyzePromptPatterns).toHaveBeenCalledWith("test-user");
        },
        { timeout: 15000 },
      );
    });

    it("should use anonymous as fallback user id", async () => {
      mockUseAuth.mockReturnValue({
        user: null,
        isAdmin: true,
        isLoading: false,
        token: "mock-token",
      });

      render(
        <TestWrapper>
          <BusinessIntelligenceDashboard />
        </TestWrapper>,
      );

      await waitFor(
        () => {
          expect(mockAnalyzePromptPatterns).toHaveBeenCalledWith("anonymous");
        },
        { timeout: 15000 },
      );
    });
  });
});
