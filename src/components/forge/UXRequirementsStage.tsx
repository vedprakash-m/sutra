/**
 * UXRequirementsStage - Comprehensive UX design and requirements specification
 * This component implements Stage 3 of the Forge workflow for creating
 * detailed user experience specifications including journeys, wireframes,
 * component specifications, and accessibility validation.
 */
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
  Layout,
  Accessibility,
  Palette,
  Monitor,
  Smartphone,
  Tablet,
  ChevronRight,
  Zap,
} from "lucide-react";
import { toast } from "@/hooks/use-toast";

import { useAuth } from "@/hooks/useAuth";
import { useLLMCost } from "@/hooks/useLLMCost";
import LLMSelector from "@/components/LLMSelector";
import { QualityGate } from "@/components/forge/QualityGate";
import { ProgressIndicator } from "@/components/forge/ProgressIndicator";

interface UXRequirementsStageProps {
  projectId: string;
  prdData: any;
  onStageComplete: (stageData: any) => void;
  onQualityUpdate: (quality: any) => void;
}

interface UserJourneyStep {
  id: string;
  stepNumber: number;
  name: string;
  description: string;
  userActions: string[];
  systemResponses: string[];
  touchpoints: string[];
  emotions: string[];
  painPoints: string[];
  opportunities: string[];
}

interface UserJourney {
  id: string;
  journeyName: string;
  userPersona: string;
  goal: string;
  scenario: string;
  steps: UserJourneyStep[];
  estimatedDuration: string;
  criticalPath: boolean;
}

interface WireframeElement {
  id: string;
  type: "container" | "header" | "nav" | "content" | "sidebar" | "footer" | "form" | "button" | "image" | "text";
  label: string;
  position: { x: number; y: number; width: number; height: number };
  children?: WireframeElement[];
  properties?: {
    text?: string;
    placeholder?: string;
    variant?: string;
    [key: string]: any;
  };
}

interface Wireframe {
  id: string;
  screenName: string;
  screenType: "desktop" | "tablet" | "mobile";
  description: string;
  userJourneyRef?: string;
  elements: WireframeElement[];
  interactions: {
    trigger: string;
    action: string;
    target: string;
  }[];
  notes: string[];
}

interface ComponentSpec {
  id: string;
  componentName: string;
  description: string;
  componentType: "layout" | "navigation" | "input" | "display" | "feedback" | "utility";
  props: {
    name: string;
    type: string;
    required: boolean;
    defaultValue?: any;
    description: string;
  }[];
  states: {
    name: string;
    description: string;
    triggers: string[];
  }[];
  behaviors: string[];
  accessibility: {
    ariaLabel?: string;
    ariaDescribedby?: string;
    role?: string;
    keyboardNavigation: string[];
    screenReaderSupport: string;
  };
  responsiveness: {
    desktop: string;
    tablet: string;
    mobile: string;
  };
  dependencies: string[];
}

interface AccessibilityCheckItem {
  id: string;
  category: "perceivable" | "operable" | "understandable" | "robust";
  criterion: string;
  level: "A" | "AA" | "AAA";
  description: string;
  implementation: string;
  validated: boolean;
  notes?: string;
}

interface UXData {
  userJourneys: UserJourney[];
  wireframes: Wireframe[];
  componentSpecs: ComponentSpec[];
  accessibilityChecklist: AccessibilityCheckItem[];
  designSystem: {
    colors: { name: string; value: string; usage: string }[];
    typography: { name: string; fontFamily: string; usage: string }[];
    spacing: { name: string; value: string }[];
    breakpoints: { name: string; value: string }[];
  };
  uxDocument: any;
  qualityAssessment: any;
}

const UX_QUALITY_THRESHOLD = 85; // 85% threshold for UX stage

