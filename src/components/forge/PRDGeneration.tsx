import React, { useState, useEffect, useCallback, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  CheckCircle,
  AlertTriangle,
  Clock,
  Download,
  Eye,
  FileText,
  Users,
  Target,
  Zap,
} from "lucide-react";
import { toast } from "@/hooks/use-toast";

import { useAuth } from "@/hooks/useAuth";
import { useLLMCost } from "@/hooks/useLLMCost";
import { forgeApi } from "@/services/api";
import LLMSelector from "@/components/LLMSelector";
import { QualityGate } from "@/components/forge/QualityGate";
import { ProgressIndicator } from "@/components/forge/ProgressIndicator";

interface PRDGenerationProps {
  projectId: string;
  ideaRefinementData: any;
  onStageComplete: (stageData: any) => void;
  onQualityUpdate: (quality: any) => void;
}

interface RequirementItem {
  id: string;
  title: string;
  description: string;
  priority: "High" | "Medium" | "Low";
  businessValue: string;
  acceptanceCriteria: string[];
}

interface UserStory {
  id: string;
  title: string;
  asA: string;
  iWant: string;
  soThat: string;
  acceptanceCriteria: string[];
  priority: "High" | "Medium" | "Low";
  estimatedEffort: string;
  businessValue: string;
  investValidation: {
    independent: boolean;
    negotiable: boolean;
    valuable: boolean;
    estimable: boolean;
    small: boolean;
    testable: boolean;
  };
}

interface PrioritizedFeature {
  featureId: string;
  featureName: string;
  description: string;
  priority: string;
  businessValue: number;
  userValue: number;
  alignmentScore: number;
  mvpCandidate: boolean;
  rationale: string;
}

interface PRDData {
  requirements: {
    functionalRequirements: RequirementItem[];
    nonFunctionalRequirements: any[];
    businessRules: any[];
    constraints: any[];
    assumptions: any[];
  };
  userStories: {
    userPersonas: any[];
    stories: UserStory[];
    epicGrouping: any[];
  };
  prioritizedFeatures: {
    features: PrioritizedFeature[];
    prioritySummary: any;
  };
  qualityAssessment: any;
  prdDocument: any;
}

const PRD_QUALITY_THRESHOLD = 80; // 80% threshold for PRD stage

