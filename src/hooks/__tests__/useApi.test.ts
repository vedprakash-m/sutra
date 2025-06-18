import { renderHook, act, waitFor } from "@testing-library/react";
import { useApi, useAsyncAction } from "../useApi";

// Mock the auth provider
const mockUseAuth = jest.fn();
jest.mock("../../components/auth/AuthProvider", () => ({
  useAuth: () => mockUseAuth(),
}));

// Import the mocked API service
import { apiService } from "../../services/api";

describe("useApi", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseAuth.mockReturnValue({
      token: "test-token",
    });
  });

  it("should initialize with loading state", () => {
    const mockApiCall = jest.fn().mockResolvedValue("test data");

    const { result } = renderHook(() => useApi(mockApiCall));

    expect(result.current.data).toBeNull();
    expect(result.current.loading).toBe(true);
    expect(result.current.error).toBeNull();
  });

  it("should fetch data successfully", async () => {
    const mockData = { id: 1, name: "Test" };
    const mockApiCall = jest.fn().mockResolvedValue(mockData);

    const { result } = renderHook(() => useApi(mockApiCall));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.data).toEqual(mockData);
    expect(result.current.error).toBeNull();
    expect(mockApiCall).toHaveBeenCalledTimes(1);
  });

  it("should set token on API service when token is available", async () => {
    const mockApiCall = jest.fn().mockResolvedValue("test data");

    renderHook(() => useApi(mockApiCall));

    await waitFor(() => {
      expect(apiService.setToken).toHaveBeenCalledWith("test-token");
    });
  });

  it("should handle API errors", async () => {
    const mockError = new Error("API Error");
    const mockApiCall = jest.fn().mockRejectedValue(mockError);

    const { result } = renderHook(() => useApi(mockApiCall));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.data).toBeNull();
    expect(result.current.error).toBe("API Error");
  });

  it("should handle non-Error exceptions", async () => {
    const mockApiCall = jest.fn().mockRejectedValue("String error");

    const { result } = renderHook(() => useApi(mockApiCall));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.data).toBeNull();
    expect(result.current.error).toBe("An error occurred");
  });

  it("should refetch data when refetch is called", async () => {
    const mockData1 = { id: 1, name: "Test 1" };
    const mockData2 = { id: 2, name: "Test 2" };
    const mockApiCall = jest
      .fn()
      .mockResolvedValueOnce(mockData1)
      .mockResolvedValueOnce(mockData2);

    const { result } = renderHook(() => useApi(mockApiCall));

    await waitFor(() => {
      expect(result.current.data).toEqual(mockData1);
    });

    await act(async () => {
      await result.current.refetch();
    });

    expect(result.current.data).toEqual(mockData2);
    expect(mockApiCall).toHaveBeenCalledTimes(2);
  });

  it("should not fetch when token is null", () => {
    mockUseAuth.mockReturnValue({
      token: null,
    });

    const mockApiCall = jest.fn().mockResolvedValue("test data");

    renderHook(() => useApi(mockApiCall));

    expect(mockApiCall).not.toHaveBeenCalled();
  });

  it("should refetch when dependencies change", async () => {
    const mockApiCall = jest.fn().mockResolvedValue("test data");
    let dependency = "dep1";

    const { rerender } = renderHook(() => useApi(mockApiCall, [dependency]));

    await waitFor(() => {
      expect(mockApiCall).toHaveBeenCalledTimes(1);
    });

    dependency = "dep2";
    rerender();

    await waitFor(() => {
      expect(mockApiCall).toHaveBeenCalledTimes(2);
    });
  });

  it("should not refetch when dependencies don't change", async () => {
    const mockApiCall = jest.fn().mockResolvedValue("test data");
    const dependency = "dep1";

    const { rerender } = renderHook(() => useApi(mockApiCall, [dependency]));

    await waitFor(() => {
      expect(mockApiCall).toHaveBeenCalledTimes(1);
    });

    rerender();

    // Should not call again since dependency didn't change
    expect(mockApiCall).toHaveBeenCalledTimes(1);
  });

  it("should set loading to true during refetch", async () => {
    const mockApiCall = jest
      .fn()
      .mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve("data"), 100)),
      );

    const { result } = renderHook(() => useApi(mockApiCall));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    act(() => {
      result.current.refetch();
    });

    expect(result.current.loading).toBe(true);
  });
});

