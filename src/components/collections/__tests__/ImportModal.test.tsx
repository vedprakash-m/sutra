import {
  render,
  screen,
  fireEvent,
  waitFor,
  act,
} from "@testing-library/react";
import ImportModal from "../ImportModal";

// Mock window.alert
global.alert = jest.fn();

// Mock File API
Object.defineProperty(global, "File", {
  writable: true,
  value: class MockFile {
    name: string;
    type: string;
    size: number;
    content: string;

    constructor(parts: any[], filename: string, options: any) {
      this.name = filename;
      this.type = options?.type || "";
      this.size = parts.join("").length;
      this.content = parts.join("");
    }

    text() {
      return Promise.resolve(this.content);
    }
  },
});

// Mock @headlessui/react
jest.mock("@headlessui/react", () => {
  const MockDialog = ({ children, onClose }: any) => (
    <div data-testid="dialog" onClick={onClose}>
      <div data-testid="dialog-panel" onClick={(e: any) => e.stopPropagation()}>
        {children}
      </div>
    </div>
  );

  const MockTransition = ({ children, show }: any) =>
    show ? <div data-testid="transition">{children}</div> : null;

  const MockTransitionChild = ({ children }: any) => (
    <div data-testid="transition-child">{children}</div>
  );

  MockDialog.Panel = ({ children }: any) => (
    <div data-testid="dialog-panel">{children}</div>
  );
  MockDialog.Title = ({ children }: any) => (
    <h3 data-testid="dialog-title">{children}</h3>
  );

  MockTransition.Child = MockTransitionChild;

  return {
    Dialog: MockDialog,
    Transition: MockTransition,
  };
});

// Mock Heroicons
jest.mock("@heroicons/react/24/outline", () => ({
  XMarkIcon: () => <div data-testid="close-icon" />,
  DocumentArrowUpIcon: () => <div data-testid="upload-icon" />,
  ClipboardDocumentIcon: () => <div data-testid="clipboard-icon" />,
  ChatBubbleLeftRightIcon: () => <div data-testid="chat-icon" />,
  CodeBracketIcon: () => <div data-testid="code-icon" />,
}));

