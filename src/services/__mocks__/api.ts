// Mock for src/services/api.ts
/* eslint-disable @typescript-eslint/no-unused-vars */
// @ts-nocheck

export interface ApiResponse<T = any> {
  data?: T;
  error?: string;
  message?: string;
  timestamp?: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  limit: number;
  hasNext: boolean;
}

export interface Collection {
  id: string;
  name: string;
  description: string;
  type: "private" | "shared_team" | "public_marketplace";
  owner_id: string;
  created_at: string;
  updated_at: string;
  prompt_count?: number;
  tags?: string[];
}

export interface Prompt {
  id: string;
  title: string;
  content: string;
  collection_id: string;
  created_at: string;
  updated_at: string;
  version: number;
  tags?: string[];
}

export interface Playbook {
  id: string;
  name: string;
  description: string;
  steps: PlaybookStep[];
  creator_id: string;
  created_at: string;
  updated_at: string;
  visibility: "private" | "shared";
}

export interface PlaybookStep {
  id: string;
  type: "prompt" | "review" | "variable";
  prompt_id?: string;
  content?: string;
  variables?: Record<string, any>;
  order: number;
}

export interface LLMIntegration {
  id: string;
  provider: string;
  name: string;
  api_key: string;
  enabled: boolean;
  configuration: Record<string, any>;
}

// Mock implementation
export const apiService = {
  setToken: jest.fn(),

  async get<T>(endpoint: string): Promise<T> {
    return {
      data: [],
      total: 0,
      page: 1,
      limit: 10,
      hasNext: false,
    } as T;
  },

  async post<T>(endpoint: string, data?: any): Promise<T> {
    return {} as T;
  },

  async put<T>(endpoint: string, data?: any): Promise<T> {
    return {} as T;
  },

  async delete<T>(endpoint: string): Promise<T> {
    return {} as T;
  },
};

export const collectionsApi = {
  list: (params?: any) =>
    Promise.resolve({ data: [], total: 0, page: 1, limit: 10, hasNext: false }),
  get: (id: string) => Promise.resolve({} as Collection),
  create: (collection: any) => Promise.resolve({} as Collection),
  update: (id: string, collection: any) => Promise.resolve({} as Collection),
  delete: (id: string) => Promise.resolve(),
};

export const playbooksApi = {
  list: (params?: any) =>
    Promise.resolve({ data: [], total: 0, page: 1, limit: 10, hasNext: false }),
  get: (id: string) => Promise.resolve({} as Playbook),
  create: (playbook: any) => Promise.resolve({} as Playbook),
  update: (id: string, playbook: any) => Promise.resolve({} as Playbook),
  delete: (id: string) => Promise.resolve(),
};

export const integrationsApi = {
  list: () =>
    Promise.resolve({ data: [], total: 0, page: 1, limit: 10, hasNext: false }),
  get: (id: string) => Promise.resolve({} as LLMIntegration),
  create: (integration: any) => Promise.resolve({} as LLMIntegration),
  update: (id: string, integration: any) =>
    Promise.resolve({} as LLMIntegration),
  delete: (id: string) => Promise.resolve(),
};

export const adminApi = {
  getStats: () => Promise.resolve({}),
  getUsers: () =>
    Promise.resolve({ data: [], total: 0, page: 1, limit: 10, hasNext: false }),
};

export const llmApi = {
  execute: (data: any) => Promise.resolve({}),
};

