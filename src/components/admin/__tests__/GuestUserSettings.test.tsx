import {
  render,
  screen,
  fireEvent,
  waitFor,
  act,
} from "@testing-library/react";
import { GuestUserSettings } from "../GuestUserSettings";

// Mock fetch globally
const mockFetch = jest.fn();
global.fetch = mockFetch;

describe("GuestUserSettings", () => {
  const mockSettings = {
    id: "guest-settings-1",
    limits: {
      llm_calls_per_day: 5,
      prompts_per_day: 10,
      collections_per_session: 3,
      playbooks_per_session: 2,
      session_duration_hours: 24,
      enabled: true,
    },
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-02T12:00:00Z",
    updated_by: "admin@example.com",
  };

  beforeEach(() => {
    mockFetch.mockClear();
  });

  it("renders loading state initially", () => {
    mockFetch.mockImplementation(() => new Promise(() => {})); // Never resolves

    render(<GuestUserSettings />);

    expect(screen.getByText("Loading guest settings...")).toBeInTheDocument();
    expect(screen.getByTestId("loading-spinner")).toBeInTheDocument();
  });

  it("loads and displays guest settings successfully", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockSettings,
    });

    render(<GuestUserSettings />);

    await waitFor(() => {
      expect(
        screen.getByText("Anonymous Guest User Settings"),
      ).toBeInTheDocument();
    });

    // Check specific form fields by their values
    expect(screen.getByDisplayValue("5")).toBeInTheDocument(); // llm_calls_per_day
    expect(screen.getByDisplayValue("10")).toBeInTheDocument(); // prompts_per_day
    expect(screen.getByDisplayValue("3")).toBeInTheDocument(); // collections_per_session
    expect(screen.getByDisplayValue("2")).toBeInTheDocument(); // playbooks_per_session
    expect(screen.getByDisplayValue("24")).toBeInTheDocument(); // session_duration_hours

    // Check that the enabled toggle is checked
    const enabledToggle = screen.getByRole("checkbox");
    expect(enabledToggle).toBeChecked();

    // Check last updated information
    expect(screen.getByText(/Last updated:/)).toBeInTheDocument();
    expect(screen.getByText(/by admin@example.com/)).toBeInTheDocument();
  });

  it("displays error when failing to load settings", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
    });

    render(<GuestUserSettings />);

    await waitFor(() => {
      expect(
        screen.getByText("Failed to load guest user settings"),
      ).toBeInTheDocument();
    });
  });

  it("displays error when fetch throws exception", async () => {
    mockFetch.mockRejectedValueOnce(new Error("Network error"));

    render(<GuestUserSettings />);

    await waitFor(() => {
      expect(
        screen.getByText("Failed to load guest user settings"),
      ).toBeInTheDocument();
    });
  });

  it("updates LLM calls limit when input changes", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockSettings,
    });

    render(<GuestUserSettings />);

    await waitFor(() => {
      expect(
        screen.getByText("Anonymous Guest User Settings"),
      ).toBeInTheDocument();
    });

    const llmCallsInput = screen.getByDisplayValue("5");
    expect(llmCallsInput).toBeInTheDocument();

    act(() => {
      fireEvent.change(llmCallsInput!, { target: { value: "10" } });
    });

    expect(llmCallsInput).toHaveValue(10);
  });

  it("toggles enabled state when checkbox is clicked", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockSettings,
    });

    render(<GuestUserSettings />);

    await waitFor(() => {
      expect(screen.getByRole("checkbox")).toBeChecked();
    });

    const enabledToggle = screen.getByRole("checkbox");

    act(() => {
      fireEvent.click(enabledToggle);
    });

    expect(enabledToggle).not.toBeChecked();
  });

  it("saves settings successfully", async () => {
    // Mock initial load
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockSettings,
    });

    // Mock save
    const updatedSettings = {
      ...mockSettings,
      limits: { ...mockSettings.limits, llm_calls_per_day: 10 },
      updated_at: "2024-01-03T12:00:00Z",
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => updatedSettings,
    });

    render(<GuestUserSettings />);

    await waitFor(() => {
      expect(screen.getByText("Save Settings")).toBeInTheDocument();
    });

    // Update a value
    const llmCallsInput = screen.getByDisplayValue("5");

    act(() => {
      fireEvent.change(llmCallsInput!, { target: { value: "10" } });
    });

    // Save
    const saveButton = screen.getByText("Save Settings");

    await act(async () => {
      fireEvent.click(saveButton);
    });

    // Check that save request was made
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith("/api/admin/guest/settings", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          limits: {
            ...mockSettings.limits,
            llm_calls_per_day: 10,
          },
        }),
      });
    });

    // Check success message appears
    await waitFor(() => {
      expect(
        screen.getByText("Guest user settings updated successfully!"),
      ).toBeInTheDocument();
    });
  });

  it("displays error message when save fails", async () => {
    // Mock initial load
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockSettings,
    });

    // Mock failed save
    mockFetch.mockResolvedValueOnce({
      ok: false,
      json: async () => ({ error: "Validation failed" }),
    });

    render(<GuestUserSettings />);

    await waitFor(() => {
      expect(screen.getByText("Save Settings")).toBeInTheDocument();
    });

    // Save
    const saveButton = screen.getByText("Save Settings");

    await act(async () => {
      fireEvent.click(saveButton);
    });

    // Check error message
    await waitFor(() => {
      expect(screen.getByText("Validation failed")).toBeInTheDocument();
    });
  });

  it("displays loading state while saving", async () => {
    // Mock initial load
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockSettings,
    });

    render(<GuestUserSettings />);

    await waitFor(() => {
      expect(screen.getByText("Save Settings")).toBeInTheDocument();
    });

    // Mock slow save
    mockFetch.mockImplementation(() => new Promise(() => {})); // Never resolves

    const saveButton = screen.getByText("Save Settings");

    act(() => {
      fireEvent.click(saveButton);
    });

    await waitFor(() => {
      expect(screen.getByText("Saving...")).toBeInTheDocument();
      expect(saveButton).toBeDisabled();
    });
  });

  it("handles network error during save", async () => {
    // Mock initial load
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockSettings,
    });

    // Mock network error
    mockFetch.mockRejectedValueOnce(new Error("Network error"));

    render(<GuestUserSettings />);

    await waitFor(() => {
      expect(screen.getByText("Save Settings")).toBeInTheDocument();
    });

    // Save
    const saveButton = screen.getByText("Save Settings");

    await act(async () => {
      fireEvent.click(saveButton);
    });

    // Check error message
    await waitFor(() => {
      expect(screen.getByText("Error saving settings")).toBeInTheDocument();
    });
  });

  it("validates number inputs properly", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockSettings,
    });

    render(<GuestUserSettings />);

    await waitFor(() => {
      expect(
        screen.getByText("Anonymous Guest User Settings"),
      ).toBeInTheDocument();
    });

    // Test empty input handling
    const llmCallsInput = screen.getByDisplayValue("5");

    act(() => {
      fireEvent.change(llmCallsInput!, { target: { value: "" } });
    });

    expect(llmCallsInput).toHaveValue(0);

    // Test invalid input handling
    act(() => {
      fireEvent.change(llmCallsInput!, { target: { value: "invalid" } });
    });

    expect(llmCallsInput).toHaveValue(0);
  });

  it("displays anonymous user features info", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockSettings,
    });

    render(<GuestUserSettings />);

    await waitFor(() => {
      expect(
        screen.getByText("📊 Anonymous User Features"),
      ).toBeInTheDocument();
    });

    // Check that feature descriptions are present
    expect(screen.getByText(/IP-based rate limiting/)).toBeInTheDocument();
    expect(screen.getByText(/Limited to GPT-3.5 Turbo/)).toBeInTheDocument();
    expect(
      screen.getByText(/Maximum 500 characters per prompt/),
    ).toBeInTheDocument();
    expect(screen.getByText(/Cannot save prompts/)).toBeInTheDocument();
  });

  it("clears success message after timeout", async () => {
    jest.useFakeTimers();

    // Mock initial load
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockSettings,
    });

    // Mock successful save
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockSettings,
    });

    render(<GuestUserSettings />);

    await waitFor(() => {
      expect(screen.getByText("Save Settings")).toBeInTheDocument();
    });

    // Save
    const saveButton = screen.getByText("Save Settings");

    await act(async () => {
      fireEvent.click(saveButton);
    });

    // Success message should appear
    await waitFor(() => {
      expect(
        screen.getByText("Guest user settings updated successfully!"),
      ).toBeInTheDocument();
    });

    // Fast forward time
    act(() => {
      jest.advanceTimersByTime(3000);
    });

    // Success message should be gone
    await waitFor(() => {
      expect(
        screen.queryByText("Guest user settings updated successfully!"),
      ).not.toBeInTheDocument();
    });

    jest.useRealTimers();
  });

  it("updates all form fields correctly", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockSettings,
    });

    render(<GuestUserSettings />);

    await waitFor(() => {
      expect(
        screen.getByText("Anonymous Guest User Settings"),
      ).toBeInTheDocument();
    });

    // Update prompts per day
    const promptsInput = screen.getByDisplayValue("10");
    act(() => {
      fireEvent.change(promptsInput, { target: { value: "15" } });
    });
    expect(promptsInput).toHaveValue(15);

    // Update collections per session
    const collectionsInput = screen.getByDisplayValue("3");
    act(() => {
      fireEvent.change(collectionsInput, { target: { value: "5" } });
    });
    expect(collectionsInput).toHaveValue(5);

    // Update playbooks per session
    const playbooksInput = screen.getByDisplayValue("2");
    act(() => {
      fireEvent.change(playbooksInput, { target: { value: "4" } });
    });
    expect(playbooksInput).toHaveValue(4);

    // Update session duration
    const durationInput = screen.getByDisplayValue("24");
    act(() => {
      fireEvent.change(durationInput, { target: { value: "48" } });
    });
    expect(durationInput).toHaveValue(48);
  });
});
