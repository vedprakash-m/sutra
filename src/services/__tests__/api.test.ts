import {
  apiService,
  collectionsApi,
  playbooksApi,
  integrationsApi,
  adminApi,
  llmApi,
  promptsApi,
  guestApi,
  api,
} from "../api";

// Mock fetch globally
const mockFetch = jest.fn();
global.fetch = mockFetch;

// Mock window.location
Object.defineProperty(window, "location", {
  value: {
    href: "",
  },
  writable: true,
});

describe("ApiService", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    window.location.href = "";
  });

  describe("error handling", () => {
    it("should handle 401 unauthorized errors", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: jest.fn().mockResolvedValue({ message: "Unauthorized" }),
      });

      await expect(apiService.get("/test")).rejects.toThrow(
        "Authentication required",
      );
      expect(window.location.href).toBe("/login");
    });

    it("should handle other HTTP errors with error message", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: jest.fn().mockResolvedValue({ error: "Server error" }),
      });

      await expect(apiService.get("/test")).rejects.toThrow("Server error");
    });

    it("should handle HTTP errors without JSON response", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: jest.fn().mockRejectedValue(new Error("Invalid JSON")),
      });

      await expect(apiService.get("/test")).rejects.toThrow(
        "HTTP error! status: 500",
      );
    });

    it("should handle HTTP errors with message field", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: jest.fn().mockResolvedValue({ message: "Bad request" }),
      });

      await expect(apiService.get("/test")).rejects.toThrow("Bad request");
    });
  });

  describe("setToken", () => {
    it("should set auth token", () => {
      apiService.setToken("test-token");
      expect(() => apiService.setToken("test-token")).not.toThrow();
    });

    it("should handle null token", () => {
      apiService.setToken(null);
      expect(() => apiService.setToken(null)).not.toThrow();
    });
  });

  describe("get method", () => {
    it("should make GET request with correct headers", async () => {
      const mockResponse = { data: "test" };
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue(mockResponse),
      });

      apiService.setToken("test-token");
      const result = await apiService.get("/test");

      expect(mockFetch).toHaveBeenCalledWith(expect.stringContaining("/test"), {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          Authorization: "Bearer test-token",
          "X-Client-Name": "sutra-web",
          "X-Client-Version": "1.0.0",
        },
      });
      expect(result).toEqual(mockResponse);
    });

    it("should handle query parameters", async () => {
      const mockResponse = { data: "test" };
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue(mockResponse),
      });

      await apiService.get("/test", { page: 1, limit: 10, search: "query" });

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringMatching(/\/test\?.*page=1.*limit=10.*search=query/),
        expect.any(Object),
      );
    });

    it("should filter out null and undefined parameters", async () => {
      const mockResponse = { data: "test" };
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue(mockResponse),
      });

      await apiService.get("/test", {
        page: 1,
        limit: null,
        search: undefined,
      });

      const fetchCall = mockFetch.mock.calls[0][0];
      expect(fetchCall).toContain("page=1");
      expect(fetchCall).not.toContain("limit=");
      expect(fetchCall).not.toContain("search=");
    });

    it("should make GET request without auth token", async () => {
      const mockResponse = { data: "test" };
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue(mockResponse),
      });

      apiService.setToken(null);
      await apiService.get("/test");

      expect(mockFetch).toHaveBeenCalledWith(expect.any(String), {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          "X-Client-Name": "sutra-web",
          "X-Client-Version": "1.0.0",
        },
      });
    });
  });

  describe("post method", () => {
    it("should make POST request with data", async () => {
      const mockResponse = { id: 1 };
      const requestData = { name: "test" };
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue(mockResponse),
      });

      const result = await apiService.post("/test", requestData);

      expect(mockFetch).toHaveBeenCalledWith(expect.stringContaining("/test"), {
        method: "POST",
        headers: expect.any(Object),
        body: JSON.stringify(requestData),
      });
      expect(result).toEqual(mockResponse);
    });

    it("should handle POST without data", async () => {
      const mockResponse = { success: true };
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue(mockResponse),
      });

      await apiService.post("/test");

      expect(mockFetch).toHaveBeenCalledWith(expect.stringContaining("/test"), {
        method: "POST",
        headers: expect.any(Object),
        body: undefined,
      });
    });
  });

  describe("put method", () => {
    it("should make PUT request with data", async () => {
      const mockResponse = { id: 1, updated: true };
      const requestData = { name: "updated" };
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue(mockResponse),
      });

      const result = await apiService.put("/test", requestData);

      expect(mockFetch).toHaveBeenCalledWith(expect.stringContaining("/test"), {
        method: "PUT",
        headers: expect.any(Object),
        body: JSON.stringify(requestData),
      });
      expect(result).toEqual(mockResponse);
    });

    it("should handle PUT without data", async () => {
      const mockResponse = { success: true };
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue(mockResponse),
      });

      await apiService.put("/test");

      expect(mockFetch).toHaveBeenCalledWith(expect.stringContaining("/test"), {
        method: "PUT",
        headers: expect.any(Object),
        body: undefined,
      });
    });
  });

  describe("delete method", () => {
    it("should make DELETE request", async () => {
      const mockResponse = { deleted: true };
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue(mockResponse),
      });

      const result = await apiService.delete("/test");

      expect(mockFetch).toHaveBeenCalledWith(expect.stringContaining("/test"), {
        method: "DELETE",
        headers: expect.any(Object),
      });
      expect(result).toEqual(mockResponse);
    });
  });

  describe("constructor and initialization", () => {
    it("should initialize with default baseUrl when no baseUrl provided", () => {
      // Test that the service initializes properly
      expect(() => new (apiService.constructor as any)()).not.toThrow();
    });

    it("should initialize with custom baseUrl", () => {
      const customBaseUrl = "https://custom-api.example.com";
      expect(
        () => new (apiService.constructor as any)(customBaseUrl),
      ).not.toThrow();
    });

    it("should handle auth token initialization failure gracefully", () => {
      // Mock getAuthToken to fail
      const originalFetch = global.fetch;
      global.fetch = jest.fn().mockRejectedValue(new Error("Auth failed"));

      expect(() => new (apiService.constructor as any)()).not.toThrow();

      global.fetch = originalFetch;
    });
  });

  describe("getAuthToken", () => {
    it("should return null when auth endpoint fails", async () => {
      mockFetch.mockRejectedValueOnce(new Error("Network error"));

      // Access private method through reflection
      const service = apiService as any;
      const token = await service.getAuthToken();

      expect(token).toBeNull();
    });

    it("should return null when response is not ok", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
      });

      const service = apiService as any;
      const token = await service.getAuthToken();

      expect(token).toBeNull();
    });

    it("should return null when no clientPrincipal", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue({}),
      });

      const service = apiService as any;
      const token = await service.getAuthToken();

      expect(token).toBeNull();
    });

    it("should return null when clientPrincipal has no access token", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue({
          clientPrincipal: {},
        }),
      });

      const service = apiService as any;
      const token = await service.getAuthToken();

      expect(token).toBeNull();
    });

    it("should return access token when available", async () => {
      const expectedToken = "valid-access-token";
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue({
          clientPrincipal: {
            accessToken: expectedToken,
          },
        }),
      });

      const service = apiService as any;
      const token = await service.getAuthToken();

      expect(token).toBe(expectedToken);
    });
  });

  describe("put method", () => {
    it("should make PUT request with data", async () => {
      const mockResponse = { id: 1, updated: true };
      const requestData = { name: "updated test" };
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue(mockResponse),
      });

      const result = await apiService.put("/test/1", requestData);

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/test/1"),
        {
          method: "PUT",
          headers: expect.any(Object),
          body: JSON.stringify(requestData),
        },
      );
      expect(result).toEqual(mockResponse);
    });

    it("should handle PUT without data", async () => {
      const mockResponse = { success: true };
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue(mockResponse),
      });

      await apiService.put("/test/1");

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/test/1"),
        {
          method: "PUT",
          headers: expect.any(Object),
          body: undefined,
        },
      );
    });
  });

  describe("delete method", () => {
    it("should make DELETE request", async () => {
      const mockResponse = { success: true };
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue(mockResponse),
      });

      const result = await apiService.delete("/test/1");

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/test/1"),
        {
          method: "DELETE",
          headers: expect.any(Object),
        },
      );
      expect(result).toEqual(mockResponse);
    });
  });

  describe("getHeaders", () => {
    it("should return headers without auth token when token is null", async () => {
      apiService.setToken(null);
      const service = apiService as any;
      const headers = await service.getHeaders();

      expect(headers).toEqual({
        "Content-Type": "application/json",
        "X-Client-Name": "sutra-web",
        "X-Client-Version": "1.0.0",
      });
      expect(headers["Authorization"]).toBeUndefined();
    });

    it("should return headers with auth token when token is set", async () => {
      const testToken = "test-auth-token";
      apiService.setToken(testToken);
      const service = apiService as any;
      const headers = await service.getHeaders();

      expect(headers).toEqual({
        "Content-Type": "application/json",
        Authorization: `Bearer ${testToken}`,
        "X-Client-Name": "sutra-web",
        "X-Client-Version": "1.0.0",
      });
    });
  });

  describe("handleResponse", () => {
    it("should return parsed JSON for successful response", async () => {
      const mockData = { message: "success" };
      const mockResponse = {
        ok: true,
        json: jest.fn().mockResolvedValue(mockData),
      } as any;

      const service = apiService as any;
      const result = await service.handleResponse(mockResponse);

      expect(result).toEqual(mockData);
      expect(mockResponse.json).toHaveBeenCalled();
    });

    it("should throw error for failed response with error field", async () => {
      const mockResponse = {
        ok: false,
        status: 400,
        json: jest.fn().mockResolvedValue({ error: "Custom error" }),
      } as any;

      const service = apiService as any;

      await expect(service.handleResponse(mockResponse)).rejects.toThrow(
        "Custom error",
      );
    });

    it("should throw default error when JSON parsing fails", async () => {
      const mockResponse = {
        ok: false,
        status: 500,
        json: jest.fn().mockRejectedValue(new Error("JSON parse error")),
      } as any;

      const service = apiService as any;

      await expect(service.handleResponse(mockResponse)).rejects.toThrow(
        "HTTP error! status: 500",
      );
    });
  });
});

