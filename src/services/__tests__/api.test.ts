import {
  apiService,
  collectionsApi,
  playbooksApi,
  integrationsApi,
  adminApi,
  llmApi,
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
        current_page: 1,
        total_pages: 1,
        total_count: 1,
        limit: 10,
        has_next: false,
        has_prev: false,
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
        current_page: 1,
        total_pages: 1,
        total_count: 1,
        limit: 10,
        has_next: false,
        has_prev: false,
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
  });
});