export const forgeApi = {
  createProject: jest.fn((data: any) => Promise.resolve({ id: "new-project-id", name: data.name, description: data.description, currentStage: "idea_refinement", status: "draft", priority: data.priority || "medium", progressPercentage: 0, createdAt: new Date().toISOString(), updatedAt: new Date().toISOString(), tags: data.tags || [], collaboratorsCount: 1, artifactsCount: 0, ownerId: "user-1" })),
  listProjects: jest.fn((_params?: any) => Promise.resolve({ projects: [], total: 0 })),
  getProject: jest.fn((id: string) => Promise.resolve({ id, name: "Test Project", description: "Test", currentStage: "idea_refinement", status: "active", priority: "medium", progressPercentage: 25, createdAt: "2024-01-01T00:00:00Z", updatedAt: "2024-01-15T00:00:00Z", tags: [], collaboratorsCount: 1, artifactsCount: 0, ownerId: "user-1" })),
  updateProject: jest.fn((_id: string, data: any) => Promise.resolve(data)),
  deleteProject: jest.fn((_id: string) => Promise.resolve()),
  advanceStage: jest.fn((_id: string, _stage: string) => Promise.resolve({})),
  analyzeIdea: jest.fn(() => Promise.resolve({})),
  refineIdeaWithLLM: jest.fn(() => Promise.resolve({})),
  getIdeaQualityAssessment: jest.fn(() => Promise.resolve({})),
  completeIdeaRefinement: jest.fn(() => Promise.resolve({})),
  generateUserStories: jest.fn(() => Promise.resolve({ userStories: [] })),
  generateFunctionalRequirements: jest.fn(() => Promise.resolve({ requirements: [] })),
  generateAcceptanceCriteria: jest.fn(() => Promise.resolve({ acceptanceCriteria: [] })),
  extractRequirements: jest.fn(() => Promise.resolve({ requirements: [] })),
  prioritizeFeatures: jest.fn(() => Promise.resolve({ prioritizedFeatures: {} })),
  generatePRDDocument: jest.fn(() => Promise.resolve({})),
  getPRDQualityAssessment: jest.fn(() => Promise.resolve({})),
  completePRDGeneration: jest.fn(() => Promise.resolve({})),
  generateUserJourneys: jest.fn(() => Promise.resolve({ userJourneys: [] })),
  generateWireframes: jest.fn(() => Promise.resolve({ wireframes: [] })),
  generateComponentSpecs: jest.fn(() => Promise.resolve({ componentSpecs: [] })),
  generateUXDocument: jest.fn(() => Promise.resolve({})),
  validateAccessibility: jest.fn(() => Promise.resolve({})),
  specifyInteractions: jest.fn(() => Promise.resolve({ interactions: {} })),
  getUXQualityAssessment: jest.fn(() => Promise.resolve({})),
  completeUXRequirements: jest.fn(() => Promise.resolve({})),
  getConsensusModels: jest.fn(() => Promise.resolve({ models: [] })),
  analyzeArchitecture: jest.fn(() => Promise.resolve({ analyses: [] })),
  getStackRecommendations: jest.fn(() => Promise.resolve({ recommendations: [] })),
  assessScalability: jest.fn(() => Promise.resolve({})),
  generateTechSpec: jest.fn(() => Promise.resolve({})),
  getConsensusAnalysis: jest.fn(() => Promise.resolve({})),
  exportTechnicalAnalysis: jest.fn(() => Promise.resolve({})),
  getTechQualityAssessment: jest.fn(() => Promise.resolve({})),
  completeTechnicalAnalysis: jest.fn(() => Promise.resolve({})),
  generateCodingPrompts: jest.fn(() => Promise.resolve({ codingPrompts: [] })),
  createDevelopmentWorkflow: jest.fn(() => Promise.resolve({})),
  generateTestingStrategy: jest.fn(() => Promise.resolve({})),
  createDeploymentGuide: jest.fn(() => Promise.resolve({})),
  validateContextIntegration: jest.fn(() => Promise.resolve({})),
  compilePlaybook: jest.fn(() => Promise.resolve({})),
  exportPlaybook: jest.fn((_id: string, format: string) => Promise.resolve({ success: true, blob: new Blob(["test"]), filename: `export.${format}` })),
  getPlaybookQualityAssessment: jest.fn(() => Promise.resolve({})),
  completeImplementationPlaybook: jest.fn(() => Promise.resolve({})),
};

export default apiService;
