/**
 * ProgressIndicator.test.tsx — Unit tests for the ProgressIndicator component
 * Tests step rendering, progress bar, current step highlighting, and percentage display.
 */
import React from "react";
import { render, screen } from "@testing-library/react";
import { ProgressIndicator } from "../ProgressIndicator";

describe("ProgressIndicator", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  // ────────────────────────────────────────────────────────────────
  // Default rendering
  // ────────────────────────────────────────────────────────────────

  it("renders default 5 steps when no props provided", () => {
    render(<ProgressIndicator />);
    expect(screen.getByText("Step 1")).toBeInTheDocument();
    expect(screen.getByText("Step 5")).toBeInTheDocument();
    expect(screen.getByText("Step 1 of 5")).toBeInTheDocument();
  });

  it("renders with custom step names", () => {
    const steps = ["Idea", "PRD", "UX", "Tech", "Playbook"];
    render(<ProgressIndicator steps={steps} currentStep={2} />);
    expect(screen.getByText("Idea")).toBeInTheDocument();
    expect(screen.getByText("PRD")).toBeInTheDocument();
    expect(screen.getByText("UX")).toBeInTheDocument();
    expect(screen.getByText("Tech")).toBeInTheDocument();
    expect(screen.getByText("Playbook")).toBeInTheDocument();
  });

  // ────────────────────────────────────────────────────────────────
  // Step index resolution (currentStep vs current)
  // ────────────────────────────────────────────────────────────────

  it("uses currentStep prop", () => {
    render(<ProgressIndicator currentStep={2} totalSteps={5} />);
    expect(screen.getByText("Step 3 of 5")).toBeInTheDocument();
  });

  it("falls back to current prop", () => {
    render(<ProgressIndicator current={3} totalSteps={5} />);
    expect(screen.getByText("Step 4 of 5")).toBeInTheDocument();
  });

  it("defaults to 0 when neither currentStep nor current provided", () => {
    render(<ProgressIndicator totalSteps={4} />);
    expect(screen.getByText("Step 1 of 4")).toBeInTheDocument();
  });

  // ────────────────────────────────────────────────────────────────
  // Step state indicators (completed ✓, current, future)
  // ────────────────────────────────────────────────────────────────

  it("shows checkmarks for completed steps", () => {
    const steps = ["A", "B", "C", "D"];
    const { container } = render(
      <ProgressIndicator steps={steps} currentStep={2} />,
    );
    // Steps 0, 1 are completed (index < currentIndex=2) → show ✓
    const circles = container.querySelectorAll(".rounded-full");
    // First two should contain ✓
    expect(circles[0].textContent).toBe("✓");
    expect(circles[1].textContent).toBe("✓");
    // Current step shows its 1-based number
    expect(circles[2].textContent).toBe("3");
    // Future step shows number
    expect(circles[3].textContent).toBe("4");
  });

  it("highlights current step with blue", () => {
    const { container } = render(
      <ProgressIndicator steps={["A", "B", "C"]} currentStep={1} />,
    );
    const circles = container.querySelectorAll(".rounded-full");
    expect(circles[1].className).toContain("bg-blue-500");
  });

  it("styles completed steps with green", () => {
    const { container } = render(
      <ProgressIndicator steps={["A", "B", "C"]} currentStep={2} />,
    );
    const circles = container.querySelectorAll(".rounded-full");
    expect(circles[0].className).toContain("bg-green-500");
    expect(circles[1].className).toContain("bg-green-500");
  });

  it("styles future steps with gray", () => {
    const { container } = render(
      <ProgressIndicator steps={["A", "B", "C"]} currentStep={0} />,
    );
    const circles = container.querySelectorAll(".rounded-full");
    expect(circles[1].className).toContain("bg-gray-200");
    expect(circles[2].className).toContain("bg-gray-200");
  });

  // ────────────────────────────────────────────────────────────────
  // Percentage display
  // ────────────────────────────────────────────────────────────────

  it("displays correct completion percentage", () => {
    const steps = ["A", "B", "C", "D"];
    render(<ProgressIndicator steps={steps} currentStep={1} />);
    // (1+1)/4 * 100 = 50%
    expect(screen.getByText("50% Complete")).toBeInTheDocument();
  });

  it("displays 100% on last step", () => {
    const steps = ["A", "B", "C"];
    render(<ProgressIndicator steps={steps} currentStep={2} />);
    // (2+1)/3 * 100 = 100%
    expect(screen.getByText("100% Complete")).toBeInTheDocument();
  });

  it("displays 20% for first step of 5", () => {
    render(<ProgressIndicator currentStep={0} totalSteps={5} />);
    // (0+1)/5 * 100 = 20%
    expect(screen.getByText("20% Complete")).toBeInTheDocument();
  });

  // ────────────────────────────────────────────────────────────────
  // Progress bar width
  // ────────────────────────────────────────────────────────────────

  it("renders progress bar with correct width for middle step", () => {
    const { container } = render(
      <ProgressIndicator steps={["A", "B", "C", "D", "E"]} currentStep={2} />,
    );
    const progressBar = container.querySelector(".bg-blue-500.h-2");
    // width = (2 / (5-1)) * 100 = 50%
    expect(progressBar).toBeTruthy();
    expect((progressBar as HTMLElement).style.width).toBe("50%");
  });

  it("renders 0% width when single step", () => {
    const { container } = render(
      <ProgressIndicator steps={["Only"]} currentStep={0} />,
    );
    const progressBar = container.querySelector(".bg-blue-500.h-2");
    // displaySteps.length is 1, so width = 0%
    expect((progressBar as HTMLElement).style.width).toBe("0%");
  });

  // ────────────────────────────────────────────────────────────────
  // CSS className passthrough
  // ────────────────────────────────────────────────────────────────

  it("applies custom className", () => {
    const { container } = render(
      <ProgressIndicator className="my-custom-class" />,
    );
    expect(container.firstChild).toHaveClass("my-custom-class");
  });
});
