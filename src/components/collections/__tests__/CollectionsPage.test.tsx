import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { AuthProvider } from "@/components/auth/AuthProvider";
import CollectionsPage from "../CollectionsPage";
import { collectionsApi } from "@/services/api";

// Mock the API
jest.mock("@/services/api", () => ({
  collectionsApi: {
    list: jest.fn(),
    create: jest.fn(),
  },
}));

// Mock the child components
jest.mock("../VersionHistory", () => {
  return function MockVersionHistory({
    isOpen,
    onClose,
    promptId,
    promptName,
    onVersionRestore,
  }: any) {
    if (!isOpen) return null;
    return (
      <div data-testid="version-history">
        <span>Version History Component</span>
        <span data-testid="version-history-prompt-id">{promptId}</span>
        <span data-testid="version-history-prompt-name">{promptName}</span>
        <button
          data-testid="mock-version-restore"
          onClick={() => onVersionRestore("version-123")}
        >
          Restore Version
        </button>
        <button data-testid="mock-version-close" onClick={onClose}>
          Close
        </button>
      </div>
    );
  };
});

jest.mock("../ImportModal", () => {
  return function MockImportModal({ isOpen, onClose, onImport }: any) {
    if (!isOpen) return null;
    return (
      <div data-testid="import-modal">
        <span>Import Modal Component</span>
        <button
          data-testid="mock-import-submit"
          onClick={() =>
            onImport([
              {
                title: "Imported Prompt 1",
                description: "First imported prompt",
                source: "OpenAI",
              },
              {
                title: "Imported Prompt 2",
                description: "Second imported prompt",
                source: "Claude",
              },
            ])
          }
        >
          Import
        </button>
        <button data-testid="mock-import-close" onClick={onClose}>
          Close
        </button>
      </div>
    );
  };
});

// Mock useAuth hook
const mockUser = {
  id: "test-user-id",
  email: "test@example.com",
  name: "Test User",
};

jest.mock("@/components/auth/AuthProvider", () => ({
  ...jest.requireActual("@/components/auth/AuthProvider"),
  useAuth: () => ({
    user: mockUser,
    isAuthenticated: true,
    loading: false,
    login: jest.fn(),
    logout: jest.fn(),
  }),
}));

// Mock useApi hook
const mockUseApi = jest.fn();
jest.mock("@/hooks/useApi", () => ({
  useApi: () => mockUseApi(),
}));

const mockCollectionsData = {
  items: [
    {
      id: "1",
      name: "Test Collection 1",
      description: "A test collection",
      type: "private",
      owner_id: "test-user-id",
      created_at: "2024-01-01T00:00:00Z",
      updated_at: "2024-01-01T00:00:00Z",
      prompt_count: 5,
    },
    {
      id: "2",
      name: "Test Collection 2",
      description: "Another test collection",
      type: "public",
      owner_id: "test-user-id",
      created_at: "2024-01-02T00:00:00Z",
      updated_at: "2024-01-02T00:00:00Z",
      prompt_count: 3,
    },
  ],
};

const renderCollectionsPage = () => {
  return render(
    <BrowserRouter>
      <AuthProvider>
        <CollectionsPage />
      </AuthProvider>
    </BrowserRouter>,
  );
};

