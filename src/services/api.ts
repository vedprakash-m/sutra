// API Configuration - Unified with Entra ID Authentication
import {
  convertObjectToCamelCase,
  convertObjectToSnakeCase,
} from "../utils/fieldConverter";
import { getAppConfig } from "../config";
import { apiCache, CacheTTL } from "./apiCache";
import { performanceMonitor } from "./performanceMonitor";

const getApiBaseUrl = () => {
  // Handle test environment where window might not be available
  if (typeof window === "undefined" && typeof global !== "undefined") {
    return "http://localhost:7071/api"; // Test environment default
  }

  const config = getAppConfig();
  return config.api.baseUrl;
};

const API_BASE_URL = getApiBaseUrl();

export interface ApiResponse<T = any> {
  data?: T;
  error?: string;
  message?: string;
  timestamp?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  pagination: {
    currentPage: number; // Updated to camelCase
    totalPages: number; // Updated to camelCase
    totalCount: number; // Updated to camelCase
    limit: number;
    hasNext: boolean; // Updated to camelCase
    has_prev: boolean;
  };
}

// Token provider type for dependency injection
export interface TokenProvider {
  getAccessToken(): Promise<string | null>;
}

class ApiService {
  private baseUrl: string;
  private tokenProvider: TokenProvider | null = null;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  // Set token provider for dependency injection
  setTokenProvider(provider: TokenProvider | null) {
    this.tokenProvider = provider;
  }

  // Legacy method for backward compatibility
  setToken(token: string | null) {
    if (token) {
      this.tokenProvider = {
        getAccessToken: async () => token,
      };
    } else {
      this.tokenProvider = null;
    }
  }

  // Get current access token
  private async getAccessToken(): Promise<string | null> {
    if (this.tokenProvider) {
      return await this.tokenProvider.getAccessToken();
    }

    // For local development, return null to allow backend to handle SWA headers
    if (window.location.hostname === "localhost") {
      return null;
    }

    return null;
  }

  private async getHeaders(): Promise<Record<string, string>> {
    const headers: Record<string, string> = {};

    // Set content type for all requests
    headers["Content-Type"] = "application/json";
    headers["Accept"] = "application/json";

    // Get access token
    const accessToken = await this.getAccessToken();
    if (accessToken) {
      if (accessToken === "mock-access-token-local-dev") {
        // For local development with mock token, use SWA headers
        const principal = {
          identityProvider: "aad",
          userId: "admin-user-local-dev",
          userDetails: "vedprakash.m@outlook.com",
          userRoles: ["authenticated"],
        };
        headers["x-ms-client-principal"] = btoa(JSON.stringify(principal));
        headers["x-ms-client-principal-id"] = principal.userId;
        headers["x-ms-client-principal-name"] = principal.userDetails;
        headers["x-ms-client-principal-idp"] = principal.identityProvider;
      } else {
        // For production or real MSAL tokens, use Bearer authentication
        headers["Authorization"] = `Bearer ${accessToken}`;
      }
    }

    // Add client info for rate limiting and analytics
    headers["X-Client-Name"] = "sutra-web";
    headers["X-Client-Version"] = "1.0.0";

    return headers;
  }

  // Determine cache TTL based on endpoint
  private getCacheTTL(endpoint: string): number {
    // Static configuration data - cache for longer
    if (endpoint.includes("/admin/") || endpoint.includes("/config/")) {
      return CacheTTL.VERY_LONG;
    }

    // Analytics data - medium cache
    if (endpoint.includes("/analytics/") || endpoint.includes("/metrics/")) {
      return CacheTTL.MEDIUM;
    }

    // User-specific data - short cache
    if (
      endpoint.includes("/prompts/") ||
      endpoint.includes("/collections/") ||
      endpoint.includes("/playbooks/")
    ) {
      return CacheTTL.SHORT;
    }

    // Default cache duration
    return CacheTTL.MEDIUM;
  }

  // Enhanced error handling for direct access with field conversion
  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      let errorMessage = `HTTP error! status: ${response.status}`;

      // Handle authentication redirects
      if (response.status === 401) {
        // Redirect to login if not authenticated
        window.location.href = "/login";
        throw new Error("Authentication required");
      }

      try {
        const errorData = await response.json();
        errorMessage = errorData.message || errorData.error || errorMessage;
      } catch (e) {
        // If JSON parsing fails, use the default error message
      }

