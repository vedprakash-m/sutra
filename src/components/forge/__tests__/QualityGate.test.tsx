/**
 * QualityGate.test.tsx — Unit tests for the QualityGate component
 * Tests pass/fail rendering, progress bar, override button, and callback behavior.
 */
import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { QualityGate } from "../QualityGate";

describe("QualityGate", () => {
  const defaultProps = {
    threshold: 75,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  // ────────────────────────────────────────────────────────────────
  // Rendering
  // ────────────────────────────────────────────────────────────────

  it("renders with default title", () => {
    render(<QualityGate {...defaultProps} />);
    expect(screen.getByText("Quality Gate")).toBeInTheDocument();
  });

  it("renders custom title and description", () => {
    render(
      <QualityGate
        {...defaultProps}
        title="Idea Gate"
        description="Minimum 75% to proceed"
      />,
    );
    expect(screen.getByText("Idea Gate")).toBeInTheDocument();
    expect(screen.getByText("Minimum 75% to proceed")).toBeInTheDocument();
  });

  it("renders threshold label", () => {
    render(<QualityGate {...defaultProps} />);
    expect(screen.getByText("Threshold: 75%")).toBeInTheDocument();
  });

  // ────────────────────────────────────────────────────────────────
  // Score resolution — supports score | currentScore | quality
  // ────────────────────────────────────────────────────────────────

  it("uses `score` prop when provided", () => {
    render(<QualityGate {...defaultProps} score={85} />);
    expect(screen.getByText("85%")).toBeInTheDocument();
    expect(screen.getByText("✓ Pass")).toBeInTheDocument();
  });

  it("falls back to `currentScore` when `score` is absent", () => {
    render(<QualityGate {...defaultProps} currentScore={60} />);
    expect(screen.getByText("60%")).toBeInTheDocument();
    expect(screen.getByText("⚠ Below Threshold")).toBeInTheDocument();
  });

  it("falls back to `quality.overallScore` when others absent", () => {
    render(<QualityGate {...defaultProps} quality={{ overallScore: 90 }} />);
    expect(screen.getByText("90%")).toBeInTheDocument();
    expect(screen.getByText("✓ Pass")).toBeInTheDocument();
  });

  it("defaults to 0 when no score is provided", () => {
    render(<QualityGate {...defaultProps} />);
    expect(screen.getByText("0%")).toBeInTheDocument();
    expect(screen.getByText("⚠ Below Threshold")).toBeInTheDocument();
  });

  // ────────────────────────────────────────────────────────────────
  // Pass / Fail styling
  // ────────────────────────────────────────────────────────────────

  it("shows green styling when score >= threshold", () => {
    const { container } = render(<QualityGate {...defaultProps} score={80} />);
    const wrapper = container.firstChild as HTMLElement;
    expect(wrapper.className).toContain("border-green-200");
    expect(wrapper.className).toContain("bg-green-50");
  });

  it("shows yellow styling when score < threshold", () => {
    const { container } = render(<QualityGate {...defaultProps} score={50} />);
    const wrapper = container.firstChild as HTMLElement;
    expect(wrapper.className).toContain("border-yellow-200");
    expect(wrapper.className).toContain("bg-yellow-50");
  });

  // ────────────────────────────────────────────────────────────────
  // Progress bar width
  // ────────────────────────────────────────────────────────────────

  it("renders progress bar with correct width", () => {
    const { container } = render(<QualityGate {...defaultProps} score={45} />);
    // The component sets width as percentage of the score
    const bars = container.querySelectorAll("[style]");
    const barWithWidth = Array.from(bars).find(
      (el) => (el as HTMLElement).style.width,
    );
    expect(barWithWidth).toBeTruthy();
    expect((barWithWidth as HTMLElement).style.width).toBe("45%");
  });

  // ────────────────────────────────────────────────────────────────
  // Callbacks (onPass / onBlock)
  // ────────────────────────────────────────────────────────────────

  it("calls onPass when score >= threshold", () => {
    const onPass = jest.fn();
    const onBlock = jest.fn();
    render(
      <QualityGate
        {...defaultProps}
        score={80}
        onPass={onPass}
        onBlock={onBlock}
      />,
    );
    expect(onPass).toHaveBeenCalled();
    expect(onBlock).not.toHaveBeenCalled();
  });

  it("calls onBlock when score < threshold", () => {
    const onPass = jest.fn();
    const onBlock = jest.fn();
    render(
      <QualityGate
        {...defaultProps}
        score={50}
        onPass={onPass}
        onBlock={onBlock}
      />,
    );
    expect(onBlock).toHaveBeenCalled();
    expect(onPass).not.toHaveBeenCalled();
  });

  it("does not call callbacks when score is 0", () => {
    const onPass = jest.fn();
    const onBlock = jest.fn();
    render(
      <QualityGate
        {...defaultProps}
        score={0}
        onPass={onPass}
        onBlock={onBlock}
      />,
    );
    // actualScore is 0, so the condition `actualScore > 0` is false
    expect(onPass).not.toHaveBeenCalled();
    expect(onBlock).not.toHaveBeenCalled();
  });

  // ────────────────────────────────────────────────────────────────
  // Override button
  // ────────────────────────────────────────────────────────────────

  it("shows override button when below threshold and allowOverride", () => {
    render(
      <QualityGate
        {...defaultProps}
        score={50}
        allowOverride={true}
        onOverride={jest.fn()}
      />,
    );
    expect(screen.getByText(/Expert Override/)).toBeInTheDocument();
  });

  it("does not show override button when passing", () => {
    render(
      <QualityGate
        {...defaultProps}
        score={80}
        allowOverride={true}
        onOverride={jest.fn()}
      />,
    );
    expect(screen.queryByText(/Expert Override/)).not.toBeInTheDocument();
  });

  it("does not show override button when allowOverride is false", () => {
    render(<QualityGate {...defaultProps} score={50} allowOverride={false} />);
    expect(screen.queryByText(/Expert Override/)).not.toBeInTheDocument();
  });

  it("calls onOverride when override button is clicked", () => {
    const onOverride = jest.fn();
    render(
      <QualityGate
        {...defaultProps}
        score={50}
        allowOverride={true}
        onOverride={onOverride}
      />,
    );
    fireEvent.click(screen.getByText(/Expert Override/));
    expect(onOverride).toHaveBeenCalledTimes(1);
  });

  // ────────────────────────────────────────────────────────────────
  // Edge cases
  // ────────────────────────────────────────────────────────────────

  it("treats exact threshold as pass", () => {
    render(<QualityGate {...defaultProps} score={75} />);
    expect(screen.getByText("✓ Pass")).toBeInTheDocument();
  });

  it("treats one below threshold as fail", () => {
    render(<QualityGate {...defaultProps} score={74} />);
    expect(screen.getByText("⚠ Below Threshold")).toBeInTheDocument();
  });

  it("handles 100% score", () => {
    render(<QualityGate {...defaultProps} score={100} />);
    expect(screen.getByText("100%")).toBeInTheDocument();
    expect(screen.getByText("✓ Pass")).toBeInTheDocument();
  });
});
