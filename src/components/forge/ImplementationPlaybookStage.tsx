/**
 * ImplementationPlaybookStage.tsx
 *
 * React component for Task 2.7 - Implementation Playbook Generation Stage of Forge Module
 * Generates step-by-step coding agent prompts and execution guides for systematic development
 * with complete project context integration and quality validation.
 *
 * Features:
 * - Context Integration: Full project context from all stages informs prompt generation
 * - Agent Optimization: Prompts specifically designed for coding agent consumption
 * - Quality Assurance: Testing and QA procedures aligned to quality standards
 * - Deployment Readiness: Complete environment setup and deployment procedures
 */

import React, { useState, useEffect, useCallback, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  CheckCircle,
  Clock,
  Download,
  Code,
  GitBranch,
  Target,
  RefreshCw,
  AlertTriangle,
  Brain,
  Rocket,
  Package,
  TestTube,
} from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { toast } from "@/hooks/use-toast";

// Import existing components
import { QualityGate } from "@/components/forge/QualityGate";
import { useLLMCost } from "@/hooks/useLLMCost";

// Types for Implementation Playbook
interface ImplementationPlaybookProps {
  projectId: string;
  projectContext: ProjectContext;
  onStageComplete: (stageData: any) => void;
  onQualityUpdate: (quality: any) => void;
}

interface ProjectContext {
  ideaRefinement: any;
  prdGeneration: any;
  uxRequirements: any;
  technicalAnalysis: any;
}

interface PlaybookSection {
  id: string;
  title: string;
  status: "pending" | "in-progress" | "completed" | "error";
  progress: number;
  data: any;
  quality: QualityAssessment;
}

interface QualityAssessment {
  score: number;
  dimensions: {
    contextIntegration: number;
    agentOptimization: number;
    completeness: number;
    actionability: number;
  };
  recommendations: string[];
  readyForImplementation: boolean;
}