      throw new Error(errorMessage);
    }

    const responseData = await response.json();

    // Convert response data from snake_case to camelCase
    return convertObjectToCamelCase(responseData) as T;
  }

  async get<T>(
    endpoint: string,
    params?: Record<string, any>,
    options?: { cache?: boolean; cacheTTL?: number },
  ): Promise<T> {
    const startTime = performance.now();
    const url = new URL(`${this.baseUrl}${endpoint}`);

    if (params) {
      // Convert params to snake_case before sending
      const convertedParams = convertObjectToSnakeCase(params);
      Object.entries(convertedParams).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          url.searchParams.append(key, String(value));
        }
      });
    }

    // Check cache if caching is enabled (default: true for GET requests)
    const shouldCache = options?.cache !== false;
    const cacheKey = `GET:${url.toString()}`;

    if (shouldCache) {
      const cachedData = apiCache.get<T>(cacheKey);
      if (cachedData) {
        const duration = performance.now() - startTime;
        performanceMonitor.recordAPICall(endpoint, "GET", duration, 200, {
          cached: true,
        });
        console.log(`📦 Cache hit for ${endpoint}`);
        return cachedData;
      }
    }

    const headers = await this.getHeaders();

    // For development, try to disable CORS by using no-cors mode
    // This will work for simple requests but not return response data
    const fetchOptions: any = {
      method: "GET",
      headers,
    };

    // In development connecting to production API, use mode: 'cors'
    // The backend should allow requests without Origin header
    if (
      process.env.NODE_ENV === "development" &&
      this.baseUrl.includes("azurewebsites.net")
    ) {
      fetchOptions.mode = "cors";
    }

    const response = await fetch(url.toString(), fetchOptions);
    const data = await this.handleResponse<T>(response);

    const duration = performance.now() - startTime;

    // Record API performance
    const responseSize = response.headers.get("content-length");
    performanceMonitor.recordAPICall(
      endpoint,
      "GET",
      duration,
      response.status,
      {
        cached: false,
        size: responseSize ? parseInt(responseSize) : undefined,
      },
    );

    // Cache the response if caching is enabled
    if (shouldCache) {
      const ttl = options?.cacheTTL || this.getCacheTTL(endpoint);
      apiCache.set(cacheKey, data, ttl);
      console.log(`💾 Cached response for ${endpoint} (TTL: ${ttl}ms)`);
    }

    return data;
  }

  // Cache invalidation helper
  private invalidateCache(endpoint: string): void {
    // Simple cache invalidation - remove all entries with similar paths
    const cacheStats = apiCache.getStats();
    console.log(
      `🗑️ Invalidating cache entries for ${endpoint} (before: ${cacheStats.totalEntries} entries)`,
    );

    // For now, clear all cache on mutations to ensure data consistency
    // In production, you'd implement more sophisticated cache invalidation
    apiCache.clear();
  }

  async post<T>(endpoint: string, data?: any): Promise<T> {
    const startTime = performance.now();

    // Convert request data to snake_case before sending
    const convertedData = data ? convertObjectToSnakeCase(data) : undefined;

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: "POST",
      headers: await this.getHeaders(),
      body: convertedData ? JSON.stringify(convertedData) : undefined,
    });

    const result = await this.handleResponse<T>(response);

    const duration = performance.now() - startTime;
    performanceMonitor.recordAPICall(
      endpoint,
      "POST",
      duration,
      response.status,
    );

    // Invalidate cache after mutation
    this.invalidateCache(endpoint);

    return result;
  }

  async put<T>(endpoint: string, data?: any): Promise<T> {
    const startTime = performance.now();

    // Convert request data to snake_case before sending
    const convertedData = data ? convertObjectToSnakeCase(data) : undefined;

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: "PUT",
      headers: await this.getHeaders(),
      body: convertedData ? JSON.stringify(convertedData) : undefined,
    });

    const result = await this.handleResponse<T>(response);

    const duration = performance.now() - startTime;
    performanceMonitor.recordAPICall(
      endpoint,
      "PUT",
      duration,
      response.status,
    );

    // Invalidate cache after mutation
    this.invalidateCache(endpoint);

    return result;
  }

  async delete<T>(endpoint: string): Promise<T> {
    const startTime = performance.now();

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: "DELETE",
      headers: await this.getHeaders(),
    });

    const result = await this.handleResponse<T>(response);

    const duration = performance.now() - startTime;
    performanceMonitor.recordAPICall(
      endpoint,
      "DELETE",
      duration,
      response.status,
    );

    // Invalidate cache after mutation
    this.invalidateCache(endpoint);

    return result;
  }
}