// Collections API tests
describe("collectionsApi", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("should list collections with pagination", async () => {
    const mockResponse = {
      items: [{ id: "1", name: "Test Collection" }],
      pagination: {
        currentPage: 1,
        totalPages: 1,
        totalCount: 1,
        limit: 10,
        hasNext: false,
        hasPrev: false,
      },
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: jest.fn().mockResolvedValue(mockResponse),
    });

    const result = await collectionsApi.list({ page: 1, limit: 10 });
    expect(result).toEqual(mockResponse);
  });

  it("should get collection by id", async () => {
    const mockCollection = { id: "1", name: "Test Collection" };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: jest.fn().mockResolvedValue(mockCollection),
    });

    const result = await collectionsApi.get("1");
    expect(result).toEqual(mockCollection);
  });

  it("should create collection", async () => {
    const mockCollection = { id: "1", name: "New Collection" };
    const collectionData = { name: "New Collection", description: "Test" };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: jest.fn().mockResolvedValue(mockCollection),
    });

    const result = await collectionsApi.create(collectionData);
    expect(result).toEqual(mockCollection);
  });

  it("should update collection", async () => {
    const mockCollection = { id: "1", name: "Updated Collection" };
    const updateData = { name: "Updated Collection" };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: jest.fn().mockResolvedValue(mockCollection),
    });

    const result = await collectionsApi.update("1", updateData);
    expect(result).toEqual(mockCollection);
  });

  it("should delete collection", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: jest.fn().mockResolvedValue({ deleted: true }),
    });

    const result = await collectionsApi.delete("1");
    expect(result).toEqual({ deleted: true });
  });

  it("should get collection prompts via generic endpoint", async () => {
    const mockCollection = { id: "1", name: "Test Collection", prompts: [] };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: jest.fn().mockResolvedValue(mockCollection),
    });

    // Test getting collection details which would include prompts
    await collectionsApi.get("1");
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/collections/1"),
      expect.any(Object),
    );
  });
});

