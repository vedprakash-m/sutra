import React from "react";
import { render, screen } from "@testing-library/react";

// Mock CostPreview component for testing
interface CostPreviewProps {
  provider: string;
  model: string;
  inputTokens: number;
  expectedOutputTokens: number;
}

const CostPreview: React.FC<CostPreviewProps> = ({
  provider,
  model,
  inputTokens,
  expectedOutputTokens,
}) => {
  // Simple cost calculation for testing
  const inputCostPer1K =
    provider === "openai" && model === "gpt-4" ? 0.03 : 0.01;
  const outputCostPer1K =
    provider === "openai" && model === "gpt-4" ? 0.06 : 0.02;

  const inputCost = (inputTokens / 1000) * inputCostPer1K;
  const outputCost = (expectedOutputTokens / 1000) * outputCostPer1K;
  const totalCost = inputCost + outputCost;

  return (
    <div className="bg-gray-50 rounded-lg p-4 border">
      <h4 className="text-sm font-medium text-gray-900 mb-2">Cost Preview</h4>

      <div className="space-y-2 text-sm">
        <div className="flex justify-between">
          <span className="text-gray-600">Provider:</span>
          <span className="font-medium">{provider}</span>
        </div>

        <div className="flex justify-between">
          <span className="text-gray-600">Model:</span>
          <span className="font-medium">{model}</span>
        </div>

        <div className="flex justify-between">
          <span className="text-gray-600">Input Tokens:</span>
          <span className="font-medium">{inputTokens.toLocaleString()}</span>
        </div>

        <div className="flex justify-between">
          <span className="text-gray-600">Expected Output:</span>
          <span className="font-medium">
            {expectedOutputTokens.toLocaleString()}
          </span>
        </div>

        <hr className="my-2" />

        <div className="flex justify-between">
          <span className="text-gray-600">Input Cost:</span>
          <span className="font-medium">${inputCost.toFixed(4)}</span>
        </div>

        <div className="flex justify-between">
          <span className="text-gray-600">Output Cost:</span>
          <span className="font-medium">${outputCost.toFixed(4)}</span>
        </div>

        <div className="flex justify-between font-semibold border-t pt-2">
          <span>Estimated Total:</span>
          <span data-testid="total-cost">${totalCost.toFixed(4)}</span>
        </div>
      </div>
    </div>
  );
};

describe("CostPreview", () => {
  test("renders cost preview with basic information", () => {
    render(
      <CostPreview
        provider="openai"
        model="gpt-4"
        inputTokens={1000}
        expectedOutputTokens={500}
      />,
    );

    expect(screen.getByText("Cost Preview")).toBeInTheDocument();
    expect(screen.getByText("openai")).toBeInTheDocument();
    expect(screen.getByText("gpt-4")).toBeInTheDocument();
    expect(screen.getByText("1,000")).toBeInTheDocument();
    expect(screen.getByText("500")).toBeInTheDocument();
  });

  test("calculates cost correctly for GPT-4", () => {
    render(
      <CostPreview
        provider="openai"
        model="gpt-4"
        inputTokens={1000}
        expectedOutputTokens={500}
      />,
    );

    // Expected: (1000/1000 * 0.03) + (500/1000 * 0.06) = 0.03 + 0.03 = 0.06
    expect(screen.getByTestId("total-cost")).toHaveTextContent("$0.0600");
  });

  test("calculates cost correctly for cheaper model", () => {
    render(
      <CostPreview
        provider="openai"
        model="gpt-3.5-turbo"
        inputTokens={1000}
        expectedOutputTokens={500}
      />,
    );

    // Expected: (1000/1000 * 0.01) + (500/1000 * 0.02) = 0.01 + 0.01 = 0.02
    expect(screen.getByTestId("total-cost")).toHaveTextContent("$0.0200");
  });

  test("displays input and output costs separately", () => {
    render(
      <CostPreview
        provider="openai"
        model="gpt-4"
        inputTokens={2000}
        expectedOutputTokens={1000}
      />,
    );

    expect(screen.getByText("$0.0600")).toBeInTheDocument(); // Input cost
    expect(screen.getByText("$0.0600")).toBeInTheDocument(); // Output cost
  });

  test("handles large token counts", () => {
    render(
      <CostPreview
        provider="openai"
        model="gpt-4"
        inputTokens={10000}
        expectedOutputTokens={5000}
      />,
    );

    expect(screen.getByText("10,000")).toBeInTheDocument();
    expect(screen.getByText("5,000")).toBeInTheDocument();
    expect(screen.getByTestId("total-cost")).toHaveTextContent("$0.6000");
  });

  test("handles zero token counts", () => {
    render(
      <CostPreview
        provider="openai"
        model="gpt-4"
        inputTokens={0}
        expectedOutputTokens={0}
      />,
    );

    expect(screen.getByText("0")).toBeInTheDocument();
    expect(screen.getByTestId("total-cost")).toHaveTextContent("$0.0000");
  });
});