export default function PRDGeneration({
  projectId,
  ideaRefinementData,
  onStageComplete,
  onQualityUpdate,
}: PRDGenerationProps) {
  const { user } = useAuth();
  const { trackCost } = useLLMCost();

  // State management
  const [selectedLLM, setSelectedLLM] = useState("gemini-flash");
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState("requirements");
  const [prdData, setPRDData] = useState<PRDData>({
    requirements: {
      functionalRequirements: [],
      nonFunctionalRequirements: [],
      businessRules: [],
      constraints: [],
      assumptions: [],
    },
    userStories: {
      userPersonas: [],
      stories: [],
      epicGrouping: [],
    },
    prioritizedFeatures: {
      features: [],
      prioritySummary: {},
    },
    qualityAssessment: null,
    prdDocument: null,
  });

  // Quality and validation state
  const [currentQuality, setCurrentQuality] = useState<any>(null);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const [canProceed, setCanProceed] = useState(false);

  // UI state
  const [expandedRequirement, setExpandedRequirement] = useState<string | null>(
    null,
  );
  const [expandedStory, setExpandedStory] = useState<string | null>(null);
  const [showDocumentPreview, setShowDocumentPreview] = useState(false);

  // Configuration state
  const [requirementFocus] = useState<string[]>([
    "Core functionality",
    "User experience",
    "Performance requirements",
    "Security considerations",
  ]);
  const [storyFormat, setStoryFormat] = useState<
    "standard" | "gherkin" | "invest"
  >("standard");
  const [prioritizationMethod, setPrioritizationMethod] = useState<
    "rice" | "moscow" | "kano"
  >("rice");

  // Memoized calculations
  const progressPercentage = useMemo(() => {
    let completed = 0;
    const total = 4; // requirements, stories, prioritization, document

    if (prdData.requirements.functionalRequirements.length > 0) completed++;
    if (prdData.userStories.stories.length > 0) completed++;
    if (prdData.prioritizedFeatures.features.length > 0) completed++;
    if (prdData.prdDocument) completed++;

    return (completed / total) * 100;
  }, [prdData]);

  const overallQualityScore = useMemo(() => {
    if (!currentQuality) return 0;
    return currentQuality.overallScore || 0;
  }, [currentQuality]);

  // API calls
  const extractRequirements = useCallback(async () => {
    if (!ideaRefinementData) {
      toast.error("Idea refinement data is required");
      return;
    }

    setIsLoading(true);
    try {
      const result = await forgeApi.extractRequirements(projectId, {
        ideaContext: ideaRefinementData,
        requirementFocus,
        selectedLLM,
      });

      // Track costs
      if ((result as any).costTracking) {
        trackCost();
      }

      setPRDData((prev) => ({
        ...prev,
        requirements: {
          ...prev.requirements,
          functionalRequirements: result.requirements as any,
        },
        qualityAssessment: (result as any).qualityAssessment,
      }));

      // Update quality tracking
      if ((result as any).qualityAssessment) {
        setCurrentQuality((result as any).qualityAssessment);
        onQualityUpdate({
          stage: "prd_generation",
          quality: (result as any).qualityAssessment,
        });
      }

      toast.success("Requirements extracted successfully");
      setActiveTab("stories");
    } catch (error) {
      console.error("Error extracting requirements:", error);
      toast.error(
        error instanceof Error
          ? error.message
          : "Failed to extract requirements",
      );
      setValidationErrors((prev) => [
        ...prev,
        "Requirements extraction failed",
      ]);
    } finally {
      setIsLoading(false);
    }
  }, [
    projectId,
    ideaRefinementData,
    requirementFocus,
    selectedLLM,
    trackCost,
    onQualityUpdate,
  ]);

  const generateUserStories = useCallback(async () => {
    if (!prdData.requirements.functionalRequirements.length) {
      toast.error("Requirements must be extracted first");
      return;
    }

    setIsLoading(true);
    try {
      const result = await forgeApi.generateUserStories(projectId, {
        requirements: prdData.requirements,
        ideaContext: ideaRefinementData,
        storyFormat,
        selectedLLM,
      } as any);

      // Track costs
      if ((result as any).costTracking) {
        trackCost();
      }

      setPRDData((prev) => ({
        ...prev,
        userStories: {
          ...prev.userStories,
          stories: result.userStories as any,
        },
      }));

      toast.success(
        `Generated ${result.userStories?.length || 0} user stories`,
      );
      setActiveTab("prioritization");
    } catch (error) {
      console.error("Error generating user stories:", error);
      toast.error(
        error instanceof Error
          ? error.message
          : "Failed to generate user stories",
      );
      setValidationErrors((prev) => [...prev, "User story generation failed"]);
    } finally {
      setIsLoading(false);
    }
  }, [
    projectId,
    prdData.requirements,
    ideaRefinementData,
    storyFormat,
    selectedLLM,
    trackCost,
  ]);

  const prioritizeFeatures = useCallback(async () => {
    if (!prdData.userStories.stories.length) {
      toast.error("User stories must be generated first");
      return;
    }

    // Extract features from user stories and requirements
    const features = [
      ...prdData.requirements.functionalRequirements.map((req) => ({
        id: req.id,
        name: req.title,
        description: req.description,
        type: "requirement",
      })),
      ...prdData.userStories.stories.map((story) => ({
        id: story.id,
        name: story.title,
        description: story.iWant,
        type: "story",
      })),
    ];

    setIsLoading(true);
    try {
      const result = await forgeApi.prioritizeFeatures(projectId, {
        features,
        userStories: prdData.userStories,
        ideaContext: ideaRefinementData,
        prioritizationMethod,
        selectedLLM,
      });

      // Track costs
      if ((result as any).costTracking) {
        trackCost();
      }

      setPRDData((prev) => ({
        ...prev,
        prioritizedFeatures: result.prioritizedFeatures as any,
      }));

      toast.success(
        `Prioritized ${(result.prioritizedFeatures as any)?.features?.length || Object.keys(result.prioritizedFeatures).length} features`,
      );
      setActiveTab("document");
    } catch (error) {
      console.error("Error prioritizing features:", error);
      toast.error(
        error instanceof Error
          ? error.message
          : "Failed to prioritize features",
      );
      setValidationErrors((prev) => [...prev, "Feature prioritization failed"]);
    } finally {
      setIsLoading(false);
    }
  }, [
    projectId,
    prdData.userStories,
    prdData.requirements,
    ideaRefinementData,
    prioritizationMethod,
    selectedLLM,
    trackCost,
  ]);

  const generatePRDDocument = useCallback(async () => {
    if (!prdData.prioritizedFeatures.features.length) {
      toast.error("Feature prioritization must be completed first");
      return;
    }

    setIsLoading(true);
    try {
      const result = await forgeApi.generatePRDDocument(projectId);

      setPRDData((prev) => ({
        ...prev,
        prdDocument: result,
      }));

      toast.success("PRD document generated successfully");
    } catch (error) {
      console.error("Error generating PRD document:", error);
      toast.error(
        error instanceof Error
          ? error.message
          : "Failed to generate PRD document",
      );
      setValidationErrors((prev) => [
        ...prev,
        "PRD document generation failed",
      ]);
    } finally {
      setIsLoading(false);
    }
  }, [projectId, prdData, ideaRefinementData]);

  // Quality assessment
  const assessQuality = useCallback(async () => {
    if (!projectId) return;

    try {
      const assessment = await forgeApi.getPRDQualityAssessment(projectId);
      setCurrentQuality(assessment as any);

      // Check if quality threshold is met
      const qualityMet = assessment.overallScore >= PRD_QUALITY_THRESHOLD;
      const consistencyOk =
        (assessment as any).crossStageValidation?.isConsistent ?? true;

      setCanProceed(qualityMet && consistencyOk);

      if (!consistencyOk) {
        setValidationErrors(
          (assessment as any).crossStageValidation?.validationErrors || [],
        );
      }

      onQualityUpdate({
        stage: "prd_generation",
        quality: assessment,
        canProceed: qualityMet && consistencyOk,
      });
    } catch (error) {
      console.error("Error assessing quality:", error);
    }
  }, [projectId, onQualityUpdate]);

  // Complete stage
  const completeStage = useCallback(
    async (forceComplete = false) => {
      if (!prdData.prdDocument && !forceComplete) {
        toast.error("PRD document must be generated before completing");
        return;
      }

      if (!canProceed && !forceComplete) {
        toast.error(
          `Quality threshold not met (${overallQualityScore}% < ${PRD_QUALITY_THRESHOLD}%)`,
        );
        return;
      }

      setIsLoading(true);
      try {
        const finalPRDData = {
          requirements: prdData.requirements,
          userStories: prdData.userStories,
          prioritizedFeatures: prdData.prioritizedFeatures,
          prdDocument: prdData.prdDocument,
          qualityMetrics: currentQuality,
          completedAt: new Date().toISOString(),
        };

        const result = await forgeApi.completePRDGeneration(projectId, {
          ...finalPRDData,
          forceComplete,
        } as any);

        toast.success(
          `PRD stage completed with ${result.qualityAssessment?.overallScore ?? "N/A"}% quality`,
        );

        onStageComplete({
          stage: "prd_generation",
          data: finalPRDData,
          quality: result.qualityAssessment?.overallScore,
          completedAt: new Date().toISOString(),
          nextStage: result.nextStage,
        });
      } catch (error) {
        console.error("Error completing PRD stage:", error);
        toast.error(
          error instanceof Error ? error.message : "Failed to complete stage",
        );
      } finally {
        setIsLoading(false);
      }
    },
    [
      projectId,
      prdData,
      currentQuality,
      canProceed,
      overallQualityScore,
      onStageComplete,
    ],
  );

  // Effects
  useEffect(() => {
    if (
      prdData.requirements.functionalRequirements.length > 0 ||
      prdData.userStories.stories.length > 0 ||
      prdData.prioritizedFeatures.features.length > 0
    ) {
      assessQuality();
    }
  }, [prdData, assessQuality]);

  // Utility functions
  const getInvestScore = (story: UserStory): number => {
    const validation = story.investValidation;
    const trueCount = Object.values(validation).filter(Boolean).length;
    return (trueCount / 6) * 100;
  };

  const getPriorityColor = (
    priority: string,
  ):
    | "default"
    | "secondary"
    | "destructive"
    | "outline"
    | "success"
    | "warning" => {
    switch (priority.toLowerCase()) {
      case "high":
      case "must-have":
      case "critical":
        return "destructive";
      case "medium":
      case "should-have":
      case "important":
        return "default";
      case "low":
      case "could-have":
      case "nice-to-have":
        return "secondary";
      default:
        return "outline";
    }
  };

  const downloadPRD = useCallback(() => {
    if (!prdData.prdDocument) {
      toast.error("No PRD document to download");
      return;
    }

    const content = prdData.prdDocument.exportData?.content || "";
    const blob = new Blob([content], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = url;
    a.download = `PRD_${projectId}_${new Date().toISOString().split("T")[0]}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    toast.success("PRD document downloaded");
  }, [prdData.prdDocument, projectId]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">PRD Generation</h2>
          <p className="text-muted-foreground">
            Transform refined ideas into comprehensive product requirements
          </p>
        </div>
        <div className="flex items-center gap-4">
          <LLMSelector
            selectedModel={selectedLLM}
            onModelChange={setSelectedLLM}
            task="requirements_analysis"
          />
          <Badge variant={canProceed ? "default" : "secondary"}>
            Quality: {overallQualityScore.toFixed(1)}%
          </Badge>
        </div>
      </div>

      {/* Progress and Quality */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Stage Progress</CardTitle>
          </CardHeader>
          <CardContent>
            <ProgressIndicator current={progressPercentage} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Quality Gate</CardTitle>
          </CardHeader>
          <CardContent>
            <QualityGate
              currentScore={overallQualityScore}
              threshold={PRD_QUALITY_THRESHOLD}
            />
          </CardContent>
        </Card>
      </div>

      {/* Validation Errors */}
      {validationErrors.length > 0 && (
        <Alert>
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            <div className="space-y-1">
              <strong>Validation Issues:</strong>
              <ul className="list-disc list-inside space-y-1">
                {validationErrors.map((error, index) => (
                  <li key={index} className="text-sm">
                    {error}
                  </li>
                ))}
              </ul>
            </div>
          </AlertDescription>
        </Alert>
      )}

      {/* Main Content Tabs */}
      <Tabs
        value={activeTab}
        onValueChange={setActiveTab}
        className="space-y-4"
      >
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="requirements" className="flex items-center gap-2">
            <FileText className="h-4 w-4" />
            Requirements
            {prdData.requirements.functionalRequirements.length > 0 && (
              <CheckCircle className="h-3 w-3 text-green-600" />
            )}
          </TabsTrigger>
          <TabsTrigger value="stories" className="flex items-center gap-2">
            <Users className="h-4 w-4" />
            User Stories
            {prdData.userStories.stories.length > 0 && (
              <CheckCircle className="h-3 w-3 text-green-600" />
            )}
          </TabsTrigger>
          <TabsTrigger
            value="prioritization"
            className="flex items-center gap-2"
          >
            <Target className="h-4 w-4" />
            Prioritization
            {prdData.prioritizedFeatures.features.length > 0 && (
              <CheckCircle className="h-3 w-3 text-green-600" />
            )}
          </TabsTrigger>
          <TabsTrigger value="document" className="flex items-center gap-2">
            <Download className="h-4 w-4" />
            Document
            {prdData.prdDocument && (
              <CheckCircle className="h-3 w-3 text-green-600" />
            )}
          </TabsTrigger>
        </TabsList>

        {/* Requirements Tab */}
        <TabsContent value="requirements" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Requirements Extraction</CardTitle>
                <Button
                  onClick={extractRequirements}
                  disabled={isLoading || !ideaRefinementData}
                  className="flex items-center gap-2"
                >
                  {isLoading ? (
                    <>
                      <Clock className="h-4 w-4 animate-spin" />
                      Extracting...
                    </>
                  ) : (
                    <>
                      <Zap className="h-4 w-4" />
                      Extract Requirements
                    </>
                  )}
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Configuration */}
              <div className="space-y-2">
                <label className="text-sm font-medium">Focus Areas</label>
                <div className="flex flex-wrap gap-2">
                  {requirementFocus.map((focus, index) => (
                    <Badge key={index} variant="outline">
                      {focus}
                    </Badge>
                  ))}
                </div>
              </div>

              {/* Results */}
              {prdData.requirements.functionalRequirements.length > 0 && (
                <div className="space-y-4">
                  <h4 className="font-semibold">
                    Functional Requirements (
                    {prdData.requirements.functionalRequirements.length})
                  </h4>
                  <div className="space-y-2">
                    {prdData.requirements.functionalRequirements.map((req) => (
                      <Card key={req.id} className="p-4">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                              <Badge variant="outline">{req.id}</Badge>
                              <Badge variant={getPriorityColor(req.priority)}>
                                {req.priority}
                              </Badge>
                            </div>
                            <h5 className="font-medium mb-1">{req.title}</h5>
                            <p className="text-sm text-muted-foreground mb-2">
                              {req.description}
                            </p>
                            {expandedRequirement === req.id && (
                              <div className="space-y-2">
                                <div>
                                  <strong className="text-sm">
                                    Business Value:
                                  </strong>
                                  <p className="text-sm text-muted-foreground">
                                    {req.businessValue}
                                  </p>
                                </div>
                                {req.acceptanceCriteria.length > 0 && (
                                  <div>
                                    <strong className="text-sm">
                                      Acceptance Criteria:
                                    </strong>
                                    <ul className="list-disc list-inside text-sm text-muted-foreground">
                                      {req.acceptanceCriteria.map(
                                        (criteria, idx) => (
                                          <li key={idx}>{criteria}</li>
                                        ),
                                      )}
                                    </ul>
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() =>
                              setExpandedRequirement(
                                expandedRequirement === req.id ? null : req.id,
                              )
                            }
                          >
                            <Eye className="h-4 w-4" />
                          </Button>
                        </div>
                      </Card>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* User Stories Tab */}
        <TabsContent value="stories" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>User Stories Generation</CardTitle>
                <div className="flex items-center gap-2">
                  <select
                    value={storyFormat}
                    onChange={(e) => setStoryFormat(e.target.value as any)}
                    className="px-3 py-1 border rounded text-sm"
                  >
                    <option value="standard">Standard</option>
                    <option value="gherkin">Gherkin</option>
                    <option value="invest">INVEST</option>
                  </select>
                  <Button
                    onClick={generateUserStories}
                    disabled={
                      isLoading ||
                      !prdData.requirements.functionalRequirements.length
                    }
                    className="flex items-center gap-2"
                  >
                    {isLoading ? (
                      <>
                        <Clock className="h-4 w-4 animate-spin" />
                        Generating...
                      </>
                    ) : (
                      <>
                        <Users className="h-4 w-4" />
                        Generate Stories
                      </>
                    )}
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {prdData.userStories.stories.length > 0 && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h4 className="font-semibold">
                      User Stories ({prdData.userStories.stories.length})
                    </h4>
                    <Badge variant="outline">
                      Avg INVEST:{" "}
                      {prdData.userStories.stories.length > 0
                        ? (
                            prdData.userStories.stories.reduce(
                              (sum, story) => sum + getInvestScore(story),
                              0,
                            ) / prdData.userStories.stories.length
                          ).toFixed(1)
                        : 0}
                      %
                    </Badge>
                  </div>
                  <div className="space-y-2">
                    {prdData.userStories.stories.map((story) => (
                      <Card key={story.id} className="p-4">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                              <Badge variant="outline">{story.id}</Badge>
                              <Badge variant={getPriorityColor(story.priority)}>
                                {story.priority}
                              </Badge>
                              <Badge variant="secondary">
                                INVEST: {getInvestScore(story).toFixed(0)}%
                              </Badge>
                            </div>
                            <h5 className="font-medium mb-2">{story.title}</h5>
                            <div className="text-sm text-muted-foreground mb-2">
                              <strong>As a</strong> {story.asA},{" "}
                              <strong>I want</strong> {story.iWant}{" "}
                              <strong>so that</strong> {story.soThat}
                            </div>
                            {expandedStory === story.id && (
                              <div className="space-y-2">
                                <div>
                                  <strong className="text-sm">
                                    Business Value:
                                  </strong>
                                  <p className="text-sm text-muted-foreground">
                                    {story.businessValue}
                                  </p>
                                </div>
                                <div>
                                  <strong className="text-sm">
                                    Estimated Effort:
                                  </strong>
                                  <p className="text-sm text-muted-foreground">
                                    {story.estimatedEffort}
                                  </p>
                                </div>
                                {story.acceptanceCriteria.length > 0 && (
                                  <div>
                                    <strong className="text-sm">
                                      Acceptance Criteria:
                                    </strong>
                                    <ul className="list-disc list-inside text-sm text-muted-foreground">
                                      {story.acceptanceCriteria.map(
                                        (criteria, idx) => (
                                          <li key={idx}>{criteria}</li>
                                        ),
                                      )}
                                    </ul>
                                  </div>
                                )}
                                <div className="grid grid-cols-3 gap-2 text-xs">
                                  {Object.entries(story.investValidation).map(
                                    ([key, value]) => (
                                      <div
                                        key={key}
                                        className={`p-1 rounded text-center ${value ? "bg-green-100 text-green-800" : "bg-gray-100 text-gray-600"}`}
                                      >
                                        {key.charAt(0).toUpperCase() +
                                          key.slice(1)}
                                      </div>
                                    ),
                                  )}
                                </div>
                              </div>
                            )}
                          </div>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() =>
                              setExpandedStory(
                                expandedStory === story.id ? null : story.id,
                              )
                            }
                          >
                            <Eye className="h-4 w-4" />
                          </Button>
                        </div>
                      </Card>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Prioritization Tab */}
        <TabsContent value="prioritization" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Feature Prioritization</CardTitle>
                <div className="flex items-center gap-2">
                  <select
                    value={prioritizationMethod}
                    onChange={(e) =>
                      setPrioritizationMethod(e.target.value as any)
                    }
                    className="px-3 py-1 border rounded text-sm"
                  >
                    <option value="rice">RICE</option>
                    <option value="moscow">MoSCoW</option>
                    <option value="kano">Kano Model</option>
                  </select>
                  <Button
                    onClick={prioritizeFeatures}
                    disabled={isLoading || !prdData.userStories.stories.length}
                    className="flex items-center gap-2"
                  >
                    {isLoading ? (
                      <>
                        <Clock className="h-4 w-4 animate-spin" />
                        Prioritizing...
                      </>
                    ) : (
                      <>
                        <Target className="h-4 w-4" />
                        Prioritize Features
                      </>
                    )}
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {prdData.prioritizedFeatures.features.length > 0 && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h4 className="font-semibold">
                      Prioritized Features (
                      {prdData.prioritizedFeatures.features.length})
                    </h4>
                    <Badge variant="outline">
                      MVP Candidates:{" "}
                      {
                        prdData.prioritizedFeatures.features.filter(
                          (f) => f.mvpCandidate,
                        ).length
                      }
                    </Badge>
                  </div>
                  <div className="space-y-2">
                    {prdData.prioritizedFeatures.features
                      .sort((a, b) => b.businessValue - a.businessValue)
                      .map((feature) => (
                        <Card
                          key={feature.featureId}
                          className={`p-4 ${feature.mvpCandidate ? "border-primary" : ""}`}
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-2">
                                <Badge variant="outline">
                                  {feature.featureId}
                                </Badge>
                                <Badge
                                  variant={getPriorityColor(feature.priority)}
                                >
                                  {feature.priority}
                                </Badge>
                                {feature.mvpCandidate && (
                                  <Badge variant="default">MVP</Badge>
                                )}
                              </div>
                              <h5 className="font-medium mb-1">
                                {feature.featureName}
                              </h5>
                              <p className="text-sm text-muted-foreground mb-2">
                                {feature.description}
                              </p>
                              <div className="grid grid-cols-3 gap-4 text-sm">
                                <div>
                                  <span className="font-medium">
                                    Business Value:
                                  </span>
                                  <div className="flex items-center gap-1">
                                    <div className="w-16 bg-gray-200 rounded-full h-2">
                                      <div
                                        className="bg-blue-600 h-2 rounded-full"
                                        style={{
                                          width: `${feature.businessValue * 10}%`,
                                        }}
                                      />
                                    </div>
                                    <span>{feature.businessValue}/10</span>
                                  </div>
                                </div>
                                <div>
                                  <span className="font-medium">
                                    User Value:
                                  </span>
                                  <div className="flex items-center gap-1">
                                    <div className="w-16 bg-gray-200 rounded-full h-2">
                                      <div
                                        className="bg-green-600 h-2 rounded-full"
                                        style={{
                                          width: `${feature.userValue * 10}%`,
                                        }}
                                      />
                                    </div>
                                    <span>{feature.userValue}/10</span>
                                  </div>
                                </div>
                                <div>
                                  <span className="font-medium">
                                    Alignment:
                                  </span>
                                  <div className="flex items-center gap-1">
                                    <div className="w-16 bg-gray-200 rounded-full h-2">
                                      <div
                                        className="bg-purple-600 h-2 rounded-full"
                                        style={{
                                          width: `${feature.alignmentScore * 10}%`,
                                        }}
                                      />
                                    </div>
                                    <span>{feature.alignmentScore}/10</span>
                                  </div>
                                </div>
                              </div>
                              <p className="text-xs text-muted-foreground mt-2">
                                {feature.rationale}
                              </p>
                            </div>
                          </div>
                        </Card>
                      ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Document Tab */}
        <TabsContent value="document" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>PRD Document</CardTitle>
                <div className="flex items-center gap-2">
                  {prdData.prdDocument && (
                    <Button
                      variant="outline"
                      onClick={downloadPRD}
                      className="flex items-center gap-2"
                    >
                      <Download className="h-4 w-4" />
                      Download
                    </Button>
                  )}
                  <Button
                    onClick={generatePRDDocument}
                    disabled={
                      isLoading || !prdData.prioritizedFeatures.features.length
                    }
                    className="flex items-center gap-2"
                  >
                    {isLoading ? (
                      <>
                        <Clock className="h-4 w-4 animate-spin" />
                        Generating...
                      </>
                    ) : (
                      <>
                        <FileText className="h-4 w-4" />
                        Generate Document
                      </>
                    )}
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {prdData.prdDocument && (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div className="text-center p-3 bg-gray-50 rounded">
                      <div className="font-semibold">
                        {prdData.prdDocument.documentMetrics?.totalSections ||
                          0}
                      </div>
                      <div className="text-muted-foreground">Sections</div>
                    </div>
                    <div className="text-center p-3 bg-gray-50 rounded">
                      <div className="font-semibold">
                        {prdData.prdDocument.documentMetrics?.wordCount || 0}
                      </div>
                      <div className="text-muted-foreground">Words</div>
                    </div>
                    <div className="text-center p-3 bg-gray-50 rounded">
                      <div className="font-semibold">
                        {prdData.prdDocument.documentMetrics
                          ?.completedSections || 0}
                      </div>
                      <div className="text-muted-foreground">Complete</div>
                    </div>
                    <div className="text-center p-3 bg-gray-50 rounded">
                      <div className="font-semibold">
                        {prdData.prdDocument.documentMetrics?.readabilityScore?.toFixed(
                          0,
                        ) || 0}
                        %
                      </div>
                      <div className="text-muted-foreground">Readability</div>
                    </div>
                  </div>

                  {showDocumentPreview &&
                    prdData.prdDocument.exportData?.content && (
                      <div className="border rounded p-4 max-h-96 overflow-y-auto">
                        <pre className="text-sm whitespace-pre-wrap">
                          {prdData.prdDocument.exportData.content}
                        </pre>
                      </div>
                    )}

                  <Button
                    variant="outline"
                    onClick={() => setShowDocumentPreview(!showDocumentPreview)}
                    className="w-full"
                  >
                    {showDocumentPreview ? "Hide Preview" : "Show Preview"}
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Action Buttons */}
      <div className="flex items-center justify-between pt-6 border-t">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <CheckCircle className="h-4 w-4" />
          {progressPercentage === 100
            ? "Stage Complete"
            : `${progressPercentage.toFixed(0)}% Complete`}
        </div>

        <div className="flex items-center gap-2">
          {!canProceed &&
            overallQualityScore < PRD_QUALITY_THRESHOLD &&
            user?.role === "expert" && (
              <Button
                variant="outline"
                onClick={() => completeStage(true)}
                disabled={isLoading}
              >
                Force Complete
              </Button>
            )}
          <Button
            onClick={() => completeStage(false)}
            disabled={isLoading || !canProceed}
            className="flex items-center gap-2"
          >
            {isLoading ? (
              <>
                <Clock className="h-4 w-4 animate-spin" />
                Completing...
              </>
            ) : (
              <>
                <CheckCircle className="h-4 w-4" />
                Complete PRD Stage
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}
