/**
 * ForgeProjectDetails - Detailed view of a Forge project with stage navigation
 */
import { useState } from "react";
import {
  ArrowLeftIcon,
  PencilIcon,
  UserGroupIcon,
  DocumentTextIcon,
  ChartBarIcon,
  CogIcon,
  SparklesIcon,
  CheckCircleIcon,
  PlayCircleIcon,
  ClockIcon,
} from "@heroicons/react/24/outline";
import IdeaRefinementStage from "./IdeaRefinementStage";
import ImplementationPlaybookStage from "./ImplementationPlaybookStage";

interface ForgeProject {
  id: string;
  name: string;
  description: string;
  currentStage:
    | "idea_refinement"
    | "prd_generation"
    | "ux_requirements"
    | "technical_analysis"
    | "implementation_playbook";
  status:
    | "draft"
    | "active"
    | "on_hold"
    | "completed"
    | "archived"
    | "cancelled";
  priority: "low" | "medium" | "high" | "critical";
  progressPercentage: number;
  createdAt: string;
  updatedAt: string;
  tags: string[];
  collaboratorsCount: number;
  artifactsCount: number;
  ownerId: string;
}

interface ForgeProjectDetailsProps {
  project: ForgeProject;
  onBackToList: () => void;
  onProjectUpdate?: (project: ForgeProject) => void;
}

const STAGES = [
  {
    id: "idea_refinement",
    name: "Idea Refinement",
    description:
      "Transform concepts into structured opportunities with systematic clarification",
    icon: SparklesIcon,
    color: "indigo",
  },
  {
    id: "prd_generation",
    name: "PRD Generation",
    description:
      "Generate comprehensive Product Requirements Document with user stories",
    icon: CheckCircleIcon,
    color: "green",
  },
  {
    id: "ux_requirements",
    name: "UX Requirements",
    description:
      "Create user experience specifications and interface design requirements",
    icon: ClockIcon,
    color: "blue",
  },
  {
    id: "technical_analysis",
    name: "Technical Analysis",
    description:
      "Multi-LLM technical architecture evaluation and stack recommendations",
    icon: CogIcon,
    color: "orange",
  },
  {
    id: "implementation_playbook",
    name: "Implementation Playbook",
    description:
      "Generate step-by-step coding agent prompts and execution guides",
    icon: PlayCircleIcon,
    color: "purple",
  },
] as const;

const PRIORITY_COLORS = {
  low: "bg-gray-100 text-gray-800",
  medium: "bg-blue-100 text-blue-800",
  high: "bg-orange-100 text-orange-800",
  critical: "bg-red-100 text-red-800",
};

const STATUS_COLORS = {
  draft: "bg-gray-100 text-gray-800",
  active: "bg-green-100 text-green-800",
  on_hold: "bg-yellow-100 text-yellow-800",
  completed: "bg-indigo-100 text-indigo-800",
  archived: "bg-gray-100 text-gray-800",
  cancelled: "bg-red-100 text-red-800",
};

