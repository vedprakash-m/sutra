/**
 * IdeaRefinementStage - Systematic idea clarification and multi-dimensional analysis
 * This component implements the first stage of the Forge workflow for transforming initial ideas
 * into structured opportunities through systematic clarification and analysis.
 */
import { useState, useEffect, useCallback } from "react";
import { forgeApi } from "@/services/api";
import {
  SparklesIcon,
  LightBulbIcon,
  UserGroupIcon,
  ChartBarIcon,
  GlobeAltIcon,
  CogIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  DocumentTextIcon,
  ArrowRightIcon,
} from "@heroicons/react/24/outline";

interface QualityAssessment {
  overallScore: number;
  dimensionScores: {
    [key: string]: number;
  };
  qualityGateStatus: "BLOCK" | "PROCEED_WITH_CAUTION" | "PROCEED_EXCELLENT";
  confidenceLevel: number;
  thresholds: {
    minimum: number;
    recommended: number;
    adjustmentsApplied: string[];
  };
}

interface ImprovementSuggestion {
  dimension: string;
  priority: "high" | "medium" | "low";
  suggestion: string;
  estimatedImpact: number;
  estimatedTime: string;
}

interface IdeaRefinementData {
  initialIdea: string;
  problemStatement: string;
  targetAudience: string;
  valueProposition: string;
  marketContext: {
    marketSize: string;
    competitors: string[];
    competitiveAdvantage: string;
  };
  technicalFeasibility: {
    complexity: "low" | "medium" | "high";
    constraints: string[];
    risks: string[];
  };
  qualityScore: number;
  qualityAssessment?: QualityAssessment;
  improvementSuggestions?: ImprovementSuggestion[];
  analysisComplete: boolean;
  lastRefinementTimestamp?: string;
}

interface IdeaRefinementStageProps {
  projectId: string;
  initialData?: Partial<IdeaRefinementData>;
  onDataUpdate: (data: IdeaRefinementData) => void;
  onStageComplete: (data: IdeaRefinementData) => void;
  selectedLLM: string;
  projectContext?: {
    complexity: string;
    project_type: string;
    user_experience: string;
  };
}

const ANALYSIS_DIMENSIONS = [
  {
    id: "problem",
    name: "Problem Definition",
    description: "Clear articulation of the problem being solved",
    icon: ExclamationTriangleIcon,
    color: "text-red-600",
  },
  {
    id: "market",
    name: "Market Analysis",
    description: "Understanding of target market and competitive landscape",
    icon: GlobeAltIcon,
    color: "text-blue-600",
  },
  {
    id: "user",
    name: "User Focus",
    description: "Clarity on target users and their needs",
    icon: UserGroupIcon,
    color: "text-green-600",
  },
  {
    id: "technical",
    name: "Technical Scope",
    description: "Understanding of technical feasibility and constraints",
    icon: CogIcon,
    color: "text-orange-600",
  },
  {
    id: "competitive",
    name: "Competitive Edge",
    description: "Differentiation and unique value proposition",
    icon: ChartBarIcon,
    color: "text-purple-600",
  },
];

