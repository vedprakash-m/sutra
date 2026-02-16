import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import ForgeProjectDetails from "../ForgeProjectDetails";
import { forgeApi } from "@/services/api";

jest.mock("@/services/api", () => {
  const actual = jest.requireActual("@/services/__mocks__/api");
  return actual;
});

jest.mock("../LLMProviderSelector", () => ({
  LLMProviderSelector: () => <div>LLM Selector Mock</div>,
}));

jest.mock("../ForgeExportButton", () => ({
  ForgeExportButton: ({ projectId }: { projectId: string }) => (
    <div>Export Mock {projectId}</div>
  ),
}));

jest.mock("../IdeaRefinementStage", () => ({
  __esModule: true,
  default: ({
    selectedLLM,
    onStageComplete,
  }: {
    selectedLLM: string;
    onStageComplete: (data: any) => void;
  }) => (
    <div>
      <div>Idea Stage Mock {selectedLLM}</div>
      <button onClick={() => onStageComplete({ idea: "done" })}>
        Complete Idea Stage
      </button>
    </div>
  ),
}));

jest.mock("../PRDGeneration", () => ({
  __esModule: true,
  default: () => <div>PRD Stage Mock</div>,
}));

jest.mock("../UXRequirementsStage", () => ({
  __esModule: true,
  default: () => <div>UX Stage Mock</div>,
}));

jest.mock("../TechnicalAnalysisStage", () => ({
  __esModule: true,
  default: () => <div>Technical Stage Mock</div>,
}));

jest.mock("../ImplementationPlaybookStage", () => ({
  __esModule: true,
  default: () => <div>Playbook Stage Mock</div>,
}));

describe("ForgeProjectDetails", () => {
  const advanceStageMock = forgeApi.advanceStage as jest.Mock;

  const project = {
    id: "proj-1",
    name: "Project Atlas",
    description: "A systematic delivery project",
    currentStage: "idea_refinement" as const,
    status: "active" as const,
    priority: "high" as const,
    progressPercentage: 40,
    createdAt: "2026-01-01T00:00:00Z",
    updatedAt: "2026-01-10T00:00:00Z",
    tags: ["ai", "forge"],
    collaboratorsCount: 3,
    artifactsCount: 5,
    ownerId: "user-1",
  };

  beforeEach(() => {
    jest.clearAllMocks();
    advanceStageMock.mockResolvedValue({});
  });

  it("renders project metadata and invokes back action", () => {
    const onBackToList = jest.fn();

    render(
      <ForgeProjectDetails
        project={project}
        onBackToList={onBackToList}
        onProjectUpdate={jest.fn()}
      />,
    );

    expect(screen.getByText("Project Atlas")).toBeInTheDocument();
    expect(screen.getByText("A systematic delivery project")).toBeInTheDocument();
    expect(screen.getByText("HIGH")).toBeInTheDocument();
    expect(screen.getByText("ACTIVE")).toBeInTheDocument();
    expect(screen.getByText("ai")).toBeInTheDocument();
    expect(screen.getByText("forge")).toBeInTheDocument();

    const backButton = document.querySelector("button") as HTMLButtonElement;
    fireEvent.click(backButton);
    expect(onBackToList).toHaveBeenCalled();
  });

  it("advances stage from header action", async () => {
    const onProjectUpdate = jest.fn();

    render(
      <ForgeProjectDetails
        project={project}
        onBackToList={jest.fn()}
        onProjectUpdate={onProjectUpdate}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /Advance to PRD Generation/i }));

    await waitFor(() => {
      expect(advanceStageMock).toHaveBeenCalledWith("proj-1", "prd_generation");
      expect(onProjectUpdate).toHaveBeenCalled();
    });

    const updated = onProjectUpdate.mock.calls[0][0];
    expect(updated.currentStage).toBe("prd_generation");
  });

  it("renders current stage work surface and advances via stage completion", async () => {
    const onProjectUpdate = jest.fn();

    render(
      <ForgeProjectDetails
        project={project}
        onBackToList={jest.fn()}
        onProjectUpdate={onProjectUpdate}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Work on Stage" }));

    expect(screen.getByText("LLM Selector Mock")).toBeInTheDocument();
    expect(screen.getByText("Idea Stage Mock gpt-4o")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Complete Idea Stage" }));

    await waitFor(() => {
      expect(advanceStageMock).toHaveBeenCalledWith("proj-1", "prd_generation");
      expect(onProjectUpdate).toHaveBeenCalled();
    });
  });

  it("switches to artifacts, collaboration, and analytics tabs", () => {
    render(
      <ForgeProjectDetails
        project={project}
        onBackToList={jest.fn()}
        onProjectUpdate={jest.fn()}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Artifacts (5)" }));
    expect(screen.getByText("Project Artifacts")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Team (3)" }));
    expect(screen.getByText("Team Collaboration")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Analytics" }));
    expect(screen.getByText("Project Analytics")).toBeInTheDocument();
  });

  it("switches from overview to work using start button", () => {
    render(
      <ForgeProjectDetails
        project={project}
        onBackToList={jest.fn()}
        onProjectUpdate={jest.fn()}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /Start Working on Idea Refinement/i }));
    expect(screen.getByText("Idea Stage Mock gpt-4o")).toBeInTheDocument();
  });

  it("renders PRD stage component when current stage is prd_generation", () => {
    render(
      <ForgeProjectDetails
        project={{ ...project, currentStage: "prd_generation" }}
        onBackToList={jest.fn()}
        onProjectUpdate={jest.fn()}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Work on Stage" }));
    expect(screen.getByText("PRD Stage Mock")).toBeInTheDocument();
  });

  it("renders UX stage component when current stage is ux_requirements", () => {
    render(
      <ForgeProjectDetails
        project={{ ...project, currentStage: "ux_requirements" }}
        onBackToList={jest.fn()}
        onProjectUpdate={jest.fn()}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Work on Stage" }));
    expect(screen.getByText("UX Stage Mock")).toBeInTheDocument();
  });

  it("renders Technical stage component when current stage is technical_analysis", () => {
    render(
      <ForgeProjectDetails
        project={{ ...project, currentStage: "technical_analysis" }}
        onBackToList={jest.fn()}
        onProjectUpdate={jest.fn()}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Work on Stage" }));
    expect(screen.getByText("Technical Stage Mock")).toBeInTheDocument();
  });

  it("renders Playbook stage component and no advance button on final stage", () => {
    render(
      <ForgeProjectDetails
        project={{ ...project, currentStage: "implementation_playbook" }}
        onBackToList={jest.fn()}
        onProjectUpdate={jest.fn()}
      />,
    );

    expect(
      screen.queryByRole("button", { name: /Advance to/i }),
    ).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Work on Stage" }));
    expect(screen.getByText("Playbook Stage Mock")).toBeInTheDocument();
  });
});