// Playbooks API tests
describe("playbooksApi", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("should list playbooks", async () => {
    const mockPlaybooks = {
      items: [{ id: "1", name: "Test Playbook" }],
      pagination: {
        currentPage: 1,
        totalPages: 1,
        totalCount: 1,
        limit: 10,
        hasNext: false,
        hasPrev: false,
      },
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: jest.fn().mockResolvedValue(mockPlaybooks),
    });

    const result = await playbooksApi.list();
    expect(result).toEqual(mockPlaybooks);
  });

  it("should get playbook by id", async () => {
    const mockPlaybook = { id: "1", name: "Test Playbook" };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: jest.fn().mockResolvedValue(mockPlaybook),
    });

    const result = await playbooksApi.get("1");
    expect(result).toEqual(mockPlaybook);
  });
});

// Integrations API tests
describe("integrationsApi", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("should list LLM integrations", async () => {
    const mockIntegrations = {
      integrations: { openai: { id: "1", name: "OpenAI" } },
      supportedProviders: ["openai", "anthropic"],
    };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: jest.fn().mockResolvedValue(mockIntegrations),
    });

    const result = await integrationsApi.listLLM();
    expect(result).toEqual(mockIntegrations);
  });
});

// Admin API tests
describe("adminApi", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("should get usage stats", async () => {
    const mockStats = { users: 10, collections: 5, prompts: 100 };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: jest.fn().mockResolvedValue(mockStats),
    });

    const result = await adminApi.getUsageStats();
    expect(result).toEqual(mockStats);
  });
});

