import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { AnonymousLLMTest } from "../AnonymousLLMTest";

// Mock fetch globally
const mockFetch = jest.fn();
global.fetch = mockFetch;

describe("AnonymousLLMTest", () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  it("renders the component with all elements", () => {
    render(<AnonymousLLMTest />);

    expect(
      screen.getByText("🚀 Try Sutra AI - No Login Required!"),
    ).toBeTruthy();
    expect(
      screen.getByText("Test our AI capabilities with a free anonymous trial"),
    ).toBeTruthy();
    expect(
      screen.getByPlaceholderText(
        /e.g., Write a short poem about technology.../,
      ),
    ).toBeTruthy();
    expect(screen.getByText("Test AI Response")).toBeTruthy();
    expect(screen.getByText("0/500")).toBeTruthy();
  });

  it("updates character count as user types", () => {
    render(<AnonymousLLMTest />);

    const textarea = screen.getByPlaceholderText(
      /e.g., Write a short poem about technology.../,
    );
    fireEvent.change(textarea, { target: { value: "Hello AI" } });

    expect(screen.getByText("8/500")).toBeTruthy();
  });

  it("makes API call and displays successful response", async () => {
    const mockResponse = {
      choices: [{ text: "This is a test AI response from Sutra!" }],
      anonymous_info: {
        remaining_calls: 4,
        daily_limit: 5,
        signup_message:
          "You have 4 free calls remaining today. Sign up for unlimited access!",
      },
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
      headers: {
        get: () => null,
      },
    });

    render(<AnonymousLLMTest />);

    const textarea = screen.getByPlaceholderText(
      /e.g., Write a short poem about technology.../,
    );
    const submitButton = screen.getByText("Test AI Response");

    fireEvent.change(textarea, { target: { value: "What is AI?" } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText("AI Response:")).toBeTruthy();
      expect(
        screen.getByText("This is a test AI response from Sutra!"),
      ).toBeTruthy();
      // Check for the usage counter by looking for the specific container
      const usageContainer = screen.getByText("4", {
        selector: ".text-blue-800 .font-semibold",
      });
      expect(usageContainer).toBeTruthy();
    });

    expect(mockFetch).toHaveBeenCalledWith(
      "http://localhost:7071/api/anonymous/llm/execute",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ prompt: "What is AI?" }),
      },
    );
  });

  it("handles rate limit exceeded error", async () => {
    const mockErrorResponse = {
      error: "daily_limit_exceeded",
      message: "Daily limit exceeded. Please sign up for unlimited access.",
    };

    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 429,
      json: async () => mockErrorResponse,
    });

    render(<AnonymousLLMTest />);

    const textarea = screen.getByPlaceholderText(
      /e.g., Write a short poem about technology.../,
    );
    const submitButton = screen.getByText("Test AI Response");

    fireEvent.change(textarea, { target: { value: "Test prompt" } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(
        screen.getByText(
          "Daily limit exceeded. Please sign up for unlimited access.",
        ),
      ).toBeTruthy();
    });
  });

  it("handles network error", async () => {
    mockFetch.mockRejectedValueOnce(new Error("Network error"));

    render(<AnonymousLLMTest />);

    const textarea = screen.getByPlaceholderText(
      /e.g., Write a short poem about technology.../,
    );
    const submitButton = screen.getByText("Test AI Response");

    fireEvent.change(textarea, { target: { value: "Test prompt" } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText("Network error: Network error")).toBeTruthy();
    });
  });
});
