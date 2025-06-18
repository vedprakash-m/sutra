import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import App from "./App";

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

// Mock the AuthProvider and useAuth hook
const mockUseAuth = jest.fn();
jest.mock("@/components/auth/AuthProvider", () => ({
  AuthProvider: ({ children }: { children: any }) => <div>{children}</div>,
  useAuth: () => mockUseAuth(),
}));

describe("App", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("should render loading state when authentication is loading", () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: false,
      isLoading: true,
      user: null,
      login: jest.fn(),
      logout: jest.fn(),
    });

    render(<App />);

    expect(screen.getByText("Loading...")).toBeInTheDocument();
    expect(screen.getByRole("status", { hidden: true })).toBeInTheDocument();
  });

  it("should render login page when not authenticated", () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: false,
      isLoading: false,
      user: null,
      login: jest.fn(),
      logout: jest.fn(),
    });

    render(<App />);

    expect(screen.getByTestId("login-page")).toBeInTheDocument();
    expect(screen.queryByTestId("navbar")).not.toBeInTheDocument();
  });

  it("should render authenticated app with navbar and dashboard", () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      user: { id: "1", email: "test@example.com", role: "user" },
      login: jest.fn(),
      logout: jest.fn(),
    });

    render(
      <MemoryRouter initialEntries={["/"]}>
        <App />
      </MemoryRouter>
    );

    expect(screen.getByTestId("navbar")).toBeInTheDocument();
    expect(screen.getByTestId("dashboard")).toBeInTheDocument();
  });

  it("should render prompt builder when navigating to /prompts/new", () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      user: { id: "1", email: "test@example.com", role: "user" },
      login: jest.fn(),
      logout: jest.fn(),
    });

    render(
      <MemoryRouter initialEntries={["/prompts/new"]}>
        <App />
      </MemoryRouter>
    );

    expect(screen.getByTestId("navbar")).toBeInTheDocument();
    expect(screen.getByTestId("prompt-builder")).toBeInTheDocument();
  });

  it("should render collections page when navigating to /collections", () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      user: { id: "1", email: "test@example.com", role: "user" },
      login: jest.fn(),
      logout: jest.fn(),
    });

    render(
      <MemoryRouter initialEntries={["/collections"]}>
        <App />
      </MemoryRouter>
    );

    expect(screen.getByTestId("navbar")).toBeInTheDocument();
    expect(screen.getByTestId("collections-page")).toBeInTheDocument();
  });

  it("should render playbook builder when navigating to /playbooks/new", () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      user: { id: "1", email: "test@example.com", role: "user" },
      login: jest.fn(),
      logout: jest.fn(),
    });

    render(
      <MemoryRouter initialEntries={["/playbooks/new"]}>
        <App />
      </MemoryRouter>
    );

    expect(screen.getByTestId("navbar")).toBeInTheDocument();
    expect(screen.getByTestId("playbook-builder")).toBeInTheDocument();
  });

  it("should render playbook runner when navigating to /playbooks/123/run", () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      user: { id: "1", email: "test@example.com", role: "user" },
      login: jest.fn(),
      logout: jest.fn(),
    });

    render(
      <MemoryRouter initialEntries={["/playbooks/123/run"]}>
        <App />
      </MemoryRouter>
    );

    expect(screen.getByTestId("navbar")).toBeInTheDocument();
    expect(screen.getByTestId("playbook-runner")).toBeInTheDocument();
  });

  it("should render integrations page when navigating to /integrations", () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      user: { id: "1", email: "test@example.com", role: "user" },
      login: jest.fn(),
      logout: jest.fn(),
    });

    render(
      <MemoryRouter initialEntries={["/integrations"]}>
        <App />
      </MemoryRouter>
    );

    expect(screen.getByTestId("navbar")).toBeInTheDocument();
    expect(screen.getByTestId("integrations-page")).toBeInTheDocument();
  });

  it("should render admin panel when navigating to /admin", () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      user: { id: "1", email: "test@example.com", role: "admin" },
      login: jest.fn(),
      logout: jest.fn(),
    });

    render(
      <MemoryRouter initialEntries={["/admin"]}>
        <App />
      </MemoryRouter>
    );

    expect(screen.getByTestId("navbar")).toBeInTheDocument();
    expect(screen.getByTestId("admin-panel")).toBeInTheDocument();
  });

  it("should render prompt builder with id when navigating to /prompts/123", () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      user: { id: "1", email: "test@example.com", role: "user" },
      login: jest.fn(),
      logout: jest.fn(),
    });

    render(
      <MemoryRouter initialEntries={["/prompts/123"]}>
        <App />
      </MemoryRouter>
    );

    expect(screen.getByTestId("navbar")).toBeInTheDocument();
    expect(screen.getByTestId("prompt-builder")).toBeInTheDocument();
  });

  it("should render playbook builder with id when navigating to /playbooks/123", () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      user: { id: "1", email: "test@example.com", role: "user" },
      login: jest.fn(),
      logout: jest.fn(),
    });

    render(
      <MemoryRouter initialEntries={["/playbooks/123"]}>
        <App />
      </MemoryRouter>
    );

    expect(screen.getByTestId("navbar")).toBeInTheDocument();
    expect(screen.getByTestId("playbook-builder")).toBeInTheDocument();
  });
});
