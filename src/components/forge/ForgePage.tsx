/**
 * ForgePage - Main Forge project overview and stage-based navigation
 * Implements the complete Forge workflow system for idea to deployment
 */
import { useState, useEffect } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import { PlusIcon, FolderIcon } from "@heroicons/react/24/outline";
import ForgeProjectCard from "./ForgeProjectCard";
import ForgeProjectCreator from "./ForgeProjectCreator";
import ForgeProjectDetails from "./ForgeProjectDetails";
import { forgeApi } from "@/services/api";

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

const STAGE_CONFIG = {
  idea_refinement: {
    name: "Idea Refinement",
    description: "Transform concepts into structured opportunities",
    icon: "💡",
    color: "bg-yellow-100 text-yellow-800 border-yellow-200",
  },
  requirements: {
    name: "Requirements",
    description: "Generate comprehensive PRDs and user stories",
    icon: "�",
    color: "bg-blue-100 text-blue-800 border-blue-200",
  },
  ux_requirements: {
    name: "UX Requirements",
    description: "Create user experience specifications and interface design",
    icon: "🎨",
    color: "bg-purple-100 text-purple-800 border-purple-200",
  },
  technical_analysis: {
    name: "Technical Analysis",
    description:
      "Multi-LLM technical architecture evaluation and recommendations",
    icon: "⚙️",
    color: "bg-orange-100 text-orange-800 border-orange-200",
  },
  implementation_playbook: {
    name: "Implementation Playbook",
    description: "Generate execution-ready development guides",
    icon: "🚀",
    color: "bg-green-100 text-green-800 border-green-200",
  },
};

const STATUS_CONFIG = {
  draft: { name: "Draft", color: "bg-gray-100 text-gray-800" },
  active: { name: "Active", color: "bg-green-100 text-green-800" },
  on_hold: { name: "On Hold", color: "bg-yellow-100 text-yellow-800" },
  completed: { name: "Completed", color: "bg-blue-100 text-blue-800" },
  archived: { name: "Archived", color: "bg-gray-100 text-gray-600" },
  cancelled: { name: "Cancelled", color: "bg-red-100 text-red-800" },
};