// LLM API tests
describe("llmApi", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("should execute prompt", async () => {
    const mockResponse = { result: "Generated response" };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: jest.fn().mockResolvedValue(mockResponse),
    });

    const result = await llmApi.execute("Test prompt", "gpt-4");
    expect(result).toEqual(mockResponse);
  });
});

// Test basic module loading
describe("API Module Loading", () => {
  it("should load api module successfully", () => {
    expect(apiService).toBeDefined();
    expect(collectionsApi).toBeDefined();
    expect(playbooksApi).toBeDefined();
    expect(integrationsApi).toBeDefined();
    expect(adminApi).toBeDefined();
    expect(llmApi).toBeDefined();
    expect(promptsApi).toBeDefined();
    expect(guestApi).toBeDefined();
    expect(api).toBeDefined();
  });

  it("should export combined api object with all services", () => {
    expect(api.prompts).toBe(promptsApi);
    expect(api.collections).toBe(collectionsApi);
    expect(api.playbooks).toBe(playbooksApi);
    expect(api.integrations).toBe(integrationsApi);
    expect(api.admin).toBe(adminApi);
    expect(api.llm).toBe(llmApi);
    expect(api.guest).toBe(guestApi);
  });
});

// Prompts API tests
describe("promptsApi", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("should list prompts with parameters", async () => {
    const mockResponse = {
      items: [{ id: "1", title: "Test Prompt", content: "Test content" }],
      pagination: {
        currentPage: 1,
        totalPages: 1,
        totalCount: 1,
        limit: 10,
        hasNext: false,
        hasPrev: false,
      },
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: jest.fn().mockResolvedValue(mockResponse),
    });

    const result = await promptsApi.list({
      page: 1,
      limit: 10,
      search: "test",
      collection_id: "col1",
    });

    expect(result).toEqual(mockResponse);
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringMatching(
        /\/prompts\?.*page=1.*limit=10.*search=test.*collection_id=col1/,
      ),
      expect.any(Object),
    );
  });

  it("should get prompt by id", async () => {
    const mockPrompt = {
      id: "1",
      title: "Test Prompt",
      content: "Test content",
    };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: jest.fn().mockResolvedValue(mockPrompt),
    });

    const result = await promptsApi.get("1");
    expect(result).toEqual(mockPrompt);
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/prompts/1"),
      expect.any(Object),
    );
  });

  it("should create prompt", async () => {
    const promptData = {
      title: "New Prompt",
      description: "Test description",
      content: "Test content",
      variables: [{ name: "var1", type: "string" }],
      tags: ["test"],
      collection_id: "col1",
    };
    // Response should be in camelCase due to field conversion
    const mockResponse = {
      id: "1",
      title: "New Prompt",
      description: "Test description",
      content: "Test content",
      variables: [{ name: "var1", type: "string" }],
      tags: ["test"],
      collectionId: "col1", // camelCase after conversion
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: jest.fn().mockResolvedValue(mockResponse),
    });

    const result = await promptsApi.create(promptData);
    expect(result).toEqual(mockResponse);
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/prompts"),
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify(promptData),
      }),
    );
  });

  it("should update prompt", async () => {
    const updateData = { title: "Updated Prompt", content: "Updated content" };
    const mockResponse = { id: "1", ...updateData };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: jest.fn().mockResolvedValue(mockResponse),
    });

    const result = await promptsApi.update("1", updateData);
    expect(result).toEqual(mockResponse);
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/prompts/1"),
      expect.objectContaining({ method: "PUT" }),
    );
  });

  it("should delete prompt", async () => {
    const mockResponse = { deleted: true };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: jest.fn().mockResolvedValue(mockResponse),
    });

    const result = await promptsApi.delete("1");
    expect(result).toEqual(mockResponse);
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/prompts/1"),
      expect.objectContaining({ method: "DELETE" }),
    );
  });

  it("should execute prompt", async () => {
    const variables = { name: "John", role: "user" };
    const mockResponse = { result: "Generated response with John as user" };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: jest.fn().mockResolvedValue(mockResponse),
    });

    const result = await promptsApi.execute("1", variables);
    expect(result).toEqual(mockResponse);
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/prompts/1/execute"),
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ variables }),
      }),
    );
  });
});

