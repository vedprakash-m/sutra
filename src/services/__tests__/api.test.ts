import { apiService, collectionsApi, playbooksApi, integrationsApi, adminApi, llmApi } from "../api";

// Mock fetch globally
const mockFetch = jest.fn();
global.fetch = mockFetch;

// Mock window.location
Object.defineProperty(window, 'location', {
  value: {
    href: '',
  },
  writable: true,
});

describe("ApiService", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    window.location.href = '';
  });

  describe("setToken", () => {
    it("should set auth token", () => {
      apiService.setToken("test-token");
      // Token is private, but we can test it indirectly through headers
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

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/test"),
        {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
            "Authorization": "Bearer test-token",
            "X-Client-Name": "sutra-web",
            "X-Client-Version": "1.0.0",
          },
        }
      );
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
        expect.any(Object)
      );
    });

    it("should filter out null and undefined parameters", async () => {
      const mockResponse = { data: "test" };
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue(mockResponse),
      });

      await apiService.get("/test", { page: 1, limit: null, search: undefined });

      const fetchCall = mockFetch.mock.calls[0][0];
      expect(fetchCall).toContain("page=1");
      expect(fetchCall).not.toContain("limit=");
      expect(fetchCall).not.toContain("search=");
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

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/test"),
        {
          method: "POST",
          headers: expect.any(Object),
          body: JSON.stringify(requestData),
        }
      );
      expect(result).toEqual(mockResponse);
    });

    it("should handle POST without data", async () => {
      const mockResponse = { success: true };
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue(mockResponse),
      });

      await apiService.post("/test");

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/test"),
        {
          method: "POST",
          headers: expect.any(Object),
          body: undefined,
        }
      );
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

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/test"),
        {
          method: "PUT",
          headers: expect.any(Object),
          body: JSON.stringify(requestData),
        }
      );
      expect(result).toEqual(mockResponse);
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

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("/test"),
        {
          method: "DELETE",
          headers: expect.any(Object),
        }
      );
      expect(result).toEqual(mockResponse);
    });
  });

  describe("error handling", () => {
    it("should handle 401 errors by redirecting to login", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: jest.fn().mockResolvedValue({ message: "Unauthorized" }),
      });

      await expect(apiService.get("/test")).rejects.toThrow("Authentication required");
      expect(window.location.href).toBe("/login");
    });

    it("should handle error responses with JSON error data", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: jest.fn().mockResolvedValue({ message: "Bad Request" }),
      });

      await expect(apiService.get("/test")).rejects.toThrow("Bad Request");
    });

    it("should handle error responses without JSON data", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: jest.fn().mockRejectedValue(new Error("Invalid JSON")),
      });

      await expect(apiService.get("/test")).rejects.toThrow("HTTP error! status: 500");
    });

    it("should handle network errors", async () => {
      mockFetch.mockRejectedValueOnce(new Error("Network error"));

      await expect(apiService.get("/test")).rejects.toThrow("Network error");
    });
  });

  describe("headers", () => {
    it("should include authorization header when token is set", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue({}),
      });

      apiService.setToken("test-token");
      await apiService.get("/test");

      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            "Authorization": "Bearer test-token",
          }),
        })
      );
    });

    it("should not include authorization header when token is null", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue({}),
      });

      apiService.setToken(null);
      await apiService.get("/test");

      const headers = mockFetch.mock.calls[0][1].headers;
      expect(headers).not.toHaveProperty("Authorization");
    });

    it("should always include client headers", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: jest.fn().mockResolvedValue({}),
      });

      await apiService.get("/test");

      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            "Content-Type": "application/json",
            "X-Client-Name": "sutra-web",
            "X-Client-Version": "1.0.0",
          }),
        })
      );
    });
  });
});

describe("Collections API", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("should list collections", async () => {
    const mockResponse = { items: [], pagination: {} };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: jest.fn().mockResolvedValue(mockResponse),
    });

    const result = await collectionsApi.list({ page: 1, limit: 10 });

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringMatching(/\/collections\?.*page=1.*limit=10/),
      expect.any(Object)
    );
    expect(result).toEqual(mockResponse);
  });

  it("should get single collection", async () => {
    const mockCollection = { id: "1", name: "Test Collection" };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: jest.fn().mockResolvedValue(mockCollection),
    });

    const result = await collectionsApi.get("1");

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/collections/1"),
      expect.any(Object)
    );
    expect(result).toEqual(mockCollection);
  });

  it("should create collection", async () => {
    const newCollection = { name: "New Collection" };
    const mockResponse = { id: "1", ...newCollection };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: jest.fn().mockResolvedValue(mockResponse),
    });

    const result = await collectionsApi.create(newCollection);

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/collections"),
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify(newCollection),
      })
    );
    expect(result).toEqual(mockResponse);
  });

  it("should update collection", async () => {
    const updateData = { name: "Updated Collection" };
    const mockResponse = { id: "1", ...updateData };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: jest.fn().mockResolvedValue(mockResponse),
    });

    const result = await collectionsApi.update("1", updateData);

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/collections/1"),
      expect.objectContaining({
        method: "PUT",
        body: JSON.stringify(updateData),
      })
    );
    expect(result).toEqual(mockResponse);
  });

  it("should delete collection", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: jest.fn().mockResolvedValue({ success: true }),
    });

    await collectionsApi.delete("1");

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/collections/1"),
      expect.objectContaining({
        method: "DELETE",
      })
    );
  });
});

describe("Playbooks API", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("should list playbooks", async () => {
    const mockResponse = { items: [], pagination: {} };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: jest.fn().mockResolvedValue(mockResponse),
    });

    await playbooksApi.list();

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/playbooks"),
      expect.any(Object)
    );
  });

  it("should execute playbook", async () => {
    const variables = { input: "test" };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: jest.fn().mockResolvedValue({ execution_id: "exec-1" }),
    });

    await playbooksApi.execute("1", variables);

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/playbooks/1/execute"),
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ variables }),
      })
    );
  });
});

describe("Integrations API", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("should list LLM integrations", async () => {
    const mockResponse = { integrations: {}, supportedProviders: [] };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: jest.fn().mockResolvedValue(mockResponse),
    });

    await integrationsApi.listLLM();

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/integrations/llm"),
      expect.any(Object)
    );
  });

  it("should save LLM integration", async () => {
    const integration = { name: "OpenAI", api_key: "key" };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: jest.fn().mockResolvedValue(integration),
    });

    await integrationsApi.saveLLM("openai", integration);

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/integrations/llm/openai"),
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify(integration),
      })
    );
  });
});

describe("Admin API", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("should get system health", async () => {
    const mockHealth = { status: "healthy" };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: jest.fn().mockResolvedValue(mockHealth),
    });

    await adminApi.getSystemHealth();

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/management/system/health"),
      expect.any(Object)
    );
  });

  it("should get usage stats", async () => {
    const mockStats = { requests: 100 };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: jest.fn().mockResolvedValue(mockStats),
    });

    await adminApi.getUsageStats();

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/management/usage"),
      expect.any(Object)
    );
  });
});

describe("LLM API", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("should execute LLM request", async () => {
    const mockResponse = { result: "Generated text" };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: jest.fn().mockResolvedValue(mockResponse),
    });

    await llmApi.execute("Test prompt", "gpt-3.5-turbo", { temp: 0.7 });

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/llm"),
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          promptText: "Test prompt",
          model: "gpt-3.5-turbo",
          variables: { temp: 0.7 },
        }),
      })
    );
  });
});