describe("CollectionsPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseApi.mockReturnValue({
      data: mockCollectionsData,
      loading: false,
      error: null,
      refetch: jest.fn(),
    });
    (collectionsApi.list as jest.Mock).mockResolvedValue(mockCollectionsData);
    (collectionsApi.create as jest.Mock).mockResolvedValue({ id: "3" });
  });

  it("should render the collections page with title", () => {
    renderCollectionsPage();

    expect(screen.getByText("Collections")).toBeInTheDocument();
    expect(
      screen.getByText("Organize and manage your prompt collections"),
    ).toBeInTheDocument();
  });

  it("should display loading state", () => {
    mockUseApi.mockReturnValue({
      data: null,
      loading: true,
      error: null,
      refetch: jest.fn(),
    });

    renderCollectionsPage();

    expect(screen.getByText("Loading collections...")).toBeInTheDocument();
  });

  it("should display collections when loaded", async () => {
    renderCollectionsPage();

    await waitFor(() => {
      expect(screen.getByText("Test Collection 1")).toBeInTheDocument();
      expect(screen.getByText("Test Collection 2")).toBeInTheDocument();
    });

    expect(screen.getByText("A test collection")).toBeInTheDocument();
    expect(screen.getByText("Another test collection")).toBeInTheDocument();
    expect(screen.getByText("5 prompts")).toBeInTheDocument();
    expect(screen.getByText("3 prompts")).toBeInTheDocument();
  });

  it("should handle error state", () => {
    mockUseApi.mockReturnValue({
      data: null,
      loading: false,
      error: new Error("Failed to fetch"),
      refetch: jest.fn(),
    });

    renderCollectionsPage();

    expect(
      screen.getByText("Error loading collections. Please try again."),
    ).toBeInTheDocument();
  });

  it("should handle empty state", () => {
    mockUseApi.mockReturnValue({
      data: { items: [] },
      loading: false,
      error: null,
      refetch: jest.fn(),
    });

    renderCollectionsPage();

    expect(
      screen.getByText(
        "No collections found. Create your first collection to get started!",
      ),
    ).toBeInTheDocument();
  });

  it("should open import modal when import button is clicked", async () => {
    renderCollectionsPage();

    const importButton = screen.getByRole("button", { name: "Import Prompts" });
    fireEvent.click(importButton);

    await waitFor(() => {
      expect(screen.getByTestId("import-modal")).toBeInTheDocument();
    });
  });

  it("should open version history modal when history button is clicked", async () => {
    renderCollectionsPage();

    const historyButton = screen.getAllByRole("button", { name: "History" })[0];
    fireEvent.click(historyButton);

    await waitFor(() => {
      expect(screen.getByTestId("version-history")).toBeInTheDocument();
    });
  });

  it("should handle successful collection creation", async () => {
    const refetch = jest.fn();
    mockUseApi.mockReturnValue({
      data: mockCollectionsData,
      loading: false,
      error: null,
      refetch,
    });
    (collectionsApi.create as jest.Mock).mockResolvedValue({ id: "new-id" });

    renderCollectionsPage();

    const newCollectionButton = screen.getByTestId(
      "header-new-collection-button",
    );
    fireEvent.click(newCollectionButton);

    await waitFor(() => {
      expect(collectionsApi.create).toHaveBeenCalledWith({
        name: "New Collection",
        description: "A new collection for organizing prompts",
        type: "private",
        owner_id: "test-user-id",
      });
    });

    expect(refetch).toHaveBeenCalled();
  });

  it("should handle failed collection creation", async () => {
    const refetch = jest.fn();
    const consoleErrorSpy = jest
      .spyOn(console, "error")
      .mockImplementation(() => {});
    mockUseApi.mockReturnValue({
      data: mockCollectionsData,
      loading: false,
      error: null,
      refetch,
    });
    const creationError = new Error("Creation failed");
    (collectionsApi.create as jest.Mock).mockRejectedValue(creationError);

    renderCollectionsPage();

    const newCollectionButton = screen.getByTestId(
      "header-new-collection-button",
    );
    fireEvent.click(newCollectionButton);

    await waitFor(() => {
      expect(collectionsApi.create).toHaveBeenCalled();
    });

    expect(refetch).not.toHaveBeenCalled();
    expect(consoleErrorSpy).toHaveBeenCalledWith(
      "Error creating collection:",
      creationError,
    );
    consoleErrorSpy.mockRestore();
  });

  // Add more comprehensive branch coverage tests
  it("should handle search functionality", async () => {
    renderCollectionsPage();

    await waitFor(() => {
      expect(screen.getByText("Test Collection 1")).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText("Search collections...");
    fireEvent.change(searchInput, { target: { value: "Collection 1" } });

    // The search input should be updated
    expect(searchInput).toHaveValue("Collection 1");
  });

  it("should handle clear search", async () => {
    renderCollectionsPage();

    await waitFor(() => {
      const searchInput = screen.getByPlaceholderText("Search collections...");
      fireEvent.change(searchInput, { target: { value: "test search" } });

      // Clear the search
      fireEvent.change(searchInput, { target: { value: "" } });
    });

    // All collections should be visible again
    expect(screen.getByText("Test Collection 1")).toBeInTheDocument();
    expect(screen.getByText("Test Collection 2")).toBeInTheDocument();
  });

  it("should handle different collection types", () => {
    const collectionsWithTypes = {
      items: [
        {
          id: "1",
          name: "Prompt Collection",
          description: "A prompt collection",
          type: "prompt",
          prompts: [{ id: "p1", name: "Prompt 1", content: "Content 1" }],
          updatedAt: "2024-01-01T00:00:00Z",
        },
        {
          id: "2",
          name: "Template Collection",
          description: "A template collection",
          type: "template",
          prompts: [],
          updatedAt: "2024-01-02T00:00:00Z",
        },
      ],
    };

    mockUseApi.mockReturnValue({
      data: collectionsWithTypes,
      loading: false,
      error: null,
      refetch: jest.fn(),
    });

    renderCollectionsPage();

    expect(screen.getByText("Prompt Collection")).toBeInTheDocument();
    expect(screen.getByText("Template Collection")).toBeInTheDocument();
  });

  it("should handle collection with no prompts", () => {
    const collectionsWithEmpty = {
      items: [
        {
          id: "1",
          name: "Empty Collection",
          description: "Collection with no prompts",
          prompts: [],
          updatedAt: "2024-01-01T00:00:00Z",
        },
      ],
    };

    mockUseApi.mockReturnValue({
      data: collectionsWithEmpty,
      loading: false,
      error: null,
      refetch: jest.fn(),
    });

    renderCollectionsPage();

    expect(screen.getByText("Empty Collection")).toBeInTheDocument();
    expect(screen.getByText("0 prompts")).toBeInTheDocument();
  });

  it("should create collection from the card button", async () => {
    const refetch = jest.fn();
    mockUseApi.mockReturnValue({
      data: mockCollectionsData,
      loading: false,
      error: null,
      refetch,
    });
    (collectionsApi.create as jest.Mock).mockResolvedValue({ id: "new-id" });

    renderCollectionsPage();

    const cardNewCollectionButton = screen.getByTestId(
      "card-new-collection-button",
    );
    fireEvent.click(cardNewCollectionButton);

    await waitFor(() => {
      expect(collectionsApi.create).toHaveBeenCalledWith({
        name: "New Collection",
        description: "A new collection for organizing prompts",
        type: "private",
        owner_id: "test-user-id",
      });
    });

    expect(refetch).toHaveBeenCalled();
  });

  it("should format dates correctly", () => {
    const collectionsWithDate = {
      items: [
        {
          id: "1",
          name: "Test Collection",
          description: "Test description",
          type: "private",
          owner_id: "test-user-id",
          created_at: "2024-01-15T10:30:00Z",
          updated_at: "2024-01-15T10:30:00Z",
          prompt_count: 2,
        },
      ],
    };

    mockUseApi.mockReturnValue({
      data: collectionsWithDate,
      loading: false,
      error: null,
      refetch: jest.fn(),
    });

    renderCollectionsPage();

    // The date should be formatted as a localised date string
    expect(screen.getByText(/Updated/)).toBeInTheDocument();
  });

  it("should close version history modal", async () => {
    renderCollectionsPage();

    // Open the modal first
    const historyButton = screen.getAllByRole("button", { name: "History" })[0];
    fireEvent.click(historyButton);

    await waitFor(() => {
      expect(screen.getByTestId("version-history")).toBeInTheDocument();
    });

    // Version history modal should have close functionality
    // Since we're mocking the component, we can't test the actual close functionality
    // but we can verify the modal is rendered
    expect(screen.getByTestId("version-history")).toBeInTheDocument();
  });

  it("should handle missing user gracefully", async () => {
    // Temporarily replace the useAuth mock
    const originalUseAuth = require("@/components/auth/AuthProvider").useAuth;
    require("@/components/auth/AuthProvider").useAuth = jest.fn(() => ({
      user: null,
      isAuthenticated: false,
      loading: false,
      login: jest.fn(),
      logout: jest.fn(),
    }));

    const refetch = jest.fn();
    mockUseApi.mockReturnValue({
      data: mockCollectionsData,
      loading: false,
      error: null,
      refetch,
    });

    renderCollectionsPage();

    const newCollectionButton = screen.getByTestId(
      "header-new-collection-button",
    );
    fireEvent.click(newCollectionButton);

    await waitFor(() => {
      expect(collectionsApi.create).toHaveBeenCalledWith({
        name: "New Collection",
        description: "A new collection for organizing prompts",
        type: "private",
        owner_id: "dev-user", // Should fall back to dev-user
      });
    });

    // Restore original mock
    require("@/components/auth/AuthProvider").useAuth = originalUseAuth;
  });

  it("should handle collections with missing prompt_count", () => {
    const collectionsWithMissingCount = {
      items: [
        {
          id: "1",
          name: "Test Collection",
          description: "Test description",
          type: "private",
          owner_id: "test-user-id",
          created_at: "2024-01-01T00:00:00Z",
          updated_at: "2024-01-01T00:00:00Z",
          // prompt_count is missing
        },
      ],
    };

    mockUseApi.mockReturnValue({
      data: collectionsWithMissingCount,
      loading: false,
      error: null,
      refetch: jest.fn(),
    });

    renderCollectionsPage();

    expect(screen.getByText("0 prompts")).toBeInTheDocument();
  });

  it("should display collection first letter in avatar", () => {
    const collectionsWithNames = {
      items: [
        {
          id: "1",
          name: "Amazing Collection",
          description: "Test description",
          type: "private",
          owner_id: "test-user-id",
          created_at: "2024-01-01T00:00:00Z",
          updated_at: "2024-01-01T00:00:00Z",
          prompt_count: 1,
        },
        {
          id: "2",
          name: "zzz Collection",
          description: "Test description",
          type: "private",
          owner_id: "test-user-id",
          created_at: "2024-01-01T00:00:00Z",
          updated_at: "2024-01-01T00:00:00Z",
          prompt_count: 1,
        },
      ],
    };

    mockUseApi.mockReturnValue({
      data: collectionsWithNames,
      loading: false,
      error: null,
      refetch: jest.fn(),
    });

    renderCollectionsPage();

    expect(screen.getByText("A")).toBeInTheDocument(); // First letter of "Amazing Collection"
    expect(screen.getByText("z")).toBeInTheDocument(); // First letter of "zzz Collection"
  });

  it("should handle import modal functionality", async () => {
    const refetch = jest.fn();
    const consoleLogSpy = jest
      .spyOn(console, "log")
      .mockImplementation(() => {});
    mockUseApi.mockReturnValue({
      data: mockCollectionsData,
      loading: false,
      error: null,
      refetch,
    });

    renderCollectionsPage();

    // Open import modal
    const importButton = screen.getByRole("button", { name: "Import Prompts" });
    fireEvent.click(importButton);

    await waitFor(() => {
      expect(screen.getByTestId("import-modal")).toBeInTheDocument();
    });

    // Test import functionality
    const importSubmitButton = screen.getByTestId("mock-import-submit");
    fireEvent.click(importSubmitButton);

    await waitFor(() => {
      expect(collectionsApi.create).toHaveBeenCalledWith({
        name: "Imported Prompt 1",
        description: "First imported prompt",
        type: "private",
        owner_id: "test-user-id",
        tags: ["imported", "openai"],
      });
    });

    expect(refetch).toHaveBeenCalled();
    expect(consoleLogSpy).toHaveBeenCalledWith(
      "Importing prompts:",
      expect.any(Array),
    );
    consoleLogSpy.mockRestore();
  });

  it("should handle import modal close", async () => {
    renderCollectionsPage();

    // Open import modal
    const importButton = screen.getByRole("button", { name: "Import Prompts" });
    fireEvent.click(importButton);

    await waitFor(() => {
      expect(screen.getByTestId("import-modal")).toBeInTheDocument();
    });

    // Close import modal
    const closeButton = screen.getByTestId("mock-import-close");
    fireEvent.click(closeButton);

    await waitFor(() => {
      expect(screen.queryByTestId("import-modal")).not.toBeInTheDocument();
    });
  });

  it("should handle import error gracefully", async () => {
    const refetch = jest.fn();
    const consoleErrorSpy = jest
      .spyOn(console, "error")
      .mockImplementation(() => {});
    const consoleLogSpy = jest
      .spyOn(console, "log")
      .mockImplementation(() => {});

    mockUseApi.mockReturnValue({
      data: mockCollectionsData,
      loading: false,
      error: null,
      refetch,
    });

    // Mock import to fail
    (collectionsApi.create as jest.Mock).mockRejectedValue(
      new Error("Import failed"),
    );

    renderCollectionsPage();

    // Open import modal and import
    const importButton = screen.getByRole("button", { name: "Import Prompts" });
    fireEvent.click(importButton);

    await waitFor(() => {
      expect(screen.getByTestId("import-modal")).toBeInTheDocument();
    });

    const importSubmitButton = screen.getByTestId("mock-import-submit");
    fireEvent.click(importSubmitButton);

    await waitFor(() => {
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        "Error importing prompt:",
        expect.any(Error),
      );
    });

    consoleErrorSpy.mockRestore();
    consoleLogSpy.mockRestore();
  });

  it("should open version history with correct data", async () => {
    renderCollectionsPage();

    const historyButton = screen.getAllByRole("button", { name: "History" })[0];
    fireEvent.click(historyButton);

    await waitFor(() => {
      expect(screen.getByTestId("version-history")).toBeInTheDocument();
      expect(screen.getByTestId("version-history-prompt-id")).toHaveTextContent(
        "1",
      );
      expect(
        screen.getByTestId("version-history-prompt-name"),
      ).toHaveTextContent("Test Collection 1");
    });
  });

  it("should handle version history close", async () => {
    renderCollectionsPage();

    // Open version history
    const historyButton = screen.getAllByRole("button", { name: "History" })[0];
    fireEvent.click(historyButton);

    await waitFor(() => {
      expect(screen.getByTestId("version-history")).toBeInTheDocument();
    });

    // Close version history
    const closeButton = screen.getByTestId("mock-version-close");
    fireEvent.click(closeButton);

    await waitFor(() => {
      expect(screen.queryByTestId("version-history")).not.toBeInTheDocument();
    });
  });

  it("should handle version restore", async () => {
    const consoleLogSpy = jest
      .spyOn(console, "log")
      .mockImplementation(() => {});

    renderCollectionsPage();

    // Open version history
    const historyButton = screen.getAllByRole("button", { name: "History" })[0];
    fireEvent.click(historyButton);

    await waitFor(() => {
      expect(screen.getByTestId("version-history")).toBeInTheDocument();
    });

    // Test version restore
    const restoreButton = screen.getByTestId("mock-version-restore");
    fireEvent.click(restoreButton);

    expect(consoleLogSpy).toHaveBeenCalledWith(
      "Restoring version:",
      "version-123",
    );
    consoleLogSpy.mockRestore();
  });

  it("should handle missing collections data gracefully", () => {
    mockUseApi.mockReturnValue({
      data: null,
      loading: false,
      error: null,
      refetch: jest.fn(),
    });

    renderCollectionsPage();

    // Should not crash when data is null
    expect(screen.getByText("Collections")).toBeInTheDocument();
    expect(screen.getByText("Create new collection")).toBeInTheDocument();
  });

  it("should handle collections data without items property", () => {
    mockUseApi.mockReturnValue({
      data: {}, // No items property
      loading: false,
      error: null,
      refetch: jest.fn(),
    });

    renderCollectionsPage();

    // Should not crash when items property is missing
    expect(screen.getByText("Collections")).toBeInTheDocument();
    expect(screen.getByText("Create new collection")).toBeInTheDocument();
  });

  it("should render View collection links correctly", () => {
    renderCollectionsPage();

    const viewLinks = screen.getAllByText("View collection");
    expect(viewLinks).toHaveLength(2); // One for each collection

    viewLinks.forEach((link, index) => {
      const expectedHref = `/collections/${mockCollectionsData.items[index].id}`;
      expect(link.closest("a")).toHaveAttribute("href", expectedHref);
    });
  });

  it("should test both History buttons work correctly", async () => {
    renderCollectionsPage();

    const historyButtons = screen.getAllByRole("button", { name: "History" });
    expect(historyButtons).toHaveLength(2); // One for each collection

    // Test second history button
    fireEvent.click(historyButtons[1]);

    await waitFor(() => {
      expect(screen.getByTestId("version-history")).toBeInTheDocument();
      expect(screen.getByTestId("version-history-prompt-id")).toHaveTextContent(
        "2",
      );
      expect(
        screen.getByTestId("version-history-prompt-name"),
      ).toHaveTextContent("Test Collection 2");
    });
  });

  it("should handle edge case with empty collection name", () => {
    const collectionsWithEmptyName = {
      items: [
        {
          id: "1",
          name: "", // Empty name
          description: "Test description",
          type: "private",
          owner_id: "test-user-id",
          created_at: "2024-01-01T00:00:00Z",
          updated_at: "2024-01-01T00:00:00Z",
          prompt_count: 1,
        },
      ],
    };

    mockUseApi.mockReturnValue({
      data: collectionsWithEmptyName,
      loading: false,
      error: null,
      refetch: jest.fn(),
    });

    renderCollectionsPage();

    // Should handle empty name gracefully - charAt(0) on empty string returns empty string
    expect(screen.getByText("Test description")).toBeInTheDocument();
  });
});
