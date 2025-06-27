import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { BusinessIntelligenceDashboard } from "../BusinessIntelligenceDashboard";

// Mock the services
jest.mock("@/services/enhancedMonitoring", () => ({
  __esModule: true,
  default: {
    getInstance: () => ({
      getDashboardMetrics: jest.fn().mockResolvedValue({}),
    }),
  },
}));

jest.mock("@/services/advancedAnalytics", () => ({
  __esModule: true,
  default: {
    getInstance: () => ({
      analyzePromptPatterns: jest.fn().mockResolvedValue({}),
    }),
  },
}));

// Mock the useAuth hook
jest.mock("@/components/auth/AuthProvider", () => ({
  useAuth: () => ({
    user: { id: "test-user", email: "test@example.com" },
    isAdmin: true,
    isLoading: false,
    token: "mock-token",
  }),
}));

const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <BrowserRouter>{children}</BrowserRouter>
);

describe("BusinessIntelligenceDashboard", () => {
  it("should render dashboard with loading state initially", async () => {
    render(
      <TestWrapper>
        <BusinessIntelligenceDashboard />
      </TestWrapper>,
    );

    // Check that loading state is displayed (skeleton with pulse animation)
    const skeletonElements = document.querySelectorAll(".animate-pulse");
    expect(skeletonElements.length).toBeGreaterThan(0);

    // Wait for loading to complete to prevent act() warnings
    await waitFor(() => {
      expect(
        screen.getByText("Business Intelligence Dashboard"),
      ).toBeInTheDocument();
    });
  });

  it("should render metrics after loading", async () => {
    render(
      <TestWrapper>
        <BusinessIntelligenceDashboard />
      </TestWrapper>,
    );

    // Wait for metrics to load
    await waitFor(() => {
      expect(screen.getByText("245ms")).toBeInTheDocument();
    });

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

    await waitFor(() => {
      expect(screen.getByText("245ms")).toBeInTheDocument();
      expect(screen.getByText("3.0%")).toBeInTheDocument();
      expect(screen.getByText("127")).toBeInTheDocument();
      expect(screen.getByText("$0.045")).toBeInTheDocument();
      expect(screen.getByText("98.5%")).toBeInTheDocument();
      expect(screen.getByText("4.7/5")).toBeInTheDocument();
    });
  });

  it("should render metric cards with appropriate icons", async () => {
    render(
      <TestWrapper>
        <BusinessIntelligenceDashboard />
      </TestWrapper>,
    );

    await waitFor(() => {
      // Check that metric cards are rendered
      expect(screen.getByText("Avg Response Time")).toBeInTheDocument();
    });

    // Check that all expected metric cards are rendered
    expect(screen.getByText("Error Rate")).toBeInTheDocument();
    expect(screen.getByText("Active Users")).toBeInTheDocument();
    expect(screen.getByText("Cost per Request")).toBeInTheDocument();
    expect(screen.getByText("System Health")).toBeInTheDocument();
    expect(screen.getByText("User Satisfaction")).toBeInTheDocument();

    // Check that metric values are displayed
    expect(screen.getByText("245ms")).toBeInTheDocument();
    expect(screen.getByText("3.0%")).toBeInTheDocument();
    expect(screen.getByText("127")).toBeInTheDocument();
  });
});
