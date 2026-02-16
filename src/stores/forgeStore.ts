/**
 * Forge State Management Store
 * Manages Forge project state, stage data, and quality assessments using Zustand.
 * Provides centralized state that persists across component navigation.
 */
import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import { forgeApi } from "@/services/api";
import type { LLMProviderName } from "@/types/forge";

// ============================================================================
// Types
// ============================================================================

export type ForgeStageId =
  | "idea_refinement"
  | "prd_generation"
  | "ux_requirements"
  | "technical_analysis"
  | "implementation_playbook";

export type ProjectStatus =
  | "draft"
  | "active"
  | "on_hold"
  | "completed"
  | "archived"
  | "cancelled";

export type ProjectPriority = "low" | "medium" | "high" | "critical";

export interface ForgeProject {
  id: string;
  name: string;
  description: string;
  currentStage: ForgeStageId;
  status: ProjectStatus;
  priority: ProjectPriority;
  progressPercentage: number;
  createdAt: string;
  updatedAt: string;
  tags: string[];
  collaboratorsCount: number;
  artifactsCount: number;
  ownerId: string;
}

export interface QualityAssessment {
  overallScore: number;
  dimensionScores: Record<string, number>;
  qualityGateStatus: "BLOCK" | "PROCEED_WITH_CAUTION" | "PROCEED_EXCELLENT";
  confidenceLevel: number;
}

/** Quality thresholds per stage (from spec) */
export const QUALITY_THRESHOLDS: Record<ForgeStageId, number> = {
  idea_refinement: 75,
  prd_generation: 80,
  ux_requirements: 82,
  technical_analysis: 85,
  implementation_playbook: 88,
};

// ============================================================================
// Store Interface
// ============================================================================

interface ForgeState {
  // Project list
  projects: ForgeProject[];
  isLoadingProjects: boolean;

  // Current project context
  currentProjectId: string | null;
  currentProject: ForgeProject | null;

  // Stage data (keyed by projectId, then stageId)
  stageData: Record<string, Partial<Record<ForgeStageId, any>>>;

  // Quality assessments (keyed by projectId, then stageId)
  qualityScores: Record<string, Partial<Record<ForgeStageId, QualityAssessment | null>>>;

  // Loading/error state
  isLoading: boolean;
  error: string | null;

  // LLM provider preferences
  selectedProvider: LLMProviderName;
  selectedModel: string;

  // Actions
  fetchProjects: () => Promise<void>;
  setCurrentProject: (projectId: string) => Promise<void>;
  clearCurrentProject: () => void;
  updateStageData: (
    projectId: string,
    stageId: ForgeStageId,
    data: any,
  ) => void;
  updateQuality: (
    projectId: string,
    stageId: ForgeStageId,
    quality: QualityAssessment,
  ) => void;
  canAdvanceStage: (projectId: string, stageId: ForgeStageId) => boolean;
  advanceStage: (projectId: string) => Promise<void>;
  createProject: (data: {
    name: string;
    description: string;
    priority: ProjectPriority;
    tags?: string[];
  }) => Promise<ForgeProject>;
  deleteProject: (projectId: string) => Promise<void>;
  setLLMProvider: (provider: LLMProviderName, model?: string) => void;
  clearError: () => void;
}

// ============================================================================
// Store Implementation
// ============================================================================

