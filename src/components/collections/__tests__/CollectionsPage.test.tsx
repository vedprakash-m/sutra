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
    </BrowserRouter>
  );
};

describe("CollectionsPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseApi.mockReturnValue({ 
      data: mockCollectionsData, 
      loading: false, 
      error: null, 
      refetch: jest.fn() 
    });
    (collectionsApi.list as jest.Mock).mockResolvedValue(mockCollectionsData);
    (collectionsApi.create as jest.Mock).mockResolvedValue({ id: "3" });
  });

  it("should render the collections page with title", () => {
    renderCollectionsPage();

    expect(screen.getByText("Collections")).toBeInTheDocument();
    expect(screen.getByText("Organize and manage your prompt collections")).toBeInTheDocument();
  });

  it("should display loading state", () => {
    mockUseApi.mockReturnValue({ 
      data: null, 
      loading: true, 
      error: null, 
      refetch: jest.fn() 
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

  it("should handle search functionality", async () => {
    const mockRefetch = jest.fn();
    mockUseApi.mockReturnValue({ 
      data: mockCollectionsData, 
      loading: false, 
      error: null, 
      refetch: mockRefetch 
    });
    
    renderCollectionsPage();

    const searchInput = screen.getByPlaceholderText("Search collections...") as HTMLInputElement;
    fireEvent.change(searchInput, { target: { value: "test search" } });

    // The search should trigger a re-render with the new search term
    expect(searchInput.value).toBe("test search");
  });

  it("should handle create collection", async () => {
    const mockRefetch = jest.fn();
    mockUseApi.mockReturnValue({ 
      data: mockCollectionsData, 
      loading: false, 
      error: null, 
      refetch: mockRefetch 
    });
    
    renderCollectionsPage();

    const createButtons = screen.getAllByText("New Collection");
    fireEvent.click(createButtons[0]); // Click the first button (in header)

    await waitFor(() => {
      expect(collectionsApi.create).toHaveBeenCalledWith({
        name: "New Collection",
        description: "A new collection for organizing prompts",
        type: "private",
        owner_id: "test-user-id",
      });
    });
  });

  it("should handle import modal", () => {
    renderCollectionsPage();

    const importButton = screen.getByText("Import Prompts");
    fireEvent.click(importButton);

    // The import modal should be rendered (mocked)
    expect(screen.getByTestId("import-modal")).toBeInTheDocument();
  });

  it("should display error state", async () => {
    const errorMessage = "Failed to load collections";
    mockUseApi.mockReturnValue({ 
      data: null, 
      loading: false, 
      error: new Error(errorMessage), 
      refetch: jest.fn() 
    });

    renderCollectionsPage();

    expect(screen.getByText("Error loading collections. Please try again.")).toBeInTheDocument();
  });

  it("should handle empty collections state", async () => {
    mockUseApi.mockReturnValue({ 
      data: { items: [] }, 
      loading: false, 
      error: null, 
      refetch: jest.fn() 
    });

    renderCollectionsPage();

    expect(screen.getByText("No collections found. Create your first collection to get started!")).toBeInTheDocument();
  });

  it("should format dates correctly", async () => {
    renderCollectionsPage();

    await waitFor(() => {
      // Check that dates are formatted - exact format depends on locale
      const date1 = new Date("2024-01-01T00:00:00Z").toLocaleDateString();
      const date2 = new Date("2024-01-02T00:00:00Z").toLocaleDateString();
      expect(screen.getByText(`Updated ${date1}`)).toBeInTheDocument();
      expect(screen.getByText(`Updated ${date2}`)).toBeInTheDocument();
    });
  });

  it("should handle version history modal", async () => {
    renderCollectionsPage();

    await waitFor(() => {
      expect(screen.getByText("Test Collection 1")).toBeInTheDocument();
    });

    // Find and click version history button
    const historyButtons = screen.getAllByText("History");
    fireEvent.click(historyButtons[0]);

    // The modal components are already mocked and rendered
    expect(screen.getByTestId("version-history")).toBeInTheDocument();
  });
});