export default function UXRequirementsStage({
  projectId,
  prdData,
  onStageComplete,
  onQualityUpdate,
}: UXRequirementsStageProps) {
  const { user } = useAuth();
  const { trackCost } = useLLMCost();

  // State management
  const [selectedLLM, setSelectedLLM] = useState("claude-3-5-sonnet");
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState("journeys");
  const [uxData, setUXData] = useState<UXData>({
    userJourneys: [],
    wireframes: [],
    componentSpecs: [],
    accessibilityChecklist: [],
    designSystem: {
      colors: [],
      typography: [],
      spacing: [],
      breakpoints: [],
    },
    uxDocument: null,
    qualityAssessment: null,
  });

  const [currentQuality, setCurrentQuality] = useState<any>(null);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const [canProceed, setCanProceed] = useState(false);

  // UI state
  const [selectedJourney, setSelectedJourney] = useState<string | null>(null);
  const [selectedWireframe, setSelectedWireframe] = useState<string | null>(null);
  const [deviceView, setDeviceView] = useState<"desktop" | "tablet" | "mobile">("desktop");
  const [showDocumentPreview, setShowDocumentPreview] = useState(false);

  // Memoized calculations
  const progressPercentage = useMemo(() => {
    let completed = 0;
    const total = 5; // journeys, wireframes, components, accessibility, document

    if (uxData.userJourneys.length > 0) completed++;
    if (uxData.wireframes.length > 0) completed++;
    if (uxData.componentSpecs.length > 0) completed++;
    if (uxData.accessibilityChecklist.filter(item => item.validated).length > 0) completed++;
    if (uxData.uxDocument) completed++;

    return (completed / total) * 100;
  }, [uxData]);

  const overallQualityScore = useMemo(() => {
    if (!currentQuality) return 0;
    return currentQuality.overallScore || 0;
  }, [currentQuality]);

  const accessibilityCompletionRate = useMemo(() => {
    if (uxData.accessibilityChecklist.length === 0) return 0;
    const validated = uxData.accessibilityChecklist.filter(item => item.validated).length;
    return (validated / uxData.accessibilityChecklist.length) * 100;
  }, [uxData.accessibilityChecklist]);

  // API calls
  const generateUserJourneys = useCallback(async () => {
    if (!prdData?.userStories) {
      toast.error("PRD user stories are required");
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch(
        `/api/forge/${projectId}/ux/generate-user-journeys`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            prdContext: prdData,
            selectedLLM,
          }),
        },
      );

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || "Failed to generate user journeys");
      }

      const result = await response.json();

      // Track costs
      if (result.costTracking) {
        trackCost();
      }

      setUXData((prev) => ({
        ...prev,
        userJourneys: result.userJourneys,
      }));

      toast.success(`Generated ${result.userJourneys.length} user journeys`);
      setActiveTab("wireframes");
    } catch (error) {
      console.error("Error generating user journeys:", error);
      toast.error(
        error instanceof Error
          ? error.message
          : "Failed to generate user journeys",
      );
      setValidationErrors((prev) => [...prev, "User journey generation failed"]);
    } finally {
      setIsLoading(false);
    }
  }, [projectId, prdData, selectedLLM, trackCost]);

  const generateWireframes = useCallback(async () => {
    if (uxData.userJourneys.length === 0) {
      toast.error("User journeys must be generated first");
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch(
        `/api/forge/${projectId}/ux/generate-wireframes`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            userJourneys: uxData.userJourneys,
            prdContext: prdData,
            deviceTypes: ["desktop", "tablet", "mobile"],
            selectedLLM,
          }),
        },
      );

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || "Failed to generate wireframes");
      }

      const result = await response.json();

      // Track costs
      if (result.costTracking) {
        trackCost();
      }

      setUXData((prev) => ({
        ...prev,
        wireframes: result.wireframes,
      }));

      toast.success(`Generated ${result.wireframes.length} wireframes`);
      setActiveTab("components");
    } catch (error) {
      console.error("Error generating wireframes:", error);
      toast.error(
        error instanceof Error
          ? error.message
          : "Failed to generate wireframes",
      );
      setValidationErrors((prev) => [...prev, "Wireframe generation failed"]);
    } finally {
      setIsLoading(false);
    }
  }, [projectId, prdData, uxData.userJourneys, selectedLLM, trackCost]);

  const generateComponentSpecs = useCallback(async () => {
    if (uxData.wireframes.length === 0) {
      toast.error("Wireframes must be generated first");
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch(
        `/api/forge/${projectId}/ux/generate-component-specs`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            wireframes: uxData.wireframes,
            designSystem: uxData.designSystem,
            selectedLLM,
          }),
        },
      );

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || "Failed to generate component specs");
      }

      const result = await response.json();

      // Track costs
      if (result.costTracking) {
        trackCost();
      }

      setUXData((prev) => ({
        ...prev,
        componentSpecs: result.componentSpecs,
        designSystem: result.designSystem || prev.designSystem,
      }));

      toast.success(`Generated ${result.componentSpecs.length} component specifications`);
      setActiveTab("accessibility");
    } catch (error) {
      console.error("Error generating component specs:", error);
      toast.error(
        error instanceof Error
          ? error.message
          : "Failed to generate component specifications",
      );
      setValidationErrors((prev) => [...prev, "Component spec generation failed"]);
    } finally {
      setIsLoading(false);
    }
  }, [projectId, uxData.wireframes, uxData.designSystem, selectedLLM, trackCost]);

  const validateAccessibility = useCallback(async () => {
    if (uxData.componentSpecs.length === 0) {
      toast.error("Component specifications must be generated first");
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch(
        `/api/forge/${projectId}/ux/validate-accessibility`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            componentSpecs: uxData.componentSpecs,
            wireframes: uxData.wireframes,
            wcagLevel: "AA",
            selectedLLM,
          }),
        },
      );

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || "Failed to validate accessibility");
      }

      const result = await response.json();

      // Track costs
      if (result.costTracking) {
        trackCost();
      }

      setUXData((prev) => ({
        ...prev,
        accessibilityChecklist: result.accessibilityChecklist,
      }));

      // Update quality
      if (result.qualityAssessment) {
        setCurrentQuality(result.qualityAssessment);
        onQualityUpdate({
          stage: "ux_requirements",
          quality: result.qualityAssessment,
        });
      }

      toast.success("Accessibility validation completed");
      setActiveTab("document");
    } catch (error) {
      console.error("Error validating accessibility:", error);
      toast.error(
        error instanceof Error
          ? error.message
          : "Failed to validate accessibility",
      );
      setValidationErrors((prev) => [...prev, "Accessibility validation failed"]);
    } finally {
      setIsLoading(false);
    }
  }, [projectId, uxData.componentSpecs, uxData.wireframes, selectedLLM, trackCost, onQualityUpdate]);

  const generateUXDocument = useCallback(async () => {
    if (accessibilityCompletionRate < 80) {
      toast.error("Complete at least 80% of accessibility checklist first");
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch(
        `/api/forge/${projectId}/ux/generate-document`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            uxData,
            selectedLLM,
          }),
        },
      );

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || "Failed to generate UX document");
      }

      const result = await response.json();

      // Track costs
      if (result.costTracking) {
        trackCost();
      }

      setUXData((prev) => ({
        ...prev,
        uxDocument: result.uxDocument,
        qualityAssessment: result.qualityAssessment,
      }));

      // Update quality tracking
      if (result.qualityAssessment) {
        setCurrentQuality(result.qualityAssessment);
        onQualityUpdate({
          stage: "ux_requirements",
          quality: result.qualityAssessment,
        });
      }

      toast.success("UX document generated successfully");
    } catch (error) {
      console.error("Error generating UX document:", error);
      toast.error(
        error instanceof Error
          ? error.message
          : "Failed to generate UX document",
      );
      setValidationErrors((prev) => [...prev, "UX document generation failed"]);
    } finally {
      setIsLoading(false);
    }
  }, [projectId, uxData, accessibilityCompletionRate, selectedLLM, trackCost, onQualityUpdate]);

  const completeStage = useCallback(
    async (forceComplete: boolean = false) => {
      if (!canProceed && !forceComplete) {
        toast.error("Quality threshold not met. Expert override required.");
        return;
      }

      setIsLoading(true);
      try {
        const response = await fetch(`/api/forge/${projectId}/ux/complete`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            uxData,
            forceComplete,
          }),
        });

        if (!response.ok) {
          const error = await response.json();
          throw new Error(error.error || "Failed to complete UX stage");
        }

        const result = await response.json();

        toast.success("UX Requirements stage completed successfully");
        onStageComplete(result.stageData);
      } catch (error) {
        console.error("Error completing UX stage:", error);
        toast.error(
          error instanceof Error
            ? error.message
            : "Failed to complete UX stage",
        );
      } finally {
        setIsLoading(false);
      }
    },
    [projectId, uxData, canProceed, onStageComplete],
  );

  // Check quality and update can proceed status
  useEffect(() => {
    const meetsThreshold = overallQualityScore >= UX_QUALITY_THRESHOLD;
    const hasRequiredComponents = 
      uxData.userJourneys.length > 0 &&
      uxData.wireframes.length > 0 &&
      uxData.componentSpecs.length > 0 &&
      accessibilityCompletionRate >= 80 &&
      uxData.uxDocument !== null;
    
    setCanProceed(meetsThreshold && hasRequiredComponents);
  }, [overallQualityScore, uxData, accessibilityCompletionRate]);

  const downloadUXDocument = useCallback(() => {
    if (!uxData.uxDocument) {
      toast.error("No UX document to download");
      return;
    }

    const content = uxData.uxDocument.exportData?.content || "";
    const blob = new Blob([content], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = url;
    a.download = `UX_Requirements_${projectId}_${new Date().toISOString().split("T")[0]}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    toast.success("UX document downloaded");
  }, [uxData.uxDocument, projectId]);

  const getAccessibilityCategoryIcon = (category: string) => {
    switch (category) {
      case "perceivable":
        return Eye;
      case "operable":
        return Monitor;
      case "understandable":
        return FileText;
      case "robust":
        return CheckCircle;
      default:
        return Accessibility;
    }
  };

  const getDeviceIcon = (device: string) => {
    switch (device) {
      case "desktop":
        return Monitor;
      case "tablet":
        return Tablet;
      case "mobile":
        return Smartphone;
      default:
        return Monitor;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">UX Requirements</h2>
          <p className="text-muted-foreground">
            Define comprehensive user experience specifications and accessibility standards
          </p>
        </div>
        <div className="flex items-center gap-4">
          <LLMSelector
            selectedModel={selectedLLM}
            onModelChange={setSelectedLLM}
            task="ux_design"
          />
          <Badge variant={canProceed ? "default" : "secondary"}>
            Quality: {overallQualityScore.toFixed(1)}%
          </Badge>
        </div>
      </div>

      {/* Progress and Quality */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
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
              threshold={UX_QUALITY_THRESHOLD}
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Accessibility</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span>WCAG 2.1 AA</span>
                <span className="font-semibold">{accessibilityCompletionRate.toFixed(0)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full transition-all ${
                    accessibilityCompletionRate >= 80 ? "bg-green-600" : "bg-yellow-600"
                  }`}
                  style={{ width: `${accessibilityCompletionRate}%` }}
                />
              </div>
            </div>
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
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="journeys" className="flex items-center gap-2">
            <Users className="h-4 w-4" />
            Journeys
            {uxData.userJourneys.length > 0 && (
              <CheckCircle className="h-3 w-3 text-green-600" />
            )}
          </TabsTrigger>
          <TabsTrigger value="wireframes" className="flex items-center gap-2">
            <Layout className="h-4 w-4" />
            Wireframes
            {uxData.wireframes.length > 0 && (
              <CheckCircle className="h-3 w-3 text-green-600" />
            )}
          </TabsTrigger>
          <TabsTrigger value="components" className="flex items-center gap-2">
            <Palette className="h-4 w-4" />
            Components
            {uxData.componentSpecs.length > 0 && (
              <CheckCircle className="h-3 w-3 text-green-600" />
            )}
          </TabsTrigger>
          <TabsTrigger value="accessibility" className="flex items-center gap-2">
            <Accessibility className="h-4 w-4" />
            A11y
            {accessibilityCompletionRate >= 80 && (
              <CheckCircle className="h-3 w-3 text-green-600" />
            )}
          </TabsTrigger>
          <TabsTrigger value="document" className="flex items-center gap-2">
            <Download className="h-4 w-4" />
            Document
            {uxData.uxDocument && (
              <CheckCircle className="h-3 w-3 text-green-600" />
            )}
          </TabsTrigger>
        </TabsList>

        {/* User Journeys Tab */}
        <TabsContent value="journeys" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>User Journeys</CardTitle>
                <Button
                  onClick={generateUserJourneys}
                  disabled={isLoading || !prdData}
                  className="flex items-center gap-2"
                >
                  {isLoading ? (
                    <>
                      <Clock className="h-4 w-4 animate-spin" />
                      Generating...
                    </>
                  ) : (
                    <>
                      <Zap className="h-4 w-4" />
                      Generate Journeys
                    </>
                  )}
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {uxData.userJourneys.length > 0 && (
                <div className="space-y-4">
                  <div className="text-sm text-muted-foreground">
                    Generated {uxData.userJourneys.length} user journey(s) based on PRD user stories
                  </div>
                  <div className="space-y-3">
                    {uxData.userJourneys.map((journey) => (
                      <Card
                        key={journey.id}
                        className={`p-4 cursor-pointer transition-colors ${
                          selectedJourney === journey.id ? "border-primary" : ""
                        }`}
                      >
                        <div onClick={() =>
                          setSelectedJourney(
                            selectedJourney === journey.id ? null : journey.id
                          )
                        }>
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                              <h5 className="font-semibold">{journey.journeyName}</h5>
                              {journey.criticalPath && (
                                <Badge variant="destructive" className="text-xs">
                                  Critical
                                </Badge>
                              )}
                            </div>
                            <p className="text-sm text-muted-foreground mb-2">
                              Persona: {journey.userPersona} | Goal: {journey.goal}
                            </p>
                            <p className="text-sm text-muted-foreground mb-2">
                              {journey.scenario}
                            </p>
                            <div className="flex items-center gap-4 text-xs text-muted-foreground">
                              <span>{journey.steps.length} steps</span>
                              <span>Est. {journey.estimatedDuration}</span>
                            </div>
                          </div>
                          <ChevronRight
                            className={`h-5 w-5 transition-transform ${
                              selectedJourney === journey.id ? "rotate-90" : ""
                            }`}
                          />
                        </div>

                        {selectedJourney === journey.id && (
                          <div className="mt-4 space-y-3 border-t pt-4">
                            {journey.steps.map((step) => (
                              <div key={step.id} className="pl-4 border-l-2 border-gray-300">
                                <div className="flex items-start gap-2">
                                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-sm font-semibold">
                                    {step.stepNumber}
                                  </div>
                                  <div className="flex-1">
                                    <h6 className="font-medium text-sm mb-1">{step.name}</h6>
                                    <p className="text-xs text-muted-foreground mb-2">
                                      {step.description}
                                    </p>
                                    <div className="grid grid-cols-2 gap-2 text-xs">
                                      <div>
                                        <strong>User Actions:</strong>
                                        <ul className="list-disc list-inside">
                                          {step.userActions.map((action, i) => (
                                            <li key={i}>{action}</li>
                                          ))}
                                        </ul>
                                      </div>
                                      <div>
                                        <strong>System Responses:</strong>
                                        <ul className="list-disc list-inside">
                                          {step.systemResponses.map((response, i) => (
                                            <li key={i}>{response}</li>
                                          ))}
                                        </ul>
                                      </div>
                                    </div>
                                    {step.painPoints.length > 0 && (
                                      <div className="mt-2">
                                        <strong className="text-xs text-red-600">Pain Points:</strong>
                                        <ul className="list-disc list-inside text-xs text-red-600">
                                          {step.painPoints.map((pain, i) => (
                                            <li key={i}>{pain}</li>
                                          ))}
                                        </ul>
                                      </div>
                                    )}
                                    {step.opportunities.length > 0 && (
                                      <div className="mt-2">
                                        <strong className="text-xs text-green-600">Opportunities:</strong>
                                        <ul className="list-disc list-inside text-xs text-green-600">
                                          {step.opportunities.map((opp, i) => (
                                            <li key={i}>{opp}</li>
                                          ))}
                                        </ul>
                                      </div>
                                    )}
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                        </div>
                      </Card>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Wireframes Tab */}
        <TabsContent value="wireframes" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Wireframes</CardTitle>
                <div className="flex items-center gap-2">
                  <div className="flex items-center gap-1 mr-4">
                    {(["desktop", "tablet", "mobile"] as const).map((device) => {
                      const Icon = getDeviceIcon(device);
                      return (
                        <Button
                          key={device}
                          variant={deviceView === device ? "default" : "outline"}
                          size="sm"
                          onClick={() => setDeviceView(device)}
                        >
                          <Icon className="h-4 w-4" />
                        </Button>
                      );
                    })}
                  </div>
                  <Button
                    onClick={generateWireframes}
                    disabled={isLoading || uxData.userJourneys.length === 0}
                    className="flex items-center gap-2"
                  >
                    {isLoading ? (
                      <>
                        <Clock className="h-4 w-4 animate-spin" />
                        Generating...
                      </>
                    ) : (
                      <>
                        <Zap className="h-4 w-4" />
                        Generate Wireframes
                      </>
                    )}
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {uxData.wireframes.length > 0 && (
                <div className="space-y-4">
                  <div className="text-sm text-muted-foreground">
                    Generated {uxData.wireframes.filter(w => w.screenType === deviceView).length} wireframe(s) for {deviceView}
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {uxData.wireframes
                      .filter((wireframe) => wireframe.screenType === deviceView)
                      .map((wireframe) => (
                        <Card
                          key={wireframe.id}
                          className={`p-4 cursor-pointer transition-colors ${
                            selectedWireframe === wireframe.id ? "border-primary" : ""
                          }`}
                        >
                          <div 
                            onClick={() =>
                              setSelectedWireframe(
                                selectedWireframe === wireframe.id ? null : wireframe.id
                              )
                            }
                          >
                          <div className="aspect-video bg-gray-100 rounded border-2 border-dashed border-gray-300 flex items-center justify-center mb-3">
                            <Layout className="h-12 w-12 text-gray-400" />
                          </div>
                          <h5 className="font-semibold text-sm mb-1">
                            {wireframe.screenName}
                          </h5>
                          <p className="text-xs text-muted-foreground mb-2">
                            {wireframe.description}
                          </p>
                          <div className="flex items-center gap-2 text-xs text-muted-foreground">
                            <span>{wireframe.elements.length} elements</span>
                            <span>•</span>
                            <span>{wireframe.interactions.length} interactions</span>
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

        {/* Component Specifications Tab */}
        <TabsContent value="components" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Component Specifications</CardTitle>
                <Button
                  onClick={generateComponentSpecs}
                  disabled={isLoading || uxData.wireframes.length === 0}
                  className="flex items-center gap-2"
                >
                  {isLoading ? (
                    <>
                      <Clock className="h-4 w-4 animate-spin" />
                      Generating...
                    </>
                  ) : (
                    <>
                      <Zap className="h-4 w-4" />
                      Generate Component Specs
                    </>
                  )}
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {uxData.componentSpecs.length > 0 && (
                <div className="space-y-4">
                  <div className="text-sm text-muted-foreground">
                    Generated {uxData.componentSpecs.length} component specification(s)
                  </div>
                  <div className="space-y-3">
                    {uxData.componentSpecs.map((spec) => (
                      <Card key={spec.id} className="p-4">
                        <div className="flex items-start justify-between mb-3">
                          <div>
                            <div className="flex items-center gap-2 mb-1">
                              <h5 className="font-semibold">{spec.componentName}</h5>
                              <Badge variant="outline" className="text-xs">
                                {spec.componentType}
                              </Badge>
                            </div>
                            <p className="text-sm text-muted-foreground">
                              {spec.description}
                            </p>
                          </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                          <div>
                            <strong className="text-xs">Props:</strong>
                            <ul className="list-disc list-inside text-xs mt-1">
                              {spec.props.slice(0, 3).map((prop, i) => (
                                <li key={i}>
                                  <code className="text-xs">{prop.name}</code>: {prop.type}
                                  {prop.required && <span className="text-red-600">*</span>}
                                </li>
                              ))}
                              {spec.props.length > 3 && (
                                <li className="text-muted-foreground">
                                  +{spec.props.length - 3} more
                                </li>
                              )}
                            </ul>
                          </div>
                          <div>
                            <strong className="text-xs">Accessibility:</strong>
                            <ul className="list-disc list-inside text-xs mt-1">
                              {spec.accessibility.role && (
                                <li>Role: {spec.accessibility.role}</li>
                              )}
                              {spec.accessibility.keyboardNavigation.slice(0, 2).map((key, i) => (
                                <li key={i}>{key}</li>
                              ))}
                            </ul>
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

        {/* Accessibility Checklist Tab */}
        <TabsContent value="accessibility" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Accessibility Checklist (WCAG 2.1 AA)</CardTitle>
                <Button
                  onClick={validateAccessibility}
                  disabled={isLoading || uxData.componentSpecs.length === 0}
                  className="flex items-center gap-2"
                >
                  {isLoading ? (
                    <>
                      <Clock className="h-4 w-4 animate-spin" />
                      Validating...
                    </>
                  ) : (
                    <>
                      <Accessibility className="h-4 w-4" />
                      Validate Accessibility
                    </>
                  )}
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {uxData.accessibilityChecklist.length > 0 && (
                <div className="space-y-4">
                  {(["perceivable", "operable", "understandable", "robust"] as const).map(
                    (category) => {
                      const categoryItems = uxData.accessibilityChecklist.filter(
                        (item) => item.category === category
                      );
                      if (categoryItems.length === 0) return null;

                      const Icon = getAccessibilityCategoryIcon(category);
                      const validatedCount = categoryItems.filter((item) => item.validated).length;

                      return (
                        <div key={category} className="border rounded p-4">
                          <div className="flex items-center justify-between mb-3">
                            <div className="flex items-center gap-2">
                              <Icon className="h-5 w-5" />
                              <h5 className="font-semibold capitalize">{category}</h5>
                            </div>
                            <Badge variant={validatedCount === categoryItems.length ? "default" : "secondary"}>
                              {validatedCount}/{categoryItems.length}
                            </Badge>
                          </div>

                          <div className="space-y-2">
                            {categoryItems.map((item) => (
                              <div
                                key={item.id}
                                className={`flex items-start gap-3 p-2 rounded ${
                                  item.validated ? "bg-green-50" : "bg-gray-50"
                                }`}
                              >
                                <div className="flex-shrink-0 mt-1">
                                  {item.validated ? (
                                    <CheckCircle className="h-4 w-4 text-green-600" />
                                  ) : (
                                    <AlertTriangle className="h-4 w-4 text-yellow-600" />
                                  )}
                                </div>
                                <div className="flex-1">
                                  <div className="flex items-center gap-2 mb-1">
                                    <span className="font-medium text-sm">{item.criterion}</span>
                                    <Badge variant="outline" className="text-xs">
                                      {item.level}
                                    </Badge>
                                  </div>
                                  <p className="text-xs text-muted-foreground mb-1">
                                    {item.description}
                                  </p>
                                  <p className="text-xs">
                                    <strong>Implementation:</strong> {item.implementation}
                                  </p>
                                  {item.notes && (
                                    <p className="text-xs text-muted-foreground mt-1">
                                      <strong>Notes:</strong> {item.notes}
                                    </p>
                                  )}
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      );
                    }
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* UX Document Tab */}
        <TabsContent value="document" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>UX Requirements Document</CardTitle>
                <div className="flex items-center gap-2">
                  {uxData.uxDocument && (
                    <Button
                      variant="outline"
                      onClick={downloadUXDocument}
                      className="flex items-center gap-2"
                    >
                      <Download className="h-4 w-4" />
                      Download
                    </Button>
                  )}
                  <Button
                    onClick={generateUXDocument}
                    disabled={isLoading || accessibilityCompletionRate < 80}
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
              {uxData.uxDocument && (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div className="text-center p-3 bg-gray-50 rounded">
                      <div className="font-semibold">
                        {uxData.uxDocument.documentMetrics?.totalSections || 0}
                      </div>
                      <div className="text-muted-foreground">Sections</div>
                    </div>
                    <div className="text-center p-3 bg-gray-50 rounded">
                      <div className="font-semibold">
                        {uxData.uxDocument.documentMetrics?.diagramCount || 0}
                      </div>
                      <div className="text-muted-foreground">Diagrams</div>
                    </div>
                    <div className="text-center p-3 bg-gray-50 rounded">
                      <div className="font-semibold">
                        {uxData.componentSpecs.length}
                      </div>
                      <div className="text-muted-foreground">Components</div>
                    </div>
                    <div className="text-center p-3 bg-gray-50 rounded">
                      <div className="font-semibold">
                        {accessibilityCompletionRate.toFixed(0)}%
                      </div>
                      <div className="text-muted-foreground">A11y</div>
                    </div>
                  </div>

                  {showDocumentPreview &&
                    uxData.uxDocument.exportData?.content && (
                      <div className="border rounded p-4 max-h-96 overflow-y-auto">
                        <pre className="text-sm whitespace-pre-wrap">
                          {uxData.uxDocument.exportData.content}
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
            overallQualityScore < UX_QUALITY_THRESHOLD &&
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
                Complete UX Stage
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}