export default function ForgePage() {
  const navigate = useNavigate();
  const { projectId } = useParams();
  const [searchParams] = useSearchParams();

  // State management
  const [projects, setProjects] = useState<ForgeProject[]>([]);
  const [selectedProject, setSelectedProject] = useState<ForgeProject | null>(
    null,
  );
  const [currentView, setCurrentView] = useState<"list" | "create" | "details">(
    "list",
  );
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [stageFilter, setStageFilter] = useState("all");
  const [sortBy, setSortBy] = useState("updated");

  // Load projects on component mount
  useEffect(() => {
    loadProjects();

    // Handle URL parameters
    if (projectId) {
      setCurrentView("details");
      loadProjectDetails(projectId);
    } else {
      const view = searchParams.get("view");
      if (view === "create") {
        setCurrentView("create");
      }
    }
  }, [projectId, searchParams]);

  const loadProjects = async () => {
    try {
      setIsLoading(true);
      const response = await forgeApi.listProjects({
        status: statusFilter !== "all" ? statusFilter : undefined,
        stage: stageFilter !== "all" ? stageFilter : undefined,
        limit: 50,
      });

      if (response?.projects) {
        setProjects(response.projects as any[]);
      } else {
        setProjects([]);
      }
    } catch (error) {
      console.error("Error loading projects:", error);
      setProjects([]);
    } finally {
      setIsLoading(false);
    }
  };

  const loadProjectDetails = async (id: string) => {
    try {
      const response = await forgeApi.getProject(id);
      if (response) {
        setSelectedProject(response as any);
      } else {
        // Fallback: try to find in already-loaded projects
        const project = projects.find((p) => p.id === id);
        if (project) {
          setSelectedProject(project);
        } else {
          navigate("/forge");
        }
      }
    } catch (error) {
      console.error("Error loading project details:", error);
      navigate("/forge");
    }
  };

  const handleCreateProject = () => {
    setCurrentView("create");
    navigate("/forge?view=create");
  };

  const handleProjectCreated = (project: ForgeProject) => {
    setProjects([project, ...projects]);
    setCurrentView("details");
    setSelectedProject(project);
    navigate(`/forge/${project.id}`);
  };

  const handleProjectSelected = (project: ForgeProject) => {
    setSelectedProject(project);
    setCurrentView("details");
    navigate(`/forge/${project.id}`);
  };

  const handleBackToList = () => {
    setCurrentView("list");
    setSelectedProject(null);
    navigate("/forge");
  };

  const handleProjectUpdated = (updatedProject: ForgeProject) => {
    setProjects(
      projects.map((p) => (p.id === updatedProject.id ? updatedProject : p)),
    );
    setSelectedProject(updatedProject);
  };

  // const handleProjectDeleted = (projectId: string) => {
  //   setProjects(projects.filter(p => p.id !== projectId));
  //   handleBackToList();
  // };

  // Filter and sort projects
  const filteredProjects = projects
    .filter((project) => {
      const matchesSearch =
        project.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        project.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
        project.tags.some((tag) =>
          tag.toLowerCase().includes(searchTerm.toLowerCase()),
        );
      const matchesStatus =
        statusFilter === "all" || project.status === statusFilter;
      const matchesStage =
        stageFilter === "all" || project.currentStage === stageFilter;
      return matchesSearch && matchesStatus && matchesStage;
    })
    .sort((a, b) => {
      switch (sortBy) {
        case "name":
          return a.name.localeCompare(b.name);
        case "created":
          return (
            new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
          );
        case "progress":
          return b.progressPercentage - a.progressPercentage;
        case "updated":
        default:
          return (
            new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
          );
      }
    });

  // Render different views
  if (currentView === "create") {
    return (
      <ForgeProjectCreator
        onProjectCreated={handleProjectCreated}
        onCancel={handleBackToList}
      />
    );
  }

  if (currentView === "details" && selectedProject) {
    return (
      <ForgeProjectDetails
        project={selectedProject}
        onProjectUpdate={handleProjectUpdated}
        onBackToList={handleBackToList}
      />
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      {/* Header Section */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Forge</h1>
            <p className="mt-2 text-gray-600">
              Transform ideas into reality with AI-powered project workflows
            </p>
          </div>
          <button
            onClick={handleCreateProject}
            className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            <PlusIcon className="h-5 w-5 mr-2" />
            New Project
          </button>
        </div>

        {/* Stage Overview */}
        <div className="mt-6 grid grid-cols-1 md:grid-cols-5 gap-4">
          {Object.entries(STAGE_CONFIG).map(([stage, config]) => {
            const stageProjects = projects.filter(
              (p) => p.currentStage === stage,
            );
            return (
              <div
                key={stage}
                className={`p-4 rounded-lg border ${config.color} cursor-pointer hover:shadow-md transition-shadow`}
                onClick={() => setStageFilter(stage)}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-lg font-semibold">
                      {config.icon} {config.name}
                    </div>
                    <div className="text-sm opacity-75 mt-1">
                      {stageProjects.length} projects
                    </div>
                  </div>
                  <div className="text-2xl font-bold">
                    {stageProjects.length}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Filters and Search */}
      <div className="mb-6 bg-white p-4 rounded-lg shadow-sm border border-gray-200">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0 sm:space-x-4">
          {/* Search */}
          <div className="flex-1 max-w-md">
            <input
              type="text"
              placeholder="Search projects..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>

          {/* Filters */}
          <div className="flex space-x-4">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="all">All Status</option>
              {Object.entries(STATUS_CONFIG).map(([status, config]) => (
                <option key={status} value={status}>
                  {config.name}
                </option>
              ))}
            </select>

            <select
              value={stageFilter}
              onChange={(e) => setStageFilter(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="all">All Stages</option>
              {Object.entries(STAGE_CONFIG).map(([stage, config]) => (
                <option key={stage} value={stage}>
                  {config.name}
                </option>
              ))}
            </select>

            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="updated">Recently Updated</option>
              <option value="created">Recently Created</option>
              <option value="name">Name</option>
              <option value="progress">Progress</option>
            </select>
          </div>
        </div>
      </div>

      {/* Projects Grid */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
          <span className="ml-3 text-gray-600">Loading projects...</span>
        </div>
      ) : filteredProjects.length === 0 ? (
        <div className="text-center py-12">
          <FolderIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            {projects.length === 0
              ? "No projects yet"
              : "No projects match your filters"}
          </h3>
          <p className="text-gray-600 mb-6">
            {projects.length === 0
              ? "Get started by creating your first Forge project"
              : "Try adjusting your search terms or filters"}
          </p>
          {projects.length === 0 && (
            <button
              onClick={handleCreateProject}
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700"
            >
              <PlusIcon className="h-5 w-5 mr-2" />
              Create Your First Project
            </button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredProjects.map((project) => (
            <ForgeProjectCard
              key={project.id}
              project={project}
              onSelect={handleProjectSelected}
              stageConfig={STAGE_CONFIG}
              statusConfig={STATUS_CONFIG}
            />
          ))}
        </div>
      )}

      {/* Quick Stats */}
      {projects.length > 0 && (
        <div className="mt-8 bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            Project Overview
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-indigo-600">
                {projects.length}
              </div>
              <div className="text-sm text-gray-600">Total Projects</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {projects.filter((p) => p.status === "active").length}
              </div>
              <div className="text-sm text-gray-600">Active</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {projects.filter((p) => p.status === "completed").length}
              </div>
              <div className="text-sm text-gray-600">Completed</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">
                {Math.round(
                  projects.reduce((sum, p) => sum + p.progressPercentage, 0) /
                    projects.length,
                ) || 0}
                %
              </div>
              <div className="text-sm text-gray-600">Avg Progress</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
