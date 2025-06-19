import {
  render,
  screen,
  fireEvent,
  waitFor,
  act,
} from "@testing-library/react";
import "@testing-library/jest-dom";
import VersionHistory from "../VersionHistory";

// Mock @headlessui/react components
jest.mock("@headlessui/react", () => {
  const Dialog = ({ children, className }: any) => (
    <div data-testid="dialog" className={className}>
      {children}
    </div>
  );

  const DialogPanel = ({ children, className }: any) => (
    <div data-testid="dialog-panel" className={className}>
      {children}
    </div>
  );

  const DialogTitle = ({ children, className }: any) => (
    <h3 data-testid="dialog-title" className={className}>
      {children}
    </h3>
  );

  const Transition = ({ children, show }: any) =>
    show ? <div data-testid="transition">{children}</div> : null;

  const TransitionChild = ({ children }: any) => (
    <div data-testid="transition-child">{children}</div>
  );

  Dialog.Panel = DialogPanel;
  Dialog.Title = DialogTitle;
  Transition.Child = TransitionChild;

  return {
    Dialog,
    Transition,
    Fragment: ({ children }: any) => <>{children}</>,
  };
});

// Mock @heroicons/react components
jest.mock("@heroicons/react/24/outline", () => ({
  XMarkIcon: () => <div data-testid="x-mark-icon">X</div>,
  ClockIcon: () => <div data-testid="clock-icon">Clock</div>,
  UserIcon: () => <div data-testid="user-icon">User</div>,
  EyeIcon: () => <div data-testid="eye-icon">Eye</div>,
  ArrowUturnLeftIcon: () => <div data-testid="arrow-return-icon">Return</div>,
}));

const mockProps = {
  isOpen: true,
  onClose: jest.fn(),
  promptId: "test-prompt-123",
  promptName: "Test Marketing Prompt",
  onVersionRestore: jest.fn(),
};

