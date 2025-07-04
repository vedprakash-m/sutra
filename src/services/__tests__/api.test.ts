import { apiService } from "../api";

// Mock the config module to provide a stable base URL
jest.mock("../../config", () => ({
  getAppConfig: jest.fn(() => ({
    api: {
      baseUrl: "http://localhost:7071/api",
      timeout: 30000,
      retryAttempts: 3,
    },
  })),
}));

// Mock window.location to prevent navigation errors
Object.defineProperty(window, "location", {
  value: {
    href: "",
    hostname: "localhost",
  },
  writable: true,
});

// Mock fetch globally
const mockFetch = jest.fn();
global.fetch = mockFetch;

describe("ApiService", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("basic functionality", () => {
    it("should make GET requests", async () => {
      const mockResponse = { data: "test" };
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: jest.fn().mockResolvedValue(mockResponse),
        headers: new Headers(),
      });

      const result = await apiService.get("/test");

      expect(mockFetch).toHaveBeenCalledWith(
        "http://localhost:7071/api/test",
        expect.objectContaining({
          method: "GET",
          headers: expect.objectContaining({
            "Content-Type": "application/json",
          }),
        }),
      );
      expect(result).toEqual(mockResponse);
    });

    it("should make POST requests with data", async () => {
      const mockResponse = { id: 1, status: "created" };
      const postData = { name: "test", description: "test description" };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 201,
        json: jest.fn().mockResolvedValue(mockResponse),
        headers: new Headers(),
      });

      const result = await apiService.post("/test", postData);

      expect(mockFetch).toHaveBeenCalledWith(
        "http://localhost:7071/api/test",
        expect.objectContaining({
          method: "POST",
          headers: expect.objectContaining({
            "Content-Type": "application/json",
          }),
          body: JSON.stringify(postData),
        }),
      );
      expect(result).toEqual(mockResponse);
    });

    it("should handle PUT requests", async () => {
      const mockResponse = { id: 1, status: "updated" };
      const updateData = { name: "updated test" };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: jest.fn().mockResolvedValue(mockResponse),
        headers: new Headers(),
      });

      const result = await apiService.put("/test/1", updateData);

      expect(mockFetch).toHaveBeenCalledWith(
        "http://localhost:7071/api/test/1",
        expect.objectContaining({
          method: "PUT",
          headers: expect.objectContaining({
            "Content-Type": "application/json",
          }),
          body: JSON.stringify(updateData),
        }),
      );
      expect(result).toEqual(mockResponse);
    });

    it("should handle DELETE requests", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 204,
        json: jest.fn().mockResolvedValue({}),
        headers: new Headers(),
      });

      await apiService.delete("/test/1");

      expect(mockFetch).toHaveBeenCalledWith(
        "http://localhost:7071/api/test/1",
        expect.objectContaining({
          method: "DELETE",
          headers: expect.objectContaining({
            "Content-Type": "application/json",
          }),
        }),
      );
    });
  });

  describe("error handling", () => {
    it("should handle 404 errors", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: jest.fn().mockResolvedValue({ message: "Not found" }),
        headers: new Headers(),
      });

      await expect(apiService.get("/nonexistent")).rejects.toThrow("Not found");
    });

    it("should handle 401 unauthorized errors", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: jest.fn().mockResolvedValue({ message: "Unauthorized" }),
        headers: new Headers(),
      });

      await expect(apiService.get("/protected")).rejects.toThrow(
        "Authentication required",
      );
    });

    it("should handle 500 server errors", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: jest.fn().mockResolvedValue({ message: "Internal Server Error" }),
        headers: new Headers(),
      });

      await expect(apiService.get("/error")).rejects.toThrow(
        "Internal Server Error",
      );
    });

    it("should handle network errors", async () => {
      mockFetch.mockRejectedValueOnce(new Error("Network error"));

      await expect(apiService.get("/test")).rejects.toThrow("Network error");
    });
  });

  describe("authentication", () => {
    it("should include auth token when provided", async () => {
      const mockResponse = { data: "authenticated" };
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: jest.fn().mockResolvedValue(mockResponse),
        headers: new Headers(),
      });

      await apiService.get("/test", { token: "test-token" });

      expect(mockFetch).toHaveBeenCalledWith(
        "http://localhost:7071/api/test?token=test-token",
        expect.objectContaining({
          method: "GET",
          headers: expect.objectContaining({
            "Content-Type": "application/json",
          }),
        }),
      );
    });

    it("should work without auth token", async () => {
      const mockResponse = { data: "public" };
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: jest.fn().mockResolvedValue(mockResponse),
        headers: new Headers(),
      });

      await apiService.get("/public");

      expect(mockFetch).toHaveBeenCalledWith(
        "http://localhost:7071/api/public",
        expect.objectContaining({
          headers: expect.not.objectContaining({
            Authorization: expect.anything(),
          }),
        }),
      );
    });
  });
});