// Create singleton instance
export const apiService = new ApiService();

// Collection related types and functions
export interface Collection {
  id: string;
  name: string;
  description: string;
  type: "private" | "shared_team" | "public_marketplace";
  userId: string; // Backend uses camelCase
  ownerId: string; // Backend field name
  createdAt: string; // Backend uses camelCase
  updatedAt: string; // Backend uses camelCase
  promptIds?: string[]; // Backend field name
  teamId?: string; // Backend field name
  tags?: string[];
  // Computed fields from backend
  prompt_count?: number; // For display
}

export interface Prompt {
  id: string;
  title: string;
  content: string;
  collectionId: string; // Backend uses camelCase
  userId: string; // Backend uses camelCase
  createdAt: string; // Backend uses camelCase
  updatedAt: string; // Backend uses camelCase
  version: number;
  tags?: string[];
}

// LLM Integration types
export interface LLMIntegration {
  id: string;
  provider: string;
  api_key: string;
  enabled: boolean;
  status?: "connected" | "disconnected" | "error";
  last_tested?: string;
  url?: string;
}

export interface Playbook {
  id: string;
  name: string;
  description: string;
  steps: any[];
  owner_id: string;
  created_at: string;
  updated_at: string;
  visibility?: "private" | "shared" | "public";
}

// API Functions
export const collectionsApi = {
  list: (params?: {
    page?: number;
    limit?: number;
    search?: string;
    type?: string;
  }) => apiService.get<PaginatedResponse<Collection>>("/collections", params),

  get: (id: string) => apiService.get<Collection>(`/collections/${id}`),

  create: (collection: Partial<Collection>) =>
    apiService.post<Collection>("/collections", collection),

  update: (id: string, collection: Partial<Collection>) =>
    apiService.put<Collection>(`/collections/${id}`, collection),

  delete: (id: string) => apiService.delete(`/collections/${id}`),
};

export const playbooksApi = {
  list: (params?: {
    page?: number;
    limit?: number;
    search?: string;
    visibility?: string;
  }) => apiService.get<PaginatedResponse<Playbook>>("/playbooks", params),

  get: (id: string) => apiService.get<Playbook>(`/playbooks/${id}`),

  create: (playbook: Partial<Playbook>) =>
    apiService.post<Playbook>("/playbooks", playbook),

  update: (id: string, playbook: Partial<Playbook>) =>
    apiService.put<Playbook>(`/playbooks/${id}`, playbook),

  delete: (id: string) => apiService.delete(`/playbooks/${id}`),

  execute: (id: string, variables?: Record<string, any>) =>
    apiService.post(`/playbooks/${id}/execute`, { variables }),
};

export const integrationsApi = {
  listLLM: () =>
    apiService.get<{
      integrations: Record<string, LLMIntegration>;
      supportedProviders: any[];
    }>("/integrations/llm"),

  saveLLM: (provider: string, integration: Partial<LLMIntegration>) =>
    apiService.post(`/integrations/llm/${provider}`, integration),

  deleteLLM: (provider: string) =>
    apiService.delete(`/integrations/llm/${provider}`),
};

export const adminApi = {
  getLLMSettings: () => apiService.get("/management/llm/settings"),

  updateLLMSettings: (settings: any) =>
    apiService.put("/management/llm/settings", settings),

  getSystemHealth: () => apiService.get("/management/system/health"),

  getUsageStats: () => apiService.get("/management/usage"),
};

export const llmApi = {
  execute: (
    promptText: string,
    model: string,
    variables?: Record<string, any>,
  ) => apiService.post("/llm", { promptText, model, variables }),
};

export const promptsApi = {
  list: (params?: {
    page?: number;
    limit?: number;
    search?: string;
    collection_id?: string;
  }) => apiService.get<PaginatedResponse<Prompt>>("/prompts", params),

  get: (id: string) => apiService.get<Prompt>(`/prompts/${id}`),

  create: (prompt: {
    title: string;
    description: string;
    content: string;
    variables?: any[];
    tags?: string[];
    collection_id?: string;
  }) => apiService.post<Prompt>("/prompts", prompt),

  update: (id: string, prompt: Partial<Prompt>) =>
    apiService.put<Prompt>(`/prompts/${id}`, prompt),

  delete: (id: string) => apiService.delete(`/prompts/${id}`),

  execute: (id: string, variables?: Record<string, any>) =>
    apiService.post(`/prompts/${id}/execute`, { variables }),
};