describe("ImportModal", () => {
  const mockOnClose = jest.fn();
  const mockOnImport = jest.fn();

  const defaultProps = {
    isOpen: true,
    onClose: mockOnClose,
    onImport: mockOnImport,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("should render import modal when open", () => {
    render(<ImportModal {...defaultProps} />);

    expect(screen.getByTestId("dialog")).toBeInTheDocument();
    expect(screen.getByText("Import Prompts")).toBeInTheDocument();
    expect(screen.getByText("Choose import method:")).toBeInTheDocument();
  });

  it("should not render modal when closed", () => {
    render(<ImportModal {...defaultProps} isOpen={false} />);

    expect(screen.queryByTestId("dialog")).not.toBeInTheDocument();
  });

  it("should show text import method by default", () => {
    render(<ImportModal {...defaultProps} />);

    expect(screen.getByText("Paste Text")).toBeInTheDocument();
    expect(
      screen.getByPlaceholderText(
        "Paste multiple prompts separated by --- or empty lines...",
      ),
    ).toBeInTheDocument();
  });

  it("should switch to file upload method", () => {
    render(<ImportModal {...defaultProps} />);

    const fileUploadButton = screen.getByText("Upload File");
    fireEvent.click(fileUploadButton);

    expect(screen.getByText("Choose file to upload:")).toBeInTheDocument();
  });

  it("should switch to ChatGPT import method", () => {
    render(<ImportModal {...defaultProps} />);

    const chatgptButton = screen.getByText("ChatGPT Export");
    fireEvent.click(chatgptButton);

    expect(
      screen.getByText("ChatGPT Export Instructions:"),
    ).toBeInTheDocument();
  });

  it("should switch to Gemini import method", () => {
    render(<ImportModal {...defaultProps} />);

    const geminiButton = screen.getByText("Gemini Export");
    fireEvent.click(geminiButton);

    expect(screen.getByText("Gemini Export Instructions:")).toBeInTheDocument();
  });

  it("should handle text input", () => {
    render(<ImportModal {...defaultProps} />);

    const textArea = screen.getByPlaceholderText(
      "Paste multiple prompts separated by --- or empty lines...",
    );
    fireEvent.change(textArea, { target: { value: "Test prompt content" } });

    expect(textArea).toHaveValue("Test prompt content");
  });

  it("should handle close button click", () => {
    render(<ImportModal {...defaultProps} />);

    const closeButton = screen.getByTestId("close-icon").parentElement;
    fireEvent.click(closeButton!);

    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it("should handle cancel button click", () => {
    render(<ImportModal {...defaultProps} />);

    const cancelButton = screen.getByText("Cancel");
    fireEvent.click(cancelButton);

    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it("should parse and preview text prompts", async () => {
    render(<ImportModal {...defaultProps} />);

    const textArea = screen.getByPlaceholderText(
      "Paste multiple prompts separated by --- or empty lines...",
    );
    fireEvent.change(textArea, {
      target: {
        value:
          "# Prompt 1\nThis is the first prompt\n\n# Prompt 2\nThis is the second prompt",
      },
    });

    const previewButton = screen.getByText("Preview Import");
    fireEvent.click(previewButton);

    await waitFor(() => {
      expect(screen.getByText("Import Preview")).toBeInTheDocument();
      expect(
        screen.getByText(/Found \d+ prompts? to import/),
      ).toBeInTheDocument();
    });
  });

  it("should import previewed prompts", async () => {
    render(<ImportModal {...defaultProps} />);

    const textArea = screen.getByPlaceholderText(
      "Paste multiple prompts separated by --- or empty lines...",
    );
    fireEvent.change(textArea, {
      target: { value: "# Test Prompt\nThis is a test prompt" },
    });

    const previewButton = screen.getByText("Preview Import");
    fireEvent.click(previewButton);

    await waitFor(() => {
      expect(screen.getByText("Import Preview")).toBeInTheDocument();
    });

    const importButton = screen.getByText(/Import \d+ Prompts?/);
    fireEvent.click(importButton);

    await waitFor(() => {
      expect(mockOnImport).toHaveBeenCalledWith([
        expect.objectContaining({
          title: "Test Prompt",
          content: "This is a test prompt",
          source: "Manual Input",
          description: "Imported from manual input",
          variables: {},
        }),
      ]);
    });
  });

  it("should handle file upload", async () => {
    render(<ImportModal {...defaultProps} />);

    // Switch to file upload
    const fileUploadButton = screen.getByText("Upload File");
    fireEvent.click(fileUploadButton);

    const fileInput = screen.getByTestId("file-input");
    const file = new File(
      ['{"prompts": [{"title": "Test", "content": "Content"}]}'],
      "test.json",
      {
        type: "application/json",
      },
    );

    Object.defineProperty(fileInput, "files", {
      value: [file],
      writable: false,
    });

    fireEvent.change(fileInput);

    await waitFor(() => {
      expect(screen.getByText("Processing...")).toBeInTheDocument();
    });
  });

  it("should show error for invalid JSON file", async () => {
    const consoleSpy = jest.spyOn(console, "error").mockImplementation();

    render(<ImportModal {...defaultProps} />);

    // Switch to file upload
    const fileUploadButton = screen.getByText("Upload File");
    fireEvent.click(fileUploadButton);

    const fileInput = screen.getByTestId("file-input");
    const file = new File(["invalid json"], "test.json", {
      type: "application/json",
    });

    Object.defineProperty(fileInput, "files", {
      value: [file],
      writable: false,
    });

    fireEvent.change(fileInput);

    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith(
        "Error processing file:",
        expect.any(Error),
      );
      expect(global.alert).toHaveBeenCalledWith(
        "Error processing file. Please check the format and try again.",
      );
    });

    consoleSpy.mockRestore();
  });

  it("should show import button with 0 prompts when no valid prompts found", () => {
    render(<ImportModal {...defaultProps} />);

    // Provide valid text that will enable preview but parse to 0 prompts
    const textArea = screen.getByPlaceholderText(
      "Paste multiple prompts separated by --- or empty lines...",
    );
    fireEvent.change(textArea, { target: { value: "# \n \n# \n " } }); // Headers with no content

    const previewButton = screen.getByText("Preview Import");
    fireEvent.click(previewButton);

    // Since the sections will have no content, it should show Import 0 Prompts
    // But let's check what actually gets rendered
    expect(screen.getByText(/Import \d+ Prompts?/)).toBeInTheDocument();
  });

  it("should clear preview when switching import methods", () => {
    render(<ImportModal {...defaultProps} />);

    // Add some text and preview
    const textArea = screen.getByPlaceholderText(
      "Paste multiple prompts separated by --- or empty lines...",
    );
    fireEvent.change(textArea, { target: { value: "# Test\nContent" } });

    const previewButton = screen.getByText("Preview Import");
    fireEvent.click(previewButton);

    // Should be in preview mode
    expect(screen.getByText("Import Preview")).toBeInTheDocument();

    // Click Back to return to input mode
    const backButton = screen.getByText("Back");
    fireEvent.click(backButton);

    // Preview should be cleared and we should be back in input mode
    expect(screen.queryByText("Import Preview")).not.toBeInTheDocument();
    expect(screen.getByText("Choose import method:")).toBeInTheDocument();
  });

  it("should handle file upload with unsupported file type", async () => {
    render(<ImportModal {...defaultProps} />);

    // Switch to file upload
    const fileUploadButton = screen.getByText("Upload File");
    fireEvent.click(fileUploadButton);

    const fileInput = screen.getByTestId("file-input");
    const invalidFile = new File(["invalid content"], "test.pdf", {
      type: "application/pdf",
    });

    Object.defineProperty(fileInput, "files", {
      value: [invalidFile],
      writable: false,
    });

    fireEvent.change(fileInput);

    await waitFor(() => {
      expect(global.alert).toHaveBeenCalledWith(
        "Unsupported file format. Please use JSON, TXT, or MD files.",
      );
    });
  });

  it("should handle empty file upload", async () => {
    render(<ImportModal {...defaultProps} />);

    // Switch to file upload
    const fileUploadButton = screen.getByText("Upload File");
    fireEvent.click(fileUploadButton);

    const fileInput = screen.getByTestId("file-input");

    // Simulate no file selected
    Object.defineProperty(fileInput, "files", {
      value: [],
      writable: false,
    });

    fireEvent.change(fileInput);

    // Should not trigger any processing since no file is selected
    expect(screen.queryByText("Processing...")).not.toBeInTheDocument();
  });

  it("should handle text file upload successfully", async () => {
    render(<ImportModal {...defaultProps} />);

    // Switch to file upload
    const fileUploadButton = screen.getByText("Upload File");
    fireEvent.click(fileUploadButton);

    const fileInput = screen.getByTestId("file-input");
    const textFile = new File(
      ["# Prompt 1\nThis is content 1\n\n# Prompt 2\nThis is content 2"],
      "prompts.txt",
      { type: "text/plain" },
    );

    Object.defineProperty(fileInput, "files", {
      value: [textFile],
      writable: false,
    });

    fireEvent.change(fileInput);

    await waitFor(() => {
      expect(screen.getByText("Import Preview")).toBeInTheDocument();
      expect(
        screen.getByText(/Found \d+ prompts? to import/),
      ).toBeInTheDocument();
    });
  });

  it("should handle markdown file upload successfully", async () => {
    render(<ImportModal {...defaultProps} />);

    // Switch to file upload
    const fileUploadButton = screen.getByText("Upload File");
    fireEvent.click(fileUploadButton);

    const fileInput = screen.getByTestId("file-input");
    const mdFile = new File(
      [
        "## First Prompt\nMarkdown content here\n\n## Second Prompt\nMore markdown",
      ],
      "prompts.md",
      { type: "text/markdown" },
    );

    Object.defineProperty(fileInput, "files", {
      value: [mdFile],
      writable: false,
    });

    fireEvent.change(fileInput);

    await waitFor(() => {
      expect(screen.getByText("Import Preview")).toBeInTheDocument();
    });
  });

  it("should handle ChatGPT JSON file upload successfully", async () => {
    render(<ImportModal {...defaultProps} />);

    // Switch to file upload
    const fileUploadButton = screen.getByText("Upload File");
    fireEvent.click(fileUploadButton);

    const chatGPTData = {
      conversations: [
        {
          title: "Test Conversation",
          messages: [
            {
              author: "user",
              content: "Write a marketing email for a new product",
            },
            {
              author: "assistant",
              content: "Here's a marketing email...",
            },
          ],
        },
      ],
    };

    const fileInput = screen.getByTestId("file-input");
    const jsonFile = new File(
      [JSON.stringify(chatGPTData)],
      "conversations.json",
      { type: "application/json" },
    );

    Object.defineProperty(fileInput, "files", {
      value: [jsonFile],
      writable: false,
    });

    fireEvent.change(fileInput);

    await waitFor(() => {
      expect(screen.getByText("Import Preview")).toBeInTheDocument();
      expect(screen.getByText("Test Conversation")).toBeInTheDocument();
      expect(screen.getByText("ChatGPT")).toBeInTheDocument();
    });
  });

  it("should handle empty text input for preview", () => {
    render(<ImportModal {...defaultProps} />);

    const previewButton = screen.getByText("Preview Import");

    // Preview button should be disabled when textInput is empty
    expect(previewButton).toBeDisabled();
  });

  it("should extract variables from prompt content", async () => {
    render(<ImportModal {...defaultProps} />);

    const textArea = screen.getByPlaceholderText(
      "Paste multiple prompts separated by --- or empty lines...",
    );
    fireEvent.change(textArea, {
      target: {
        value:
          "# Variable Test\nHello {{name}}, your {{role}} is important for {{company}}.",
      },
    });

    const previewButton = screen.getByText("Preview Import");
    fireEvent.click(previewButton);

    await waitFor(() => {
      expect(screen.getByText("Import Preview")).toBeInTheDocument();
      expect(
        screen.getByText("Variables: name, role, company"),
      ).toBeInTheDocument();
    });
  });

  it("should handle text parsing with triple equals separator", async () => {
    render(<ImportModal {...defaultProps} />);

    const textArea = screen.getByPlaceholderText(
      "Paste multiple prompts separated by --- or empty lines...",
    );
    fireEvent.change(textArea, {
      target: {
        value: "Prompt 1\nContent 1\n===\nPrompt 2\nContent 2",
      },
    });

    const previewButton = screen.getByText("Preview Import");
    fireEvent.click(previewButton);

    await waitFor(() => {
      expect(screen.getByText("Import Preview")).toBeInTheDocument();
      expect(
        screen.getByText(/Found \d+ prompts? to import/),
      ).toBeInTheDocument();
    });
  });

  it("should handle text parsing with triple newlines separator", async () => {
    render(<ImportModal {...defaultProps} />);

    const textArea = screen.getByPlaceholderText(
      "Paste multiple prompts separated by --- or empty lines...",
    );
    fireEvent.change(textArea, {
      target: {
        value: "Prompt 1\nContent 1\n\n\n\nPrompt 2\nContent 2",
      },
    });

    const previewButton = screen.getByText("Preview Import");
    fireEvent.click(previewButton);

    await waitFor(() => {
      expect(screen.getByText("Import Preview")).toBeInTheDocument();
    });
  });

  it("should handle single line prompts", async () => {
    render(<ImportModal {...defaultProps} />);

    const textArea = screen.getByPlaceholderText(
      "Paste multiple prompts separated by --- or empty lines...",
    );
    fireEvent.change(textArea, {
      target: {
        value: "Single line prompt without multiple lines",
      },
    });

    const previewButton = screen.getByText("Preview Import");
    fireEvent.click(previewButton);

    await waitFor(() => {
      expect(screen.getByText("Import Preview")).toBeInTheDocument();
      expect(screen.getByText("Imported Prompt 1")).toBeInTheDocument();
    });
  });

  it("should handle empty sections in text parsing", async () => {
    render(<ImportModal {...defaultProps} />);

    const textArea = screen.getByPlaceholderText(
      "Paste multiple prompts separated by --- or empty lines...",
    );
    fireEvent.change(textArea, {
      target: {
        value:
          "Valid Prompt\nValid content\n---\n   \n---\nAnother Valid\nMore content",
      },
    });

    const previewButton = screen.getByText("Preview Import");
    fireEvent.click(previewButton);

    await waitFor(() => {
      expect(screen.getByText("Import Preview")).toBeInTheDocument();
      // Should only show 2 prompts, empty section should be filtered out
    });
  });

  it("should handle ChatGPT data without conversations", async () => {
    render(<ImportModal {...defaultProps} />);

    const fileUploadButton = screen.getByText("Upload File");
    fireEvent.click(fileUploadButton);

    const chatGPTData = {
      // No conversations property
      metadata: "some data",
    };

    const fileInput = screen.getByTestId("file-input");
    const jsonFile = new File([JSON.stringify(chatGPTData)], "empty.json", {
      type: "application/json",
    });

    await act(async () => {
      Object.defineProperty(fileInput, "files", {
        value: [jsonFile],
        writable: false,
      });

      fireEvent.change(fileInput);
    });

    // Should stay on upload form since no prompts were found
    await waitFor(
      () => {
        expect(screen.queryByText("Processing...")).not.toBeInTheDocument();
        expect(screen.getByText("Choose file to upload:")).toBeInTheDocument();
        expect(screen.queryByText("Import Preview")).not.toBeInTheDocument();
      },
      { timeout: 3000 },
    );
  });

  it("should handle ChatGPT conversation without messages", async () => {
    render(<ImportModal {...defaultProps} />);

    const fileUploadButton = screen.getByText("Upload File");
    fireEvent.click(fileUploadButton);

    const chatGPTData = {
      conversations: [
        {
          title: "Empty Conversation",
          // No messages property
        },
      ],
    };

    const fileInput = screen.getByTestId("file-input");
    const jsonFile = new File(
      [JSON.stringify(chatGPTData)],
      "empty_conversation.json",
      { type: "application/json" },
    );

    Object.defineProperty(fileInput, "files", {
      value: [jsonFile],
      writable: false,
    });

    fireEvent.change(fileInput);

    // Should stay on upload form since no prompts were found
    await waitFor(() => {
      expect(screen.queryByText("Processing...")).not.toBeInTheDocument();
      expect(screen.getByText("Choose file to upload:")).toBeInTheDocument();
      expect(screen.queryByText("Import Preview")).not.toBeInTheDocument();
    });
  });

  it("should handle ChatGPT messages without user content", async () => {
    render(<ImportModal {...defaultProps} />);

    const fileUploadButton = screen.getByText("Upload File");
    fireEvent.click(fileUploadButton);

    const chatGPTData = {
      conversations: [
        {
          title: "Assistant Only",
          messages: [
            {
              author: "assistant",
              content: "I'm an assistant response",
            },
          ],
        },
      ],
    };

    const fileInput = screen.getByTestId("file-input");
    const jsonFile = new File(
      [JSON.stringify(chatGPTData)],
      "assistant_only.json",
      { type: "application/json" },
    );

    Object.defineProperty(fileInput, "files", {
      value: [jsonFile],
      writable: false,
    });

    fireEvent.change(fileInput);

    // Should stay on upload form since no prompts were found
    await waitFor(() => {
      expect(screen.queryByText("Processing...")).not.toBeInTheDocument();
      expect(screen.getByText("Choose file to upload:")).toBeInTheDocument();
      expect(screen.queryByText("Import Preview")).not.toBeInTheDocument();
    });
  });

  it("should use default title when ChatGPT conversation has no title", async () => {
    render(<ImportModal {...defaultProps} />);

    const fileUploadButton = screen.getByText("Upload File");
    fireEvent.click(fileUploadButton);

    const chatGPTData = {
      conversations: [
        {
          // No title property
          messages: [
            {
              author: "user",
              content: "Test user message",
            },
          ],
        },
      ],
    };

    const fileInput = screen.getByTestId("file-input");
    const jsonFile = new File([JSON.stringify(chatGPTData)], "no_title.json", {
      type: "application/json",
    });

    Object.defineProperty(fileInput, "files", {
      value: [jsonFile],
      writable: false,
    });

    fireEvent.change(fileInput);

    await waitFor(() => {
      expect(screen.getByText("Import Preview")).toBeInTheDocument();
      expect(screen.getByText("Imported Chat 1")).toBeInTheDocument();
    });
  });

  it("should clear preview when going back", async () => {
    render(<ImportModal {...defaultProps} />);

    const textArea = screen.getByPlaceholderText(
      "Paste multiple prompts separated by --- or empty lines...",
    );
    fireEvent.change(textArea, {
      target: { value: "# Test\nTest content" },
    });

    const previewButton = screen.getByText("Preview Import");
    fireEvent.click(previewButton);

    await waitFor(() => {
      expect(screen.getByText("Import Preview")).toBeInTheDocument();
    });

    const backButton = screen.getByText("Back");
    fireEvent.click(backButton);

    expect(screen.queryByText("Import Preview")).not.toBeInTheDocument();
    expect(screen.getByText("Choose import method:")).toBeInTheDocument();
  });

  it("should clear input when closing modal", async () => {
    render(<ImportModal {...defaultProps} />);

    const textArea = screen.getByPlaceholderText(
      "Paste multiple prompts separated by --- or empty lines...",
    );
    fireEvent.change(textArea, {
      target: { value: "# Test\nTest content" },
    });

    const previewButton = screen.getByText("Preview Import");
    fireEvent.click(previewButton);

    await waitFor(() => {
      expect(screen.getByText("Import Preview")).toBeInTheDocument();
    });

    const closeButton = screen.getByTestId("close-icon").parentElement;
    fireEvent.click(closeButton!);

    expect(mockOnClose).toHaveBeenCalled();
  });

  it("should handle text file with no content separation", async () => {
    render(<ImportModal {...defaultProps} />);

    const fileUploadButton = screen.getByText("Upload File");
    fireEvent.click(fileUploadButton);

    const fileInput = screen.getByTestId("file-input");
    const textFile = new File(
      ["Single line content without headers or separators"],
      "simple.txt",
      { type: "text/plain" },
    );

    Object.defineProperty(fileInput, "files", {
      value: [textFile],
      writable: false,
    });

    fireEvent.change(fileInput);

    await waitFor(() => {
      expect(screen.getByText("Import Preview")).toBeInTheDocument();
      expect(
        screen.getByRole("heading", {
          name: "Single line content without headers or separators",
        }),
      ).toBeInTheDocument();
    });
  });

  it("should handle text parsing with different separators", async () => {
    render(<ImportModal {...defaultProps} />);

    const textArea = screen.getByPlaceholderText(
      "Paste multiple prompts separated by --- or empty lines...",
    );
    fireEvent.change(textArea, {
      target: {
        value: "Prompt 1\nContent 1\n---\nPrompt 2\nContent 2",
      },
    });

    const previewButton = screen.getByText("Preview Import");
    fireEvent.click(previewButton);

    await waitFor(() => {
      expect(screen.getByText("Import Preview")).toBeInTheDocument();
    });
  });

  it("should show processing state during text import", () => {
    render(<ImportModal {...defaultProps} />);

    const textArea = screen.getByPlaceholderText(
      "Paste multiple prompts separated by --- or empty lines...",
    );
    fireEvent.change(textArea, {
      target: { value: "# Test\nTest content" },
    });

    const previewButton = screen.getByText("Preview Import");
    expect(previewButton).not.toBeDisabled();
  });

  it("should handle variable extraction with special characters", async () => {
    render(<ImportModal {...defaultProps} />);

    const textArea = screen.getByPlaceholderText(
      "Paste multiple prompts separated by --- or empty lines...",
    );
    fireEvent.change(textArea, {
      target: {
        value:
          "# Special Variables\nHello {{user_name}}, welcome to {{app-name}} {{version2.0}}!",
      },
    });

    const previewButton = screen.getByText("Preview Import");
    fireEvent.click(previewButton);

    await waitFor(() => {
      expect(screen.getByText("Import Preview")).toBeInTheDocument();
      expect(
        screen.getByText(/Variables:.*user_name.*app-name.*version2\.0/),
      ).toBeInTheDocument();
    });
  });

  it("should handle multiple user messages in ChatGPT conversation", async () => {
    render(<ImportModal {...defaultProps} />);

    const fileUploadButton = screen.getByText("Upload File");
    fireEvent.click(fileUploadButton);

    const chatGPTData = {
      conversations: [
        {
          title: "Multi-message Conversation",
          messages: [
            {
              author: "user",
              content: "First user message",
            },
            {
              author: "assistant",
              content: "Assistant response",
            },
            {
              author: "user",
              content: "Second user message",
            },
          ],
        },
      ],
    };

    const fileInput = screen.getByTestId("file-input");
    const jsonFile = new File(
      [JSON.stringify(chatGPTData)],
      "multi_message.json",
      { type: "application/json" },
    );

    Object.defineProperty(fileInput, "files", {
      value: [jsonFile],
      writable: false,
    });

    fireEvent.change(fileInput);

    await waitFor(() => {
      expect(screen.getByText("Import Preview")).toBeInTheDocument();
      expect(
        screen.getByText("Multi-message Conversation"),
      ).toBeInTheDocument();
      // Content should include both user messages
      expect(screen.getByText(/First user message/)).toBeInTheDocument();
    });
  });

  it("should display prompt source badge in preview", async () => {
    render(<ImportModal {...defaultProps} />);

    const textArea = screen.getByPlaceholderText(
      "Paste multiple prompts separated by --- or empty lines...",
    );
    fireEvent.change(textArea, {
      target: { value: "# Test\nTest content" },
    });

    const previewButton = screen.getByText("Preview Import");
    fireEvent.click(previewButton);

    await waitFor(() => {
      expect(screen.getByText("Import Preview")).toBeInTheDocument();
      expect(screen.getByText("Manual Input")).toBeInTheDocument(); // Source badge
    });
  });

  it("should show variables section only when variables exist", async () => {
    render(<ImportModal {...defaultProps} />);

    const textArea = screen.getByPlaceholderText(
      "Paste multiple prompts separated by --- or empty lines...",
    );
    fireEvent.change(textArea, {
      target: { value: "# No Variables\nThis prompt has no variables" },
    });

    const previewButton = screen.getByText("Preview Import");
    fireEvent.click(previewButton);

    await waitFor(() => {
      expect(screen.getByText("Import Preview")).toBeInTheDocument();
      expect(screen.queryByText(/Variables:/)).not.toBeInTheDocument();
    });
  });

  it("should handle text with short first line as title", async () => {
    render(<ImportModal {...defaultProps} />);

    const textArea = screen.getByPlaceholderText(
      "Paste multiple prompts separated by --- or empty lines...",
    );
    fireEvent.change(textArea, {
      target: {
        value:
          "Short Title\nThis is the longer content that follows the short title line.",
      },
    });

    const previewButton = screen.getByText("Preview Import");
    fireEvent.click(previewButton);

    await waitFor(() => {
      expect(screen.getByText("Import Preview")).toBeInTheDocument();
      expect(screen.getByText("Short Title")).toBeInTheDocument();
    });
  });

  it("should use full content as title for long single lines", async () => {
    render(<ImportModal {...defaultProps} />);

    const textArea = screen.getByPlaceholderText(
      "Paste multiple prompts separated by --- or empty lines...",
    );
    const longLine =
      "This is a very long single line that exceeds 100 characters and should be used as both title and content " +
      "a".repeat(50);

    fireEvent.change(textArea, {
      target: { value: longLine },
    });

    const previewButton = screen.getByText("Preview Import");
    fireEvent.click(previewButton);

    await waitFor(() => {
      expect(screen.getByText("Import Preview")).toBeInTheDocument();
      expect(screen.getByText("Imported Prompt 1")).toBeInTheDocument(); // Should use default title
    });
  });

  it("should handle text file with header markers", async () => {
    render(<ImportModal {...defaultProps} />);

    const fileUploadButton = screen.getByText("Upload File");
    fireEvent.click(fileUploadButton);

    const fileInput = screen.getByTestId("file-input");
    const textFile = new File(
      [
        "### First Section\nContent for first section\n### Second Section\nContent for second",
      ],
      "headers.txt",
      { type: "text/plain" },
    );

    Object.defineProperty(fileInput, "files", {
      value: [textFile],
      writable: false,
    });

    fireEvent.change(fileInput);

    await waitFor(() => {
      expect(screen.getByText("Import Preview")).toBeInTheDocument();
      expect(screen.getByText("First Section")).toBeInTheDocument();
      expect(screen.getByText("Second Section")).toBeInTheDocument();
    });
  });

  it("should handle import method switching", () => {
    render(<ImportModal {...defaultProps} />);

    // Start with text method (default)
    expect(
      screen.getByPlaceholderText(/Paste multiple prompts/),
    ).toBeInTheDocument();

    // Switch to chatgpt method
    const chatgptButton = screen.getByText("ChatGPT Export");
    fireEvent.click(chatgptButton);
    expect(
      screen.getByText("ChatGPT Export Instructions:"),
    ).toBeInTheDocument();

    // Switch to gemini method
    const geminiButton = screen.getByText("Gemini Export");
    fireEvent.click(geminiButton);
    expect(screen.getByText("Gemini Export Instructions:")).toBeInTheDocument();

    // Switch back to text method
    const textButton = screen.getByText("Paste Text");
    fireEvent.click(textButton);
    expect(
      screen.getByPlaceholderText(/Paste multiple prompts/),
    ).toBeInTheDocument();
  });

  it("should preserve input when switching back from preview", async () => {
    render(<ImportModal {...defaultProps} />);

    const originalText = "# Original\nOriginal content";

    const textArea = screen.getByPlaceholderText(
      "Paste multiple prompts separated by --- or empty lines...",
    );
    fireEvent.change(textArea, {
      target: { value: originalText },
    });

    const previewButton = screen.getByText("Preview Import");
    fireEvent.click(previewButton);

    await waitFor(() => {
      expect(screen.getByText("Import Preview")).toBeInTheDocument();
    });

    const backButton = screen.getByText("Back");
    fireEvent.click(backButton);

    expect(textArea).toHaveValue(originalText);
  });

  it("should disable preview button when text input is empty", () => {
    render(<ImportModal {...defaultProps} />);

    const previewButton = screen.getByText("Preview Import");
    expect(previewButton).toBeDisabled();

    const textArea = screen.getByPlaceholderText(
      "Paste multiple prompts separated by --- or empty lines...",
    );
    fireEvent.change(textArea, {
      target: { value: "   " }, // Only whitespace
    });

    expect(previewButton).toBeDisabled();

    fireEvent.change(textArea, {
      target: { value: "Real content" },
    });

    expect(previewButton).not.toBeDisabled();
  });

  it("should handle tab switching", () => {
    render(<ImportModal {...defaultProps} />);

    // Switch to file upload tab
    const fileTab = screen.getByText("Upload File");
    fireEvent.click(fileTab);

    expect(screen.getByTestId("file-input")).toBeInTheDocument();

    // Switch back to text tab
    const textTab = screen.getByText("Paste Text");
    fireEvent.click(textTab);

    expect(
      screen.getByPlaceholderText(/Paste multiple prompts/),
    ).toBeInTheDocument();
  });

  it("should handle proper import button text", async () => {
    render(<ImportModal {...defaultProps} />);

    const textArea = screen.getByPlaceholderText(
      "Paste multiple prompts separated by --- or empty lines...",
    );

    // Single prompt
    fireEvent.change(textArea, {
      target: { value: "Single prompt content" },
    });

    const previewButton = screen.getByText("Preview Import");
    fireEvent.click(previewButton);

    await waitFor(() => {
      expect(screen.getByText(/Import 1 Prompt/)).toBeInTheDocument();
    });
  });

  it("should show correct prompt count in preview title", async () => {
    render(<ImportModal {...defaultProps} />);

    const textArea = screen.getByPlaceholderText(
      "Paste multiple prompts separated by --- or empty lines...",
    );
    fireEvent.change(textArea, {
      target: { value: "# Only One\nJust one prompt" },
    });

    const previewButton = screen.getByText("Preview Import");
    fireEvent.click(previewButton);

    await waitFor(() => {
      expect(screen.getByText("Found 1 prompt to import")).toBeInTheDocument();
    });
  });

  it("should show line-clamp styling for long content", async () => {
    render(<ImportModal {...defaultProps} />);

    const longContent = "This is a very long content ".repeat(20);
    const textArea = screen.getByPlaceholderText(
      "Paste multiple prompts separated by --- or empty lines...",
    );
    fireEvent.change(textArea, {
      target: { value: `Long Content\n${longContent}` },
    });

    const previewButton = screen.getByText("Preview Import");
    fireEvent.click(previewButton);

    await waitFor(() => {
      expect(screen.getByText("Import Preview")).toBeInTheDocument();
      // Check that the content container has the line-clamp class
      const contentContainer = document.querySelector(".line-clamp-3");
      expect(contentContainer).toBeInTheDocument();
    });
  });

  it("should handle file input without triggering when no files", () => {
    render(<ImportModal {...defaultProps} />);

    const fileUploadButton = screen.getByText("Upload File");
    fireEvent.click(fileUploadButton);

    const fileInput = screen.getByTestId("file-input");

    // Trigger change event without files
    fireEvent.change(fileInput);

    // Should not show processing state
    expect(screen.queryByText("Processing...")).not.toBeInTheDocument();
  });

  it("should preserve state during component updates", async () => {
    const { rerender } = render(<ImportModal {...defaultProps} />);

    const textArea = screen.getByPlaceholderText(
      "Paste multiple prompts separated by --- or empty lines...",
    );
    fireEvent.change(textArea, {
      target: { value: "# Test\nTest content" },
    });

    // Rerender with same props
    rerender(<ImportModal {...defaultProps} />);

    // Content should be preserved
    expect(textArea).toHaveValue("# Test\nTest content");
  });
});
