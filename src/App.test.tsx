import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import App, { AppWithoutRouter } from "./App";

// Mock the child components
jest.mock("@/components/auth/LoginPage", () => {
  return function MockLoginPage() {
    return <div data-testid="login-page">Login Page</div>;
  };
});

jest.mock("@/components/layout/NavBar", () => {
  return function MockNavBar() {
    return <div data-testid="navbar">Navigation Bar</div>;
  };
});

jest.mock("@/components/dashboard/Dashboard", () => {
  return function MockDashboard() {
    return <div data-testid="dashboard">Dashboard</div>;
  };
});

jest.mock("@/components/prompt/PromptBuilder", () => {
  return function MockPromptBuilder() {
    return <div data-testid="prompt-builder">Prompt Builder</div>;
  };
});

jest.mock("@/components/collections/CollectionsPage", () => {
  return function MockCollectionsPage() {
    return <div data-testid="collections-page">Collections Page</div>;
  };
});

jest.mock("@/components/playbooks/PlaybookBuilder", () => {
  return function MockPlaybookBuilder() {
    return <div data-testid="playbook-builder">Playbook Builder</div>;
  };
});

jest.mock("@/components/playbooks/PlaybookRunner", () => {
  return function MockPlaybookRunner() {
    return <div data-testid="playbook-runner">Playbook Runner</div>;
  };
});

jest.mock("@/components/integrations/IntegrationsPage", () => {
  return function MockIntegrationsPage() {
    return <div data-testid="integrations-page">Integrations Page</div>;
  };
});

jest.mock("@/components/admin/AdminPanel", () => {
  return function MockAdminPanel() {
    return <div data-testid="admin-panel">Admin Panel</div>;
  };
});

// Mock the MSALAuthProvider and useAuth hook
const mockUseAuth = jest.fn();
jest.mock("@/components/auth/MSALAuthProvider", () => ({
  AuthProvider: ({ children }: { children: any }) => <div>{children}</div>,
  useAuth: () => mockUseAuth(),
}));

// Mock the LoadingSpinner component
jest.mock("@/components/shared/LoadingSpinner", () => {
  return function MockLoadingSpinner() {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div
            className="animate-spin rounded-full h-32 w-32 border-b-2 border-indigo-600 mx-auto"
            data-testid="loading-spinner"
          />
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  };
});