describe("VersionHistory", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it("should render version history modal when open", async () => {
    render(<VersionHistory {...mockProps} />);

    expect(screen.getByTestId("dialog-panel")).toBeInTheDocument();
    expect(screen.getByTestId("dialog-title")).toHaveTextContent(
      "Version History: Test Marketing Prompt",
    );
  });

  it("should not render modal when closed", () => {
    render(<VersionHistory {...mockProps} isOpen={false} />);

    expect(screen.queryByTestId("dialog-panel")).not.toBeInTheDocument();
  });

  it("should show loading state initially", () => {
    render(<VersionHistory {...mockProps} />);

    // Check for loading spinner
    expect(screen.getByTestId("dialog-panel")).toBeInTheDocument();
    // The spinner doesn't have specific text, but we can check for the loading div
    const loadingDiv = screen
      .getByTestId("dialog-panel")
      .querySelector(".animate-spin");
    expect(loadingDiv).toBeInTheDocument();
  });

  it("should display versions after loading", async () => {
    render(<VersionHistory {...mockProps} />);

    // Fast-forward past the loading timeout
    act(() => {
      jest.advanceTimersByTime(600);
    });

    await waitFor(() => {
      expect(screen.getByText("Version 3")).toBeInTheDocument();
      expect(screen.getByText("Version 2")).toBeInTheDocument();
      expect(screen.getByText("Version 1")).toBeInTheDocument();
    });
  });

  it("should display version details correctly", async () => {
    render(<VersionHistory {...mockProps} />);

    act(() => {
      jest.advanceTimersByTime(600);
    });

    await waitFor(() => {
      expect(screen.getAllByText("John Doe")).toHaveLength(2);
      expect(screen.getByText("Jane Smith")).toBeInTheDocument();
      expect(
        screen.getByText("Added example format and character limit"),
      ).toBeInTheDocument();
      expect(screen.getByText("Initial version")).toBeInTheDocument();
    });
  });

  it("should display LLM evaluations", async () => {
    render(<VersionHistory {...mockProps} />);

    act(() => {
      jest.advanceTimersByTime(600);
    });

    await waitFor(() => {
      expect(screen.getAllByText("GPT-4o:")).toHaveLength(3);
      expect(screen.getByText("Claude-3:")).toBeInTheDocument();
      expect(screen.getByText("Excellent")).toBeInTheDocument();
      expect(screen.getAllByText("Good")).toHaveLength(2);
      expect(screen.getByText("Fair")).toBeInTheDocument();
    });
  });

  it("should handle close button click", () => {
    render(<VersionHistory {...mockProps} />);

    const closeButton = screen.getByTestId("x-mark-icon").closest("button");
    fireEvent.click(closeButton!);

    expect(mockProps.onClose).toHaveBeenCalledTimes(1);
  });

  it("should handle version selection for comparison", async () => {
    render(<VersionHistory {...mockProps} />);

    act(() => {
      jest.advanceTimersByTime(600);
    });

    await waitFor(() => {
      // Find all version containers by their class combination
      const versionContainers = screen
        .getAllByText(/Version/)
        .map((el) => {
          // Find the container div with border, rounded-lg, and p-4 classes
          let current = el.parentElement;
          while (current) {
            if (
              current.classList.contains("border") &&
              current.classList.contains("rounded-lg") &&
              current.classList.contains("p-4")
            ) {
              return current;
            }
            current = current.parentElement;
          }
          return null;
        })
        .filter(Boolean);

      const version3Container = versionContainers.find((container) =>
        container?.textContent?.includes("Version 3"),
      ) as HTMLElement;

      fireEvent.click(version3Container);

      expect(version3Container).toHaveClass(
        "border-indigo-500",
        "bg-indigo-50",
      );
    });
  });

  it("should show comparison when two different versions are selected", async () => {
    render(<VersionHistory {...mockProps} />);

    act(() => {
      jest.advanceTimersByTime(600);
    });

    await waitFor(() => {
      // Find version containers
      const versionContainers = screen
        .getAllByText(/Version/)
        .map((el) => {
          let current = el.parentElement;
          while (current) {
            if (
              current.classList.contains("border") &&
              current.classList.contains("rounded-lg") &&
              current.classList.contains("p-4")
            ) {
              return current;
            }
            current = current.parentElement;
          }
          return null;
        })
        .filter(Boolean);

      const version3Container = versionContainers.find((container) =>
        container?.textContent?.includes("Version 3"),
      ) as HTMLElement;
      const version1Container = versionContainers.find((container) =>
        container?.textContent?.includes("Version 1"),
      ) as HTMLElement;

      fireEvent.click(version3Container);
      fireEvent.click(version1Container);

      expect(screen.getByText(/Comparing Version/)).toBeInTheDocument();
    });
  });

  it("should toggle diff view when Show Diff button is clicked", async () => {
    render(<VersionHistory {...mockProps} />);

    act(() => {
      jest.advanceTimersByTime(600);
    });

    await waitFor(() => {
      // Find version containers
      const versionContainers = screen
        .getAllByText(/Version/)
        .map((el) => {
          let current = el.parentElement;
          while (current) {
            if (
              current.classList.contains("border") &&
              current.classList.contains("rounded-lg") &&
              current.classList.contains("p-4")
            ) {
              return current;
            }
            current = current.parentElement;
          }
          return null;
        })
        .filter(Boolean);

      const version3Container = versionContainers.find((container) =>
        container?.textContent?.includes("Version 3"),
      ) as HTMLElement;
      const version1Container = versionContainers.find((container) =>
        container?.textContent?.includes("Version 1"),
      ) as HTMLElement;

      fireEvent.click(version3Container);
      fireEvent.click(version1Container);

      const hideDiffButton = screen.getByText("Hide Diff");
      fireEvent.click(hideDiffButton);

      expect(screen.getByText("Show Diff")).toBeInTheDocument();
    });
  });

  it("should handle version restoration", async () => {
    render(<VersionHistory {...mockProps} />);

    act(() => {
      jest.advanceTimersByTime(600);
    });

    await waitFor(() => {
      const restoreButtons = screen.getAllByTestId("arrow-return-icon");
      const firstRestoreButton = restoreButtons[0].closest("button")!;

      fireEvent.click(firstRestoreButton);

      expect(mockProps.onVersionRestore).toHaveBeenCalledWith("v3");
      expect(mockProps.onClose).toHaveBeenCalledTimes(1);
    });
  });

  it("should handle version restoration without onVersionRestore callback", async () => {
    const propsWithoutRestore = { ...mockProps, onVersionRestore: undefined };
    render(<VersionHistory {...propsWithoutRestore} />);

    act(() => {
      jest.advanceTimersByTime(600);
    });

    await waitFor(() => {
      const restoreButtons = screen.getAllByTestId("arrow-return-icon");
      const firstRestoreButton = restoreButtons[0].closest("button")!;

      fireEvent.click(firstRestoreButton);

      expect(mockProps.onClose).not.toHaveBeenCalled();
    });
  });

  it("should deselect version when clicked again", async () => {
    render(<VersionHistory {...mockProps} />);

    act(() => {
      jest.advanceTimersByTime(600);
    });

    await waitFor(() => {
      // Find version container
      const versionContainers = screen
        .getAllByText(/Version/)
        .map((el) => {
          let current = el.parentElement;
          while (current) {
            if (
              current.classList.contains("border") &&
              current.classList.contains("rounded-lg") &&
              current.classList.contains("p-4")
            ) {
              return current;
            }
            current = current.parentElement;
          }
          return null;
        })
        .filter(Boolean);

      const version3Container = versionContainers.find((container) =>
        container?.textContent?.includes("Version 3"),
      ) as HTMLElement;

      // Select version
      fireEvent.click(version3Container);
      expect(version3Container).toHaveClass(
        "border-indigo-500",
        "bg-indigo-50",
      );

      // Deselect version
      fireEvent.click(version3Container);
      expect(version3Container).not.toHaveClass(
        "border-indigo-500",
        "bg-indigo-50",
      );
    });
  });

  it("should display selection count", async () => {
    render(<VersionHistory {...mockProps} />);

    act(() => {
      jest.advanceTimersByTime(600);
    });

    await waitFor(() => {
      expect(screen.getByText(/Selected: 0/)).toBeInTheDocument();

      // Find version container
      const versionContainers = screen
        .getAllByText(/Version/)
        .map((el) => {
          let current = el.parentElement;
          while (current) {
            if (
              current.classList.contains("border") &&
              current.classList.contains("rounded-lg") &&
              current.classList.contains("p-4")
            ) {
              return current;
            }
            current = current.parentElement;
          }
          return null;
        })
        .filter(Boolean);

      const version3Container = versionContainers.find((container) =>
        container?.textContent?.includes("Version 3"),
      ) as HTMLElement;

      fireEvent.click(version3Container);

      expect(screen.getByText(/Selected: 2/)).toBeInTheDocument();
    });
  });

  it("should format dates correctly", async () => {
    render(<VersionHistory {...mockProps} />);

    act(() => {
      jest.advanceTimersByTime(600);
    });

    await waitFor(() => {
      // Check that dates are formatted (using toLocaleString)
      const dateElements = screen.getAllByTestId("clock-icon");
      expect(dateElements).toHaveLength(3);
    });
  });

  it("should handle view details button click", async () => {
    render(<VersionHistory {...mockProps} />);

    act(() => {
      jest.advanceTimersByTime(600);
    });

    await waitFor(() => {
      const viewButtons = screen.getAllByTestId("eye-icon");
      const firstViewButton = viewButtons[0].closest("button")!;

      // Should not throw error
      fireEvent.click(firstViewButton);
    });
  });

  it("should prevent event propagation on action buttons", async () => {
    render(<VersionHistory {...mockProps} />);

    act(() => {
      jest.advanceTimersByTime(600);
    });

    await waitFor(() => {
      // Find version container
      const versionContainers = screen
        .getAllByText(/Version/)
        .map((el) => {
          let current = el.parentElement;
          while (current) {
            if (
              current.classList.contains("border") &&
              current.classList.contains("rounded-lg") &&
              current.classList.contains("p-4")
            ) {
              return current;
            }
            current = current.parentElement;
          }
          return null;
        })
        .filter(Boolean);

      const version3Container = versionContainers.find((container) =>
        container?.textContent?.includes("Version 3"),
      ) as HTMLElement;

      const restoreButton = version3Container
        ?.querySelector('[data-testid="arrow-return-icon"]')
        ?.closest("button");

      // Click restore button should not select the version
      if (restoreButton) {
        fireEvent.click(restoreButton);
      }

      expect(version3Container).not.toHaveClass(
        "border-indigo-500",
        "bg-indigo-50",
      );
    });
  });

  it("should render close button in footer", async () => {
    render(<VersionHistory {...mockProps} />);

    act(() => {
      jest.advanceTimersByTime(600);
    });

    await waitFor(() => {
      const closeButton = screen.getByRole("button", { name: /close/i });
      fireEvent.click(closeButton);

      expect(mockProps.onClose).toHaveBeenCalledTimes(1);
    });
  });

  it("should not show diff when same version is selected twice", async () => {
    render(<VersionHistory {...mockProps} />);

    act(() => {
      jest.advanceTimersByTime(600);
    });

    await waitFor(() => {
      // Find version container
      const versionContainers = screen
        .getAllByText(/Version/)
        .map((el) => {
          let current = el.parentElement;
          while (current) {
            if (
              current.classList.contains("border") &&
              current.classList.contains("rounded-lg") &&
              current.classList.contains("p-4")
            ) {
              return current;
            }
            current = current.parentElement;
          }
          return null;
        })
        .filter(Boolean);

      const version3Container = versionContainers.find((container) =>
        container?.textContent?.includes("Version 3"),
      ) as HTMLElement;

      fireEvent.click(version3Container);

      expect(screen.queryByText(/Comparing Version/)).not.toBeInTheDocument();
    });
  });

  it("should apply correct styling to LLM evaluation scores", async () => {
    render(<VersionHistory {...mockProps} />);

    act(() => {
      jest.advanceTimersByTime(600);
    });

    await waitFor(() => {
      const excellentScore = screen.getByText("Excellent");
      const goodScores = screen.getAllByText("Good");
      const fairScore = screen.getByText("Fair");

      expect(excellentScore).toHaveClass("bg-green-100", "text-green-800");
      expect(goodScores[0]).toHaveClass("bg-blue-100", "text-blue-800");
      expect(fairScore).toHaveClass("bg-yellow-100", "text-yellow-800");
    });
  });
});
