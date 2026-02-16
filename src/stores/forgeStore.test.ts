import { forgeApi } from "@/services/api";
import { useForgeStore } from "./forgeStore";

jest.mock("@/services/api", () => {
  const actual = jest.requireActual("@/services/__mocks__/api");
  return actual;
});

const SAMPLE_PROJECT = {
  id: "project-1",
  name: "Forge Project",
  description: "desc",
  currentStage: "idea_refinement" as const,
  status: "active" as const,
  priority: "medium" as const,
  progressPercentage: 10,
  createdAt: "2026-01-01T00:00:00Z",
  updatedAt: "2026-01-01T00:00:00Z",
  tags: [],
  collaboratorsCount: 1,
  artifactsCount: 0,
  ownerId: "user-1",
};

describe("forgeStore", () => {
  const listProjectsMock = forgeApi.listProjects as jest.Mock;
  const getProjectMock = forgeApi.getProject as jest.Mock;
  const advanceStageMock = forgeApi.advanceStage as jest.Mock;
  const createProjectMock = forgeApi.createProject as jest.Mock;
  const deleteProjectMock = forgeApi.deleteProject as jest.Mock;

  beforeEach(() => {
    jest.clearAllMocks();
    sessionStorage.clear();
    useForgeStore.setState(useForgeStore.getInitialState(), true);
  });

  it("fetchProjects loads projects into state", async () => {
    listProjectsMock.mockResolvedValueOnce({
      projects: [SAMPLE_PROJECT],
      total: 1,
    });

    await useForgeStore.getState().fetchProjects();

    expect(useForgeStore.getState().projects).toHaveLength(1);
    expect(useForgeStore.getState().projects[0].id).toBe("project-1");
    expect(useForgeStore.getState().isLoadingProjects).toBe(false);
  });

  it("fetchProjects sets error on failure", async () => {
    listProjectsMock.mockRejectedValueOnce(new Error("fetch failed"));

    await useForgeStore.getState().fetchProjects();

    expect(useForgeStore.getState().error).toBe("fetch failed");
    expect(useForgeStore.getState().isLoadingProjects).toBe(false);
  });

  it("setCurrentProject loads current project", async () => {
    getProjectMock.mockResolvedValueOnce(SAMPLE_PROJECT);

    await useForgeStore.getState().setCurrentProject("project-1");

    expect(useForgeStore.getState().currentProjectId).toBe("project-1");
    expect(useForgeStore.getState().currentProject?.name).toBe("Forge Project");
  });

  it("clearCurrentProject resets current project context", async () => {
    getProjectMock.mockResolvedValueOnce(SAMPLE_PROJECT);

    await useForgeStore.getState().setCurrentProject("project-1");
    useForgeStore.getState().clearCurrentProject();

    expect(useForgeStore.getState().currentProjectId).toBeNull();
    expect(useForgeStore.getState().currentProject).toBeNull();
  });

  it("updateStageData stores data by project and stage", () => {
    useForgeStore
      .getState()
      .updateStageData("project-1", "idea_refinement", { value: 123 });

    expect(
      useForgeStore.getState().stageData["project-1"]?.idea_refinement,
    ).toEqual({ value: 123 });
  });

  it("updateQuality stores quality by project and stage", () => {
    useForgeStore.getState().updateQuality("project-1", "idea_refinement", {
      overallScore: 80,
      dimensionScores: { clarity: 80 },
      qualityGateStatus: "PROCEED_EXCELLENT",
      confidenceLevel: 0.9,
    });

    expect(
      useForgeStore.getState().qualityScores["project-1"]?.idea_refinement
        ?.overallScore,
    ).toBe(80);
  });

  it("canAdvanceStage returns false when no quality exists", () => {
    expect(
      useForgeStore.getState().canAdvanceStage("project-1", "idea_refinement"),
    ).toBe(false);
  });

  it("canAdvanceStage validates stage threshold", () => {
    useForgeStore.getState().updateQuality("project-1", "idea_refinement", {
      overallScore: 74,
      dimensionScores: {},
      qualityGateStatus: "BLOCK",
      confidenceLevel: 0.6,
    });
    expect(
      useForgeStore.getState().canAdvanceStage("project-1", "idea_refinement"),
    ).toBe(false);

    useForgeStore.getState().updateQuality("project-1", "idea_refinement", {
      overallScore: 75,
      dimensionScores: {},
      qualityGateStatus: "PROCEED_WITH_CAUTION",
      confidenceLevel: 0.7,
    });
    expect(
      useForgeStore.getState().canAdvanceStage("project-1", "idea_refinement"),
    ).toBe(true);
  });

  it("advanceStage blocks when threshold is not met", async () => {
    useForgeStore.setState({
      currentProjectId: "project-1",
      currentProject: SAMPLE_PROJECT,
      projects: [SAMPLE_PROJECT],
      qualityScores: {
        "project-1": {
          idea_refinement: {
            overallScore: 60,
            dimensionScores: {},
            qualityGateStatus: "BLOCK",
            confidenceLevel: 0.5,
          },
        },
      },
    });

    await useForgeStore.getState().advanceStage("project-1");

    expect(advanceStageMock).not.toHaveBeenCalled();
    expect(useForgeStore.getState().error).toContain(
      "Quality threshold not met",
    );
  });

  it("advanceStage advances when threshold is met", async () => {
    advanceStageMock.mockResolvedValueOnce({});

    useForgeStore.setState({
      currentProjectId: "project-1",
      currentProject: SAMPLE_PROJECT,
      projects: [SAMPLE_PROJECT],
      qualityScores: {
        "project-1": {
          idea_refinement: {
            overallScore: 80,
            dimensionScores: {},
            qualityGateStatus: "PROCEED_EXCELLENT",
            confidenceLevel: 0.9,
          },
        },
      },
    });

    await useForgeStore.getState().advanceStage("project-1");

    expect(advanceStageMock).toHaveBeenCalledWith(
      "project-1",
      "prd_generation",
    );
    expect(useForgeStore.getState().currentProject?.currentStage).toBe(
      "prd_generation",
    );
  });

  it("createProject prepends project to projects list", async () => {
    createProjectMock.mockResolvedValueOnce(SAMPLE_PROJECT);

    await useForgeStore.getState().createProject({
      name: "Forge Project",
      description: "desc",
      priority: "medium",
    });

    expect(useForgeStore.getState().projects[0].id).toBe("project-1");
  });

  it("deleteProject removes project from store", async () => {
    deleteProjectMock.mockResolvedValueOnce(undefined);

    useForgeStore.setState({
      projects: [SAMPLE_PROJECT],
      currentProjectId: "project-1",
      currentProject: SAMPLE_PROJECT,
    });

    await useForgeStore.getState().deleteProject("project-1");

    expect(useForgeStore.getState().projects).toHaveLength(0);
    expect(useForgeStore.getState().currentProjectId).toBeNull();
    expect(useForgeStore.getState().currentProject).toBeNull();
  });

  it("setLLMProvider updates provider and default model", () => {
    useForgeStore.getState().setLLMProvider("anthropic");
    expect(useForgeStore.getState().selectedProvider).toBe("anthropic");
    expect(useForgeStore.getState().selectedModel).toBe("claude-3.5-sonnet");
  });

  it("setLLMProvider keeps explicit model when provided", () => {
    useForgeStore.getState().setLLMProvider("google", "gemini-1.5-flash");
    expect(useForgeStore.getState().selectedProvider).toBe("google");
    expect(useForgeStore.getState().selectedModel).toBe("gemini-1.5-flash");
  });

  it("clearError resets error state", () => {
    useForgeStore.setState({ error: "some error" });

    useForgeStore.getState().clearError();
    expect(useForgeStore.getState().error).toBeNull();
  });
});
