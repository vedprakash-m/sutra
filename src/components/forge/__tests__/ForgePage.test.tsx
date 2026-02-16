import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import ForgePage from "../ForgePage";
import { forgeApi } from "@/services/api";

jest.mock("@/services/api", () => {
  const actual = jest.requireActual("@/services/__mocks__/api");
  return actual;
});

const navigateMock = jest.fn();
const useParamsMock = jest.fn();
const useSearchParamsMock = jest.fn();

jest.mock("react-router-dom", () => {
  const actual = jest.requireActual("react-router-dom");
  return {
    ...actual,
    useNavigate: () => navigateMock,
    useParams: () => useParamsMock(),
    useSearchParams: () => useSearchParamsMock(),
  };
});

jest.mock("../ForgeProjectCreator", () => ({
  __esModule: true,
  default: ({ onProjectCreated, onCancel }: { onProjectCreated: (project: any) => void; onCancel: () => void }) => (
    <div>
      <button onClick={() => onProjectCreated({
        id: "created-project",
        name: "Created",
        description: "Created project",
        currentStage: "idea_refinement",
        status: "draft",
        priority: "medium",
        progressPercentage: 0,
        createdAt: "2026-01-01T00:00:00Z",
        updatedAt: "2026-01-01T00:00:00Z",
        tags: [],
        collaboratorsCount: 1,
        artifactsCount: 0,
        ownerId: "user-1",
      })}>
        Create Mock Project
      </button>
      <button onClick={onCancel}>Cancel Create</button>
    </div>
  ),
}));

jest.mock("../ForgeProjectCard", () => ({
  __esModule: true,
  default: ({ project, onSelect }: { project: any; onSelect: (project: any) => void }) => (
    <button onClick={() => onSelect(project)}>Select {project.name}</button>
  ),
}));

jest.mock("../ForgeProjectDetails", () => ({
  __esModule: true,
  default: ({ project, onBackToList }: { project: any; onBackToList: () => void }) => (
    <div>
      <div>Details: {project.name}</div>
      <button onClick={onBackToList}>Back To List</button>
    </div>
  ),
}));

jest.mock("@heroicons/react/24/outline", () => ({
  PlusIcon: () => <span data-testid="plus-icon" />,
  FolderIcon: () => <span data-testid="folder-icon" />,
}));

describe("ForgePage", () => {
  const listProjectsMock = forgeApi.listProjects as jest.Mock;
  const getProjectMock = forgeApi.getProject as jest.Mock;

  const projects = [
    {
      id: "project-1",
      name: "Alpha",
      description: "First project",
      currentStage: "idea_refinement",
      status: "active",
      priority: "high",
      progressPercentage: 40,
      createdAt: "2026-01-01T00:00:00Z",
      updatedAt: "2026-01-10T00:00:00Z",
      tags: ["alpha"],
      collaboratorsCount: 2,
      artifactsCount: 1,
      ownerId: "user-1",
    },
    {
      id: "project-2",
      name: "Beta",
      description: "Second project",
      currentStage: "technical_analysis",
      status: "completed",
      priority: "medium",
      progressPercentage: 100,
      createdAt: "2026-01-02T00:00:00Z",
      updatedAt: "2026-01-12T00:00:00Z",
      tags: ["beta", "forge"],
      collaboratorsCount: 1,
      artifactsCount: 4,
      ownerId: "user-1",
    },
  ];

  beforeEach(() => {
    jest.clearAllMocks();
    useParamsMock.mockReturnValue({ projectId: undefined });
    useSearchParamsMock.mockReturnValue([new URLSearchParams(), jest.fn()]);
    listProjectsMock.mockResolvedValue({ projects, total: 2 });
    getProjectMock.mockResolvedValue(projects[0]);
  });

  it("loads and renders projects list", async () => {
    render(<ForgePage />);

    await waitFor(() => {
      expect(listProjectsMock).toHaveBeenCalled();
    });

    expect(screen.getByRole("button", { name: /Select Alpha/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Select Beta/i })).toBeInTheDocument();
    expect(screen.getByText("Project Overview")).toBeInTheDocument();
  });

  it("shows empty state when no projects", async () => {
    listProjectsMock.mockResolvedValueOnce({ projects: [], total: 0 });
    render(<ForgePage />);

    await waitFor(() => {
      expect(screen.getByText("No projects yet")).toBeInTheDocument();
    });

    expect(screen.getByText("Create Your First Project")).toBeInTheDocument();
  });

  it("navigates to create view when New Project is clicked", async () => {
    render(<ForgePage />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "New Project" })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "New Project" }));
    expect(navigateMock).toHaveBeenCalledWith("/forge?view=create");
    expect(screen.getByRole("button", { name: "Create Mock Project" })).toBeInTheDocument();
  });

  it("opens details when project card is selected", async () => {
    render(<ForgePage />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /Select Alpha/i })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: /Select Alpha/i }));
    expect(navigateMock).toHaveBeenCalledWith("/forge/project-1");
    expect(screen.getByText("Details: Alpha")).toBeInTheDocument();
  });

  it("loads details view when projectId is present in route", async () => {
    useParamsMock.mockReturnValue({ projectId: "project-1" });
    render(<ForgePage />);

    await waitFor(() => {
      expect(getProjectMock).toHaveBeenCalledWith("project-1");
    });

    expect(screen.getByText("Details: Alpha")).toBeInTheDocument();
  });

  it("opens create view when search param view=create is set", async () => {
    useSearchParamsMock.mockReturnValue([new URLSearchParams("view=create"), jest.fn()]);
    render(<ForgePage />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Create Mock Project" })).toBeInTheDocument();
    });
  });

  it("filters projects by search term", async () => {
    render(<ForgePage />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /Select Alpha/i })).toBeInTheDocument();
    });

    fireEvent.change(screen.getByPlaceholderText("Search projects..."), {
      target: { value: "beta" },
    });

    expect(screen.queryByRole("button", { name: /Select Alpha/i })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Select Beta/i })).toBeInTheDocument();
  });

  it("handles project list API error gracefully", async () => {
    const errorSpy = jest.spyOn(console, "error").mockImplementation(() => {});
    listProjectsMock.mockRejectedValueOnce(new Error("network"));

    render(<ForgePage />);

    await waitFor(() => {
      expect(errorSpy).toHaveBeenCalled();
      expect(screen.getByText("No projects yet")).toBeInTheDocument();
    });

    errorSpy.mockRestore();
  });
});
