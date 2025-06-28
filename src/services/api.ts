// API Configuration - Enhanced with Field Conversion and Unified Auth
import {
  convertObjectToCamelCase,
  convertObjectToSnakeCase,
} from "../utils/fieldConverter";

const getApiBaseUrl = () => {
  // Handle test environment where import.meta might not be available
  if (typeof window === "undefined" && typeof global !== "undefined") {
    return "http://localhost:7071/api"; // Test environment default
  }

  // Handle import.meta safely for Jest
  const importMeta =
    typeof window !== "undefined" || typeof global === "undefined"
      ? (globalThis as any).import?.meta || { env: {} }
      : { env: {} };

  // Check if we have an explicit API URL override
  if (importMeta.env.VITE_API_URL) {
    return importMeta.env.VITE_API_URL;
  }

  // In development, check if local API is available via Vite config
  if (importMeta.env.NODE_ENV === "development") {
    const useLocalAPI = importMeta.env.VITE_USE_LOCAL_API === "true";
    if (useLocalAPI) {
      return "/api"; // Use proxy when local API is available
    } else {
      // Use production API directly when local API is not available
      return "https://sutra-api-hvyqgbrvnx4ii.azurewebsites.net/api";
    }
  }

  // Production default
  return "https://sutra-api-hvyqgbrvnx4ii.azurewebsites.net/api";
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

class ApiService {
  private baseUrl: string;
  private token: string | null = null;

  // Initialize with auth token on construction
  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
    // Try to get auth token on initialization
    this.getAuthToken()
      .then((token) => {
        if (token) {
          this.setToken(token);
        }
      })
      .catch(() => {
        // Ignore auth errors during initialization
      });
  }

  setToken(token: string | null) {
    this.token = token;
  }

  // Static Web App authentication integration
  private async getAuthToken(): Promise<string | null> {
    try {
      // Static Web App provides auth info at /.auth/me
      const response = await fetch("/.auth/me");
      if (response.ok) {
        const authInfo = await response.json();
        if (authInfo.clientPrincipal) {
          // User is authenticated, get access token if available
          return authInfo.clientPrincipal.accessToken || null;
        }
      }
    } catch (error) {
      console.debug("Auth token not available:", error);
    }
    return null;
  }

  private async getHeaders(): Promise<Record<string, string>> {
    const headers: Record<string, string> = {};

    // In development connecting to production API, use minimal headers to avoid CORS preflight
    if (
      process.env.NODE_ENV === "development" &&
      this.baseUrl.includes("azurewebsites.net")
    ) {
      // Use only simple headers that don't trigger CORS preflight
      headers["Accept"] = "application/json";
    } else {
      // For local development or production, use full headers
      headers["Content-Type"] = "application/json";
    }

    if (this.token) {
      headers["Authorization"] = `Bearer ${this.token}`;
    }

    // Add client info for rate limiting and analytics
    headers["X-Client-Name"] = "sutra-web";
    headers["X-Client-Version"] = "1.0.0";

    // Development mode: Add Azure Static Web Apps headers
    if (
      process.env.NODE_ENV === "development" ||
      window.location.hostname === "localhost"
    ) {
      try {
        // Try to get user info from /.auth/me endpoint (mock auth)
        const authResponse = await fetch("/.auth/me");
        if (authResponse.ok) {
          const authData = await authResponse.json();
          if (authData.clientPrincipal) {
            const principal = authData.clientPrincipal;
            headers["x-ms-client-principal"] = btoa(JSON.stringify(principal));
            headers["x-ms-client-principal-id"] = principal.userId;
            headers["x-ms-client-principal-name"] = principal.userDetails;
            headers["x-ms-client-principal-idp"] = principal.identityProvider;
          }
        } else {
          // Fallback to localStorage if /.auth/me doesn't work
          const demoUser = localStorage.getItem("sutra_demo_user");
          if (demoUser) {
            const user = JSON.parse(demoUser);
            const principal = {
              userId: user.id,
              userDetails: user.email,
              identityProvider: "azureActiveDirectory",
              userRoles: user.role === "admin" ? ["admin", "user"] : ["user"],
            };
            headers["x-ms-client-principal"] = btoa(JSON.stringify(principal));
            headers["x-ms-client-principal-id"] = user.id;
            headers["x-ms-client-principal-name"] = user.email;
            headers["x-ms-client-principal-idp"] = "azureActiveDirectory";
          }
        }

        // For requests to production API from localhost, don't send Origin header to avoid CORS
        // The backend allows requests without Origin header
      } catch (e) {
        console.warn("Failed to get auth headers for development:", e);
      }
    }

    return headers;
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

  async get<T>(endpoint: string, params?: Record<string, any>): Promise<T> {
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

    return this.handleResponse<T>(response);
  }

  async post<T>(endpoint: string, data?: any): Promise<T> {
    // Convert request data to snake_case before sending
    const convertedData = data ? convertObjectToSnakeCase(data) : undefined;

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: "POST",
      headers: await this.getHeaders(),
      body: convertedData ? JSON.stringify(convertedData) : undefined,
    });

    return this.handleResponse<T>(response);
  }

  async put<T>(endpoint: string, data?: any): Promise<T> {
    // Convert request data to snake_case before sending
    const convertedData = data ? convertObjectToSnakeCase(data) : undefined;

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: "PUT",
      headers: await this.getHeaders(),
      body: convertedData ? JSON.stringify(convertedData) : undefined,
    });

    return this.handleResponse<T>(response);
  }

  async delete<T>(endpoint: string): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: "DELETE",
      headers: await this.getHeaders(),
    });

    return this.handleResponse<T>(response);
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

// Combined API export for easier access
export const api = {
  prompts: promptsApi,
  collections: collectionsApi,
  playbooks: playbooksApi,
  integrations: integrationsApi,
  admin: adminApi,
  llm: llmApi,
  guest: guestApi,
};

export default apiService;