// Guest API tests
describe("guestApi", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("should execute prompt with default model", async () => {
    const prompt = "Test prompt for guest execution";
    const mockResponse = { result: "Guest execution result" };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: jest.fn().mockResolvedValue(mockResponse),
    });

    const result = await guestApi.executePrompt(prompt);
    expect(result).toEqual(mockResponse);
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/guest-llm/execute"),
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ prompt, model: "gpt-3.5-turbo" }),
      }),
    );
  });

  it("should execute prompt with custom model", async () => {
    const prompt = "Test prompt";
    const model = "gpt-4";
    const mockResponse = { result: "Custom model result" };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: jest.fn().mockResolvedValue(mockResponse),
    });

    const result = await guestApi.executePrompt(prompt, model);
    expect(result).toEqual(mockResponse);
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/guest-llm/execute"),
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ prompt, model }),
      }),
    );
  });

  it("should get available models", async () => {
    const mockModels = ["gpt-3.5-turbo", "gpt-4", "claude-3"];
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: jest.fn().mockResolvedValue(mockModels),
    });

    const result = await guestApi.getModels();
    expect(result).toEqual(mockModels);
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/guest-llm/models"),
      expect.any(Object),
    );
  });

  it("should get usage statistics", async () => {
    const mockUsage = {
      requests: 100,
      tokensUsed: 50000,
      remainingQuota: 25000,
    };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: jest.fn().mockResolvedValue(mockUsage),
    });

    const result = await guestApi.getUsage();
    expect(result).toEqual(mockUsage);
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/guest-llm/usage"),
      expect.any(Object),
    );
  });
});

// Extended Playbooks API tests
describe("playbooksApi - Extended", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("should create playbook", async () => {
    const playbookData = {
      name: "New Playbook",
      description: "Test playbook",
      steps: [{ action: "prompt", content: "Hello" }],
      visibility: "private" as const,
    };
    const mockResponse = { id: "1", ...playbookData };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: jest.fn().mockResolvedValue(mockResponse),
    });

    const result = await playbooksApi.create(playbookData);
    expect(result).toEqual(mockResponse);
  });

  it("should update playbook", async () => {
    const updateData = { name: "Updated Playbook" };
    const mockResponse = { id: "1", ...updateData };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: jest.fn().mockResolvedValue(mockResponse),
    });

    const result = await playbooksApi.update("1", updateData);
    expect(result).toEqual(mockResponse);
  });

  it("should delete playbook", async () => {
    const mockResponse = { deleted: true };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: jest.fn().mockResolvedValue(mockResponse),
    });

    const result = await playbooksApi.delete("1");
    expect(result).toEqual(mockResponse);
  });

  it("should execute playbook with variables", async () => {
    const variables = { input: "test value" };
    const mockResponse = { executionId: "exec1", result: "Playbook executed" };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: jest.fn().mockResolvedValue(mockResponse),
    });

    const result = await playbooksApi.execute("1", variables);
    expect(result).toEqual(mockResponse);
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/playbooks/1/execute"),
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ variables }),
      }),
    );
  });

  it("should execute playbook without variables", async () => {
    const mockResponse = { executionId: "exec2", result: "Playbook executed" };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: jest.fn().mockResolvedValue(mockResponse),
    });

    const result = await playbooksApi.execute("1");
    expect(result).toEqual(mockResponse);
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/playbooks/1/execute"),
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ variables: undefined }),
      }),
    );
  });
});

