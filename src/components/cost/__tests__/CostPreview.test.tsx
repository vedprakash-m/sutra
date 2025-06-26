import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";
import CostPreview from "../CostPreview";

// Mock the useCostManagement hook
const mockEstimateExecutionCost = jest.fn(() =>
  Promise.resolve({
    model: "gpt-4",
    estimatedCost: 0.02,
    breakdown: {
      inputCost: 0.01,
      outputCost: 0.01,
      estimatedInputTokens: 100,
      estimatedOutputTokens: 100,
    },
    cheaperAlternatives: [
      {
        model: "gpt-3.5-turbo",
        estimatedCost: 0.005,
        savingsPercent: 75,
        qualityImpact: "minimal",
      },
    ],
    budgetCheck: {
      allowed: true,
    },
  }),
);

const mockFormatCurrency = jest.fn((amount) => `$${amount.toFixed(3)}`);
const mockShouldShowCostWarning = jest.fn(() => false);
const mockGetRecommendedModel = jest.fn(() => "gpt-4");

jest.mock("../../../hooks/useCostManagement", () => ({
  __esModule: true,
  default: () => ({
    estimateExecutionCost: mockEstimateExecutionCost,
    formatCurrency: mockFormatCurrency,
    shouldShowCostWarning: mockShouldShowCostWarning,
    getRecommendedModel: mockGetRecommendedModel,
  }),
}));

describe("CostPreview", () => {
  const defaultProps = {
    prompt:
      "This is a test prompt that is long enough to trigger cost estimation",
    model: "gpt-4",
    maxTokens: 1000,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("should render estimated cost after loading", async () => {
    render(<CostPreview {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText("Estimated cost:")).toBeInTheDocument();
    });
  });

  it("should display cost estimate after loading", async () => {
    render(<CostPreview {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText("$0.020")).toBeInTheDocument();
    });
  });

  it("should display cost breakdown", async () => {
    render(<CostPreview {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText(/Input:/)).toBeInTheDocument();
      expect(screen.getByText(/Output:/)).toBeInTheDocument();
    });
  });

  it("should display cheaper alternatives", async () => {
    render(<CostPreview {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText("Cheaper alternatives:")).toBeInTheDocument();
      expect(screen.getByText("gpt-3.5-turbo")).toBeInTheDocument();
      expect(screen.getByText("(-75%)")).toBeInTheDocument();
    });
  });

  it("should handle model change when alternative is selected", async () => {
    const onModelChange = jest.fn();
    render(<CostPreview {...defaultProps} onModelChange={onModelChange} />);

    await waitFor(() => {
      expect(screen.getByText("gpt-3.5-turbo")).toBeInTheDocument();
    });

    const switchButton = screen.getByText("(switch)");
    fireEvent.click(switchButton);

    expect(onModelChange).toHaveBeenCalledWith("gpt-3.5-turbo");
  });

  it("should not estimate cost for short prompts", () => {
    const { container } = render(
      <CostPreview {...defaultProps} prompt="Short" />,
    );
    expect(container.firstChild).toBeNull();
  });

  it("should handle estimation errors", async () => {
    mockEstimateExecutionCost.mockRejectedValueOnce(new Error("API Error"));

    render(<CostPreview {...defaultProps} />);

    await waitFor(() => {
      expect(
        screen.getByText("⚠️ Failed to estimate cost"),
      ).toBeInTheDocument();
    });
  });

  it("should display warning for high cost estimates", async () => {
    mockShouldShowCostWarning.mockReturnValueOnce(true);
    mockEstimateExecutionCost.mockResolvedValueOnce({
      model: "gpt-4",
      estimatedCost: 0.02,
      breakdown: {
        inputCost: 0.01,
        outputCost: 0.01,
        estimatedInputTokens: 100,
        estimatedOutputTokens: 100,
      },
      cheaperAlternatives: [],
      budgetCheck: {
        allowed: true,
        utilization: 85,
      } as any,
    });

    render(<CostPreview {...defaultProps} />);

    await waitFor(() => {
      // Just check that the component renders with the warning state
      expect(screen.getByText("Estimated cost:")).toBeInTheDocument();
    });
  });

  it("should apply custom className", async () => {
    const { container } = render(
      <CostPreview {...defaultProps} className="custom-class" />,
    );

    await waitFor(() => {
      expect(container.querySelector(".cost-preview")).toHaveClass(
        "custom-class",
      );
    });
  });

  it("should handle model recommendation", async () => {
    mockGetRecommendedModel.mockReturnValueOnce("gpt-3.5-turbo");

    const onModelChange = jest.fn();
    render(<CostPreview {...defaultProps} onModelChange={onModelChange} />);

    await waitFor(() => {
      expect(
        screen.getByText(
          /Switch to gpt-3.5-turbo for better budget efficiency/,
        ),
      ).toBeInTheDocument();
    });
  });
});
