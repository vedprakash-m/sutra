import { render, screen, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import NavBar from "../NavBar";

// Mock the useAuth hook
const mockLogout = jest.fn();
const mockUseAuth = jest.fn();

jest.mock("@/components/auth/AuthProvider", () => ({
  useAuth: () => mockUseAuth(),
}));

// Helper function to render NavBar with router
const renderNavBar = (path = "/") => {
  return render(
    <MemoryRouter
      initialEntries={[path]}
      future={{
        v7_startTransition: true,
        v7_relativeSplatPath: true,
      }}
    >
      <NavBar />
    </MemoryRouter>,
  );
};

describe("NavBar", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("should return null when user is not authenticated", () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: false,
      user: null,
      logout: mockLogout,
      isAdmin: false,
    });

    const { container } = renderNavBar();
    expect(container.firstChild).toBeNull();
  });

  it("should render navigation when user is authenticated", () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      user: { name: "John Doe", email: "john@example.com" },
      logout: mockLogout,
      isAdmin: false,
    });

    renderNavBar();

    expect(screen.getByText("Sutra")).toBeInTheDocument();
    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(screen.getByText("Prompt Builder")).toBeInTheDocument();
    expect(screen.getByText("Collections")).toBeInTheDocument();
    expect(screen.getByText("Playbooks")).toBeInTheDocument();
    expect(screen.getByText("Integrations")).toBeInTheDocument();
  });

  it("should show user name when authenticated", () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      user: { name: "John Doe", email: "john@example.com" },
      logout: mockLogout,
      isAdmin: false,
    });

    renderNavBar();

    expect(screen.getByText("John Doe")).toBeInTheDocument();
  });

  it("should show Sign out button when authenticated", () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      user: { name: "John Doe", email: "john@example.com" },
      logout: mockLogout,
      isAdmin: false,
    });

    renderNavBar();

    expect(screen.getByText("Sign out")).toBeInTheDocument();
  });

  it("should call logout when Sign out button is clicked", () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      user: { name: "John Doe", email: "john@example.com" },
      logout: mockLogout,
      isAdmin: false,
    });

    renderNavBar();

    const signOutButton = screen.getByText("Sign out");
    fireEvent.click(signOutButton);

    expect(mockLogout).toHaveBeenCalledTimes(1);
  });

  it("should show Admin link when user is admin", () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      user: { name: "Admin User", email: "admin@example.com" },
      logout: mockLogout,
      isAdmin: true,
    });

    renderNavBar();

    expect(screen.getByText("Admin")).toBeInTheDocument();
  });

  it("should not show Admin link when user is not admin", () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      user: { name: "Regular User", email: "user@example.com" },
      logout: mockLogout,
      isAdmin: false,
    });

    renderNavBar();

    expect(screen.queryByText("Admin")).not.toBeInTheDocument();
  });

  it("should highlight Dashboard link when on home page", () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      user: { name: "John Doe", email: "john@example.com" },
      logout: mockLogout,
      isAdmin: false,
    });

    renderNavBar("/");

    const dashboardLink = screen.getByText("Dashboard");
    expect(dashboardLink).toHaveClass("border-indigo-500", "text-gray-900");
  });

  it("should highlight Prompt Builder link when on prompts page", () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      user: { name: "John Doe", email: "john@example.com" },
      logout: mockLogout,
      isAdmin: false,
    });

    renderNavBar("/prompts/new");

    const promptBuilderLink = screen.getByText("Prompt Builder");
    expect(promptBuilderLink).toHaveClass("border-indigo-500", "text-gray-900");
  });

  it("should highlight Collections link when on collections page", () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      user: { name: "John Doe", email: "john@example.com" },
      logout: mockLogout,
      isAdmin: false,
    });

    renderNavBar("/collections");

    const collectionsLink = screen.getByText("Collections");
    expect(collectionsLink).toHaveClass("border-indigo-500", "text-gray-900");
  });

  it("should highlight Playbooks link when on playbooks page", () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      user: { name: "John Doe", email: "john@example.com" },
      logout: mockLogout,
      isAdmin: false,
    });

    renderNavBar("/playbooks/new");

    const playbooksLink = screen.getByText("Playbooks");
    expect(playbooksLink).toHaveClass("border-indigo-500", "text-gray-900");
  });

  it("should highlight Integrations link when on integrations page", () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      user: { name: "John Doe", email: "john@example.com" },
      logout: mockLogout,
      isAdmin: false,
    });

    renderNavBar("/integrations");

    const integrationsLink = screen.getByText("Integrations");
    expect(integrationsLink).toHaveClass("border-indigo-500", "text-gray-900");
  });

  it("should highlight Admin link when on admin page", () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      user: { name: "Admin User", email: "admin@example.com" },
      logout: mockLogout,
      isAdmin: true,
    });

    renderNavBar("/admin");

    const adminLink = screen.getByText("Admin");
    expect(adminLink).toHaveClass("border-indigo-500", "text-gray-900");
  });

  it("should render all navigation links as Link components with correct href", () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      user: { name: "John Doe", email: "john@example.com" },
      logout: mockLogout,
      isAdmin: true,
    });

    renderNavBar();

    const dashboardLink = screen.getByText("Dashboard").closest("a");
    const promptBuilderLink = screen.getByText("Prompt Builder").closest("a");
    const collectionsLink = screen.getByText("Collections").closest("a");
    const playbooksLink = screen.getByText("Playbooks").closest("a");
    const integrationsLink = screen.getByText("Integrations").closest("a");
    const adminLink = screen.getByText("Admin").closest("a");

    expect(dashboardLink).toHaveAttribute("href", "/");
    expect(promptBuilderLink).toHaveAttribute("href", "/prompts/new");
    expect(collectionsLink).toHaveAttribute("href", "/collections");
    expect(playbooksLink).toHaveAttribute("href", "/playbooks/new");
    expect(integrationsLink).toHaveAttribute("href", "/integrations");
    expect(adminLink).toHaveAttribute("href", "/admin");
  });

  it("should handle user without name gracefully", () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      user: { email: "user@example.com" }, // No name property
      logout: mockLogout,
      isAdmin: false,
    });

    expect(() => renderNavBar()).not.toThrow();
  });
});