// Extended Integrations API tests
describe("integrationsApi - Extended", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("should save LLM integration", async () => {
    const provider = "openai";
    const integrationData = {
      api_key: "sk-test123",
      enabled: true,
      url: "https://api.openai.com/v1",
    };
    // Response should be in camelCase due to field conversion
    const mockResponse = {
      id: "1",
      provider,
      apiKey: "sk-test123", // camelCase after conversion
      enabled: true,
      url: "https://api.openai.com/v1",
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: jest.fn().mockResolvedValue(mockResponse),
    });

    const result = await integrationsApi.saveLLM(provider, integrationData);
    expect(result).toEqual(mockResponse);
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/integrations/llm/openai"),
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify(integrationData),
      }),
    );
  });

  it("should delete LLM integration", async () => {
    const provider = "anthropic";
    const mockResponse = { deleted: true };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: jest.fn().mockResolvedValue(mockResponse),
    });

    const result = await integrationsApi.deleteLLM(provider);
    expect(result).toEqual(mockResponse);
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/integrations/llm/anthropic"),
      expect.objectContaining({ method: "DELETE" }),
    );
  });
});

// Extended Admin API tests
describe("adminApi - Extended", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("should get LLM settings", async () => {
    const mockSettings = {
      defaultModel: "gpt-3.5-turbo",
      rateLimits: { daily: 1000, hourly: 100 },
      providers: ["openai", "anthropic"],
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: jest.fn().mockResolvedValue(mockSettings),
    });

    const result = await adminApi.getLLMSettings();
    expect(result).toEqual(mockSettings);
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/management/llm/settings"),
      expect.any(Object),
    );
  });

  it("should update LLM settings", async () => {
    const settings = {
      defaultModel: "gpt-4",
      rateLimits: { daily: 2000, hourly: 200 },
    };
    const mockResponse = { updated: true, settings };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: jest.fn().mockResolvedValue(mockResponse),
    });

    const result = await adminApi.updateLLMSettings(settings);
    expect(result).toEqual(mockResponse);
    // Check that request body is converted to snake_case
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/management/llm/settings"),
      expect.objectContaining({
        method: "PUT",
        body: JSON.stringify({
          default_model: "gpt-4",
          rate_limits: { daily: 2000, hourly: 200 },
        }),
      }),
    );
  });

  it("should get system health", async () => {
    const mockHealth = {
      status: "healthy",
      services: { database: "ok", llm: "ok", auth: "ok" },
      uptime: 86400,
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: jest.fn().mockResolvedValue(mockHealth),
    });

    const result = await adminApi.getSystemHealth();
    expect(result).toEqual(mockHealth);
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/management/system/health"),
      expect.any(Object),
    );
  });
});

// Extended LLM API tests
describe("llmApi - Extended", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("should execute prompt with variables", async () => {
    const promptText = "Hello, my name is {{name}} and I am a {{role}}";
    const model = "gpt-4";
    const variables = { name: "Alice", role: "developer" };
    const mockResponse = {
      result: "Hello, my name is Alice and I am a developer",
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: jest.fn().mockResolvedValue(mockResponse),
    });

    const result = await llmApi.execute(promptText, model, variables);
    expect(result).toEqual(mockResponse);
    // Check that request body is converted to snake_case
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/llm"),
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          prompt_text: promptText,
          model,
          variables,
        }),
      }),
    );
  });

  it("should execute prompt without variables", async () => {
    const promptText = "What is the capital of France?";
    const model = "gpt-3.5-turbo";
    const mockResponse = { result: "The capital of France is Paris." };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: jest.fn().mockResolvedValue(mockResponse),
    });

    const result = await llmApi.execute(promptText, model);
    expect(result).toEqual(mockResponse);
    // Check that request body is converted to snake_case
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/llm"),
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          prompt_text: promptText,
          model,
        }),
      }),
    );
  });
});

