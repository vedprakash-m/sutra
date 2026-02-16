import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { ForgeExportButton } from "../ForgeExportButton";
import { forgeApi } from "@/services/api";

jest.mock("@/services/api", () => {
  const actual = jest.requireActual("@/services/__mocks__/api");
  return actual;
});

describe("ForgeExportButton", () => {
  const exportMock = forgeApi.exportPlaybook as jest.Mock;
  const createObjectURLMock = jest.fn(() => "blob:test-url");
  const revokeObjectURLMock = jest.fn();
  const openMock = jest.fn();
  let anchorClickSpy: jest.SpyInstance;

  beforeEach(() => {
    jest.clearAllMocks();
    anchorClickSpy = jest
      .spyOn(HTMLAnchorElement.prototype, "click")
      .mockImplementation(() => {});
    exportMock.mockResolvedValue({
      success: true,
      blob: new Blob(["x"]),
      filename: "artifact.json",
    });

    Object.defineProperty(window, "open", {
      writable: true,
      value: openMock,
    });

    Object.defineProperty(global.URL, "createObjectURL", {
      writable: true,
      value: createObjectURLMock,
    });
    Object.defineProperty(global.URL, "revokeObjectURL", {
      writable: true,
      value: revokeObjectURLMock,
    });
  });

  afterEach(() => {
    anchorClickSpy.mockRestore();
  });

  it("renders with default label", () => {
    render(<ForgeExportButton projectId="project-1" />);
    expect(screen.getByRole("button", { name: "Export" })).toBeInTheDocument();
  });

  it("renders custom label", () => {
    render(<ForgeExportButton projectId="project-1" label="Download" />);
    expect(
      screen.getByRole("button", { name: "Download" }),
    ).toBeInTheDocument();
  });

  it("opens and shows export format options", () => {
    render(<ForgeExportButton projectId="project-1" />);

    fireEvent.click(screen.getByRole("button", { name: "Export" }));
    expect(screen.getByRole("button", { name: /JSON/i })).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Markdown/i }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /PDF/i })).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /ZIP Archive/i }),
    ).toBeInTheDocument();
  });

  it("calls export API with selected format", async () => {
    render(<ForgeExportButton projectId="project-123" />);

    fireEvent.click(screen.getByRole("button", { name: "Export" }));
    fireEvent.click(screen.getByRole("button", { name: /Markdown/i }));

    await waitFor(() => {
      expect(exportMock).toHaveBeenCalledWith("project-123", "markdown");
    });
  });

  it("downloads blob result", async () => {
    const appendSpy = jest.spyOn(document.body, "appendChild");
    const removeSpy = jest.spyOn(document.body, "removeChild");

    render(<ForgeExportButton projectId="project-1" />);
    fireEvent.click(screen.getByRole("button", { name: "Export" }));
    fireEvent.click(screen.getByRole("button", { name: /JSON/i }));

    await waitFor(() => {
      expect(createObjectURLMock).toHaveBeenCalled();
      expect(appendSpy).toHaveBeenCalled();
      expect(removeSpy).toHaveBeenCalled();
      expect(revokeObjectURLMock).toHaveBeenCalledWith("blob:test-url");
    });

    appendSpy.mockRestore();
    removeSpy.mockRestore();
  });

  it("opens downloadUrl in new tab when no blob is returned", async () => {
    exportMock.mockResolvedValueOnce({
      success: true,
      downloadUrl: "https://example.com/export.pdf",
      filename: "artifact.pdf",
    });

    render(<ForgeExportButton projectId="project-1" />);
    fireEvent.click(screen.getByRole("button", { name: "Export" }));
    fireEvent.click(screen.getByRole("button", { name: /PDF/i }));

    await waitFor(() => {
      expect(openMock).toHaveBeenCalledWith(
        "https://example.com/export.pdf",
        "_blank",
      );
    });
  });

  it("closes menu after export", async () => {
    render(<ForgeExportButton projectId="project-1" />);
    fireEvent.click(screen.getByRole("button", { name: "Export" }));
    expect(screen.getByRole("button", { name: /JSON/i })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /JSON/i }));

    await waitFor(() => {
      expect(
        screen.queryByRole("button", { name: /JSON/i }),
      ).not.toBeInTheDocument();
    });
  });
});
