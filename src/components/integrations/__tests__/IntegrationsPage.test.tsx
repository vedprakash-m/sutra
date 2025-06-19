import { render, screen } from "@testing-library/react";
import IntegrationsPage from "../IntegrationsPage";

describe("IntegrationsPage", () => {
  it("should render the integrations page with title", () => {
    render(<IntegrationsPage />);

    expect(screen.getByText("Integrations")).toBeInTheDocument();
    expect(screen.getByText("Connect to LLM providers and external services")).toBeInTheDocument();
  });

  it("should display integration cards", () => {
    render(<IntegrationsPage />);

    // Check for integration names
    expect(screen.getByText("OpenAI GPT")).toBeInTheDocument();
    expect(screen.getByText("Anthropic Claude")).toBeInTheDocument();
    expect(screen.getByText("Google Gemini")).toBeInTheDocument();
  });

  it("should display integration descriptions", () => {
    render(<IntegrationsPage />);

    expect(screen.getByText("Connect to OpenAI's GPT models for text generation")).toBeInTheDocument();
    expect(screen.getByText("Connect to Anthropic's Claude models for AI assistance")).toBeInTheDocument();
    expect(screen.getByText("Connect to Google's Gemini models for AI capabilities")).toBeInTheDocument();
  });

  it("should display status badges", () => {
    render(<IntegrationsPage />);

    // All integrations start as disconnected
    const disconnectedElements = screen.getAllByText("disconnected");
    expect(disconnectedElements).toHaveLength(3);
  });

  it("should have configure buttons for each integration", () => {
    render(<IntegrationsPage />);

    const configureButtons = screen.getAllByText("Configure");
    expect(configureButtons).toHaveLength(3);
  });

  it("should apply correct status colors", () => {
    render(<IntegrationsPage />);

    const statusBadges = screen.getAllByText("disconnected");
    statusBadges.forEach(badge => {
      expect(badge).toHaveClass("bg-gray-100", "text-gray-800");
    });
  });

  it("should render integration cards with proper structure", () => {
    render(<IntegrationsPage />);

    // Check that each integration has the expected structure
    const openAICard = screen.getByText("OpenAI GPT").closest('div');
    expect(openAICard).toBeInTheDocument();
    
    const claudeCard = screen.getByText("Anthropic Claude").closest('div');
    expect(claudeCard).toBeInTheDocument();
    
    const geminiCard = screen.getByText("Google Gemini").closest('div');
    expect(geminiCard).toBeInTheDocument();
  });
});