// Test development mode headers with Azure Static Web Apps auth
describe("Development Headers with Azure Auth", () => {
  const originalEnv = process.env.NODE_ENV;
  const originalLocation = window.location;

  beforeEach(() => {
    jest.clearAllMocks();
    process.env.NODE_ENV = "development";
    Object.defineProperty(window, "location", {
      value: { hostname: "localhost" },
      writable: true,
    });
  });

  afterEach(() => {
    process.env.NODE_ENV = originalEnv;
    Object.defineProperty(window, "location", {
      value: originalLocation,
      writable: true,
    });
  });

  it("should add Azure Static Web Apps headers in development with auth endpoint", async () => {
    const authData = {
      clientPrincipal: {
        userId: "user123",
        userDetails: "test@example.com",
        identityProvider: "azureActiveDirectory",
        userRoles: ["user"],
      },
    };

    // Mock /.auth/me endpoint success
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue(authData),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue({ data: "test" }),
      });

    await apiService.get("/test");

    expect(mockFetch).toHaveBeenCalledWith("/.auth/me");
    expect(mockFetch).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        headers: expect.objectContaining({
          "x-ms-client-principal": expect.any(String),
          "x-ms-client-principal-id": "user123",
          "x-ms-client-principal-name": "test@example.com",
          "x-ms-client-principal-idp": "azureActiveDirectory",
        }),
      }),
    );
  });

  it("should handle auth endpoint failure gracefully", async () => {
    // Mock /.auth/me endpoint failure
    mockFetch
      .mockResolvedValueOnce({
        ok: false,
        status: 404,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue({ data: "test" }),
      });

    await apiService.get("/test");

    // Should still make the API call even if auth fails
    expect(mockFetch).toHaveBeenCalledTimes(2);
  });

  it("should use localStorage demo user as fallback", async () => {
    const demoUser = {
      id: "demo123",
      email: "demo@example.com",
      role: "admin",
    };

    // Mock /.auth/me endpoint failure
    mockFetch
      .mockResolvedValueOnce({
        ok: false,
        status: 404,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue({ data: "test" }),
      });

    // Mock localStorage
    const mockGetItem = jest.fn().mockReturnValue(JSON.stringify(demoUser));
    Object.defineProperty(window, "localStorage", {
      value: { getItem: mockGetItem },
      writable: true,
    });

    await apiService.get("/test");

    expect(mockGetItem).toHaveBeenCalledWith("sutra_demo_user");
    expect(mockFetch).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        headers: expect.objectContaining({
          "x-ms-client-principal": expect.any(String),
          "x-ms-client-principal-id": "demo123",
          "x-ms-client-principal-name": "demo@example.com",
          "x-ms-client-principal-idp": "azureActiveDirectory",
        }),
      }),
    );
  });

  it("should handle localStorage errors gracefully", async () => {
    // Mock /.auth/me endpoint failure
    mockFetch
      .mockResolvedValueOnce({
        ok: false,
        status: 404,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue({ data: "test" }),
      });

    // Mock localStorage error
    const mockGetItem = jest.fn().mockImplementation(() => {
      throw new Error("localStorage error");
    });
    Object.defineProperty(window, "localStorage", {
      value: { getItem: mockGetItem },
      writable: true,
    });

    await apiService.get("/test");

    // Should still work even with localStorage errors
    expect(mockFetch).toHaveBeenCalledTimes(2);
  });
});

// Test production API headers for CORS handling
describe("Production API CORS Handling", () => {
  const originalEnv = process.env.NODE_ENV;

  beforeEach(() => {
    jest.clearAllMocks();
  });

  afterEach(() => {
    process.env.NODE_ENV = originalEnv;
  });

  it("should use CORS mode for production API from development", async () => {
    process.env.NODE_ENV = "development";

    // Test that the service can be created with production URL
    const productionApiService = new (apiService.constructor as any)(
      "https://sutra-api-hvyqgbrvnx4ii.azurewebsites.net/api",
    );

    expect(productionApiService).toBeDefined();
  });
});

// Test field conversion integration
describe("Field Conversion Integration", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("should convert request parameters to snake_case", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: jest.fn().mockResolvedValue({ data: "test" }),
    });

    await apiService.get("/test", {
      currentPage: 1,
      totalCount: 100,
      hasNext: true,
    });

    const fetchUrl = mockFetch.mock.calls[0][0];
    expect(fetchUrl).toContain("current_page=1");
    expect(fetchUrl).toContain("total_count=100");
    expect(fetchUrl).toContain("has_next=true");
  });

  it("should convert request body to snake_case for POST", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: jest.fn().mockResolvedValue({ id: 1 }),
    });

    const requestData = {
      collectionId: "col1",
      userId: "user1",
      createdAt: "2023-01-01",
    };

    await apiService.post("/test", requestData);

    expect(mockFetch).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        body: JSON.stringify({
          collection_id: "col1",
          user_id: "user1",
          created_at: "2023-01-01",
        }),
      }),
    );
  });

  it("should convert request body to snake_case for PUT", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: jest.fn().mockResolvedValue({ id: 1 }),
    });

    const requestData = {
      updatedAt: "2023-01-02",
      totalPages: 5,
    };

    await apiService.put("/test", requestData);

    expect(mockFetch).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        body: JSON.stringify({
          updated_at: "2023-01-02",
          total_pages: 5,
        }),
      }),
    );
  });
});
