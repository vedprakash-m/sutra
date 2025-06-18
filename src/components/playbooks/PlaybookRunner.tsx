import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import {
  PlayIcon,
  PauseIcon,
  StopIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  EyeIcon,
} from "@heroicons/react/24/outline";

interface PlaybookStep {
  id: string;
  name: string;
  type: "prompt" | "manual_review" | "text_explanation";
  status: "pending" | "running" | "completed" | "failed" | "paused";
  input?: any;
  output?: string;
  error?: string;
  startTime?: string;
  endTime?: string;
  reviewNote?: string;
}

interface PlaybookExecution {
  id: string;
  playbookId: string;
  playbookName: string;
  status: "running" | "paused" | "completed" | "failed";
  currentStepIndex: number;
  steps: PlaybookStep[];
  startTime: string;
  endTime?: string;
  totalSteps: number;
  completedSteps: number;
}

export default function PlaybookRunner() {
  const { id } = useParams();

  const [execution, setExecution] = useState<PlaybookExecution | null>(null);
  const [reviewInput, setReviewInput] = useState("");

  // Mock execution data
  useEffect(() => {
    if (id) {
      setExecution({
        id: "exec-1",
        playbookId: id,
        playbookName: "Customer Support Resolution Flow",
        status: "paused",
        currentStepIndex: 1,
        steps: [
          {
            id: "step1",
            name: "Generate Initial Response",
            type: "prompt",
            status: "completed",
            input: {
              customer_query: "My order is delayed",
              customer_name: "John Smith",
            },
            output:
              "Dear John Smith,\n\nThank you for contacting us regarding your order delay. I sincerely apologize for any inconvenience this may have caused.\n\nI have looked into your order status and can see that there was an unexpected delay in our fulfillment center. Your order is currently being prioritized and should ship within the next 24 hours.\n\nAs a gesture of goodwill, I would like to offer you free expedited shipping on this order. You will receive a tracking number via email once your order ships.\n\nIs there anything else I can help you with today?\n\nBest regards,\nCustomer Support Team",
            startTime: "2025-06-15T10:00:00Z",
            endTime: "2025-06-15T10:00:45Z",
          },
          {
            id: "step2",
            name: "Manual Review - Response Quality",
            type: "manual_review",
            status: "paused",
            input: { response_to_review: "Generated response from step 1" },
            startTime: "2025-06-15T10:00:45Z",
          },
          {
            id: "step3",
            name: "Generate Follow-up Email",
            type: "prompt",
            status: "pending",
          },
          {
            id: "step4",
            name: "Final Review",
            type: "manual_review",
            status: "pending",
          },
        ],
        startTime: "2025-06-15T10:00:00Z",
        totalSteps: 4,
        completedSteps: 1,
      });
    }
  }, [id]);

  const handleStartExecution = () => {
    setExecution((prev) => (prev ? { ...prev, status: "running" } : null));
    // TODO: Call API to start execution
  };

  const handlePauseExecution = () => {
    setExecution((prev) => (prev ? { ...prev, status: "paused" } : null));
  };

  const handleStopExecution = () => {
    setExecution((prev) => (prev ? { ...prev, status: "completed" } : null));
  };

  const handleApproveStep = (stepId: string) => {
    setExecution((prev) => {
      if (!prev) return null;

      const updatedSteps = prev.steps.map((step) =>
        step.id === stepId
          ? {
              ...step,
              status: "completed" as const,
              endTime: new Date().toISOString(),
              reviewNote: reviewInput,
            }
          : step,
      );

      return {
        ...prev,
        steps: updatedSteps,
        currentStepIndex: prev.currentStepIndex + 1,
        completedSteps: prev.completedSteps + 1,
      };
    });
    setReviewInput("");
  };

  const handleRejectStep = (stepId: string) => {
    setExecution((prev) => {
      if (!prev) return null;

      const updatedSteps = prev.steps.map((step) =>
        step.id === stepId
          ? {
              ...step,
              status: "failed" as const,
              error: "Rejected during manual review",
              reviewNote: reviewInput,
            }
          : step,
      );

      return {
        ...prev,
        steps: updatedSteps,
        status: "failed",
      };
    });
    setReviewInput("");
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case "failed":
        return <XCircleIcon className="h-5 w-5 text-red-500" />;
      case "running":
        return (
          <div className="h-5 w-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
        );
      case "paused":
        return <PauseIcon className="h-5 w-5 text-yellow-500" />;
      default:
        return <ClockIcon className="h-5 w-5 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "bg-green-50 border-green-200";
      case "failed":
        return "bg-red-50 border-red-200";
      case "running":
        return "bg-blue-50 border-blue-200";
      case "paused":
        return "bg-yellow-50 border-yellow-200";
      default:
        return "bg-gray-50 border-gray-200";
    }
  };

  const currentStep = execution?.steps[execution.currentStepIndex];

  if (!execution) {
    return (
      <div className="max-w-4xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        <div className="text-center">
          <p className="text-gray-500">Loading playbook execution...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              {execution.playbookName}
            </h1>
            <p className="mt-1 text-sm text-gray-600">
              Step {execution.currentStepIndex + 1} of {execution.totalSteps} •
              {execution.completedSteps} completed
            </p>
          </div>
          <div className="flex space-x-3">
            {execution.status === "paused" && (
              <button
                onClick={handleStartExecution}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-green-600 hover:bg-green-700"
              >
                <PlayIcon className="h-4 w-4 mr-2" />
                Continue
              </button>
            )}
            {execution.status === "running" && (
              <button
                onClick={handlePauseExecution}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-yellow-600 hover:bg-yellow-700"
              >
                <PauseIcon className="h-4 w-4 mr-2" />
                Pause
              </button>
            )}
            <button
              onClick={handleStopExecution}
              className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
            >
              <StopIcon className="h-4 w-4 mr-2" />
              Stop
            </button>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mt-4">
          <div className="bg-gray-200 rounded-full h-2">
            <div
              className="bg-indigo-600 h-2 rounded-full transition-all duration-300"
              style={{
                width: `${(execution.completedSteps / execution.totalSteps) * 100}%`,
              }}
            />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Steps Timeline */}
        <div className="lg:col-span-2">
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">
              Execution Timeline
            </h2>
            <div className="space-y-4">
              {execution.steps.map((step, index) => (
                <div
                  key={step.id}
                  className={`border rounded-lg p-4 ${getStatusColor(step.status)} ${
                    index === execution.currentStepIndex
                      ? "ring-2 ring-indigo-500"
                      : ""
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-2">
                        {getStatusIcon(step.status)}
                        <h3 className="font-medium text-gray-900">
                          {step.name}
                        </h3>
                        <span className="text-xs text-gray-500 bg-white px-2 py-1 rounded">
                          {step.type.replace("_", " ")}
                        </span>
                      </div>

                      {step.output && (
                        <div className="mt-2 bg-white rounded p-3 text-sm">
                          <p className="text-gray-700 line-clamp-3">
                            {step.output}
                          </p>
                        </div>
                      )}

                      {step.error && (
                        <div className="mt-2 bg-red-100 border border-red-200 rounded p-3 text-sm text-red-800">
                          {step.error}
                        </div>
                      )}

                      {step.reviewNote && (
                        <div className="mt-2 bg-blue-100 border border-blue-200 rounded p-3 text-sm text-blue-800">
                          <strong>Review Note:</strong> {step.reviewNote}
                        </div>
                      )}
                    </div>

                    <div className="flex space-x-2 ml-4">
                      {step.output && (
                        <button
                          onClick={() =>
                            console.log("Show step details:", step.id)
                          }
                          className="p-2 text-gray-400 hover:text-gray-500"
                        >
                          <EyeIcon className="h-4 w-4" />
                        </button>
                      )}
                    </div>
                  </div>

                  {step.startTime && (
                    <div className="mt-2 text-xs text-gray-500">
                      Started: {new Date(step.startTime).toLocaleString()}
                      {step.endTime &&
                        ` • Completed: ${new Date(step.endTime).toLocaleString()}`}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Current Step Actions */}
        <div className="space-y-6">
          {currentStep &&
            currentStep.type === "manual_review" &&
            currentStep.status === "paused" && (
              <div className="bg-white shadow rounded-lg p-6">
                <h2 className="text-lg font-medium text-gray-900 mb-4">
                  Manual Review Required
                </h2>
                <div className="mb-4">
                  <h3 className="font-medium text-gray-700 mb-2">
                    {currentStep.name}
                  </h3>
                  {execution.steps[execution.currentStepIndex - 1]?.output && (
                    <div className="bg-gray-50 rounded p-3 text-sm mb-4">
                      <strong>Previous Step Output:</strong>
                      <p className="mt-1">
                        {execution.steps[execution.currentStepIndex - 1].output}
                      </p>
                    </div>
                  )}
                </div>

                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Review Notes (Optional)
                  </label>
                  <textarea
                    value={reviewInput}
                    onChange={(e) => setReviewInput(e.target.value)}
                    rows={3}
                    className="block w-full border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                    placeholder="Add your review comments..."
                  />
                </div>

                <div className="flex space-x-3">
                  <button
                    onClick={() => handleApproveStep(currentStep.id)}
                    className="flex-1 inline-flex justify-center items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700"
                  >
                    <CheckCircleIcon className="h-4 w-4 mr-2" />
                    Approve
                  </button>
                  <button
                    onClick={() => handleRejectStep(currentStep.id)}
                    className="flex-1 inline-flex justify-center items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                  >
                    <XCircleIcon className="h-4 w-4 mr-2" />
                    Reject
                  </button>
                </div>
              </div>
            )}

          {/* Execution Log */}
          <div className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">
              Execution Log
            </h2>
            <div className="space-y-2 max-h-96 overflow-y-auto">
              <div className="text-sm text-gray-600">
                <span className="text-gray-500">
                  {new Date(execution.startTime).toLocaleString()}
                </span>
                <span className="ml-2">Playbook execution started</span>
              </div>

              {execution.steps.map(
                (step) =>
                  step.status !== "pending" && (
                    <div key={step.id} className="text-sm text-gray-600">
                      <span className="text-gray-500">
                        {step.startTime &&
                          new Date(step.startTime).toLocaleString()}
                      </span>
                      <span className="ml-2">
                        {step.status === "completed"
                          ? "✓"
                          : step.status === "failed"
                            ? "✗"
                            : step.status === "running"
                              ? "▶"
                              : "⏸"}{" "}
                        {step.name}
                      </span>
                    </div>
                  ),
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