export const useForgeStore = create<ForgeState>()(
  persist(
    (set, get) => ({
      // Initial state
      projects: [],
      isLoadingProjects: false,
      currentProjectId: null,
      currentProject: null,
      stageData: {},
      qualityScores: {},
      isLoading: false,
      error: null,
      selectedProvider: "openai" as LLMProviderName,
      selectedModel: "gpt-4o",

      // Fetch all projects
      fetchProjects: async () => {
        set({ isLoadingProjects: true, error: null });
        try {
          const response = await forgeApi.listProjects();
          set({
            projects: (response as any)?.projects || [],
            isLoadingProjects: false,
          });
        } catch (error) {
          set({
            error:
              error instanceof Error
                ? error.message
                : "Failed to fetch projects",
            isLoadingProjects: false,
          });
        }
      },

      // Set current project (fetch details from API)
      setCurrentProject: async (projectId: string) => {
        set({ isLoading: true, error: null });
        try {
          const project = await forgeApi.getProject(projectId);
          set({
            currentProjectId: projectId,
            currentProject: project as any,
            isLoading: false,
          });
        } catch (error) {
          set({
            error:
              error instanceof Error
                ? error.message
                : "Failed to fetch project",
            isLoading: false,
          });
        }
      },

      clearCurrentProject: () => {
        set({ currentProjectId: null, currentProject: null });
      },

      // Update stage data locally (persisted via Zustand persist middleware)
      updateStageData: (projectId, stageId, data) => {
        set((state) => ({
          stageData: {
            ...state.stageData,
            [projectId]: {
              ...(state.stageData[projectId] || {}),
              [stageId]: data,
            },
          },
        }));
      },

      // Update quality score for a stage
      updateQuality: (projectId, stageId, quality) => {
        set((state) => ({
          qualityScores: {
            ...state.qualityScores,
            [projectId]: {
              ...(state.qualityScores[projectId] || {}),
              [stageId]: quality,
            },
          },
        }));
      },

      // Check if stage quality meets threshold for advancement
      canAdvanceStage: (projectId, stageId) => {
        const { qualityScores } = get();
        const quality = qualityScores[projectId]?.[stageId];
        if (!quality) return false;
        return quality.overallScore >= QUALITY_THRESHOLDS[stageId];
      },

      // Advance to next stage (with quality gate enforcement)
      advanceStage: async (projectId) => {
        const { currentProject, qualityScores } = get();
        if (!currentProject) return;

        const currentStage = currentProject.currentStage;
        const quality = qualityScores[projectId]?.[currentStage];

        if (
          !quality ||
          quality.overallScore < QUALITY_THRESHOLDS[currentStage]
        ) {
          set({
            error: `Quality threshold not met: ${quality?.overallScore || 0}% < ${QUALITY_THRESHOLDS[currentStage]}%`,
          });
          return;
        }

        const stageOrder: ForgeStageId[] = [
          "idea_refinement",
          "prd_generation",
          "ux_requirements",
          "technical_analysis",
          "implementation_playbook",
        ];
        const currentIndex = stageOrder.indexOf(currentStage);
        if (currentIndex >= stageOrder.length - 1) return;

        const nextStage = stageOrder[currentIndex + 1];
        set({ isLoading: true });

        try {
          await forgeApi.advanceStage(projectId, nextStage);
          set((state) => ({
            currentProject: state.currentProject
              ? {
                  ...state.currentProject,
                  currentStage: nextStage,
                  updatedAt: new Date().toISOString(),
                }
              : null,
            projects: state.projects.map((p) =>
              p.id === projectId
                ? {
                    ...p,
                    currentStage: nextStage,
                    updatedAt: new Date().toISOString(),
                  }
                : p,
            ),
            isLoading: false,
          }));
        } catch (error) {
          set({
            error:
              error instanceof Error
                ? error.message
                : "Failed to advance stage",
            isLoading: false,
          });
        }
      },

      // Create new project
      createProject: async (data) => {
        set({ isLoading: true, error: null });
        try {
          const project = (await forgeApi.createProject(data)) as any;
          set((state) => ({
            projects: [project, ...state.projects],
            isLoading: false,
          }));
          return project;
        } catch (error) {
          set({
            error:
              error instanceof Error
                ? error.message
                : "Failed to create project",
            isLoading: false,
          });
          throw error;
        }
      },

      // Delete project
      deleteProject: async (projectId) => {
        set({ isLoading: true, error: null });
        try {
          await forgeApi.deleteProject(projectId);
          set((state) => ({
            projects: state.projects.filter((p) => p.id !== projectId),
            currentProjectId:
              state.currentProjectId === projectId
                ? null
                : state.currentProjectId,
            currentProject:
              state.currentProjectId === projectId
                ? null
                : state.currentProject,
            isLoading: false,
          }));
        } catch (error) {
          set({
            error:
              error instanceof Error
                ? error.message
                : "Failed to delete project",
            isLoading: false,
          });
        }
      },

      clearError: () => set({ error: null }),

      setLLMProvider: (provider: LLMProviderName, model?: string) => {
        const defaultModels: Record<LLMProviderName, string> = {
          openai: "gpt-4o",
          anthropic: "claude-3.5-sonnet",
          google: "gemini-1.5-pro",
        };
        set({
          selectedProvider: provider,
          selectedModel: model || defaultModels[provider],
        });
      },
    }),
    {
      name: "sutra-forge-store",
      storage: createJSONStorage(() => sessionStorage),
      // Only persist stage data and quality scores (not loading states)
      partialize: (state) => ({
        stageData: state.stageData,
        qualityScores: state.qualityScores,
        currentProjectId: state.currentProjectId,
        selectedProvider: state.selectedProvider,
        selectedModel: state.selectedModel,
      }),
    },
  ),
);