describe("App", () => {
  const setupMockAuth = (authState: any) => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: false,
      isLoading: false,
      user: null,
      guestSession: null,
      isGuest: false,
      isAdmin: false,
      token: null,
      login: jest.fn(),
      loginAsGuest: jest.fn(),
      logout: jest.fn(),
      ...authState,
    });
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("should render loading state when authentication is loading", () => {
    setupMockAuth({
      isLoading: true,
    });

    render(<AppWithoutRouter />);

    expect(screen.getByText("Loading...")).toBeInTheDocument();
    // Fix: Use a more specific selector for the loading spinner
    expect(screen.getByTestId("loading-spinner")).toBeInTheDocument();
  });

  it("should render login page when not authenticated", async () => {
    setupMockAuth({
      isAuthenticated: false,
      isLoading: false,
    });

    render(<App />);

    // Wait for auth to complete and render login page
    await waitFor(
      () => {
        expect(screen.getByTestId("login-page")).toBeInTheDocument();
      },
      { timeout: 5000 },
    );

    expect(screen.queryByTestId("navbar")).not.toBeInTheDocument();
  });

  it("should render authenticated app with navbar and dashboard", async () => {
    setupMockAuth({
      isAuthenticated: true,
      isLoading: false,
      user: { id: "1", email: "test@example.com", role: "user" },
    });

    render(
      <MemoryRouter initialEntries={["/"]}>
        <AppWithoutRouter />
      </MemoryRouter>,
    );

    // Wait for auth to complete and render main app
    await waitFor(
      () => {
        expect(screen.getByTestId("navbar")).toBeInTheDocument();
      },
      { timeout: 5000 },
    );

    expect(screen.getByTestId("dashboard")).toBeInTheDocument();
  });

  it("should render prompt builder when navigating to /prompts/new", async () => {
    setupMockAuth({
      isAuthenticated: true,
      isLoading: false,
      user: { id: "1", email: "test@example.com", role: "user" },
    });

    render(
      <MemoryRouter initialEntries={["/prompts/new"]}>
        <AppWithoutRouter />
      </MemoryRouter>,
    );

    await waitFor(
      () => {
        expect(screen.getByTestId("navbar")).toBeInTheDocument();
      },
      { timeout: 5000 },
    );
    expect(screen.getByTestId("prompt-builder")).toBeInTheDocument();
  });

  it("should render collections page when navigating to /collections", async () => {
    setupMockAuth({
      isAuthenticated: true,
      isLoading: false,
      user: { id: "1", email: "test@example.com", role: "user" },
    });

    render(
      <MemoryRouter initialEntries={["/collections"]}>
        <AppWithoutRouter />
      </MemoryRouter>,
    );

    await waitFor(
      () => {
        expect(screen.getByTestId("navbar")).toBeInTheDocument();
      },
      { timeout: 5000 },
    );
    expect(screen.getByTestId("collections-page")).toBeInTheDocument();
  });

  it("should render playbook builder when navigating to /playbooks/new", async () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      user: { id: "1", email: "test@example.com", role: "user" },
      login: jest.fn(),
      logout: jest.fn(),
    });

    render(
      <MemoryRouter initialEntries={["/playbooks/new"]}>
        <AppWithoutRouter />
      </MemoryRouter>,
    );

    await waitFor(
      () => {
        expect(screen.getByTestId("navbar")).toBeInTheDocument();
      },
      { timeout: 3000 },
    );
    expect(screen.getByTestId("playbook-builder")).toBeInTheDocument();
  });

  it("should render playbook runner when navigating to /playbooks/123/run", async () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      user: { id: "1", email: "test@example.com", role: "user" },
      login: jest.fn(),
      logout: jest.fn(),
    });

    render(
      <MemoryRouter initialEntries={["/playbooks/123/run"]}>
        <AppWithoutRouter />
      </MemoryRouter>,
    );

    await waitFor(
      () => {
        expect(screen.getByTestId("navbar")).toBeInTheDocument();
      },
      { timeout: 3000 },
    );
    expect(screen.getByTestId("playbook-runner")).toBeInTheDocument();
  });

  it("should render integrations page when navigating to /integrations", async () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      user: { id: "1", email: "test@example.com", role: "user" },
      login: jest.fn(),
      logout: jest.fn(),
    });

    render(
      <MemoryRouter initialEntries={["/integrations"]}>
        <AppWithoutRouter />
      </MemoryRouter>,
    );

    await waitFor(
      () => {
        expect(screen.getByTestId("navbar")).toBeInTheDocument();
      },
      { timeout: 3000 },
    );
    expect(screen.getByTestId("integrations-page")).toBeInTheDocument();
  });

  it("should render admin panel when navigating to /admin", async () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      user: { id: "1", email: "test@example.com", role: "admin" },
      login: jest.fn(),
      logout: jest.fn(),
    });

    render(
      <MemoryRouter initialEntries={["/admin"]}>
        <AppWithoutRouter />
      </MemoryRouter>,
    );

    await waitFor(
      () => {
        expect(screen.getByTestId("navbar")).toBeInTheDocument();
      },
      { timeout: 3000 },
    );
    expect(screen.getByTestId("admin-panel")).toBeInTheDocument();
  });

  it("should render prompt builder with id when navigating to /prompts/123", async () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      user: { id: "1", email: "test@example.com", role: "user" },
      login: jest.fn(),
      logout: jest.fn(),
    });

    render(
      <MemoryRouter initialEntries={["/prompts/123"]}>
        <AppWithoutRouter />
      </MemoryRouter>,
    );

    await waitFor(
      () => {
        expect(screen.getByTestId("navbar")).toBeInTheDocument();
      },
      { timeout: 3000 },
    );
    expect(screen.getByTestId("prompt-builder")).toBeInTheDocument();
  });

  it("should render playbook builder with id when navigating to /playbooks/123", async () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      user: { id: "1", email: "test@example.com", role: "user" },
      login: jest.fn(),
      logout: jest.fn(),
    });

    render(
      <MemoryRouter initialEntries={["/playbooks/123"]}>
        <AppWithoutRouter />
      </MemoryRouter>,
    );

    await waitFor(
      () => {
        expect(screen.getByTestId("navbar")).toBeInTheDocument();
      },
      { timeout: 3000 },
    );
    expect(screen.getByTestId("playbook-builder")).toBeInTheDocument();
  });
});
