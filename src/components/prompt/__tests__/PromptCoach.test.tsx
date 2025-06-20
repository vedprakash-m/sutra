import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import PromptCoach from "../PromptCoach";

const defaultProps = {
  promptContent: "",
  intention: "",
  contextDetails: {},
};

describe("PromptCoach", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("should render without crashing", () => {
    render(<PromptCoach {...defaultProps} promptContent="Write an email" />);
    expect(screen.getByText("PromptCoach")).toBeInTheDocument();
  });

  it("should show no suggestions for empty prompt", () => {
    render(<PromptCoach {...defaultProps} promptContent="" />);
    expect(screen.getByText("Great prompt structure!")).toBeInTheDocument();
  });

  it("should suggest adding role specification", async () => {
    render(
      <PromptCoach
        {...defaultProps}
        promptContent="Write an email about product features"
      />,
    );

    await waitFor(() => {
      expect(screen.getByText("Add Role Specification")).toBeInTheDocument();
    });

    expect(
      screen.getByText(/Start with "Act as \[role\]"/),
    ).toBeInTheDocument();
  });

  it("should suggest adding more details for short prompts", async () => {
    render(<PromptCoach {...defaultProps} promptContent="Write text" />);

    await waitFor(() => {
      expect(
        screen.getByText("Add More Specific Instructions"),
      ).toBeInTheDocument();
    });

    expect(
      screen.getByText("Provide more detailed requirements for better results"),
    ).toBeInTheDocument();
  });

  it("should suggest adding examples", async () => {
    render(
      <PromptCoach
        {...defaultProps}
        promptContent="Write a compelling marketing email for our new product launch"
      />,
    );

    await waitFor(() => {
      expect(screen.getByText("Include Examples")).toBeInTheDocument();
    });

    expect(
      screen.getByText("Add examples to clarify the expected output format"),
    ).toBeInTheDocument();
  });

  it("should suggest specifying output format", async () => {
    render(
      <PromptCoach
        {...defaultProps}
        promptContent="Create a comprehensive analysis of our quarterly performance"
      />,
    );

    await waitFor(() => {
      expect(screen.getByText("Specify Output Format")).toBeInTheDocument();
    });

    expect(
      screen.getByText(
        "Define the desired output structure (bullet points, paragraphs, etc.)",
      ),
    ).toBeInTheDocument();
  });

  it("should suggest using variables for template intention", async () => {
    render(
      <PromptCoach
        {...defaultProps}
        promptContent="Write an email about our product"
        intention="template for reusable content"
      />,
    );

    await waitFor(() => {
      expect(
        screen.getByText("Use Variables for Reusability"),
      ).toBeInTheDocument();
    });

    expect(
      screen.getByText("Add {{variables}} to make this prompt reusable"),
    ).toBeInTheDocument();
  });

  it("should suggest step-by-step approach for complex tasks", async () => {
    render(
      <PromptCoach
        {...defaultProps}
        promptContent="Analyze the market trends and create a report"
        intention="complex analysis task"
      />,
    );

    await waitFor(() => {
      expect(screen.getByText("Use Step-by-Step Approach")).toBeInTheDocument();
    });

    expect(
      screen.getByText("Break down complex tasks into clear steps"),
    ).toBeInTheDocument();
  });

  it("should suggest adding constraints", async () => {
    render(
      <PromptCoach
        {...defaultProps}
        promptContent="Write a blog post about artificial intelligence and its applications"
      />,
    );

    await waitFor(() => {
      expect(screen.getByText("Set Clear Constraints")).toBeInTheDocument();
    });
  });

  it("should handle suggestion dismissal", async () => {
    render(<PromptCoach {...defaultProps} promptContent="Write an email" />);

    await waitFor(() => {
      const dismissButton = screen.getAllByRole("button")[0]; // First dismiss button
      fireEvent.click(dismissButton);
    });

    // The dismissed suggestion should not be visible anymore
    await waitFor(() => {
      const suggestions = screen.queryAllByText("Add Role Specification");
      expect(suggestions).toHaveLength(0);
    });
  });

  it("should handle suggestion application", async () => {
    const mockOnSuggestionApply = jest.fn();
    render(
      <PromptCoach
        {...defaultProps}
        promptContent="Write an email"
        onSuggestionApply={mockOnSuggestionApply}
      />,
    );

    await waitFor(() => {
      const applyButtons = screen.getAllByTitle("Apply suggestion");
      fireEvent.click(applyButtons[0]);
    });

    expect(mockOnSuggestionApply).toHaveBeenCalled();
  });

  it("should show priority badges correctly", async () => {
    render(<PromptCoach {...defaultProps} promptContent="Write" />);

    await waitFor(() => {
      expect(screen.getAllByText("HIGH")).toHaveLength(2);
    });
  });

  it("should handle toggle expansion", async () => {
    render(<PromptCoach {...defaultProps} promptContent="Write an email" />);

    // Find the collapse/expand button
    const toggleButton = screen.getByRole("button", {
      name: /collapse|expand/i,
    });
    fireEvent.click(toggleButton);

    // The content should be hidden
    await waitFor(() => {
      expect(
        screen.queryByText("Add Role Specification"),
      ).not.toBeInTheDocument();
    });
  });

  it("should apply custom className", () => {
    render(<PromptCoach {...defaultProps} className="custom-class" />);

    const container =
      screen.getByTestId("prompt-coach") ||
      document.querySelector(".custom-class");
    expect(container).toHaveClass("custom-class");
  });

  it("should not suggest role when already present", async () => {
    render(
      <PromptCoach
        {...defaultProps}
        promptContent="Act as a professional writer and create an email"
      />,
    );

    await waitFor(() => {
      expect(
        screen.queryByText("Add Role Specification"),
      ).not.toBeInTheDocument();
    });
  });

  it("should not suggest examples when already present", async () => {
    render(
      <PromptCoach
        {...defaultProps}
        promptContent="Write an email like this: Subject: Welcome to our service"
      />,
    );

    await waitFor(() => {
      expect(screen.queryByText("Include Examples")).not.toBeInTheDocument();
    });
  });

  it("should not suggest format when already specified", async () => {
    render(
      <PromptCoach
        {...defaultProps}
        promptContent="Write an email and format it as a professional business letter"
      />,
    );

    await waitFor(() => {
      expect(
        screen.queryByText("Specify Output Format"),
      ).not.toBeInTheDocument();
    });
  });

  it("should not suggest variables when already using them", async () => {
    render(
      <PromptCoach
        {...defaultProps}
        promptContent="Write an email about {{product_name}} for {{target_audience}}"
        intention="template"
      />,
    );

    await waitFor(() => {
      expect(
        screen.queryByText("Use Variables for Reusability"),
      ).not.toBeInTheDocument();
    });
  });

  it("should not suggest steps when already present", async () => {
    render(
      <PromptCoach
        {...defaultProps}
        promptContent="First analyze the data, then create a report"
        intention="complex task"
      />,
    );

    await waitFor(() => {
      expect(
        screen.queryByText("Use Step-by-Step Approach"),
      ).not.toBeInTheDocument();
    });
  });

  it("should show different priority levels", async () => {
    render(
      <PromptCoach
        {...defaultProps}
        promptContent="Write an email about our product launch for marketing team"
      />,
    );

    await waitFor(() => {
      // Should have both high and medium priority suggestions
      expect(screen.getAllByText("HIGH")).toHaveLength(1);
      expect(screen.getAllByText("MEDIUM")).toHaveLength(2);
    });
  });

  it("should update suggestions when prompt content changes", async () => {
    const { rerender } = render(
      <PromptCoach {...defaultProps} promptContent="" />,
    );

    expect(screen.getByText("Great prompt structure!")).toBeInTheDocument();

    rerender(<PromptCoach {...defaultProps} promptContent="Write an email" />);

    await waitFor(() => {
      expect(screen.getByText("Add Role Specification")).toBeInTheDocument();
    });
  });

  it("should handle multiple suggestion types", async () => {
    render(
      <PromptCoach
        {...defaultProps}
        promptContent="Write text"
        intention="complex template"
      />,
    );

    await waitFor(() => {
      // Should show multiple suggestions for a minimal prompt
      expect(screen.getByText("Add Role Specification")).toBeInTheDocument();
      expect(
        screen.getByText("Add More Specific Instructions"),
      ).toBeInTheDocument();
      expect(screen.getByText("Include Examples")).toBeInTheDocument();
    });
  });

  it("should show suggestion examples", async () => {
    render(<PromptCoach {...defaultProps} promptContent="Write an email" />);

    await waitFor(() => {
      expect(
        screen.getByText(/Act as a professional marketing copywriter/),
      ).toBeInTheDocument();
    });
  });

  it("should handle constraints suggestion properly", async () => {
    render(
      <PromptCoach
        {...defaultProps}
        promptContent="Write a comprehensive analysis of market trends in technology sector"
      />,
    );

    await waitFor(() => {
      expect(screen.getByText("Set Clear Constraints")).toBeInTheDocument();
    });
  });
});
