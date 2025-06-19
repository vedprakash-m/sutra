import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { useParams, useNavigate } from "react-router-dom";
import PromptBuilder from "../PromptBuilder";
import { llmApi, collectionsApi } from "@/services/api";

// Mock the useAuth hook
jest.mock("@/components/auth/AuthProvider", () => ({
  useAuth: () => ({
    user: {
      id: "test-user",
      email: "test@example.com",
      name: "Test User",
    },
    isAuthenticated: true,
  }),
}));

// Mock the API
jest.mock("@/services/api", () => ({
  llmApi: {
    execute: jest.fn(),
  },
  collectionsApi: {
    create: jest.fn(),
    addPrompt: jest.fn(),
  },
}));

// Mock react-router-dom hooks
jest.mock("react-router-dom", () => ({
  ...jest.requireActual("react-router-dom"),
  useParams: jest.fn(),
  useNavigate: jest.fn(),
}));

// Mock PromptCoach component
jest.mock("../PromptCoach", () => {
  return function MockPromptCoach() {
    return <div data-testid="prompt-coach">Prompt Coach Component</div>;
  };
});

const mockNavigate = jest.fn();

beforeEach(() => {
  jest.clearAllMocks();
  (llmApi.execute as jest.Mock).mockResolvedValue({
    data: "Test response",
  });
  (collectionsApi.create as jest.Mock).mockResolvedValue({
    id: "test-collection-id",
  });
  (useParams as jest.Mock).mockReturnValue({});
  (useNavigate as jest.Mock).mockReturnValue(mockNavigate);
});

const renderPromptBuilder = () => {
  return render(
    <BrowserRouter>
      <PromptBuilder />
    </BrowserRouter>,
  );
};

describe("PromptBuilder", () => {
  it("should render the prompt builder with title", () => {
    renderPromptBuilder();

    expect(screen.getByText("Prompt Builder")).toBeInTheDocument();
    expect(
      screen.getByText("Create and test AI prompts with multi-LLM comparison"),
    ).toBeInTheDocument();
  });

  it("should render form inputs", () => {
    renderPromptBuilder();

    expect(screen.getByLabelText(/title/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/description/i)).toBeInTheDocument();
    expect(
      screen.getByPlaceholderText("Write your prompt here..."),
    ).toBeInTheDocument();
  });

  it("should handle title input changes", () => {
    renderPromptBuilder();

    const titleInput = screen.getByLabelText(/title/i);
    fireEvent.change(titleInput, { target: { value: "My Test Prompt" } });

    expect(titleInput).toHaveValue("My Test Prompt");
  });

  it("should handle description input changes", () => {
    renderPromptBuilder();

    const descriptionInput = screen.getByLabelText(/description/i);
    fireEvent.change(descriptionInput, {
      target: { value: "This is a test prompt" },
    });

    expect(descriptionInput).toHaveValue("This is a test prompt");
  });

  it("should handle content input changes", () => {
    renderPromptBuilder();

    const contentTextarea = screen.getByPlaceholderText(
      "Write your prompt here...",
    );
    fireEvent.change(contentTextarea, {
      target: { value: "Write a story about {topic}" },
    });

    expect(contentTextarea).toHaveValue("Write a story about {topic}");
  });

  it("should handle LLM selection", () => {
    renderPromptBuilder();

    const anthropicCheckbox = screen.getByLabelText(/anthropic/i);
    fireEvent.click(anthropicCheckbox);

    expect(anthropicCheckbox).toBeChecked();
  });

  it("should test prompt with selected LLMs", async () => {
    renderPromptBuilder();

    // Fill in prompt content
    const contentTextarea = screen.getByPlaceholderText(
      "Write your prompt here...",
    );
    fireEvent.change(contentTextarea, {
      target: { value: "Write a story about cats" },
    });

    // Test prompt
    const testButton = screen.getByText("Test Prompt");
    fireEvent.click(testButton);

    await waitFor(() => {
      expect(llmApi.execute).toHaveBeenCalledWith(
        "Write a story about cats",
        "openai",
        {},
      );
    });
  });

  it("should display loading state during testing", async () => {
    (llmApi.execute as jest.Mock).mockImplementation(
      () => new Promise(() => {}),
    );

    renderPromptBuilder();

    const contentTextarea = screen.getByPlaceholderText(
      "Write your prompt here...",
    );
    fireEvent.change(contentTextarea, { target: { value: "Test prompt" } });

    const testButton = screen.getByText("Test Prompt");
    fireEvent.click(testButton);

    expect(screen.getByText("Testing...")).toBeInTheDocument();
  });

  it("should display LLM responses", async () => {
    renderPromptBuilder();

    const contentTextarea = screen.getByPlaceholderText(
      "Write your prompt here...",
    );
    fireEvent.change(contentTextarea, { target: { value: "Test prompt" } });

    const testButton = screen.getByText("Test Prompt");
    fireEvent.click(testButton);

    // Wait for the loading state first
    await waitFor(
      () => {
        expect(screen.getByText("Generating response...")).toBeInTheDocument();
      },
      { timeout: 1000 },
    );

    // Then wait for the response
    await waitFor(
      () => {
        expect(screen.getByText("Test response")).toBeInTheDocument();
      },
      { timeout: 3000 },
    );
  });

  it("should handle test errors", async () => {
    (llmApi.execute as jest.Mock).mockRejectedValue(new Error("Test error"));

    renderPromptBuilder();

    const contentTextarea = screen.getByPlaceholderText(
      "Write your prompt here...",
    );
    fireEvent.change(contentTextarea, { target: { value: "Test prompt" } });

    const testButton = screen.getByText("Test Prompt");
    fireEvent.click(testButton);

    // The component should handle errors gracefully
    await waitFor(() => {
      expect(llmApi.execute).toHaveBeenCalled();
    });
  });

  it("should save prompt", async () => {
    renderPromptBuilder();

    // Fill in form
    const titleInput = screen.getByLabelText(/title/i);
    fireEvent.change(titleInput, { target: { value: "Test Prompt" } });

    const contentTextarea = screen.getByPlaceholderText(
      "Write your prompt here...",
    );
    fireEvent.change(contentTextarea, { target: { value: "Test content" } });

    // Save prompt
    const saveButton = screen.getByText("Save Prompt");
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(collectionsApi.create).toHaveBeenCalledWith({
        name: "Test Prompt",
        description: "\n\nPrompt Content:\nTest content",
        type: "private",
        owner_id: "test-user",
        tags: ["prompt"],
      });
    });
  });

  it("should display prompt coach", () => {
    renderPromptBuilder();

    expect(screen.getByTestId("prompt-coach")).toBeInTheDocument();
  });

  it("should handle variables in prompt", () => {
    renderPromptBuilder();

    const contentTextarea = screen.getByPlaceholderText(
      "Write your prompt here...",
    );
    fireEvent.change(contentTextarea, {
      target: { value: "Write about {topic} in {style}" },
    });

    // Variables should be detected and inputs should appear
    expect(contentTextarea).toHaveValue("Write about {topic} in {style}");
  });

  it("should disable test button when content is empty", () => {
    renderPromptBuilder();

    const testButton = screen.getByText("Test Prompt");
    expect(testButton).toBeDisabled();
  });

  it("should enable test button when content is provided", () => {
    renderPromptBuilder();

    const contentTextarea = screen.getByPlaceholderText(
      "Write your prompt here...",
    );
    fireEvent.change(contentTextarea, { target: { value: "Test content" } });

    const testButton = screen.getByText("Test Prompt");
    expect(testButton).not.toBeDisabled();
  });
});
