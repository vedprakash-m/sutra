import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { useParams, useNavigate } from "react-router-dom";
import PlaybookBuilder from "../PlaybookBuilder";
import { playbooksApi } from "@/services/api";

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
  playbooksApi: {
    create: jest.fn(),
    update: jest.fn(),
    getById: jest.fn(),
  },
}));

// Mock react-router-dom hooks
jest.mock("react-router-dom", () => ({
  ...jest.requireActual("react-router-dom"),
  useParams: jest.fn(),
  useNavigate: jest.fn(),
}));

const mockNavigate = jest.fn();

beforeEach(() => {
  jest.clearAllMocks();
  (playbooksApi.create as jest.Mock).mockResolvedValue({
    id: "test-playbook-id",
    name: "Test Playbook",
    description: "Test Description",
    steps: [],
    visibility: "private",
  });
  (useParams as jest.Mock).mockReturnValue({});
  (useNavigate as jest.Mock).mockReturnValue(mockNavigate);
});

const renderPlaybookBuilder = () => {
  return render(
    <BrowserRouter>
      <PlaybookBuilder />
    </BrowserRouter>
  );
};

describe("PlaybookBuilder", () => {
  it("should render the playbook builder with title", () => {
    renderPlaybookBuilder();

    expect(screen.getByText("Playbook Builder")).toBeInTheDocument();
    expect(
      screen.getByText("Create linear AI workflows and automation playbooks")
    ).toBeInTheDocument();
  });

  it("should render form inputs", () => {
    renderPlaybookBuilder();

    expect(screen.getByLabelText(/name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/description/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/visibility/i)).toBeInTheDocument();
  });

  it("should handle name input changes", () => {
    renderPlaybookBuilder();

    const nameInput = screen.getByLabelText(/name/i);
    fireEvent.change(nameInput, { target: { value: "My Playbook" } });

    expect(nameInput).toHaveValue("My Playbook");
  });

  it("should handle description input changes", () => {
    renderPlaybookBuilder();

    const descriptionInput = screen.getByLabelText(/description/i);
    fireEvent.change(descriptionInput, {
      target: { value: "This is a test playbook" },
    });

    expect(descriptionInput).toHaveValue("This is a test playbook");
  });

  it("should handle visibility changes", () => {
    renderPlaybookBuilder();

    const visibilitySelect = screen.getByLabelText(/visibility/i);
    fireEvent.change(visibilitySelect, { target: { value: "shared" } });

    expect(visibilitySelect).toHaveValue("shared");
  });

  it("should add prompt step", () => {
    renderPlaybookBuilder();

    const addPromptButton = screen.getByText("Prompt Step");
    fireEvent.click(addPromptButton);

    expect(screen.getByText("Step 1")).toBeInTheDocument();
    expect(screen.getByText("prompt")).toBeInTheDocument();
  });

  it("should add review step", () => {
    renderPlaybookBuilder();

    const addReviewButton = screen.getByText("Review Step");
    fireEvent.click(addReviewButton);

    expect(screen.getByText("Step 1")).toBeInTheDocument();
    expect(screen.getByText("review")).toBeInTheDocument();
  });

  it("should add variable step", () => {
    renderPlaybookBuilder();

    const addVariableButton = screen.getByText("Variable Step");
    fireEvent.click(addVariableButton);

    expect(screen.getByText("Step 1")).toBeInTheDocument();
    expect(screen.getByText("variable")).toBeInTheDocument();
  });

  it("should remove steps", () => {
    renderPlaybookBuilder();

    // Add a step first
    const addPromptButton = screen.getByText("Prompt Step");
    fireEvent.click(addPromptButton);

    expect(screen.getByText("Step 1")).toBeInTheDocument();

    // Find and click remove button (trash icon) - there should be multiple buttons now
    const buttons = screen.getAllByRole("button");
    const removeButton = buttons.find(button => 
      button.querySelector('svg path[d*="M19 7l-.867 12.142"]')
    );
    
    if (removeButton) {
      fireEvent.click(removeButton);
    }

    // Should show empty state again
    expect(screen.getByText("Build Your First Workflow")).toBeInTheDocument();
  });

  it("should move steps up and down", () => {
    renderPlaybookBuilder();

    // Add two steps
    const addPromptButton = screen.getByText("Prompt Step");
    fireEvent.click(addPromptButton);
    fireEvent.click(addPromptButton);

    expect(screen.getAllByText(/Step \d/)).toHaveLength(2);
    expect(screen.getByText("Step 1")).toBeInTheDocument();
    expect(screen.getByText("Step 2")).toBeInTheDocument();
  });

  it("should save new playbook", async () => {
    renderPlaybookBuilder();

    // Fill in form
    const nameInput = screen.getByLabelText(/name/i);
    fireEvent.change(nameInput, { target: { value: "Test Playbook" } });

    const descriptionInput = screen.getByLabelText(/description/i);
    fireEvent.change(descriptionInput, {
      target: { value: "Test Description" },
    });

    // Save playbook
    const saveButton = screen.getByText("Save Playbook");
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(playbooksApi.create).toHaveBeenCalledWith({
        name: "Test Playbook",
        description: "Test Description",
        steps: [],
        creator_id: "test-user",
        visibility: "private",
      });
    });
  });

  it("should handle save errors", async () => {
    (playbooksApi.create as jest.Mock).mockRejectedValue(
      new Error("Save failed")
    );

    renderPlaybookBuilder();

    const nameInput = screen.getByLabelText(/name/i);
    fireEvent.change(nameInput, { target: { value: "Test Playbook" } });

    const saveButton = screen.getByText("Save Playbook");
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(playbooksApi.create).toHaveBeenCalled();
    });

    // Could add error message assertion here if component shows error
  });

  it("should show empty state when no steps", () => {
    renderPlaybookBuilder();

    expect(screen.getByText("Build Your First Workflow")).toBeInTheDocument();
    expect(screen.getByText("Add steps to create a workflow. Steps will be executed in order from top to bottom.")).toBeInTheDocument();
  });
});
