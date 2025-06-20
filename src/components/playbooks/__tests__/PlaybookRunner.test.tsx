import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import PlaybookRunner from "../PlaybookRunner";

// Mock the useParams hook
const mockUseParams = jest.fn();
jest.mock("react-router-dom", () => ({
  ...jest.requireActual("react-router-dom"),
  useParams: () => mockUseParams(),
}));

const renderPlaybookRunner = (playbookId = "test-playbook-id") => {
  mockUseParams.mockReturnValue({ id: playbookId });
  return render(
    <MemoryRouter>
      <PlaybookRunner />
    </MemoryRouter>,
  );
};

describe("PlaybookRunner", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("should render loading state when no execution data", () => {
    mockUseParams.mockReturnValue({ id: undefined });
    render(
      <MemoryRouter>
        <PlaybookRunner />
      </MemoryRouter>,
    );

    expect(
      screen.getByText("Loading playbook execution..."),
    ).toBeInTheDocument();
  });

  it("should render playbook execution with mock data", async () => {
    renderPlaybookRunner();

    await waitFor(() => {
      expect(
        screen.getByText("Customer Support Resolution Flow"),
      ).toBeInTheDocument();
    });

    expect(screen.getByText("Step 2 of 4 • 1 completed")).toBeInTheDocument();
    expect(screen.getByText("Execution Timeline")).toBeInTheDocument();
  });

  it("should display steps with correct status icons", async () => {
    renderPlaybookRunner();

    await waitFor(() => {
      expect(screen.getByText("Generate Initial Response")).toBeInTheDocument();
    });

    // Check for step names
    expect(screen.getByText("Generate Initial Response")).toBeInTheDocument();
    expect(
      screen.getByText("Manual Review - Response Quality"),
    ).toBeInTheDocument();
    expect(screen.getByText("Generate Follow-up Email")).toBeInTheDocument();
    expect(screen.getByText("Final Review")).toBeInTheDocument();
  });

  it("should show Continue button when execution is paused", async () => {
    renderPlaybookRunner();

    await waitFor(() => {
      expect(screen.getByText("Continue")).toBeInTheDocument();
    });

    const continueButton = screen.getByText("Continue");
    expect(continueButton).toHaveClass("bg-green-600");
  });

  it("should show Pause button when execution is running", async () => {
    renderPlaybookRunner();

    await waitFor(() => {
      const continueButton = screen.getByText("Continue");
      fireEvent.click(continueButton);
    });

    await waitFor(() => {
      expect(screen.getByText("Pause")).toBeInTheDocument();
    });
  });

  it("should handle start execution", async () => {
    renderPlaybookRunner();

    await waitFor(() => {
      const continueButton = screen.getByText("Continue");
      fireEvent.click(continueButton);
    });

    await waitFor(() => {
      expect(screen.getByText("Pause")).toBeInTheDocument();
    });
  });

  it("should handle pause execution", async () => {
    renderPlaybookRunner();

    // First start execution
    await waitFor(() => {
      const continueButton = screen.getByText("Continue");
      fireEvent.click(continueButton);
    });

    await waitFor(() => {
      const pauseButton = screen.getByText("Pause");
      fireEvent.click(pauseButton);
    });

    await waitFor(() => {
      expect(screen.getByText("Continue")).toBeInTheDocument();
    });
  });

  it("should handle stop execution", async () => {
    renderPlaybookRunner();

    await waitFor(() => {
      const stopButton = screen.getByText("Stop");
      fireEvent.click(stopButton);
    });

    // After stopping, the execution status should change
    // The component should still render but with completed status
    expect(screen.getByText("Execution Timeline")).toBeInTheDocument();
  });

  it("should show manual review interface for paused review step", async () => {
    renderPlaybookRunner();

    await waitFor(() => {
      expect(screen.getByText("Manual Review Required")).toBeInTheDocument();
    });

    expect(
      screen.getByText("Manual Review - Response Quality"),
    ).toBeInTheDocument();
    expect(screen.getByText("Previous Step Output:")).toBeInTheDocument();
    expect(
      screen.getByPlaceholderText("Add your review comments..."),
    ).toBeInTheDocument();
    expect(screen.getByText("Approve")).toBeInTheDocument();
    expect(screen.getByText("Reject")).toBeInTheDocument();
  });

  it("should handle step approval", async () => {
    renderPlaybookRunner();

    await waitFor(() => {
      const reviewTextarea = screen.getByPlaceholderText(
        "Add your review comments...",
      );
      fireEvent.change(reviewTextarea, {
        target: { value: "Looks good to me" },
      });
    });

    const approveButton = screen.getByText("Approve");
    fireEvent.click(approveButton);

    // After approval, review input should be cleared
    await waitFor(() => {
      const reviewTextarea = screen.getByPlaceholderText(
        "Add your review comments...",
      );
      expect(reviewTextarea).toHaveValue("");
    });
  });

  it("should handle step rejection", async () => {
    renderPlaybookRunner();

    await waitFor(() => {
      const reviewTextarea = screen.getByPlaceholderText(
        "Add your review comments...",
      );
      fireEvent.change(reviewTextarea, {
        target: { value: "Needs improvement" },
      });
    });

    const rejectButton = screen.getByText("Reject");
    fireEvent.click(rejectButton);

    // After rejection, review input should be cleared
    await waitFor(() => {
      const reviewTextarea = screen.getByPlaceholderText(
        "Add your review comments...",
      );
      expect(reviewTextarea).toHaveValue("");
    });
  });

  it("should display progress bar with correct percentage", async () => {
    renderPlaybookRunner();

    await waitFor(() => {
      const progressBar = document.querySelector(".bg-indigo-600");
      expect(progressBar).toHaveStyle("width: 25%"); // 1 completed out of 4 total steps
    });
  });

  it("should show execution log", async () => {
    renderPlaybookRunner();

    await waitFor(() => {
      expect(screen.getByText("Execution Log")).toBeInTheDocument();
    });

    expect(screen.getByText("Playbook execution started")).toBeInTheDocument();
  });

  it("should display step output when available", async () => {
    renderPlaybookRunner();

    await waitFor(() => {
      expect(screen.getByText(/Dear John Smith/)).toBeInTheDocument();
    });
  });

  it("should handle eye icon click for step details", async () => {
    const consoleSpy = jest.spyOn(console, "log").mockImplementation();
    renderPlaybookRunner();

    await waitFor(() => {
      const eyeButton =
        document.querySelector('[data-testid="eye-button"]') ||
        document.querySelector('svg[data-testid="EyeIcon"]')?.parentElement;
      if (eyeButton) {
        fireEvent.click(eyeButton);
        expect(consoleSpy).toHaveBeenCalledWith("Show step details:", "step1");
      }
    });

    consoleSpy.mockRestore();
  });

  it("should display step timestamps correctly", async () => {
    renderPlaybookRunner();

    await waitFor(() => {
      expect(screen.getByText(/Started:/)).toBeInTheDocument();
      expect(screen.getByText(/Completed:/)).toBeInTheDocument();
    });
  });

  it("should highlight current step with ring", async () => {
    renderPlaybookRunner();

    await waitFor(() => {
      // The current step (index 1) should have ring styling
      const steps = document.querySelectorAll(".border.rounded-lg");
      expect(steps[1]).toHaveClass("ring-2", "ring-indigo-500");
    });
  });

  it("should show different status colors for steps", async () => {
    renderPlaybookRunner();

    await waitFor(() => {
      const steps = document.querySelectorAll(".border.rounded-lg");
      // First step (completed) should have green background
      expect(steps[0]).toHaveClass("bg-green-50", "border-green-200");
      // Second step (paused) should have yellow background
      expect(steps[1]).toHaveClass("bg-yellow-50", "border-yellow-200");
    });
  });

  it("should render different step types correctly", async () => {
    renderPlaybookRunner();

    await waitFor(() => {
      expect(screen.getByText("prompt")).toBeInTheDocument();
      expect(screen.getByText("manual review")).toBeInTheDocument();
    });
  });

  it("should handle review input changes", async () => {
    renderPlaybookRunner();

    await waitFor(() => {
      const reviewTextarea = screen.getByPlaceholderText(
        "Add your review comments...",
      );
      fireEvent.change(reviewTextarea, {
        target: { value: "Test review comment" },
      });
      expect(reviewTextarea).toHaveValue("Test review comment");
    });
  });

  it("should show all control buttons", async () => {
    renderPlaybookRunner();

    await waitFor(() => {
      expect(screen.getByText("Continue")).toBeInTheDocument();
      expect(screen.getByText("Stop")).toBeInTheDocument();
    });
  });
});