describe("useAsyncAction", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseAuth.mockReturnValue({
      token: "test-token",
    });
  });

  it("should initialize with default state", () => {
    const { result } = renderHook(() => useAsyncAction());

    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
    expect(typeof result.current.execute).toBe("function");
  });

  it("should execute action successfully", async () => {
    const mockAction = jest.fn().mockResolvedValue("success");
    const { result } = renderHook(() => useAsyncAction());

    let executionResult;
    await act(async () => {
      executionResult = await result.current.execute(mockAction);
    });

    expect(executionResult).toBe("success");
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
    expect(mockAction).toHaveBeenCalledTimes(1);
  });

  it("should set loading state during execution", async () => {
    const mockAction = jest
      .fn()
      .mockImplementation(
        () =>
          new Promise((resolve) => setTimeout(() => resolve("success"), 100)),
      );
    const { result } = renderHook(() => useAsyncAction());

    act(() => {
      result.current.execute(mockAction);
    });

    expect(result.current.loading).toBe(true);

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
  });

  it("should handle action errors", async () => {
    const mockError = new Error("Action failed");
    const mockAction = jest.fn().mockRejectedValue(mockError);
    const { result } = renderHook(() => useAsyncAction());

    await act(async () => {
      try {
        await result.current.execute(mockAction);
      } catch (error) {
        // Expected to throw
      }
    });

    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBe("Action failed");
  });

  it("should handle non-Error exceptions in actions", async () => {
    const mockAction = jest.fn().mockRejectedValue("String error");
    const { result } = renderHook(() => useAsyncAction());

    await act(async () => {
      try {
        await result.current.execute(mockAction);
      } catch (error) {
        // Expected to throw
      }
    });

    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBe("An error occurred");
  });

  it("should set token on API service when executing action", async () => {
    const mockAction = jest.fn().mockResolvedValue("success");
    const { result } = renderHook(() => useAsyncAction());

    await act(async () => {
      await result.current.execute(mockAction);
    });

    expect(apiService.setToken).toHaveBeenCalledWith("test-token");
  });

  it("should not set token when token is null", async () => {
    mockUseAuth.mockReturnValue({
      token: null,
    });

    const mockAction = jest.fn().mockResolvedValue("success");
    const { result } = renderHook(() => useAsyncAction());

    await act(async () => {
      await result.current.execute(mockAction);
    });

    expect(apiService.setToken).not.toHaveBeenCalled();
  });

  it("should clear error on subsequent execution", async () => {
    const mockAction = jest
      .fn()
      .mockRejectedValueOnce(new Error("First error"))
      .mockResolvedValueOnce("success");
    const { result } = renderHook(() => useAsyncAction());

    // First execution with error
    await act(async () => {
      try {
        await result.current.execute(mockAction);
      } catch (error) {
        // Expected to throw
      }
    });

    expect(result.current.error).toBe("First error");

    // Second execution should clear error
    await act(async () => {
      await result.current.execute(mockAction);
    });

    expect(result.current.error).toBeNull();
  });

  it("should return null when action throws", async () => {
    const mockAction = jest.fn().mockRejectedValue(new Error("Action failed"));
    const { result } = renderHook(() => useAsyncAction());

    let executionResult;
    await act(async () => {
      try {
        executionResult = await result.current.execute(mockAction);
      } catch (error) {
        executionResult = null;
      }
    });

    expect(executionResult).toBeNull();
  });
});
