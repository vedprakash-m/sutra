import React from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import ForgeProjectCard from "../ForgeProjectCard";

jest.mock("@heroicons/react/24/outline", () => ({
  CalendarIcon: () => <span data-testid="calendar-icon" />,
  UserGroupIcon: () => <span data-testid="usergroup-icon" />,
  DocumentTextIcon: () => <span data-testid="document-icon" />,
  ArrowRightIcon: () => <span data-testid="arrow-icon" />,
}));

describe("ForgeProjectCard", () => {
  const project = {
    id: "project-1",
    name: "Sutra Forge",
    description: "Build a robust forge workflow",
    currentStage: "idea_refinement" as const,
    status: "active" as const,
    priority: "high" as const,
    progressPercentage: 62,
    createdAt: "2026-01-01T00:00:00Z",
    updatedAt: "2026-01-15T00:00:00Z",
    tags: ["ai", "workflow", "architecture", "testing"],
    collaboratorsCount: 3,
    artifactsCount: 5,
    ownerId: "user-1",
  };

  const stageConfig = {
    idea_refinement: {
      name: "Idea Refinement",
      description: "desc",
      icon: "💡",
      color: "stage-color",
    },
  };

  const statusConfig = {
    active: {
      name: "Active",
      color: "status-color",
    },
  };

  it("renders project name and description", () => {
    render(
      <ForgeProjectCard
        project={project}
        onSelect={jest.fn()}
        stageConfig={stageConfig}
        statusConfig={statusConfig}
      />,
    );

    expect(screen.getByText("Sutra Forge")).toBeInTheDocument();
    expect(
      screen.getByText("Build a robust forge workflow"),
    ).toBeInTheDocument();
  });

  it("renders stage, status and priority badges", () => {
    render(
      <ForgeProjectCard
        project={project}
        onSelect={jest.fn()}
        stageConfig={stageConfig}
        statusConfig={statusConfig}
      />,
    );

    expect(screen.getByText("Idea Refinement")).toBeInTheDocument();
    expect(screen.getByText("Active")).toBeInTheDocument();
    expect(screen.getByText("High")).toBeInTheDocument();
  });

  it("renders progress and metadata", () => {
    render(
      <ForgeProjectCard
        project={project}
        onSelect={jest.fn()}
        stageConfig={stageConfig}
        statusConfig={statusConfig}
      />,
    );

    expect(screen.getByText("62%")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
    expect(screen.getByText("5")).toBeInTheDocument();
  });

  it("shows only first three tags and overflow count", () => {
    render(
      <ForgeProjectCard
        project={project}
        onSelect={jest.fn()}
        stageConfig={stageConfig}
        statusConfig={statusConfig}
      />,
    );

    expect(screen.getByText("ai")).toBeInTheDocument();
    expect(screen.getByText("workflow")).toBeInTheDocument();
    expect(screen.getByText("architecture")).toBeInTheDocument();
    expect(screen.getByText("+1 more")).toBeInTheDocument();
    expect(screen.queryByText("testing")).not.toBeInTheDocument();
  });

  it("calls onSelect when card body is clicked", () => {
    const onSelect = jest.fn();
    render(
      <ForgeProjectCard
        project={project}
        onSelect={onSelect}
        stageConfig={stageConfig}
        statusConfig={statusConfig}
      />,
    );

    fireEvent.click(screen.getByText("Sutra Forge"));
    expect(onSelect).toHaveBeenCalledWith(project);
  });
});
