/**
 * ForgeProjectCard - Individual project card component for the Forge project list
 */
import {
  CalendarIcon,
  UserGroupIcon,
  DocumentTextIcon,
  ArrowRightIcon,
} from "@heroicons/react/24/outline";

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

interface StageConfig {
  name: string;
  description: string;
  icon: string;
  color: string;
}

interface StatusConfig {
  name: string;
  color: string;
}

interface ForgeProjectCardProps {
  project: ForgeProject;
  onSelect: (project: ForgeProject) => void;
  stageConfig: Record<string, StageConfig>;
  statusConfig: Record<string, StatusConfig>;
}

export default function ForgeProjectCard({
  project,
  onSelect,
  stageConfig,
  statusConfig,
}: ForgeProjectCardProps) {
  const stage = stageConfig[project.currentStage];
  const status = statusConfig[project.status];

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "critical":
        return "bg-red-100 text-red-800";
      case "high":
        return "bg-orange-100 text-orange-800";
      case "medium":
        return "bg-yellow-100 text-yellow-800";
      case "low":
        return "bg-gray-100 text-gray-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow cursor-pointer">
      <div className="p-6" onClick={() => onSelect(project)}>
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900 mb-1 line-clamp-1">
              {project.name}
            </h3>
            <p className="text-sm text-gray-600 line-clamp-2">
              {project.description}
            </p>
          </div>
          <ArrowRightIcon className="h-5 w-5 text-gray-400 ml-4" />
        </div>

        {/* Stage and Status */}
        <div className="flex items-center space-x-2 mb-4">
          <span
            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${stage.color}`}
          >
            <span className="mr-1">{stage.icon}</span>
            {stage.name}
          </span>
          <span
            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${status.color}`}
          >
            {status.name}
          </span>
          <span
            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getPriorityColor(project.priority)}`}
          >
            {project.priority.charAt(0).toUpperCase() +
              project.priority.slice(1)}
          </span>
        </div>

        {/* Progress Bar */}
        <div className="mb-4">
          <div className="flex items-center justify-between text-sm text-gray-600 mb-1">
            <span>Progress</span>
            <span>{project.progressPercentage}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-indigo-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${project.progressPercentage}%` }}
            />
          </div>
        </div>

        {/* Tags */}
        {project.tags.length > 0 && (
          <div className="mb-4">
            <div className="flex flex-wrap gap-1">
              {project.tags.slice(0, 3).map((tag, index) => (
                <span
                  key={index}
                  className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800"
                >
                  {tag}
                </span>
              ))}
              {project.tags.length > 3 && (
                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-600">
                  +{project.tags.length - 3} more
                </span>
              )}
            </div>
          </div>
        )}

        {/* Footer Info */}
        <div className="flex items-center justify-between text-sm text-gray-500">
          <div className="flex items-center space-x-4">
            <div className="flex items-center">
              <UserGroupIcon className="h-4 w-4 mr-1" />
              <span>{project.collaboratorsCount}</span>
            </div>
            <div className="flex items-center">
              <DocumentTextIcon className="h-4 w-4 mr-1" />
              <span>{project.artifactsCount}</span>
            </div>
          </div>
          <div className="flex items-center">
            <CalendarIcon className="h-4 w-4 mr-1" />
            <span>{formatDate(project.updatedAt)}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