export default function IdeaRefinementStage({
  projectId,
  initialData,
  onDataUpdate,
  onStageComplete,
  selectedLLM,
  projectContext = {
    complexity: "medium",
    project_type: "mvp",
    user_experience: "intermediate",
  },
}: IdeaRefinementStageProps) {
  const [data, setData] = useState<IdeaRefinementData>({
    initialIdea: initialData?.initialIdea || "",
    problemStatement: initialData?.problemStatement || "",
    targetAudience: initialData?.targetAudience || "",
    valueProposition: initialData?.valueProposition || "",
    marketContext: {
      marketSize: initialData?.marketContext?.marketSize || "",
      competitors: initialData?.marketContext?.competitors || [],
      competitiveAdvantage:
        initialData?.marketContext?.competitiveAdvantage || "",
    },
    technicalFeasibility: {
      complexity: initialData?.technicalFeasibility?.complexity || "medium",
      constraints: initialData?.technicalFeasibility?.constraints || [],
      risks: initialData?.technicalFeasibility?.risks || [],
    },
    qualityScore: initialData?.qualityScore || 0,
    analysisComplete: initialData?.analysisComplete || false,
  });

  const [currentSection, setCurrentSection] = useState<
    "input" | "analysis" | "refinement"
  >("input");
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResults, setAnalysisResults] = useState<any>(null);
  const [competitorInput, setCompetitorInput] = useState("");
  const [constraintInput, setConstraintInput] = useState("");
  const [riskInput, setRiskInput] = useState("");

  // API Integration Functions
  const analyzeIdeaQuality = useCallback(
    async (ideaData: IdeaRefinementData, context: any) => {
      try {
        return await forgeApi.analyzeIdea(projectId, ideaData, context);
      } catch (error) {
        console.error("Error analyzing idea quality:", error);
        throw error;
      }
    },
    [projectId],
  );

  const getQualityAssessment = useCallback(async () => {
    try {
      return await forgeApi.getIdeaQualityAssessment(projectId);
    } catch (error) {
      console.error("Error getting quality assessment:", error);
      throw error;
    }
  }, [projectId]);

  // Update parent component when data changes
  useEffect(() => {
    onDataUpdate(data);
  }, [data, onDataUpdate]);

  // Load quality assessment on component mount
  useEffect(() => {
    const loadQualityAssessment = async () => {
      try {
        const assessment = await getQualityAssessment();
        if (assessment) {
          setData((prev) => ({
            ...prev,
            qualityAssessment: assessment as any,
            improvementSuggestions: (assessment as any).improvementSuggestions,
          }));
          setAnalysisResults(assessment as any);
        }
      } catch (error) {
        console.log("No existing quality assessment found");
      }
    };

    if (projectId) {
      loadQualityAssessment();
    }
  }, [projectId]);

  // Auto-analyze when data changes
  useEffect(() => {
    const performAnalysis = async () => {
      if (data.initialIdea && data.problemStatement && data.targetAudience) {
        setIsAnalyzing(true);
        try {
          const analysis = await analyzeIdeaQuality(data, projectContext);
          setAnalysisResults(analysis);
          setData((prev) => ({
            ...prev,
            qualityAssessment: analysis.qualityAssessment as any,
            improvementSuggestions: analysis.qualityAssessment?.improvementSuggestions as any,
            qualityScore: analysis.qualityAssessment.overallScore,
          }));
        } catch (error) {
          console.error("Auto-analysis failed:", error);
        } finally {
          setIsAnalyzing(false);
        }
      }
    };

    const debounceTimer = setTimeout(performAnalysis, 1000);
    return () => clearTimeout(debounceTimer);
  }, [
    data.initialIdea,
    data.problemStatement,
    data.targetAudience,
    data.valueProposition,
  ]);

  const handleInitialIdeaSubmit = async () => {
    if (!data.initialIdea.trim()) return;

    setIsAnalyzing(true);
    setCurrentSection("analysis");

    try {
      // TODO: Implement AI analysis with selected LLM
      // This would call the API to perform multi-dimensional analysis
      await performMultiDimensionalAnalysis();
    } catch (error) {
      console.error("Error performing analysis:", error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const performMultiDimensionalAnalysis = async () => {
    // Mock implementation - would integrate with actual LLM API
    setTimeout(() => {
      const mockAnalysis = {
        problem: {
          score: 75,
          insights: [
            "Problem is well-defined but could be more specific",
            "Clear pain point identified",
          ],
          suggestions: [
            "Consider narrowing the scope to a specific user segment",
            "Define measurable success criteria",
          ],
        },
        market: {
          score: 60,
          insights: [
            "Market size needs validation",
            "Competitive landscape partially understood",
          ],
          suggestions: [
            "Research specific market segments",
            "Identify direct and indirect competitors",
          ],
        },
        user: {
          score: 80,
          insights: [
            "Target audience clearly identified",
            "User needs well articulated",
          ],
          suggestions: [
            "Create detailed user personas",
            "Validate assumptions with user interviews",
          ],
        },
        technical: {
          score: 70,
          insights: [
            "Technical approach seems feasible",
            "Some complexity concerns identified",
          ],
          suggestions: [
            "Break down technical requirements",
            "Identify potential technical risks early",
          ],
        },
        competitive: {
          score: 65,
          insights: [
            "Some differentiation identified",
            "Competitive advantage could be stronger",
          ],
          suggestions: [
            "Strengthen unique value proposition",
            "Identify barriers to entry",
          ],
        },
      };

      setAnalysisResults(mockAnalysis);

      // Calculate overall quality score
      const overallScore = Math.round(
        Object.values(mockAnalysis).reduce(
          (sum, dimension: any) => sum + dimension.score,
          0,
        ) / 5,
      );

      setData((prev) => ({
        ...prev,
        qualityScore: overallScore,
      }));

      setCurrentSection("refinement");
    }, 2000);
  };

  const addCompetitor = () => {
    if (
      competitorInput.trim() &&
      !data.marketContext.competitors.includes(competitorInput.trim())
    ) {
      setData((prev) => ({
        ...prev,
        marketContext: {
          ...prev.marketContext,
          competitors: [
            ...prev.marketContext.competitors,
            competitorInput.trim(),
          ],
        },
      }));
      setCompetitorInput("");
    }
  };

  const removeCompetitor = (competitor: string) => {
    setData((prev) => ({
      ...prev,
      marketContext: {
        ...prev.marketContext,
        competitors: prev.marketContext.competitors.filter(
          (c) => c !== competitor,
        ),
      },
    }));
  };

  const addConstraint = () => {
    if (
      constraintInput.trim() &&
      !data.technicalFeasibility.constraints.includes(constraintInput.trim())
    ) {
      setData((prev) => ({
        ...prev,
        technicalFeasibility: {
          ...prev.technicalFeasibility,
          constraints: [
            ...prev.technicalFeasibility.constraints,
            constraintInput.trim(),
          ],
        },
      }));
      setConstraintInput("");
    }
  };

  const addRisk = () => {
    if (
      riskInput.trim() &&
      !data.technicalFeasibility.risks.includes(riskInput.trim())
    ) {
      setData((prev) => ({
        ...prev,
        technicalFeasibility: {
          ...prev.technicalFeasibility,
          risks: [...prev.technicalFeasibility.risks, riskInput.trim()],
        },
      }));
      setRiskInput("");
    }
  };

  const handleCompleteStage = () => {
    const completedData = {
      ...data,
      analysisComplete: true,
    };
    setData(completedData);
    onStageComplete(completedData);
  };

  const getQualityColor = (score: number) => {
    if (score >= 80) return "text-green-600";
    if (score >= 60) return "text-yellow-600";
    return "text-red-600";
  };

  // Handle LLM refinement
  return (
    <div className="max-w-4xl mx-auto p-6 space-y-8">
      {/* Header */}
      <div className="text-center">
        <div className="flex items-center justify-center mb-4">
          <div className="p-3 bg-indigo-100 rounded-full">
            <SparklesIcon className="h-8 w-8 text-indigo-600" />
          </div>
        </div>
        <h1 className="text-3xl font-bold text-gray-900">Idea Refinement</h1>
        <p className="mt-2 text-lg text-gray-600">
          Transform your concept into a structured opportunity through
          systematic analysis
        </p>
        <div className="mt-4 text-sm text-gray-500">
          Using LLM:{" "}
          <span className="font-medium text-indigo-600">{selectedLLM}</span>
        </div>
      </div>

      {/* Progress Indicator */}
      <div className="flex items-center justify-center space-x-4">
        <div
          className={`flex items-center space-x-2 ${currentSection === "input" ? "text-indigo-600" : "text-gray-400"}`}
        >
          <div
            className={`w-8 h-8 rounded-full flex items-center justify-center ${currentSection === "input" ? "bg-indigo-100" : "bg-gray-100"}`}
          >
            <LightBulbIcon className="h-4 w-4" />
          </div>
          <span className="text-sm font-medium">Input</span>
        </div>
        <ArrowRightIcon className="h-4 w-4 text-gray-400" />
        <div
          className={`flex items-center space-x-2 ${currentSection === "analysis" ? "text-indigo-600" : "text-gray-400"}`}
        >
          <div
            className={`w-8 h-8 rounded-full flex items-center justify-center ${currentSection === "analysis" ? "bg-indigo-100" : "bg-gray-100"}`}
          >
            <ChartBarIcon className="h-4 w-4" />
          </div>
          <span className="text-sm font-medium">Analysis</span>
        </div>
        <ArrowRightIcon className="h-4 w-4 text-gray-400" />
        <div
          className={`flex items-center space-x-2 ${currentSection === "refinement" ? "text-indigo-600" : "text-gray-400"}`}
        >
          <div
            className={`w-8 h-8 rounded-full flex items-center justify-center ${currentSection === "refinement" ? "bg-indigo-100" : "bg-gray-100"}`}
          >
            <DocumentTextIcon className="h-4 w-4" />
          </div>
          <span className="text-sm font-medium">Refinement</span>
        </div>
      </div>

      {/* Section: Initial Idea Input */}
      {currentSection === "input" && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Initial Idea
          </h2>
          <div className="space-y-4">
            <div>
              <label
                htmlFor="initialIdea"
                className="block text-sm font-medium text-gray-700 mb-2"
              >
                Describe your project idea in detail
              </label>
              <textarea
                id="initialIdea"
                rows={6}
                value={data.initialIdea}
                onChange={(e) =>
                  setData((prev) => ({ ...prev, initialIdea: e.target.value }))
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="Describe your project idea, the problem it solves, who would use it, and why it matters..."
              />
            </div>
            <div className="flex justify-end">
              <button
                onClick={handleInitialIdeaSubmit}
                disabled={!data.initialIdea.trim()}
                className="px-6 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Start Analysis
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Section: Multi-Dimensional Analysis */}
      {currentSection === "analysis" && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="text-center">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Multi-Dimensional Analysis
            </h2>
            {isAnalyzing ? (
              <div className="py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
                <p className="text-gray-600">
                  Analyzing your idea across multiple dimensions...
                </p>
                <div className="mt-4 space-y-2">
                  {ANALYSIS_DIMENSIONS.map((dimension, index) => (
                    <div
                      key={dimension.id}
                      className={`text-sm ${index <= 2 ? "text-indigo-600" : "text-gray-400"}`}
                    >
                      {index <= 2 ? "✓" : "○"} Analyzing {dimension.name}
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {ANALYSIS_DIMENSIONS.map((dimension) => {
                  const result = analysisResults[dimension.id];
                  const Icon = dimension.icon;

                  return (
                    <div
                      key={dimension.id}
                      className="p-4 border border-gray-200 rounded-lg"
                    >
                      <div className="flex items-center mb-3">
                        <Icon className={`h-6 w-6 ${dimension.color} mr-2`} />
                        <h3 className="font-medium text-gray-900">
                          {dimension.name}
                        </h3>
                      </div>
                      {result && (
                        <>
                          <div
                            className={`text-2xl font-bold mb-2 ${getQualityColor(result.score)}`}
                          >
                            {result.score}%
                          </div>
                          <ul className="text-sm text-gray-600 space-y-1">
                            {result.insights.map(
                              (insight: string, index: number) => (
                                <li key={index}>• {insight}</li>
                              ),
                            )}
                          </ul>
                        </>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Section: Idea Refinement */}
      {currentSection === "refinement" && (
        <div className="space-y-6">
          {/* Quality Score */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-gray-900">
                Overall Quality Score
              </h2>
              <div
                className={`text-3xl font-bold ${getQualityColor(data.qualityScore)}`}
              >
                {data.qualityScore}%
              </div>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div
                className={`h-3 rounded-full transition-all duration-300 ${
                  data.qualityScore >= 80
                    ? "bg-green-500"
                    : data.qualityScore >= 60
                      ? "bg-yellow-500"
                      : "bg-red-500"
                }`}
                style={{ width: `${data.qualityScore}%` }}
              />
            </div>
          </div>

          {/* Refinement Form */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-6">
              Refine Your Idea
            </h2>

            <div className="space-y-6">
              {/* Problem Statement */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Problem Statement
                </label>
                <textarea
                  rows={3}
                  value={data.problemStatement}
                  onChange={(e) =>
                    setData((prev) => ({
                      ...prev,
                      problemStatement: e.target.value,
                    }))
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  placeholder="Clearly define the problem your solution addresses..."
                />
                {analysisResults.problem && (
                  <div className="mt-2 text-sm text-gray-600">
                    <strong>AI Suggestions:</strong>
                    <ul className="mt-1 list-disc list-inside">
                      {analysisResults.problem.suggestions.map(
                        (suggestion: string, index: number) => (
                          <li key={index}>{suggestion}</li>
                        ),
                      )}
                    </ul>
                  </div>
                )}
              </div>

              {/* Target Audience */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Target Audience
                </label>
                <textarea
                  rows={3}
                  value={data.targetAudience}
                  onChange={(e) =>
                    setData((prev) => ({
                      ...prev,
                      targetAudience: e.target.value,
                    }))
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  placeholder="Describe who will use your solution and their characteristics..."
                />
              </div>

              {/* Value Proposition */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Value Proposition
                </label>
                <textarea
                  rows={3}
                  value={data.valueProposition}
                  onChange={(e) =>
                    setData((prev) => ({
                      ...prev,
                      valueProposition: e.target.value,
                    }))
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  placeholder="Explain the unique value and benefits your solution provides..."
                />
              </div>

              {/* Market Context */}
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">
                  Market Context
                </h3>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Market Size & Opportunity
                    </label>
                    <textarea
                      rows={2}
                      value={data.marketContext.marketSize}
                      onChange={(e) =>
                        setData((prev) => ({
                          ...prev,
                          marketContext: {
                            ...prev.marketContext,
                            marketSize: e.target.value,
                          },
                        }))
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                      placeholder="Describe the market size and growth opportunity..."
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Competitors
                    </label>
                    <div className="flex space-x-2 mb-2">
                      <input
                        type="text"
                        value={competitorInput}
                        onChange={(e) => setCompetitorInput(e.target.value)}
                        onKeyPress={(e) =>
                          e.key === "Enter" &&
                          (e.preventDefault(), addCompetitor())
                        }
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                        placeholder="Add a competitor..."
                      />
                      <button
                        onClick={addCompetitor}
                        className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
                      >
                        Add
                      </button>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {data.marketContext.competitors.map(
                        (competitor, index) => (
                          <span
                            key={index}
                            className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800"
                          >
                            {competitor}
                            <button
                              onClick={() => removeCompetitor(competitor)}
                              className="ml-1 h-4 w-4 text-gray-600 hover:text-gray-800"
                            >
                              ×
                            </button>
                          </span>
                        ),
                      )}
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Competitive Advantage
                    </label>
                    <textarea
                      rows={2}
                      value={data.marketContext.competitiveAdvantage}
                      onChange={(e) =>
                        setData((prev) => ({
                          ...prev,
                          marketContext: {
                            ...prev.marketContext,
                            competitiveAdvantage: e.target.value,
                          },
                        }))
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                      placeholder="What makes your solution unique and better than alternatives..."
                    />
                  </div>
                </div>
              </div>

              {/* Technical Feasibility */}
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">
                  Technical Feasibility
                </h3>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Technical Complexity
                    </label>
                    <select
                      value={data.technicalFeasibility.complexity}
                      onChange={(e) =>
                        setData((prev) => ({
                          ...prev,
                          technicalFeasibility: {
                            ...prev.technicalFeasibility,
                            complexity: e.target.value as
                              | "low"
                              | "medium"
                              | "high",
                          },
                        }))
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                    >
                      <option value="low">Low - Simple implementation</option>
                      <option value="medium">
                        Medium - Moderate complexity
                      </option>
                      <option value="high">
                        High - Complex implementation
                      </option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Technical Constraints
                    </label>
                    <div className="flex space-x-2 mb-2">
                      <input
                        type="text"
                        value={constraintInput}
                        onChange={(e) => setConstraintInput(e.target.value)}
                        onKeyPress={(e) =>
                          e.key === "Enter" &&
                          (e.preventDefault(), addConstraint())
                        }
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                        placeholder="Add a technical constraint..."
                      />
                      <button
                        onClick={addConstraint}
                        className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
                      >
                        Add
                      </button>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {data.technicalFeasibility.constraints.map(
                        (constraint, index) => (
                          <span
                            key={index}
                            className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-orange-100 text-orange-800"
                          >
                            {constraint}
                            <button
                              onClick={() =>
                                setData((prev) => ({
                                  ...prev,
                                  technicalFeasibility: {
                                    ...prev.technicalFeasibility,
                                    constraints:
                                      prev.technicalFeasibility.constraints.filter(
                                        (_, i) => i !== index,
                                      ),
                                  },
                                }))
                              }
                              className="ml-1 h-4 w-4 text-orange-600 hover:text-orange-800"
                            >
                              ×
                            </button>
                          </span>
                        ),
                      )}
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Technical Risks
                    </label>
                    <div className="flex space-x-2 mb-2">
                      <input
                        type="text"
                        value={riskInput}
                        onChange={(e) => setRiskInput(e.target.value)}
                        onKeyPress={(e) =>
                          e.key === "Enter" && (e.preventDefault(), addRisk())
                        }
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                        placeholder="Add a technical risk..."
                      />
                      <button
                        onClick={addRisk}
                        className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
                      >
                        Add
                      </button>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {data.technicalFeasibility.risks.map((risk, index) => (
                        <span
                          key={index}
                          className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800"
                        >
                          {risk}
                          <button
                            onClick={() =>
                              setData((prev) => ({
                                ...prev,
                                technicalFeasibility: {
                                  ...prev.technicalFeasibility,
                                  risks: prev.technicalFeasibility.risks.filter(
                                    (_, i) => i !== index,
                                  ),
                                },
                              }))
                            }
                            className="ml-1 h-4 w-4 text-red-600 hover:text-red-800"
                          >
                            ×
                          </button>
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Complete Stage Button */}
            <div className="mt-8 flex justify-end">
              <button
                onClick={handleCompleteStage}
                disabled={
                  !data.problemStatement ||
                  !data.targetAudience ||
                  !data.valueProposition
                }
                className="flex items-center space-x-2 px-6 py-3 bg-green-600 text-white rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <CheckCircleIcon className="h-5 w-5" />
                <span>Complete Idea Refinement</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