const ImplementationPlaybookStage: React.FC<ImplementationPlaybookProps> = ({
  projectId,
  projectContext,
  onStageComplete,
  onQualityUpdate,
}) => {
  // State management
  const [activeTab, setActiveTab] = useState("overview");
  const [isGenerating, setIsGenerating] = useState(false);
  const [sections, setSections] = useState<Record<string, PlaybookSection>>({});
  const [overallQuality, setOverallQuality] =
    useState<QualityAssessment | null>(null);
  const [contextValidation, setContextValidation] = useState<any>(null);
  const [exportFormat, setExportFormat] = useState("json");
  const [agentType, setAgentType] = useState("general");
  const [workflowMethodology, setWorkflowMethodology] =
    useState("agile_sprints");

  // Hooks
  const { trackCost } = useLLMCost();

  // Initialize sections
  useEffect(() => {
    initializeSections();
  }, []);

  const initializeSections = () => {
    const initialSections: Record<string, PlaybookSection> = {
      codingPrompts: {
        id: "codingPrompts",
        title: "Coding Agent Prompts",
        status: "pending",
        progress: 0,
        data: null,
        quality: getInitialQuality(),
      },
      developmentWorkflow: {
        id: "developmentWorkflow",
        title: "Development Workflow",
        status: "pending",
        progress: 0,
        data: null,
        quality: getInitialQuality(),
      },
      testingStrategy: {
        id: "testingStrategy",
        title: "Testing Strategy",
        status: "pending",
        progress: 0,
        data: null,
        quality: getInitialQuality(),
      },
      deploymentGuide: {
        id: "deploymentGuide",
        title: "Deployment Guide",
        status: "pending",
        progress: 0,
        data: null,
        quality: getInitialQuality(),
      },
      finalPlaybook: {
        id: "finalPlaybook",
        title: "Complete Playbook",
        status: "pending",
        progress: 0,
        data: null,
        quality: getInitialQuality(),
      },
    };
    setSections(initialSections);
  };

  const getInitialQuality = (): QualityAssessment => ({
    score: 0,
    dimensions: {
      contextIntegration: 0,
      agentOptimization: 0,
      completeness: 0,
      actionability: 0,
    },
    recommendations: [],
    readyForImplementation: false,
  });

  // Generate coding prompts
  const generateCodingPrompts = useCallback(async () => {
    try {
      updateSectionStatus("codingPrompts", "in-progress");
      setIsGenerating(true);

      const response = await fetch("/api/forge/generate-coding-prompts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          project_id: projectId,
          context_data: projectContext,
          prompt_focus: "full-stack",
          optimization_level: "production",
          agent_type: agentType,
        }),
      });

      if (!response.ok) throw new Error("Failed to generate coding prompts");

      const data = await response.json();

      // Track cost
      if (data.cost_info) {
        trackCost();
      }

      updateSectionData("codingPrompts", data.coding_prompts);
      updateSectionStatus("codingPrompts", "completed");

      toast({
        title: "Coding Prompts Generated",
        description:
          "Agent-optimized coding prompts have been created successfully.",
      });
    } catch (error) {
      console.error("Error generating coding prompts:", error);
      updateSectionStatus("codingPrompts", "error");
      toast({
        title: "Generation Failed",
        description: "Failed to generate coding prompts. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsGenerating(false);
    }
  }, [projectId, projectContext, agentType, trackCost]);

  // Create development workflow
  const createDevelopmentWorkflow = useCallback(async () => {
    try {
      updateSectionStatus("developmentWorkflow", "in-progress");

      const response = await fetch("/api/forge/create-development-workflow", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          project_id: projectId,
          technical_analysis: projectContext.technicalAnalysis,
          ux_requirements: projectContext.uxRequirements,
          prd_data: projectContext.prdGeneration,
          workflow_type: workflowMethodology,
        }),
      });

      if (!response.ok)
        throw new Error("Failed to create development workflow");

      const data = await response.json();
      updateSectionData("developmentWorkflow", data.development_workflow);
      updateSectionStatus("developmentWorkflow", "completed");

      toast({
        title: "Development Workflow Created",
        description:
          "Systematic development workflow has been generated successfully.",
      });
    } catch (error) {
      console.error("Error creating development workflow:", error);
      updateSectionStatus("developmentWorkflow", "error");
      toast({
        title: "Creation Failed",
        description: "Failed to create development workflow. Please try again.",
        variant: "destructive",
      });
    }
  }, [projectId, projectContext, workflowMethodology]);

  // Generate testing strategy
  const generateTestingStrategy = useCallback(async () => {
    try {
      updateSectionStatus("testingStrategy", "in-progress");

      const response = await fetch("/api/forge/generate-testing-strategy", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          project_context: projectContext,
          testing_scope: "comprehensive",
        }),
      });

      if (!response.ok) throw new Error("Failed to generate testing strategy");

      const data = await response.json();
      updateSectionData("testingStrategy", data.testing_strategy);
      updateSectionStatus("testingStrategy", "completed");

      toast({
        title: "Testing Strategy Generated",
        description:
          "Comprehensive testing strategy has been created successfully.",
      });
    } catch (error) {
      console.error("Error generating testing strategy:", error);
      updateSectionStatus("testingStrategy", "error");
      toast({
        title: "Generation Failed",
        description: "Failed to generate testing strategy. Please try again.",
        variant: "destructive",
      });
    }
  }, [projectContext]);

  // Create deployment guide
  const createDeploymentGuide = useCallback(async () => {
    try {
      updateSectionStatus("deploymentGuide", "in-progress");

      const response = await fetch("/api/forge/create-deployment-guide", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          technical_specs: projectContext.technicalAnalysis,
          deployment_target: "cloud",
          environment_requirements: {},
        }),
      });

      if (!response.ok) throw new Error("Failed to create deployment guide");

      const data = await response.json();
      updateSectionData("deploymentGuide", data.deployment_guide);
      updateSectionStatus("deploymentGuide", "completed");

      toast({
        title: "Deployment Guide Created",
        description:
          "Comprehensive deployment guide has been generated successfully.",
      });
    } catch (error) {
      console.error("Error creating deployment guide:", error);
      updateSectionStatus("deploymentGuide", "error");
      toast({
        title: "Creation Failed",
        description: "Failed to create deployment guide. Please try again.",
        variant: "destructive",
      });
    }
  }, [projectContext]);

  // Compile final playbook
  const compileFinalPlaybook = useCallback(async () => {
    try {
      updateSectionStatus("finalPlaybook", "in-progress");

      const response = await fetch("/api/forge/compile-playbook", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          project_id: projectId,
          coding_prompts: sections.codingPrompts.data,
          development_workflow: sections.developmentWorkflow.data,
          testing_strategy: sections.testingStrategy.data,
          deployment_guide: sections.deploymentGuide.data,
        }),
      });

      if (!response.ok) throw new Error("Failed to compile playbook");

      const data = await response.json();
      updateSectionData("finalPlaybook", data.implementation_playbook);
      setContextValidation(data.context_validation);
      updateSectionStatus("finalPlaybook", "completed");

      // Calculate overall quality
      const quality = calculateOverallQuality();
      setOverallQuality(quality);
      onQualityUpdate(quality);

      // Check if stage is complete
      if (quality.score >= 85) {
        onStageComplete({
          implementation_playbook: data.implementation_playbook,
          context_validation: data.context_validation,
          quality_assessment: quality,
        });
      }

      toast({
        title: "Playbook Compiled",
        description: "Implementation playbook has been compiled successfully.",
      });
    } catch (error) {
      console.error("Error compiling playbook:", error);
      updateSectionStatus("finalPlaybook", "error");
      toast({
        title: "Compilation Failed",
        description: "Failed to compile playbook. Please try again.",
        variant: "destructive",
      });
    }
  }, [projectId, sections, onStageComplete, onQualityUpdate]);

  // Validate context integration
  const validateContextIntegration = useCallback(async () => {
    try {
      const response = await fetch("/api/forge/validate-context-integration", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          project_id: projectId,
        }),
      });

      if (!response.ok)
        throw new Error("Failed to validate context integration");

      const data = await response.json();
      setContextValidation(data.validation_result);

      toast({
        title: "Context Validated",
        description: `Context integration score: ${data.validation_result.overall_score}%`,
      });
    } catch (error) {
      console.error("Error validating context integration:", error);
      toast({
        title: "Validation Failed",
        description:
          "Failed to validate context integration. Please try again.",
        variant: "destructive",
      });
    }
  }, [projectId]);

  // Export playbook
  const exportPlaybook = useCallback(async () => {
    try {
      setIsGenerating(true);

      const response = await fetch(
        `/api/forge/export-playbook/${projectId}?format=${exportFormat}`,
        {
          method: "GET",
        },
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || "Failed to export playbook");
      }

      // Get the appropriate file extension
      const fileExtensions: Record<string, string> = {
        json: "json",
        markdown: "md",
        pdf: "pdf",
        zip: "zip",
      };
      const extension = fileExtensions[exportFormat] || exportFormat;

      // Handle the download
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `implementation_playbook_${projectId.substring(0, 8)}.${extension}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      toast({
        title: "Playbook Exported Successfully",
        description: `Implementation playbook exported as ${exportFormat.toUpperCase()} format.`,
      });
    } catch (error) {
      console.error("Error exporting playbook:", error);
      toast({
        title: "Export Failed",
        description:
          error instanceof Error
            ? error.message
            : "Failed to export playbook. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsGenerating(false);
    }
  }, [projectId, exportFormat]);

  // Helper functions
  const updateSectionStatus = (
    sectionId: string,
    status: PlaybookSection["status"],
  ) => {
    setSections((prev) => ({
      ...prev,
      [sectionId]: {
        ...prev[sectionId],
        status,
        progress:
          status === "completed" ? 100 : status === "in-progress" ? 50 : 0,
      },
    }));
  };

  const updateSectionData = (sectionId: string, data: any) => {
    setSections((prev) => ({
      ...prev,
      [sectionId]: {
        ...prev[sectionId],
        data,
        quality: assessSectionQuality(),
      },
    }));
  };

  const assessSectionQuality = (): QualityAssessment => {
    // Mock quality assessment - in real implementation this would be more sophisticated
    return {
      score: 85,
      dimensions: {
        contextIntegration: 85,
        agentOptimization: 90,
        completeness: 80,
        actionability: 85,
      },
      recommendations: [],
      readyForImplementation: true,
    };
  };

  const calculateOverallQuality = (): QualityAssessment => {
    const completedSections = Object.values(sections).filter(
      (section) => section.status === "completed",
    );
    if (completedSections.length === 0) return getInitialQuality();

    const avgScore =
      completedSections.reduce(
        (sum, section) => sum + section.quality.score,
        0,
      ) / completedSections.length;

    return {
      score: avgScore,
      dimensions: {
        contextIntegration: avgScore,
        agentOptimization: avgScore,
        completeness: avgScore,
        actionability: avgScore,
      },
      recommendations:
        avgScore < 85
          ? ["Improve prompt quality", "Add more context integration"]
          : [],
      readyForImplementation: avgScore >= 85,
    };
  };

  const getStatusIcon = (status: PlaybookSection["status"]) => {
    switch (status) {
      case "completed":
        return <CheckCircle className="h-5 w-5 text-green-600" />;
      case "in-progress":
        return <RefreshCw className="h-5 w-5 text-blue-600 animate-spin" />;
      case "error":
        return <AlertTriangle className="h-5 w-5 text-red-600" />;
      default:
        return <Clock className="h-5 w-5 text-gray-400" />;
    }
  };

  const canProceedToNext = (sectionId: string): boolean => {
    const dependencies: Record<string, string[]> = {
      developmentWorkflow: ["codingPrompts"],
      testingStrategy: ["codingPrompts"],
      deploymentGuide: ["codingPrompts"],
      finalPlaybook: [
        "codingPrompts",
        "developmentWorkflow",
        "testingStrategy",
        "deploymentGuide",
      ],
    };

    const deps = dependencies[sectionId] || [];
    return deps.every((dep) => sections[dep]?.status === "completed");
  };

  const overallProgress = useMemo(() => {
    const totalSections = Object.keys(sections).length;
    const completedSections = Object.values(sections).filter(
      (s) => s.status === "completed",
    ).length;
    return totalSections > 0 ? (completedSections / totalSections) * 100 : 0;
  }, [sections]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">
            Implementation Playbook Generation
          </h2>
          <p className="mt-1 text-sm text-gray-600">
            Generate comprehensive implementation guides with coding agent
            prompts
          </p>
        </div>
        <div className="flex space-x-3">
          <Select value={agentType} onValueChange={setAgentType}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="Agent Type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="general">General</SelectItem>
              <SelectItem value="cursor">Cursor</SelectItem>
              <SelectItem value="copilot">GitHub Copilot</SelectItem>
              <SelectItem value="custom">Custom</SelectItem>
            </SelectContent>
          </Select>

          <Select
            value={workflowMethodology}
            onValueChange={setWorkflowMethodology}
          >
            <SelectTrigger className="w-40">
              <SelectValue placeholder="Methodology" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="agile_sprints">Agile Sprints</SelectItem>
              <SelectItem value="waterfall">Waterfall</SelectItem>
              <SelectItem value="kanban">Kanban</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Progress Overview */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Overall Progress</CardTitle>
            {overallQuality && (
              <div className="flex items-center space-x-4">
                <Badge
                  variant={
                    overallQuality.readyForImplementation
                      ? "success"
                      : "secondary"
                  }
                >
                  Quality: {overallQuality.score.toFixed(0)}%
                </Badge>
                {contextValidation && (
                  <Badge
                    variant={
                      contextValidation.context_integrity
                        ? "success"
                        : "warning"
                    }
                  >
                    Context: {contextValidation.overall_score || 0}%
                  </Badge>
                )}
              </div>
            )}
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Stage Progress</span>
              <span className="text-sm text-gray-600">
                {overallProgress.toFixed(0)}%
              </span>
            </div>
            <Progress value={overallProgress} className="w-full" />

            {overallQuality && (
              <QualityGate quality={overallQuality} threshold={85} />
            )}
          </div>
        </CardContent>
      </Card>

      {/* Context Validation */}
      {contextValidation && (
        <Alert>
          <Target className="h-4 w-4" />
          <AlertDescription>
            Context Integration: {contextValidation.overall_score}% -
            {contextValidation.context_integrity
              ? " All stages properly integrated"
              : " Some context issues detected"}
          </AlertDescription>
        </Alert>
      )}

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-6">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="prompts">Coding Prompts</TabsTrigger>
          <TabsTrigger value="workflow">Workflow</TabsTrigger>
          <TabsTrigger value="testing">Testing</TabsTrigger>
          <TabsTrigger value="deployment">Deployment</TabsTrigger>
          <TabsTrigger value="playbook">Final Playbook</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {Object.entries(sections).map(([key, section]) => (
              <Card key={key} className="relative">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">
                    {section.title}
                  </CardTitle>
                  {getStatusIcon(section.status)}
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-gray-600">Progress</span>
                      <span className="text-xs font-medium">
                        {section.progress}%
                      </span>
                    </div>
                    <Progress value={section.progress} className="w-full" />

                    {section.quality.score > 0 && (
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-gray-600">Quality</span>
                        <Badge
                          variant={
                            section.quality.readyForImplementation
                              ? "success"
                              : "secondary"
                          }
                          className="text-xs"
                        >
                          {section.quality.score.toFixed(0)}%
                        </Badge>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Action Buttons */}
          <div className="flex flex-wrap gap-3">
            <Button
              onClick={generateCodingPrompts}
              disabled={
                isGenerating || sections.codingPrompts.status === "completed"
              }
              className="flex items-center space-x-2"
            >
              <Brain className="h-4 w-4" />
              <span>Generate Coding Prompts</span>
            </Button>

            <Button
              onClick={createDevelopmentWorkflow}
              disabled={
                !canProceedToNext("developmentWorkflow") ||
                sections.developmentWorkflow.status === "completed"
              }
              variant="outline"
              className="flex items-center space-x-2"
            >
              <GitBranch className="h-4 w-4" />
              <span>Create Workflow</span>
            </Button>

            <Button
              onClick={generateTestingStrategy}
              disabled={
                !canProceedToNext("testingStrategy") ||
                sections.testingStrategy.status === "completed"
              }
              variant="outline"
              className="flex items-center space-x-2"
            >
              <TestTube className="h-4 w-4" />
              <span>Generate Testing Strategy</span>
            </Button>

            <Button
              onClick={createDeploymentGuide}
              disabled={
                !canProceedToNext("deploymentGuide") ||
                sections.deploymentGuide.status === "completed"
              }
              variant="outline"
              className="flex items-center space-x-2"
            >
              <Rocket className="h-4 w-4" />
              <span>Create Deployment Guide</span>
            </Button>

            <Button
              onClick={compileFinalPlaybook}
              disabled={
                !canProceedToNext("finalPlaybook") ||
                sections.finalPlaybook.status === "completed"
              }
              variant="default"
              className="flex items-center space-x-2"
            >
              <Package className="h-4 w-4" />
              <span>Compile Playbook</span>
            </Button>
          </div>
        </TabsContent>

        {/* Coding Prompts Tab */}
        <TabsContent value="prompts" className="space-y-6">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Agent-Optimized Coding Prompts</CardTitle>
                <div className="flex space-x-2">
                  <Button
                    onClick={generateCodingPrompts}
                    disabled={isGenerating}
                    size="sm"
                  >
                    {isGenerating ? (
                      <RefreshCw className="h-4 w-4 animate-spin" />
                    ) : (
                      <Brain className="h-4 w-4" />
                    )}
                    {isGenerating ? "Generating..." : "Generate Prompts"}
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {sections.codingPrompts.data ? (
                <div className="space-y-4">
                  {Object.entries(sections.codingPrompts.data).map(
                    ([key, prompt]: [string, any]) => (
                      <Card key={key} className="border-l-4 border-blue-500">
                        <CardHeader>
                          <div className="flex items-center justify-between">
                            <CardTitle className="text-lg capitalize">
                              {key.replace(/([A-Z])/g, " $1")}
                            </CardTitle>
                            <Badge variant="outline">
                              {prompt.category || "general"}
                            </Badge>
                          </div>
                        </CardHeader>
                        <CardContent>
                          <div className="space-y-3">
                            <div className="prose max-w-none">
                              <p className="text-sm text-gray-700">
                                {prompt.content?.substring(0, 200)}...
                              </p>
                            </div>

                            {prompt.agent_instructions && (
                              <div>
                                <h4 className="text-sm font-medium text-gray-900 mb-2">
                                  Agent Instructions:
                                </h4>
                                <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                                  {prompt.agent_instructions
                                    .slice(0, 3)
                                    .map((instruction: string, idx: number) => (
                                      <li key={idx}>{instruction}</li>
                                    ))}
                                </ul>
                              </div>
                            )}

                            {prompt.validation_criteria && (
                              <div>
                                <h4 className="text-sm font-medium text-gray-900 mb-2">
                                  Validation Criteria:
                                </h4>
                                <div className="flex flex-wrap gap-2">
                                  {prompt.validation_criteria
                                    .slice(0, 3)
                                    .map((criteria: string, idx: number) => (
                                      <Badge
                                        key={idx}
                                        variant="secondary"
                                        className="text-xs"
                                      >
                                        {criteria}
                                      </Badge>
                                    ))}
                                </div>
                              </div>
                            )}
                          </div>
                        </CardContent>
                      </Card>
                    ),
                  )}
                </div>
              ) : (
                <div className="text-center py-12">
                  <Code className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">
                    No Coding Prompts Generated
                  </h3>
                  <p className="text-gray-600 mb-4">
                    Generate agent-optimized coding prompts to get started.
                  </p>
                  <Button
                    onClick={generateCodingPrompts}
                    disabled={isGenerating}
                  >
                    Generate Prompts
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Additional tabs would be implemented similarly */}
        <TabsContent value="workflow" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Development Workflow</CardTitle>
            </CardHeader>
            <CardContent>
              {sections.developmentWorkflow.data ? (
                <div className="space-y-6">
                  {/* Workflow content */}
                  <div className="text-center py-12">
                    <p>Development workflow content would be displayed here</p>
                  </div>
                </div>
              ) : (
                <div className="text-center py-12">
                  <GitBranch className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">
                    No Workflow Created
                  </h3>
                  <p className="text-gray-600 mb-4">
                    Create a systematic development workflow.
                  </p>
                  <Button
                    onClick={createDevelopmentWorkflow}
                    disabled={!canProceedToNext("developmentWorkflow")}
                  >
                    Create Workflow
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="testing" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Testing Strategy</CardTitle>
            </CardHeader>
            <CardContent>
              {sections.testingStrategy.data ? (
                <div className="space-y-6">
                  {/* Testing strategy content */}
                  <div className="text-center py-12">
                    <p>Testing strategy content would be displayed here</p>
                  </div>
                </div>
              ) : (
                <div className="text-center py-12">
                  <TestTube className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">
                    No Testing Strategy
                  </h3>
                  <p className="text-gray-600 mb-4">
                    Generate comprehensive testing strategy.
                  </p>
                  <Button
                    onClick={generateTestingStrategy}
                    disabled={!canProceedToNext("testingStrategy")}
                  >
                    Generate Strategy
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="deployment" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Deployment Guide</CardTitle>
            </CardHeader>
            <CardContent>
              {sections.deploymentGuide.data ? (
                <div className="space-y-6">
                  {/* Deployment guide content */}
                  <div className="text-center py-12">
                    <p>Deployment guide content would be displayed here</p>
                  </div>
                </div>
              ) : (
                <div className="text-center py-12">
                  <Rocket className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">
                    No Deployment Guide
                  </h3>
                  <p className="text-gray-600 mb-4">
                    Create comprehensive deployment guide.
                  </p>
                  <Button
                    onClick={createDeploymentGuide}
                    disabled={!canProceedToNext("deploymentGuide")}
                  >
                    Create Guide
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="playbook" className="space-y-6">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Complete Implementation Playbook</CardTitle>
                <div className="flex space-x-2">
                  <Select value={exportFormat} onValueChange={setExportFormat}>
                    <SelectTrigger className="w-40">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="json">JSON</SelectItem>
                      <SelectItem value="markdown">Markdown</SelectItem>
                      <SelectItem value="pdf">PDF Document</SelectItem>
                      <SelectItem value="zip">ZIP Archive</SelectItem>
                    </SelectContent>
                  </Select>

                  <Button
                    onClick={exportPlaybook}
                    disabled={!sections.finalPlaybook.data}
                    size="sm"
                    variant="outline"
                  >
                    <Download className="h-4 w-4 mr-2" />
                    Export
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {sections.finalPlaybook.data ? (
                <div className="space-y-6">
                  {/* Final playbook content */}
                  <div className="text-center py-12">
                    <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">
                      Implementation Playbook Ready
                    </h3>
                    <p className="text-gray-600 mb-4">
                      Complete implementation playbook has been generated and
                      validated.
                    </p>
                    <div className="flex justify-center space-x-3">
                      <Button
                        onClick={validateContextIntegration}
                        variant="outline"
                      >
                        <Target className="h-4 w-4 mr-2" />
                        Validate Context
                      </Button>
                      <Button onClick={exportPlaybook}>
                        <Download className="h-4 w-4 mr-2" />
                        Export Playbook
                      </Button>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-12">
                  <Package className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">
                    Playbook Not Compiled
                  </h3>
                  <p className="text-gray-600 mb-4">
                    Complete all sections to compile the final playbook.
                  </p>
                  <Button
                    onClick={compileFinalPlaybook}
                    disabled={!canProceedToNext("finalPlaybook")}
                  >
                    Compile Playbook
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default ImplementationPlaybookStage;
