/**
 * TechnicalAnalysisStage.tsx
 * 
 * React component for Task 2.6 - Technical Analysis Stage of Forge Module
 * Implements multi-LLM consensus scoring and comprehensive technical architecture evaluation
 * with 85% quality threshold and detailed feasibility assessment.
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { 
  Card, 
  CardContent, 
  CardHeader, 
  CardTitle 
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  AlertCircle, 
  CheckCircle, 
  Clock, 
  Users, 
  TrendingUp,
  Brain,
  Shield,
  Zap,
  BarChart3,
  GitBranch,
  Download,
  RefreshCw,
  AlertTriangle,
  Target,
  Settings,
  Database,
  Globe
} from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { toast } from '@/hooks/use-toast';

// Types for Technical Analysis
interface LLMModel {
  id: string;
  name: string;
  provider: string;
  strengths: string[];
  cost_per_1k_tokens: number;
  recommended_for: string[];
  weight: number;
}

interface ConsensusResult {
  consensus_level: 'strong_agreement' | 'moderate_agreement' | 'weak_agreement' | 'no_consensus';
  agreement_score: number;
  confidence_level: number;
  conflict_areas: string[];
  models_used: string[];
}

interface ArchitectureRecommendation {
  pattern: string;
  rationale: string;
  votes: number;
  total_responses: number;
  consensus_strength: number;
  resolution_method: string;
}

interface TechnologyStack {
  [category: string]: {
    name: string;
    weighted_score: number;
    vote_count: number;
    average_score: number;
    reasons: string[];
    consensus_strength: number;
  };
}

interface FeasibilityAssessment {
  overall_feasibility_score: number;
  estimated_timeline_weeks: number;
  recommended_team_size: number;
  confidence_level: number;
  key_challenges: string[];
  success_factors: string[];
  risk_mitigation: string[];
}

interface RiskAnalysis {
  overall_risk_level: number;
  risk_categories: {
    [category: string]: {
      severity: number;
      confidence: number;
      mitigation_strategies: string[];
    };
  };
  top_risks: Array<{
    category: string;
    severity: number;
    confidence: number;
    priority_score: number;
  }>;
  risk_mitigation_priority: string[];
  monitoring_recommendations: string[];
}

interface ImplementationRoadmap {
  phases: Array<{
    phase: number;
    name: string;
    duration_weeks: number;
    deliverables: string[];
    dependencies: string[];
    risk_level: string;
  }>;
  total_timeline_weeks: number;
  team_requirements: {
    recommended_size: number;
    key_roles: string[];
    skill_requirements: string[];
  };
  success_criteria: string[];
  quality_gates: Array<{
    phase: number;
    criteria: string;
  }>;
  risk_mitigation: string[];
}

interface TechnicalEvaluation {
  architecture_recommendation: ArchitectureRecommendation;
  technology_stack: TechnologyStack;
  feasibility_assessment: FeasibilityAssessment;
  risk_analysis: RiskAnalysis;
  implementation_roadmap: ImplementationRoadmap;
}

interface QualityMetrics {
  overall_score: number;
  meets_threshold: boolean;
  threshold: number;
  quality_engine_assessment: number;
}

interface TechnicalAnalysisStageProps {
  userId: string;
  sessionId: string;
  projectContext: any;
  onComplete: (data: any) => void;
  onBack: () => void;
}

const TechnicalAnalysisStage: React.FC<TechnicalAnalysisStageProps> = ({
  userId,
  sessionId,
  projectContext,
  onComplete,
  onBack
}) => {
  // State management
  const [isLoading, setIsLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState<'setup' | 'evaluation' | 'review' | 'export'>('setup');
  const [selectedModels, setSelectedModels] = useState<string[]>(['gpt-4', 'claude-3-5-sonnet', 'gemini-1.5-pro']);
  const [availableModels, setAvailableModels] = useState<LLMModel[]>([]);
  const [evaluationParams, setEvaluationParams] = useState({
    quality_threshold: 85,
    consensus_threshold: 60,
    max_retries: 2
  });
  
  // Results state
  const [technicalEvaluation, setTechnicalEvaluation] = useState<TechnicalEvaluation | null>(null);
  const [consensusResult, setConsensusResult] = useState<ConsensusResult | null>(null);
  const [qualityMetrics, setQualityMetrics] = useState<QualityMetrics | null>(null);
  const [costSummary, setCostSummary] = useState<any>(null);
  const [operationId, setOperationId] = useState<string>('');
  
  // UI state
  const [activeTab, setActiveTab] = useState('architecture');
  const [exportFormat, setExportFormat] = useState<'markdown' | 'json'>('markdown');
  const [exportSections, setExportSections] = useState<string[]>(['architecture', 'technology_stack', 'feasibility', 'risks', 'roadmap']);

  // Load available models on mount
  useEffect(() => {
    loadAvailableModels();
  }, []);

  const loadAvailableModels = async () => {
    try {
      const response = await fetch('/api/forge/technical-analysis/consensus-models');
      const data = await response.json();
      
      if (data.models) {
        setAvailableModels(data.models);
      }
    } catch (error) {
      console.error('Error loading available models:', error);
      toast({
        title: "Error",
        description: "Failed to load available models",
        variant: "destructive"
      });
    }
  };

  const handleModelSelectionChange = (modelId: string, checked: boolean) => {
    setSelectedModels(prev => {
      if (checked) {
        return [...prev, modelId];
      } else {
        return prev.filter(id => id !== modelId);
      }
    });
  };

  const estimatedCost = useMemo(() => {
    if (!availableModels.length) return 0;
    
    const selectedModelData = availableModels.filter(model => selectedModels.includes(model.id));
    const avgCost = selectedModelData.reduce((sum, model) => sum + model.cost_per_1k_tokens, 0) / selectedModelData.length;
    const estimatedTokens = 4000; // Estimated tokens per model for technical analysis
    
    return (avgCost * estimatedTokens * selectedModels.length) / 1000;
  }, [availableModels, selectedModels]);

  const canProceedToEvaluation = useMemo(() => {
    return selectedModels.length >= 2 && projectContext && 
           projectContext.idea_refinement && 
           projectContext.prd_generation && 
           projectContext.ux_requirements;
  }, [selectedModels, projectContext]);

  const handleStartEvaluation = async () => {
    if (!canProceedToEvaluation) {
      toast({
        title: "Cannot Start Evaluation",
        description: "Please select at least 2 models and ensure all previous stages are complete",
        variant: "destructive"
      });
      return;
    }

    setIsLoading(true);
    setCurrentStep('evaluation');

    try {
      const response = await fetch('/api/forge/technical-analysis/evaluate-architecture', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          user_id: userId,
          session_id: sessionId,
          project_context: projectContext,
          selected_models: selectedModels,
          evaluation_params: evaluationParams
        })
      });

      const result = await response.json();

      if (result.success) {
        setTechnicalEvaluation(result.architecture_evaluation);
        setConsensusResult(result.consensus_analysis);
        setQualityMetrics(result.quality_metrics);
        setCostSummary(result.cost_summary);
        setOperationId(result.operation_id);
        
        setCurrentStep('review');
        
        toast({
          title: "Technical Analysis Complete",
          description: `Evaluation completed with ${result.quality_metrics.overall_score.toFixed(1)}% quality score`,
          variant: result.quality_metrics.meets_threshold ? "default" : "destructive"
        });
      } else {
        throw new Error(result.error || 'Evaluation failed');
      }
    } catch (error) {
      console.error('Error in technical evaluation:', error);
      toast({
        title: "Evaluation Failed",
        description: error instanceof Error ? error.message : "An unexpected error occurred",
        variant: "destructive"
      });
      setCurrentStep('setup');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRetryEvaluation = async () => {
    // Add one more model for better consensus
    const availableForRetry = availableModels
      .filter(model => !selectedModels.includes(model.id))
      .sort((a, b) => b.weight - a.weight);
    
    if (availableForRetry.length > 0) {
      setSelectedModels(prev => [...prev, availableForRetry[0].id]);
      await handleStartEvaluation();
    } else {
      toast({
        title: "No Additional Models",
        description: "All available models have been used. Consider adjusting parameters instead.",
        variant: "destructive"
      });
    }
  };

  const handleExport = async () => {
    if (!technicalEvaluation) return;

    setIsLoading(true);

    try {
      const response = await fetch('/api/forge/technical-analysis/export-technical-analysis', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          user_id: userId,
          session_id: sessionId,
          export_format: exportFormat,
          include_sections: exportSections
        })
      });

      const result = await response.json();

      if (result.success) {
        // Create and download file
        const filename = `technical_analysis_${sessionId}.${exportFormat === 'markdown' ? 'md' : 'json'}`;
        const content = exportFormat === 'markdown' ? result.exported_content : JSON.stringify(result.exported_content, null, 2);
        
        const blob = new Blob([content], { 
          type: exportFormat === 'markdown' ? 'text/markdown' : 'application/json' 
        });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        toast({
          title: "Export Complete",
          description: `Technical analysis exported as ${filename}`,
          variant: "default"
        });
      } else {
        throw new Error(result.error || 'Export failed');
      }
    } catch (error) {
      console.error('Error exporting:', error);
      toast({
        title: "Export Failed",
        description: error instanceof Error ? error.message : "Failed to export analysis",
        variant: "destructive"
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleComplete = () => {
    if (technicalEvaluation && qualityMetrics?.meets_threshold) {
      onComplete({
        technical_evaluation: technicalEvaluation,
        consensus_result: consensusResult,
        quality_metrics: qualityMetrics,
        operation_id: operationId
      });
    } else {
      toast({
        title: "Quality Threshold Not Met",
        description: "Please retry evaluation or adjust parameters to meet the 85% quality threshold",
        variant: "destructive"
      });
    }
  };

  const renderSetupStep = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            Multi-LLM Consensus Configuration
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm font-medium mb-2 block">
              Select LLM Models for Consensus Analysis (minimum 2)
            </label>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {availableModels.map(model => (
                <div key={model.id} className="flex items-start space-x-3 p-3 border rounded-lg">
                  <Checkbox
                    id={model.id}
                    checked={selectedModels.includes(model.id)}
                    onCheckedChange={(checked) => handleModelSelectionChange(model.id, checked as boolean)}
                  />
                  <div className="flex-1 space-y-1">
                    <label htmlFor={model.id} className="text-sm font-medium cursor-pointer">
                      {model.name}
                    </label>
                    <p className="text-xs text-muted-foreground">
                      {model.provider} • ${model.cost_per_1k_tokens.toFixed(3)}/1K tokens
                    </p>
                    <div className="flex flex-wrap gap-1">
                      {model.strengths.slice(0, 2).map(strength => (
                        <Badge key={strength} variant="secondary" className="text-xs">
                          {strength}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
            
            <div className="mt-4 p-3 bg-muted rounded-lg">
              <div className="flex justify-between items-center text-sm">
                <span>Selected Models: {selectedModels.length}</span>
                <span>Estimated Cost: ${estimatedCost.toFixed(3)}</span>
              </div>
              {selectedModels.length < 2 && (
                <p className="text-xs text-destructive mt-1">
                  Select at least 2 models for consensus analysis
                </p>
              )}
            </div>
          </div>

          <div className="space-y-3">
            <label className="text-sm font-medium">Quality Threshold</label>
            <div className="flex items-center space-x-4">
              <span className="text-sm">75%</span>
              <input
                type="range"
                min="75"
                max="95"
                value={evaluationParams.quality_threshold}
                onChange={(e) => setEvaluationParams(prev => ({
                  ...prev,
                  quality_threshold: parseInt(e.target.value)
                }))}
                className="flex-1"
              />
              <span className="text-sm">95%</span>
              <Badge variant="outline">
                {evaluationParams.quality_threshold}%
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground">
              Minimum quality threshold for accepting technical analysis results
            </p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Project Context Validation</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              {projectContext?.idea_refinement ? (
                <CheckCircle className="h-4 w-4 text-green-500" />
              ) : (
                <AlertCircle className="h-4 w-4 text-red-500" />
              )}
              <span className="text-sm">Idea Refinement Stage</span>
            </div>
            <div className="flex items-center gap-2">
              {projectContext?.prd_generation ? (
                <CheckCircle className="h-4 w-4 text-green-500" />
              ) : (
                <AlertCircle className="h-4 w-4 text-red-500" />
              )}
              <span className="text-sm">PRD Generation Stage</span>
            </div>
            <div className="flex items-center gap-2">
              {projectContext?.ux_requirements ? (
                <CheckCircle className="h-4 w-4 text-green-500" />
              ) : (
                <AlertCircle className="h-4 w-4 text-red-500" />
              )}
              <span className="text-sm">UX Requirements Stage</span>
            </div>
            
            {!canProceedToEvaluation && (
              <Alert>
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>
                  Complete previous stages and select at least 2 models to proceed
                </AlertDescription>
              </Alert>
            )}
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-between">
        <Button variant="outline" onClick={onBack}>
          Back to UX Requirements
        </Button>
        <Button 
          onClick={handleStartEvaluation}
          disabled={!canProceedToEvaluation || isLoading}
          className="flex items-center gap-2"
        >
          {isLoading ? (
            <RefreshCw className="h-4 w-4 animate-spin" />
          ) : (
            <Brain className="h-4 w-4" />
          )}
          Start Technical Analysis
        </Button>
      </div>
    </div>
  );

  const renderEvaluationStep = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="h-5 w-5 animate-pulse" />
            Multi-LLM Consensus Analysis in Progress
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <RefreshCw className="h-4 w-4 animate-spin" />
              <span>Analyzing architecture across {selectedModels.length} LLM models...</span>
            </div>
            
            <div className="space-y-2">
              {selectedModels.map((modelId, index) => {
                const model = availableModels.find(m => m.id === modelId);
                return (
                  <div key={modelId} className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
                    <span className="text-sm">{model?.name || modelId}</span>
                  </div>
                );
              })}
            </div>

            <Progress value={75} className="w-full" />
            
            <p className="text-sm text-muted-foreground">
              This may take 30-60 seconds depending on the number of models selected.
              Please wait while we generate comprehensive technical recommendations.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );

  const renderReviewStep = () => {
    if (!technicalEvaluation || !consensusResult || !qualityMetrics) {
      return <div>Loading results...</div>;
    }

    return (
      <div className="space-y-6">
        {/* Quality Overview */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Target className="h-5 w-5" />
              Quality Assessment Overview
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="text-center space-y-2">
                <div className="text-2xl font-bold">
                  {qualityMetrics.overall_score.toFixed(1)}%
                </div>
                <div className="text-sm text-muted-foreground">Overall Quality Score</div>
                <Progress value={qualityMetrics.overall_score} className="w-full" />
              </div>
              
              <div className="text-center space-y-2">
                <div className="text-2xl font-bold">
                  {(consensusResult.agreement_score * 100).toFixed(1)}%
                </div>
                <div className="text-sm text-muted-foreground">Consensus Agreement</div>
                <Badge 
                  variant={consensusResult.consensus_level === 'strong_agreement' ? 'default' : 
                           consensusResult.consensus_level === 'moderate_agreement' ? 'secondary' : 'destructive'}
                  className="mt-1"
                >
                  {consensusResult.consensus_level.replace('_', ' ').toUpperCase()}
                </Badge>
              </div>
              
              <div className="text-center space-y-2">
                <div className="text-2xl font-bold">
                  {qualityMetrics.meets_threshold ? (
                    <CheckCircle className="h-8 w-8 text-green-500 mx-auto" />
                  ) : (
                    <AlertTriangle className="h-8 w-8 text-red-500 mx-auto" />
                  )}
                </div>
                <div className="text-sm text-muted-foreground">
                  {qualityMetrics.meets_threshold ? 'Threshold Met' : 'Below Threshold'}
                </div>
                <div className="text-xs">
                  Target: {qualityMetrics.threshold}%
                </div>
              </div>
            </div>

            {!qualityMetrics.meets_threshold && (
              <Alert className="mt-4">
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>
                  Quality score is below the {qualityMetrics.threshold}% threshold. 
                  Consider retrying with additional models or reviewing consensus conflicts.
                </AlertDescription>
              </Alert>
            )}

            {consensusResult.conflict_areas.length > 0 && (
              <div className="mt-4">
                <h4 className="text-sm font-medium mb-2">Areas of Conflict:</h4>
                <div className="flex flex-wrap gap-2">
                  {consensusResult.conflict_areas.map(conflict => (
                    <Badge key={conflict} variant="destructive" className="text-xs">
                      {conflict}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Detailed Results Tabs */}
        <Card>
          <CardHeader>
            <CardTitle>Technical Analysis Results</CardTitle>
          </CardHeader>
          <CardContent>
            <Tabs value={activeTab} onValueChange={setActiveTab}>
              <TabsList className="grid w-full grid-cols-5">
                <TabsTrigger value="architecture" className="flex items-center gap-1">
                  <GitBranch className="h-3 w-3" />
                  Architecture
                </TabsTrigger>
                <TabsTrigger value="technology" className="flex items-center gap-1">
                  <Database className="h-3 w-3" />
                  Technology
                </TabsTrigger>
                <TabsTrigger value="feasibility" className="flex items-center gap-1">
                  <BarChart3 className="h-3 w-3" />
                  Feasibility
                </TabsTrigger>
                <TabsTrigger value="risks" className="flex items-center gap-1">
                  <Shield className="h-3 w-3" />
                  Risks
                </TabsTrigger>
                <TabsTrigger value="roadmap" className="flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  Roadmap
                </TabsTrigger>
              </TabsList>

              <TabsContent value="architecture" className="space-y-4">
                <div>
                  <h3 className="text-lg font-semibold mb-2">Architecture Recommendation</h3>
                  <div className="space-y-3">
                    <div>
                      <Badge variant="default" className="text-sm">
                        {technicalEvaluation.architecture_recommendation.pattern}
                      </Badge>
                      <div className="mt-2 text-sm text-muted-foreground">
                        Consensus: {technicalEvaluation.architecture_recommendation.votes}/{technicalEvaluation.architecture_recommendation.total_responses} models 
                        ({(technicalEvaluation.architecture_recommendation.consensus_strength * 100).toFixed(1)}% agreement)
                      </div>
                    </div>
                    
                    <div className="p-3 bg-muted rounded-lg">
                      <h4 className="font-medium mb-1">Rationale</h4>
                      <p className="text-sm">{technicalEvaluation.architecture_recommendation.rationale}</p>
                    </div>
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="technology" className="space-y-4">
                <div>
                  <h3 className="text-lg font-semibold mb-2">Technology Stack</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {Object.entries(technicalEvaluation.technology_stack).map(([category, tech]) => (
                      <Card key={category}>
                        <CardHeader className="pb-2">
                          <CardTitle className="text-sm capitalize">{category.replace('_', ' ')}</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="space-y-2">
                            <div className="flex items-center justify-between">
                              <span className="font-medium">{tech.name}</span>
                              <Badge variant="secondary">
                                Score: {tech.weighted_score.toFixed(2)}
                              </Badge>
                            </div>
                            <div className="text-xs text-muted-foreground">
                              {tech.vote_count}/{consensusResult.models_used.length} models ({(tech.consensus_strength * 100).toFixed(1)}% consensus)
                            </div>
                            {tech.reasons.length > 0 && (
                              <div className="space-y-1">
                                <div className="text-xs font-medium">Reasons:</div>
                                <ul className="text-xs space-y-0.5">
                                  {tech.reasons.slice(0, 2).map((reason, idx) => (
                                    <li key={idx} className="text-muted-foreground">• {reason}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="feasibility" className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm flex items-center gap-1">
                        <TrendingUp className="h-4 w-4" />
                        Feasibility Score
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">
                        {technicalEvaluation.feasibility_assessment.overall_feasibility_score.toFixed(1)}/10
                      </div>
                      <Progress 
                        value={technicalEvaluation.feasibility_assessment.overall_feasibility_score * 10} 
                        className="mt-2" 
                      />
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm flex items-center gap-1">
                        <Clock className="h-4 w-4" />
                        Timeline
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">
                        {technicalEvaluation.feasibility_assessment.estimated_timeline_weeks} weeks
                      </div>
                      <div className="text-xs text-muted-foreground mt-1">
                        Estimated development time
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm flex items-center gap-1">
                        <Users className="h-4 w-4" />
                        Team Size
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">
                        {technicalEvaluation.feasibility_assessment.recommended_team_size} people
                      </div>
                      <div className="text-xs text-muted-foreground mt-1">
                        Recommended team size
                      </div>
                    </CardContent>
                  </Card>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm">Key Challenges</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <ul className="space-y-1">
                        {technicalEvaluation.feasibility_assessment.key_challenges.map((challenge, idx) => (
                          <li key={idx} className="text-sm flex items-start gap-2">
                            <AlertCircle className="h-3 w-3 text-orange-500 mt-0.5 flex-shrink-0" />
                            {challenge}
                          </li>
                        ))}
                      </ul>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm">Success Factors</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <ul className="space-y-1">
                        {technicalEvaluation.feasibility_assessment.success_factors.map((factor, idx) => (
                          <li key={idx} className="text-sm flex items-start gap-2">
                            <CheckCircle className="h-3 w-3 text-green-500 mt-0.5 flex-shrink-0" />
                            {factor}
                          </li>
                        ))}
                      </ul>
                    </CardContent>
                  </Card>
                </div>
              </TabsContent>

              <TabsContent value="risks" className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm">Overall Risk Level</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">
                        {technicalEvaluation.risk_analysis.overall_risk_level.toFixed(1)}/10
                      </div>
                      <Progress 
                        value={technicalEvaluation.risk_analysis.overall_risk_level * 10} 
                        className="mt-2" 
                      />
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm">Top Risks</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        {technicalEvaluation.risk_analysis.top_risks.slice(0, 3).map((risk, idx) => (
                          <div key={idx} className="flex items-center justify-between">
                            <span className="text-sm capitalize">{risk.category}</span>
                            <Badge 
                              variant={risk.severity > 7 ? 'destructive' : risk.severity > 5 ? 'secondary' : 'default'}
                              className="text-xs"
                            >
                              {risk.severity.toFixed(1)}
                            </Badge>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                </div>

                <div className="space-y-3">
                  {Object.entries(technicalEvaluation.risk_analysis.risk_categories).map(([category, riskData]) => (
                    <Card key={category}>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm capitalize flex items-center justify-between">
                          {category} Risk
                          <Badge 
                            variant={riskData.severity > 7 ? 'destructive' : riskData.severity > 5 ? 'secondary' : 'default'}
                          >
                            {riskData.severity.toFixed(1)}/10
                          </Badge>
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-2">
                          <Progress value={riskData.severity * 10} className="w-full" />
                          <div className="text-xs text-muted-foreground">
                            Confidence: {(riskData.confidence * 100).toFixed(0)}%
                          </div>
                          {riskData.mitigation_strategies.length > 0 && (
                            <div>
                              <div className="text-xs font-medium mb-1">Mitigation Strategies:</div>
                              <ul className="text-xs space-y-0.5">
                                {riskData.mitigation_strategies.slice(0, 2).map((strategy, idx) => (
                                  <li key={idx} className="text-muted-foreground">• {strategy}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </TabsContent>

              <TabsContent value="roadmap" className="space-y-4">
                <div>
                  <h3 className="text-lg font-semibold mb-4">Implementation Roadmap</h3>
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm">Total Timeline</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold">
                          {technicalEvaluation.implementation_roadmap.total_timeline_weeks} weeks
                        </div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm">Team Size</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold">
                          {technicalEvaluation.implementation_roadmap.team_requirements.recommended_size} people
                        </div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm">Phases</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold">
                          {technicalEvaluation.implementation_roadmap.phases.length}
                        </div>
                      </CardContent>
                    </Card>
                  </div>

                  <div className="space-y-4">
                    {technicalEvaluation.implementation_roadmap.phases.map((phase, idx) => (
                      <Card key={idx}>
                        <CardHeader className="pb-2">
                          <CardTitle className="text-sm flex items-center justify-between">
                            Phase {phase.phase}: {phase.name}
                            <Badge 
                              variant={phase.risk_level === 'High' ? 'destructive' : 
                                      phase.risk_level === 'Medium' ? 'secondary' : 'default'}
                            >
                              {phase.risk_level} Risk
                            </Badge>
                          </CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="space-y-2">
                            <div className="text-sm text-muted-foreground">
                              Duration: {phase.duration_weeks} weeks
                            </div>
                            <div>
                              <div className="text-xs font-medium mb-1">Deliverables:</div>
                              <ul className="text-xs space-y-0.5">
                                {phase.deliverables.map((deliverable, didx) => (
                                  <li key={didx} className="text-muted-foreground">• {deliverable}</li>
                                ))}
                              </ul>
                            </div>
                            {phase.dependencies.length > 0 && (
                              <div>
                                <div className="text-xs font-medium mb-1">Dependencies:</div>
                                <div className="text-xs text-muted-foreground">
                                  {phase.dependencies.join(', ')}
                                </div>
                              </div>
                            )}
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>

                  <Card className="mt-6">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm">Required Roles</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="flex flex-wrap gap-2">
                        {technicalEvaluation.implementation_roadmap.team_requirements.key_roles.map(role => (
                          <Badge key={role} variant="outline">{role}</Badge>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>

        {/* Action Buttons */}
        <div className="flex justify-between">
          <div className="flex gap-2">
            <Button 
              variant="outline" 
              onClick={handleRetryEvaluation}
              disabled={isLoading}
              className="flex items-center gap-2"
            >
              <RefreshCw className="h-4 w-4" />
              Retry with More Models
            </Button>
            
            <Button
              variant="outline"
              onClick={() => setCurrentStep('export')}
              className="flex items-center gap-2"
            >
              <Download className="h-4 w-4" />
              Export Analysis
            </Button>
          </div>
          
          <Button 
            onClick={handleComplete}
            disabled={!qualityMetrics?.meets_threshold}
            className="flex items-center gap-2"
          >
            <CheckCircle className="h-4 w-4" />
            Complete Technical Analysis
          </Button>
        </div>
      </div>
    );
  };

  const renderExportStep = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Download className="h-5 w-5" />
            Export Technical Analysis
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm font-medium mb-2 block">Export Format</label>
            <Select value={exportFormat} onValueChange={(value: 'markdown' | 'json') => setExportFormat(value)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="markdown">Markdown (.md)</SelectItem>
                <SelectItem value="json">JSON (.json)</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div>
            <label className="text-sm font-medium mb-2 block">Include Sections</label>
            <div className="space-y-2">
              {[
                { id: 'architecture', label: 'Architecture Recommendation' },
                { id: 'technology_stack', label: 'Technology Stack' },
                { id: 'feasibility', label: 'Feasibility Assessment' },
                { id: 'risks', label: 'Risk Analysis' },
                { id: 'roadmap', label: 'Implementation Roadmap' }
              ].map(section => (
                <div key={section.id} className="flex items-center space-x-2">
                  <Checkbox
                    id={section.id}
                    checked={exportSections.includes(section.id)}
                    onCheckedChange={(checked) => {
                      if (checked) {
                        setExportSections(prev => [...prev, section.id]);
                      } else {
                        setExportSections(prev => prev.filter(id => id !== section.id));
                      }
                    }}
                  />
                  <label htmlFor={section.id} className="text-sm">{section.label}</label>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-between">
        <Button variant="outline" onClick={() => setCurrentStep('review')}>
          Back to Review
        </Button>
        <Button 
          onClick={handleExport}
          disabled={isLoading || exportSections.length === 0}
          className="flex items-center gap-2"
        >
          {isLoading ? (
            <RefreshCw className="h-4 w-4 animate-spin" />
          ) : (
            <Download className="h-4 w-4" />
          )}
          Export Analysis
        </Button>
      </div>
    </div>
  );

  // Main render
  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold">Technical Analysis Stage</h1>
        <p className="text-muted-foreground">
          Multi-LLM consensus evaluation for architecture, feasibility, and implementation planning
        </p>
        
        {/* Progress indicator */}
        <div className="flex justify-center items-center gap-2 mt-4">
          {['setup', 'evaluation', 'review', 'export'].map((step, index) => (
            <React.Fragment key={step}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium ${
                step === currentStep ? 'bg-primary text-primary-foreground' :
                ['setup', 'evaluation', 'review'].indexOf(currentStep) > index ? 'bg-green-500 text-white' :
                'bg-muted text-muted-foreground'
              }`}>
                {['setup', 'evaluation', 'review'].indexOf(currentStep) > index ? (
                  <CheckCircle className="h-4 w-4" />
                ) : (
                  index + 1
                )}
              </div>
              {index < 3 && <div className="w-8 h-0.5 bg-muted" />}
            </React.Fragment>
          ))}
        </div>
      </div>

      {currentStep === 'setup' && renderSetupStep()}
      {currentStep === 'evaluation' && renderEvaluationStep()}
      {currentStep === 'review' && renderReviewStep()}
      {currentStep === 'export' && renderExportStep()}
    </div>
  );
};

export default TechnicalAnalysisStage;
