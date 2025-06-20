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
  return function MockVersionHistory() {
    return <div data-testid="version-history">Version History Component</div>;
  };
});

jest.mock("../ImportModal", () => {
  return function MockImportModal() {
    return <div data-testid="import-modal">Import Modal Component</div>;
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

  // These tests are skipped because the features are not implemented in the component yet
  it.skip("should handle sorting by date", async () => {
    // Feature not implemented - no sort functionality exists
  });

  it.skip("should handle view mode toggle", async () => {
    // Feature not implemented - no view toggle functionality exists
  });

  it.skip("should handle collection actions menu", async () => {
    // Feature not implemented - no actions menu exists
  });

  it.skip("should handle edit collection", async () => {
    // Feature not implemented - no edit functionality exists
  });

  it.skip("should handle delete collection", async () => {
    // Feature not implemented - no delete functionality exists
  });

  it.skip("should handle refresh/refetch", async () => {
    // Feature not implemented - no explicit refresh button exists
  });

  it.skip("should handle keyboard navigation", async () => {
    // Feature not implemented - no keyboard navigation exists
  });

  it.skip("should handle collection card hover states", async () => {
    // Feature not implemented - no special hover states exist
  });

  it.skip("should handle filter by collection type", async () => {
    // Feature not implemented - no filter functionality exists
  });
});