export const guestApi = {
  executePrompt: (prompt: string, model?: string) =>
    apiService.post("/guest-llm/execute", {
      prompt,
      model: model || "gpt-3.5-turbo",
    }),

  getModels: () => apiService.get("/guest-llm/models"),

  getUsage: () => apiService.get("/guest-llm/usage"),
};

// Import Forge types
import type {
  ForgeProject,
  IdeaData,
  RefinementRequest,
  AnalysisResult,
  RefinedIdea,
  QualityAssessment,
  StageCompletionResponse,
  UserStory,
  FunctionalRequirement,
  AcceptanceCriteria,
  PRDDocument,
  UserJourney,
  Wireframe,
  ComponentSpec,
  UXDocument,
  AccessibilityReport,
  ArchitectureAnalysis,
  StackRecommendation,
  ScalabilityAssessment,
  TechSpecDocument,
  ConsensusResult,
  CodingPrompt,
  DevelopmentWorkflow,
  TestingStrategy,
  ImplementationPlaybook,
  ExportFormat,
  ExportResponse,
} from "../types/forge";

export const forgeApi = {
  // ============================================================================
  // Forge Project Management
  // ============================================================================
  
  /**
   * Create a new Forge project
   */
  createProject: (data: {
    name: string;
    description: string;
    priority?: string;
    tags?: string[];
  }) => apiService.post<ForgeProject>("/forge/create", data),

  /**
   * List all Forge projects for the authenticated user
   */
  listProjects: (params?: {
    status?: string;
    stage?: string;
    limit?: number;
    offset?: number;
  }) => apiService.get<{ projects: ForgeProject[]; total: number }>("/forge/list", params),

  /**
   * Get a specific Forge project by ID
   */
  getProject: (projectId: string) =>
    apiService.get<ForgeProject>(`/forge/get?project_id=${projectId}`),

  /**
   * Update a Forge project
   */
  updateProject: (projectId: string, data: Partial<ForgeProject>) =>
    apiService.put<ForgeProject>(`/forge/update?project_id=${projectId}`, data),

  /**
   * Delete a Forge project
   */
  deleteProject: (projectId: string) =>
    apiService.delete(`/forge/delete?project_id=${projectId}`),

  // ============================================================================
  // Stage 1: Idea Refinement
  // ============================================================================

  /**
   * Analyze idea with multi-dimensional quality assessment
   */
  analyzeIdea: (projectId: string, ideaData: IdeaData, projectContext?: Record<string, any>) =>
    apiService.post<AnalysisResult>(
      `/forge/idea-refinement/analyze?project_id=${projectId}`,
      { ideaData, projectContext }
    ),

  /**
   * Refine idea with LLM-powered suggestions
   */
  refineIdeaWithLLM: (projectId: string, request: RefinementRequest) =>
    apiService.post<RefinedIdea>(
      `/forge/idea-refinement/refine?project_id=${projectId}`,
      request
    ),

  /**
   * Get quality assessment for idea refinement stage
   */
  getIdeaQualityAssessment: (projectId: string) =>
    apiService.get<QualityAssessment>(
      `/forge/idea-refinement/assessment?project_id=${projectId}`
    ),

  /**
   * Complete idea refinement stage
   */
  completeIdeaRefinement: (projectId: string, ideaData: IdeaData) =>
    apiService.post<StageCompletionResponse>(
      `/forge/idea-refinement/complete?project_id=${projectId}`,
      { ideaData }
    ),

  // ============================================================================
  // Stage 2: PRD Generation
  // ============================================================================

  /**
   * Generate user stories from refined idea
   */
  generateUserStories: (projectId: string, context?: Record<string, any>) =>
    apiService.post<{ userStories: UserStory[] }>(
      `/forge/prd-generation/generate-user-stories?project_id=${projectId}`,
      { context }
    ),

  /**
   * Generate functional requirements from user stories
   */
  generateFunctionalRequirements: (projectId: string, userStories: UserStory[]) =>
    apiService.post<{ requirements: FunctionalRequirement[] }>(
      `/forge/prd-generation/generate-functional-requirements?project_id=${projectId}`,
      { userStories }
    ),

  /**
   * Generate acceptance criteria for a specific requirement
   */
  generateAcceptanceCriteria: (projectId: string, requirement: FunctionalRequirement) =>
    apiService.post<{ acceptanceCriteria: AcceptanceCriteria[] }>(
      `/forge/prd-generation/generate-acceptance-criteria?project_id=${projectId}`,
      { requirement }
    ),

  /**
   * Generate complete PRD document with all sections
   */
  generatePRDDocument: (projectId: string) =>
    apiService.post<PRDDocument>(
      `/forge/prd-generation/generate-prd-document?project_id=${projectId}`,
      {}
    ),

  /**
   * Get quality assessment for PRD generation stage
   */
  getPRDQualityAssessment: (projectId: string) =>
    apiService.get<QualityAssessment>(
      `/forge/prd-generation/quality-assessment?project_id=${projectId}`
    ),

  /**
   * Complete PRD generation stage
   */
  completePRDGeneration: (projectId: string, prdData: PRDDocument) =>
    apiService.post<StageCompletionResponse>(
      `/forge/prd-generation/complete?project_id=${projectId}`,
      { prdData }
    ),

  // ============================================================================
  // Stage 3: UX Requirements
  // ============================================================================

  /**
   * Generate user journeys from user stories
   */
  generateUserJourneys: (projectId: string, userStories: UserStory[]) =>
    apiService.post<{ userJourneys: UserJourney[] }>(
      `/forge/ux-requirements/generate-user-journeys?project_id=${projectId}`,
      { userStories }
    ),

  /**
   * Generate wireframes from user journeys
   */
  generateWireframes: (projectId: string, userJourneys: UserJourney[]) =>
    apiService.post<{ wireframes: Wireframe[] }>(
      `/forge/ux-requirements/generate-wireframes?project_id=${projectId}`,
      { userJourneys }
    ),

  /**
   * Generate component specifications
   */
  generateComponentSpecs: (projectId: string, wireframes: Wireframe[]) =>
    apiService.post<{ componentSpecs: ComponentSpec[] }>(
      `/forge/ux-requirements/generate-component-specs?project_id=${projectId}`,
      { wireframes }
    ),

  /**
   * Generate complete UX document
   */
  generateUXDocument: (projectId: string) =>
    apiService.post<UXDocument>(
      `/forge/ux-requirements/generate-ux-document?project_id=${projectId}`,
      {}
    ),

  /**
   * Validate accessibility compliance (WCAG 2.1 AA)
   */
  validateAccessibility: (projectId: string, uxData: Partial<UXDocument>) =>
    apiService.post<AccessibilityReport>(
      `/forge/ux-requirements/accessibility-validation?project_id=${projectId}`,
      { uxData }
    ),

  /**
   * Get quality assessment for UX requirements stage
   */
  getUXQualityAssessment: (projectId: string) =>
    apiService.get<QualityAssessment>(
      `/forge/ux-requirements/quality-assessment?project_id=${projectId}`
    ),

  /**
   * Complete UX requirements stage
   */
  completeUXRequirements: (projectId: string, uxData: UXDocument) =>
    apiService.post<StageCompletionResponse>(
      `/forge/ux-requirements/complete?project_id=${projectId}`,
      { uxData }
    ),

  // ============================================================================
  // Stage 4: Technical Analysis
  // ============================================================================

  /**
   * Analyze architecture with multi-LLM evaluation
   */
  analyzeArchitecture: (projectId: string, requirements: Record<string, any>) =>
    apiService.post<{ analyses: ArchitectureAnalysis[] }>(
      `/forge/technical-analysis/analyze-architecture?project_id=${projectId}`,
      { requirements }
    ),

  /**
   * Get technology stack recommendations
   */
  getStackRecommendations: (projectId: string, constraints?: Record<string, any>) =>
    apiService.post<{ recommendations: StackRecommendation[] }>(
      `/forge/technical-analysis/stack-recommendation?project_id=${projectId}`,
      { constraints }
    ),

  /**
   * Assess scalability of proposed architecture
   */
  assessScalability: (projectId: string, architecture: ArchitectureAnalysis) =>
    apiService.post<ScalabilityAssessment>(
      `/forge/technical-analysis/scalability-assessment?project_id=${projectId}`,
      { architecture }
    ),

  /**
   * Generate complete technical specification document
   */
  generateTechSpec: (projectId: string) =>
    apiService.post<TechSpecDocument>(
      `/forge/technical-analysis/generate-tech-spec?project_id=${projectId}`,
      {}
    ),

  /**
   * Get multi-LLM consensus analysis
   */
  getConsensusAnalysis: (projectId: string) =>
    apiService.post<ConsensusResult>(
      `/forge/technical-analysis/consensus-analysis?project_id=${projectId}`,
      {}
    ),

  /**
   * Get quality assessment for technical analysis stage
   */
  getTechQualityAssessment: (projectId: string) =>
    apiService.get<QualityAssessment>(
      `/forge/technical-analysis/quality-assessment?project_id=${projectId}`
    ),

  /**
   * Complete technical analysis stage
   */
  completeTechnicalAnalysis: (projectId: string, techData: TechSpecDocument) =>
    apiService.post<StageCompletionResponse>(
      `/forge/technical-analysis/complete?project_id=${projectId}`,
      { techData }
    ),

  // ============================================================================
  // Stage 5: Implementation Playbook
  // ============================================================================

  /**
   * Generate coding agent prompts
   */
  generateCodingPrompts: (projectId: string, techSpec: TechSpecDocument) =>
    apiService.post<{ codingPrompts: CodingPrompt[] }>(
      `/forge/generate-coding-prompts?project_id=${projectId}`,
      { techSpec }
    ),

  /**
   * Create development workflow
   */
  createDevelopmentWorkflow: (projectId: string, prompts: CodingPrompt[]) =>
    apiService.post<DevelopmentWorkflow>(
      `/forge/create-development-workflow?project_id=${projectId}`,
      { prompts }
    ),

  /**
   * Generate testing strategy
   */
  generateTestingStrategy: (projectId: string, requirements: Record<string, any>) =>
    apiService.post<TestingStrategy>(
      `/forge/generate-testing-strategy?project_id=${projectId}`,
      { requirements }
    ),

  /**
   * Compile complete implementation playbook
   */
  compilePlaybook: (projectId: string) =>
    apiService.post<ImplementationPlaybook>(
      `/forge/compile-playbook?project_id=${projectId}`,
      {}
    ),

  /**
   * Export playbook in specified format (JSON, Markdown, PDF, ZIP)
   * Note: This method handles blob responses for non-JSON formats
   */
  exportPlaybook: async (projectId: string, format: ExportFormat, options?: {
    includeArtifacts?: boolean;
    stages?: string[];
  }): Promise<ExportResponse> => {
    // For JSON format, use standard API call
    if (format === "json") {
      return apiService.post<ExportResponse>(
        `/forge/export-playbook?project_id=${projectId}`,
        { format, ...options }
      );
    }

    // For blob formats (markdown, pdf, zip), handle blob response
    const response = await fetch(
      `${API_BASE_URL}/forge/export-playbook?project_id=${projectId}`,
      {
        method: "POST",
        headers: await (apiService as any).getHeaders(),
        body: JSON.stringify({ format, ...options }),
      }
    );

    if (!response.ok) {
      throw new Error(`Export failed: ${response.statusText}`);
    }

    const blob = await response.blob();
    const filename = response.headers.get("content-disposition")?.split("filename=")[1] || `forge-playbook-${projectId}.${format}`;
    
    return {
      success: true,
      blob,
      filename: filename.replace(/['"]/g, ""),
    };
  },

  /**
   * Get quality assessment for implementation playbook stage
   */
  getPlaybookQualityAssessment: (projectId: string) =>
    apiService.get<QualityAssessment>(
      `/forge/quality-validation?project_id=${projectId}`
    ),

  /**
   * Complete implementation playbook stage
   */
  completeImplementationPlaybook: (projectId: string, playbookData: ImplementationPlaybook) =>
    apiService.post<StageCompletionResponse>(
      `/forge/implementation-playbook/complete?project_id=${projectId}`,
      { playbookData }
    ),
};

// Combined API export for easier access
export const api = {
  prompts: promptsApi,
  collections: collectionsApi,
  playbooks: playbooksApi,
  integrations: integrationsApi,
  admin: adminApi,
  llm: llmApi,
  guest: guestApi,
  forge: forgeApi,
};

export default apiService;