export default function ForgeProjectDetails({
  project,
  onBackToList,
  onProjectUpdate,
}: ForgeProjectDetailsProps) {
  const [activeTab, setActiveTab] = useState<
    "overview" | "work" | "artifacts" | "collaboration" | "analytics"
  >("overview");
  // const [isEditing, setIsEditing] = useState(false); // TODO: Implement editing functionality
  const [stageData, setStageData] = useState<Record<string, any>>({});

  const currentStageIndex = STAGES.findIndex(
    (stage) => stage.id === project.currentStage,
  );
  const currentStage = STAGES[currentStageIndex];

  const handleAdvanceStage = () => {
    if (currentStageIndex < STAGES.length - 1) {
      const nextStage = STAGES[currentStageIndex + 1];
      const updatedProject = {
        ...project,
        currentStage: nextStage.id as ForgeProject["currentStage"],
        updatedAt: new Date().toISOString(),
      };
      onProjectUpdate?.(updatedProject);
    }
  };

  const getStageProgress = (stageIndex: number) => {
    if (stageIndex < currentStageIndex) return 100;
    if (stageIndex === currentStageIndex) return project.progressPercentage;
    return 0;
  };

  const tabs = [
    { id: "overview", name: "Overview", icon: DocumentTextIcon },
    { id: "work", name: "Work on Stage", icon: PlayCircleIcon },
    {
      id: "artifacts",
      name: `Artifacts (${project.artifactsCount})`,
      icon: DocumentTextIcon,
    },
    {
      id: "collaboration",
      name: `Team (${project.collaboratorsCount})`,
      icon: UserGroupIcon,
    },
    { id: "analytics", name: "Analytics", icon: ChartBarIcon },
  ] as const;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <button
              onClick={onBackToList}
              className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-full"
            >
              <ArrowLeftIcon className="h-6 w-6" />
            </button>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                {project.name}
              </h1>
              <p className="mt-2 text-gray-600">{project.description}</p>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <span
              className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${PRIORITY_COLORS[project.priority]}`}
            >
              {project.priority.toUpperCase()}
            </span>
            <span
              className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[project.status]}`}
            >
              {project.status.replace("_", " ").toUpperCase()}
            </span>
            <button
              onClick={() => {
                /* TODO: Implement edit functionality */
              }}
              className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-full"
            >
              <PencilIcon className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Tags */}
        <div className="mt-4 flex flex-wrap gap-2">
          {project.tags.map((tag, index) => (
            <span
              key={index}
              className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800"
            >
              {tag}
            </span>
          ))}
        </div>
      </div>

      {/* Stage Progress */}
      <div className="mb-8 bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-semibold text-gray-900">
            Project Stages
          </h2>
          {currentStageIndex < STAGES.length - 1 && (
            <button
              onClick={handleAdvanceStage}
              className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              Advance to {STAGES[currentStageIndex + 1]?.name}
            </button>
          )}
        </div>

        <div className="space-y-4">
          {STAGES.map((stage, index) => {
            const Icon = stage.icon;
            const progress = getStageProgress(index);
            const isActive = index === currentStageIndex;
            const isCompleted = index < currentStageIndex;

            return (
              <div key={stage.id} className="flex items-center space-x-4">
                <div
                  className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center ${
                    isCompleted
                      ? "bg-green-100"
                      : isActive
                        ? "bg-indigo-100"
                        : "bg-gray-100"
                  }`}
                >
                  <Icon
                    className={`h-5 w-5 ${
                      isCompleted
                        ? "text-green-600"
                        : isActive
                          ? "text-indigo-600"
                          : "text-gray-400"
                    }`}
                  />
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3
                        className={`font-medium ${isActive ? "text-indigo-900" : "text-gray-900"}`}
                      >
                        {stage.name}
                      </h3>
                      <p className="text-sm text-gray-600">
                        {stage.description}
                      </p>
                    </div>
                    <div className="text-sm text-gray-500">{progress}%</div>
                  </div>
                  <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full transition-all duration-300 ${
                        isCompleted
                          ? "bg-green-500"
                          : isActive
                            ? "bg-indigo-500"
                            : "bg-gray-300"
                      }`}
                      style={{ width: `${progress}%` }}
                    />
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2 py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? "border-indigo-500 text-indigo-600"
                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                }`}
              >
                <Icon className="h-5 w-5" />
                <span>{tab.name}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        {activeTab === "overview" && (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Current Stage: {currentStage.name}
              </h3>
              <p className="text-gray-600 mb-4">{currentStage.description}</p>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="font-medium text-gray-900">Progress</h4>
                  <p className="text-2xl font-bold text-indigo-600">
                    {project.progressPercentage}%
                  </p>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="font-medium text-gray-900">Created</h4>
                  <p className="text-gray-600">
                    {new Date(project.createdAt).toLocaleDateString()}
                  </p>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="font-medium text-gray-900">Last Updated</h4>
                  <p className="text-gray-600">
                    {new Date(project.updatedAt).toLocaleDateString()}
                  </p>
                </div>
              </div>

              <div className="mt-6 flex justify-center">
                <button
                  onClick={() => setActiveTab("work")}
                  className="px-6 py-3 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                >
                  Start Working on {currentStage.name}
                </button>
              </div>
            </div>

            {/* Stage-specific content */}
            <div>
              <h4 className="font-medium text-gray-900 mb-3">Stage Actions</h4>
              <div className="space-y-2">
                {project.currentStage === "idea_refinement" && (
                  <>
                    <p className="text-gray-600">
                      • Multi-dimensional idea analysis (market, technical,
                      user, competitive)
                    </p>
                    <p className="text-gray-600">
                      • Stakeholder interview automation using selected LLM
                    </p>
                    <p className="text-gray-600">
                      • Market research synthesis and opportunity statement
                      generation
                    </p>
                  </>
                )}
                {project.currentStage === "prd_generation" && (
                  <>
                    <p className="text-gray-600">
                      • Intelligent requirement extraction and validation
                    </p>
                    <p className="text-gray-600">
                      • User story generation with acceptance criteria
                    </p>
                    <p className="text-gray-600">
                      • Feature prioritization with business impact scoring
                    </p>
                  </>
                )}
                {project.currentStage === "ux_requirements" && (
                  <>
                    <p className="text-gray-600">
                      • User journey mapping and wireframe generation
                    </p>
                    <p className="text-gray-600">
                      • Prototype generation and design system integration
                    </p>
                    <p className="text-gray-600">
                      • Accessibility compliance checking
                    </p>
                  </>
                )}
                {project.currentStage === "technical_analysis" && (
                  <>
                    <p className="text-gray-600">
                      • Multi-LLM technical architecture evaluation
                    </p>
                    <p className="text-gray-600">
                      • Architecture comparison and recommendation engine
                    </p>
                    <p className="text-gray-600">
                      • Comprehensive feasibility assessment across all
                      configured LLMs
                    </p>
                  </>
                )}
                {project.currentStage === "implementation_playbook" && (
                  <>
                    <p className="text-gray-600">
                      • Generate coding-agent-optimized prompts
                    </p>
                    <p className="text-gray-600">
                      • Create step-by-step development workflow
                    </p>
                    <p className="text-gray-600">
                      • Generate testing strategy and deployment procedures
                    </p>
                  </>
                )}
              </div>
            </div>
          </div>
        )}

        {activeTab === "work" && (
          <div>
            {project.currentStage === "idea_refinement" && (
              <IdeaRefinementStage
                projectId={project.id}
                initialData={stageData.idea_refinement}
                selectedLLM="gpt-4" // TODO: Get from user preferences
                onDataUpdate={(data) => {
                  setStageData((prev) => ({ ...prev, idea_refinement: data }));
                }}
                onStageComplete={(data) => {
                  setStageData((prev) => ({ ...prev, idea_refinement: data }));
                  handleAdvanceStage();
                }}
              />
            )}
            {project.currentStage === "prd_generation" && (
              <div className="text-center py-12">
                <DocumentTextIcon className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">
                  PRD Generation Stage
                </h3>
                <p className="mt-1 text-sm text-gray-500">
                  Coming soon - Generate comprehensive Product Requirements
                  Document
                </p>
              </div>
            )}
            {project.currentStage === "ux_requirements" && (
              <div className="text-center py-12">
                <UserGroupIcon className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">
                  UX Requirements Stage
                </h3>
                <p className="mt-1 text-sm text-gray-500">
                  Coming soon - Create user experience specifications
                </p>
              </div>
            )}
            {project.currentStage === "technical_analysis" && (
              <div className="text-center py-12">
                <CogIcon className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">
                  Technical Analysis Stage
                </h3>
                <p className="mt-1 text-sm text-gray-500">
                  Coming soon - Multi-LLM technical architecture evaluation
                </p>
              </div>
            )}
            {project.currentStage === "implementation_playbook" && (
              <ImplementationPlaybookStage
                projectId={project.id}
                projectContext={{
                  ideaRefinement: stageData.idea_refinement || {},
                  prdGeneration: stageData.prd_generation || {},
                  uxRequirements: stageData.ux_requirements || {},
                  technicalAnalysis: stageData.technical_analysis || {},
                }}
                onStageComplete={(data) => {
                  setStageData((prev) => ({
                    ...prev,
                    implementation_playbook: data,
                  }));
                  handleAdvanceStage();
                }}
                onQualityUpdate={(quality) => {
                  // Handle quality updates if needed
                  console.log("Implementation Playbook Quality:", quality);
                }}
              />
            )}
          </div>
        )}

        {activeTab === "artifacts" && (
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Project Artifacts
            </h3>
            <div className="text-center py-12">
              <DocumentTextIcon className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">
                No artifacts yet
              </h3>
              <p className="mt-1 text-sm text-gray-500">
                Artifacts will be generated as you progress through the stages
              </p>
            </div>
          </div>
        )}

        {activeTab === "collaboration" && (
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Team Collaboration
            </h3>
            <div className="text-center py-12">
              <UserGroupIcon className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">
                Solo project
              </h3>
              <p className="mt-1 text-sm text-gray-500">
                Invite team members to collaborate on this project
              </p>
              <button className="mt-4 px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700">
                Invite Collaborators
              </button>
            </div>
          </div>
        )}

        {activeTab === "analytics" && (
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Project Analytics
            </h3>
            <div className="text-center py-12">
              <ChartBarIcon className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">
                Analytics coming soon
              </h3>
              <p className="mt-1 text-sm text-gray-500">
                Track progress, time spent, and project metrics
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
