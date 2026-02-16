import React from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import { LLMProviderSelector } from "../LLMProviderSelector";

const mockUseForgeStore = jest.fn();

jest.mock("@/stores/forgeStore", () => ({
  useForgeStore: () => mockUseForgeStore(),
}));

describe("LLMProviderSelector", () => {
  const setLLMProvider = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseForgeStore.mockReturnValue({
      selectedProvider: "openai",
      selectedModel: "gpt-4o",
      setLLMProvider,
    });
  });

  it("renders available provider tabs", () => {
    render(<LLMProviderSelector />);

    expect(screen.getByRole("button", { name: "OpenAI" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Anthropic" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Google" })).toBeInTheDocument();
  });

  it("renders model dropdown for selected provider", () => {
    render(<LLMProviderSelector />);

    const select = screen.getByRole("combobox");
    expect(select).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "GPT-4o" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: "GPT-4 Turbo" })).toBeInTheDocument();
  });

  it("calls setLLMProvider when provider is changed", () => {
    render(<LLMProviderSelector />);

    fireEvent.click(screen.getByRole("button", { name: "Anthropic" }));
    expect(setLLMProvider).toHaveBeenCalledWith("anthropic");
  });

  it("calls setLLMProvider with selected model on model change", () => {
    render(<LLMProviderSelector />);

    fireEvent.change(screen.getByRole("combobox"), {
      target: { value: "gpt-3.5-turbo" },
    });

    expect(setLLMProvider).toHaveBeenCalledWith("openai", "gpt-3.5-turbo");
  });

  it("shows cost tier indicator for current model", () => {
    render(<LLMProviderSelector />);

    expect(screen.getByText("$$$")).toBeInTheDocument();
  });

  it("does not render cost indicator when selected model is not in available list", () => {
    mockUseForgeStore.mockReturnValue({
      selectedProvider: "openai",
      selectedModel: "unknown-model",
      setLLMProvider,
    });

    render(<LLMProviderSelector />);
    expect(screen.queryByText("$")).not.toBeInTheDocument();
    expect(screen.queryByText("$$")).not.toBeInTheDocument();
    expect(screen.queryByText("$$$")).not.toBeInTheDocument();
  });
});
