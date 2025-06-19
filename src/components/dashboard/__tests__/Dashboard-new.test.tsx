import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import "@testing-library/jest-dom";
import Dashboard from "../Dashboard-new";

// Mock the auth provider
const mockAuthContext = {
  user: { name: "John Doe", email: "john@example.com" },
  isAuthenticated: true,
  isAdmin: false,
  isLoading: false,
  login: jest.fn(),
  logout: jest.fn(),
};

jest.mock("@/components/auth/AuthProvider", () => ({
  useAuth: () => mockAuthContext,
}));

// Mock the useApi hook
const mockUseApi = jest.fn();
jest.mock("@/hooks/useApi", () => ({
  useApi: () => mockUseApi(),
}));

// Mock the API services
jest.mock("@/services/api", () => ({
  collectionsApi: {
    list: jest.fn(),
  },
  playbooksApi: {
    list: jest.fn(),
  },
}));

const renderWithRouter = (component: any) => {
  return render(<MemoryRouter>{component}</MemoryRouter>);
};

describe("Dashboard-new", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Reset mock to ensure fresh state for each test
    mockUseApi.mockReset();
  });

  it("should render welcome message with user name", () => {
    // Setup specific mock values for this test
    mockUseApi
      .mockReturnValueOnce({ data: null, loading: true })
      .mockReturnValueOnce({ data: null, loading: true });

    renderWithRouter(<Dashboard />);

    expect(screen.getByText("Welcome back, John Doe")).toBeInTheDocument();
    expect(
      screen.getByText("Here's what you can do with Sutra today"),
    ).toBeInTheDocument();
  });

  it("should render all quick action cards", () => {
    mockUseApi
      .mockReturnValueOnce({ data: null, loading: true })
      .mockReturnValueOnce({ data: null, loading: true });

    renderWithRouter(<Dashboard />);

    expect(screen.getByText("Create Prompt")).toBeInTheDocument();
    expect(screen.getByText("Collections")).toBeInTheDocument();
    expect(screen.getByText("Create Playbook")).toBeInTheDocument();
    expect(screen.getByText("Integrations")).toBeInTheDocument();
  });

  it("should render quick action links with correct hrefs", () => {
    mockUseApi
      .mockReturnValueOnce({ data: null, loading: true })
      .mockReturnValueOnce({ data: null, loading: true });

    renderWithRouter(<Dashboard />);

    expect(screen.getByText("Create Prompt").closest("a")).toHaveAttribute(
      "href",
      "/prompts/new",
    );
    expect(screen.getByText("Collections").closest("a")).toHaveAttribute(
      "href",
      "/collections",
    );
    expect(screen.getByText("Create Playbook").closest("a")).toHaveAttribute(
      "href",
      "/playbooks/new",
    );
    expect(screen.getByText("Integrations").closest("a")).toHaveAttribute(
      "href",
      "/integrations",
    );
  });

  it("should show loading state for collections", () => {
    mockUseApi
      .mockReturnValueOnce({ data: null, loading: true })
      .mockReturnValueOnce({ data: null, loading: true });

    renderWithRouter(<Dashboard />);

    expect(screen.getByText("Loading...")).toBeInTheDocument();
  });

  it("should display collections count when data is loaded", () => {
    const collectionsData = {
      items: [
        {
          id: "1",
          name: "Collection 1",
          description: "Desc 1",
          type: "prompt",
        },
        {
          id: "2",
          name: "Collection 2",
          description: "Desc 2",
          type: "template",
        },
      ],
      pagination: { total_count: 15 },
    };

    mockUseApi
      .mockReturnValueOnce({ data: collectionsData, loading: false })
      .mockReturnValueOnce({ data: null, loading: true });

    renderWithRouter(<Dashboard />);

    expect(screen.getByText("15")).toBeInTheDocument();
  });

  it("should display 0 collections when no data", () => {
    mockUseApi
      .mockReturnValueOnce({ data: null, loading: false })
      .mockReturnValueOnce({ data: null, loading: true });

    renderWithRouter(<Dashboard />);

    expect(screen.getByText("0")).toBeInTheDocument();
  });

  it("should render recent collections section", () => {
    mockUseApi
      .mockReturnValueOnce({ data: null, loading: true })
      .mockReturnValueOnce({ data: null, loading: true });

    renderWithRouter(<Dashboard />);

    expect(screen.getByText("Recent Collections")).toBeInTheDocument();
  });

  it("should show loading skeleton for collections", () => {
    mockUseApi
      .mockReturnValueOnce({ data: null, loading: true })
      .mockReturnValueOnce({ data: null, loading: true });

    renderWithRouter(<Dashboard />);

    const skeletonElements = document.querySelectorAll(".animate-pulse");
    expect(skeletonElements.length).toBeGreaterThan(0);
  });

  it("should display collection items when loaded", () => {
    const collectionsData = {
      items: [
        {
          id: "1",
          name: "Marketing Collection",
          description: "Email templates",
          type: "prompt",
        },
        {
          id: "2",
          name: "Sales Collection",
          description: "Sales scripts",
          type: "template",
        },
      ],
      pagination: { total_count: 2 },
    };

    mockUseApi
      .mockReturnValueOnce({ data: collectionsData, loading: false })
      .mockReturnValueOnce({ data: null, loading: true });

    renderWithRouter(<Dashboard />);

    expect(screen.getByText("Marketing Collection")).toBeInTheDocument();
    expect(screen.getByText("Email templates")).toBeInTheDocument();
    expect(screen.getByText("Sales Collection")).toBeInTheDocument();
    expect(screen.getByText("Sales scripts")).toBeInTheDocument();
  });

  it("should show empty state message for collections", () => {
    const collectionsData = {
      items: [],
      pagination: { total_count: 0 },
    };

    mockUseApi
      .mockReturnValueOnce({ data: collectionsData, loading: false })
      .mockReturnValueOnce({ data: null, loading: true });

    renderWithRouter(<Dashboard />);

    expect(
      screen.getByText("No collections yet. Create your first collection!"),
    ).toBeInTheDocument();
  });

  it("should render recent playbooks section", () => {
    mockUseApi
      .mockReturnValueOnce({ data: null, loading: true })
      .mockReturnValueOnce({ data: null, loading: true });

    renderWithRouter(<Dashboard />);

    expect(screen.getByText("Recent Playbooks")).toBeInTheDocument();
  });

  it("should display playbook items when loaded", () => {
    const playbooksData = {
      items: [
        {
          id: "1",
          name: "Marketing Workflow",
          description: "Email campaign",
          visibility: "private",
        },
        {
          id: "2",
          name: "Sales Process",
          description: "Lead qualification",
          visibility: "public",
        },
      ],
      pagination: { total_count: 2 },
    };

    mockUseApi
      .mockReturnValueOnce({ data: null, loading: true })
      .mockReturnValueOnce({ data: playbooksData, loading: false });

    renderWithRouter(<Dashboard />);

    expect(screen.getByText("Marketing Workflow")).toBeInTheDocument();
    expect(screen.getByText("Email campaign")).toBeInTheDocument();
    expect(screen.getByText("Sales Process")).toBeInTheDocument();
    expect(screen.getByText("Lead qualification")).toBeInTheDocument();
  });

  it("should show empty state message for playbooks", () => {
    const playbooksData = {
      items: [],
      pagination: { total_count: 0 },
    };

    mockUseApi
      .mockReturnValueOnce({ data: null, loading: true })
      .mockReturnValueOnce({ data: playbooksData, loading: false });

    renderWithRouter(<Dashboard />);

    expect(
      screen.getByText("No playbooks yet. Create your first workflow!"),
    ).toBeInTheDocument();
  });

  it('should render "View all" links', () => {
    mockUseApi
      .mockReturnValueOnce({ data: null, loading: false })
      .mockReturnValueOnce({ data: null, loading: false });

    renderWithRouter(<Dashboard />);

    expect(screen.getByText("View all collections →")).toBeInTheDocument();
    expect(screen.getByText("View all playbooks →")).toBeInTheDocument();
  });

  it("should not show admin section for non-admin users", () => {
    mockUseApi
      .mockReturnValueOnce({ data: null, loading: false })
      .mockReturnValueOnce({ data: null, loading: false });

    renderWithRouter(<Dashboard />);

    expect(screen.queryByText("Admin Dashboard")).not.toBeInTheDocument();
  });

  it("should show admin section for admin users", () => {
    mockAuthContext.isAdmin = true;

    mockUseApi
      .mockReturnValueOnce({ data: null, loading: false })
      .mockReturnValueOnce({ data: null, loading: false });

    renderWithRouter(<Dashboard />);

    expect(screen.getByText("Admin Dashboard")).toBeInTheDocument();
    expect(screen.getByText("System Management")).toBeInTheDocument();
    expect(screen.getByText("LLM Configuration")).toBeInTheDocument();
    expect(screen.getByText("Usage Monitoring")).toBeInTheDocument();
  });

  it("should render admin links with correct hrefs", () => {
    mockAuthContext.isAdmin = true;

    mockUseApi
      .mockReturnValueOnce({ data: null, loading: false })
      .mockReturnValueOnce({ data: null, loading: false });

    renderWithRouter(<Dashboard />);

    expect(screen.getByText("System Management").closest("a")).toHaveAttribute(
      "href",
      "/admin",
    );
    expect(screen.getByText("LLM Configuration").closest("a")).toHaveAttribute(
      "href",
      "/admin#llm",
    );
    expect(screen.getByText("Usage Monitoring").closest("a")).toHaveAttribute(
      "href",
      "/admin#usage",
    );
  });

  it("should render admin section descriptions", () => {
    mockAuthContext.isAdmin = true;

    mockUseApi
      .mockReturnValueOnce({ data: null, loading: false })
      .mockReturnValueOnce({ data: null, loading: false });

    renderWithRouter(<Dashboard />);

    expect(screen.getByText("Users, settings, health")).toBeInTheDocument();
    expect(screen.getByText("Providers, budgets, limits")).toBeInTheDocument();
    expect(screen.getByText("Costs, alerts, analytics")).toBeInTheDocument();
  });

  it("should display collection type badges", () => {
    const collectionsData = {
      items: [
        {
          id: "1",
          name: "Collection 1",
          description: "Desc 1",
          type: "prompt",
        },
        {
          id: "2",
          name: "Collection 2",
          description: "Desc 2",
          type: "template",
        },
      ],
      pagination: { total_count: 2 },
    };

    mockUseApi
      .mockReturnValueOnce({ data: collectionsData, loading: false })
      .mockReturnValueOnce({ data: null, loading: false });

    renderWithRouter(<Dashboard />);

    expect(screen.getByText("prompt")).toBeInTheDocument();
    expect(screen.getByText("template")).toBeInTheDocument();
  });

  it("should display playbook visibility badges", () => {
    const playbooksData = {
      items: [
        {
          id: "1",
          name: "Playbook 1",
          description: "Desc 1",
          visibility: "private",
        },
        {
          id: "2",
          name: "Playbook 2",
          description: "Desc 2",
          visibility: "public",
        },
      ],
      pagination: { total_count: 2 },
    };

    mockUseApi
      .mockReturnValueOnce({ data: null, loading: false })
      .mockReturnValueOnce({ data: playbooksData, loading: false });

    renderWithRouter(<Dashboard />);

    expect(screen.getByText("private")).toBeInTheDocument();
    expect(screen.getByText("public")).toBeInTheDocument();
  });

  afterEach(() => {
    // Reset admin status for clean tests
    mockAuthContext.isAdmin = false;
  });
});
