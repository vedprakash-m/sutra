/**
 * TypeScript interfaces for Forge module
 * Comprehensive type definitions for all 5 Forge stages
 */

// ============================================================================
// Core Forge Types
// ============================================================================

export type ForgeStage =
  | "idea_refinement"
  | "prd_generation"
  | "ux_requirements"
  | "technical_analysis"
  | "implementation_playbook";

export type ProjectStatus =
  | "draft"
  | "active"
  | "on_hold"
  | "completed"
  | "archived"
  | "cancelled";

export type ProjectPriority = "low" | "medium" | "high" | "critical";

export type QualityGateStatus =
  | "BLOCK"
  | "PROCEED_WITH_CAUTION"
  | "PROCEED_EXCELLENT";

// ============================================================================
// Stage 1: Idea Refinement Types
// ============================================================================

export interface IdeaData {
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
}

export interface RefinementRequest {
  ideaData: IdeaData;
  dimension?: string; // Specific dimension to refine
  context?: Record<string, any>;
}

export interface QualityDimensionScore {
  score: number;
  weight: number;
  feedback: string;
  suggestions: string[];
}

export interface QualityAssessment {
  overallScore: number;
  dimensionScores: Record<string, QualityDimensionScore>;
  qualityGateStatus: QualityGateStatus;
  confidenceLevel: number;
  thresholds: {
    minimum: number;
    recommended: number;
    adjustmentsApplied: string[];
  };
  improvementSuggestions: ImprovementSuggestion[];
  contextCompleteness: number;
}

export interface ImprovementSuggestion {
  dimension: string;
  priority: "high" | "medium" | "low";
  suggestion: string;
  estimatedImpact: number;
  estimatedTime: string;
  actionable: boolean;
}

export interface AnalysisResult {
  projectId: string;
  analysisTimestamp: string;
  qualityAssessment: QualityAssessment;
  contextGaps: ContextGap[];
  recommendations: string[];
  nextSteps: string[];
}

export interface ContextGap {
  stage: string;
  field: string;
  severity: "critical" | "high" | "medium" | "low";
  description: string;
  remediation: string;
  blocksProgression: boolean;
}

export interface RefinedIdea extends IdeaData {
  qualityScore: number;
  refinementHistory: RefinementHistoryEntry[];
  lastRefinementTimestamp: string;
}

export interface RefinementHistoryEntry {
  timestamp: string;
  dimension: string;
  changes: string[];
  qualityScoreBefore: number;
  qualityScoreAfter: number;
}

// ============================================================================
// Stage 2: PRD Generation Types
// ============================================================================

export interface UserStory {
  id: string;
  role: string;
  action: string;
  benefit: string;
  priority: "high" | "medium" | "low";
  acceptanceCriteria: string[];
  estimatedComplexity?: "low" | "medium" | "high";
  dependencies?: string[];
  tags?: string[];
}

export interface FunctionalRequirement {
  id: string;
  title: string;
  description: string;
  category: string;
  priority: "high" | "medium" | "low";
  acceptanceCriteria: AcceptanceCriteria[];
  relatedUserStories: string[];
  technicalNotes?: string;
}

export interface NonFunctionalRequirement {
  id: string;
  category:
    | "performance"
    | "security"
    | "scalability"
    | "usability"
    | "reliability"
    | "maintainability";
  description: string;
  metric: string;
  target: string;
  priority: "high" | "medium" | "low";
}

export interface AcceptanceCriteria {
  id: string;
  description: string;
  testable: boolean;
  verificationMethod: string;
}

export interface PRDDocument {
  projectTitle: string;
  executiveSummary: string;
  functionalRequirements: FunctionalRequirement[];
  nonFunctionalRequirements: NonFunctionalRequirement[];
  userStories: UserStory[];
  successMetrics: SuccessMetric[];
  assumptions: string[];
  constraints: string[];
  outOfScope: string[];
  qualityScore: number;
  contextIntegration: {
    ideaRefinementIntegrated: boolean;
    alignmentScore: number;
    gaps: string[];
  };
}

export interface SuccessMetric {
  name: string;
  description: string;
  target: string;
  measurementMethod: string;
  frequency: string;
}

// ============================================================================
// Stage 3: UX Requirements Types
// ============================================================================

export interface UserJourney {
  id: string;
  name: string;
  persona: string;
  steps: JourneyStep[];
  painPoints: string[];
  opportunities: string[];
  successCriteria: string[];
}

export interface JourneyStep {
  id: string;
  order: number;
  action: string;
  touchpoint: string;
  userThoughts: string;
  userEmotions: string;
  systemResponse: string;
  duration?: string;
}

export interface Wireframe {
  id: string;
  name: string;
  screenType: "page" | "modal" | "component";
  description: string;
  userStoryIds: string[];
  elements: WireframeElement[];
  interactions: Interaction[];
  responsive: {
    mobile: boolean;
    tablet: boolean;
    desktop: boolean;
  };
}

export interface WireframeElement {
  id: string;
  type:
    | "button"
    | "input"
    | "text"
    | "image"
    | "container"
    | "navigation"
    | "form";
  label: string;
  position: { x: number; y: number };
  size: { width: number; height: number };
  properties: Record<string, any>;
}

export interface Interaction {
  id: string;
  trigger: string;
  action: string;
  outcome: string;
  elementIds: string[];
}

export interface ComponentSpec {
  id: string;
  name: string;
  type: string;
  description: string;
  props: ComponentProp[];
  states: ComponentState[];
  accessibility: AccessibilitySpec;
  responsive: ResponsiveSpec;
}

export interface ComponentProp {
  name: string;
  type: string;
  required: boolean;
  default?: any;
  description: string;
}

export interface ComponentState {
  name: string;
  description: string;
  visualChanges: string[];
}

export interface AccessibilitySpec {
  ariaLabels: Record<string, string>;
  keyboardNavigation: boolean;
  screenReaderSupport: boolean;
  colorContrast: "AAA" | "AA" | "A";
  wcagLevel: "AAA" | "AA" | "A";
  issues: AccessibilityIssue[];
}

export interface AccessibilityIssue {
  severity: "critical" | "high" | "medium" | "low";
  wcagCriterion: string;
  description: string;
  remediation: string;
}

export interface ResponsiveSpec {
  breakpoints: Breakpoint[];
  layoutChanges: LayoutChange[];
}

export interface Breakpoint {
  name: string;
  minWidth: number;
  maxWidth?: number;
}

export interface LayoutChange {
  breakpoint: string;
  changes: string[];
}

export interface UXDocument {
  projectTitle: string;
  designPrinciples: string[];
  userJourneys: UserJourney[];
  wireframes: Wireframe[];
  componentSpecs: ComponentSpec[];
  designSystem: {
    colors: Record<string, string>;
    typography: Record<string, any>;
    spacing: Record<string, number>;
  };
  accessibilityReport: AccessibilityReport;
  qualityScore: number;
}

export interface AccessibilityReport {
  wcagCompliance: "AAA" | "AA" | "A" | "Non-compliant";
  overallScore: number;
  issues: AccessibilityIssue[];
  recommendations: string[];
}

// ============================================================================
// Stage 4: Technical Analysis Types
// ============================================================================

export interface ArchitectureAnalysis {
  id: string;
  llmProvider: string;
  architectureStyle: string;
  components: ArchitectureComponent[];
  dataFlow: DataFlowDescription[];
  securityConsiderations: string[];
  scalabilityAssessment: ScalabilityAssessment;
  performanceConsiderations: string[];
  riskAssessment: RiskAssessment;
  score: number;
}

export interface ArchitectureComponent {
  name: string;
  type: string;
  responsibilities: string[];
  dependencies: string[];
  technologySuggestions: string[];
}

export interface DataFlowDescription {
  from: string;
  to: string;
  dataType: string;
  frequency: string;
  protocol?: string;
}

export interface ScalabilityAssessment {
  horizontalScaling: {
    feasibility: "excellent" | "good" | "moderate" | "poor";
    considerations: string[];
  };
  verticalScaling: {
    feasibility: "excellent" | "good" | "moderate" | "poor";
    considerations: string[];
  };
  bottlenecks: Bottleneck[];
  recommendations: string[];
}

export interface Bottleneck {
  component: string;
  description: string;
  impact: "critical" | "high" | "medium" | "low";
  mitigation: string[];
}

export interface RiskAssessment {
  overallRiskLevel: "critical" | "high" | "medium" | "low";
  risks: Risk[];
  mitigationStrategy: string[];
}

export interface Risk {
  id: string;
  category:
    | "technical"
    | "security"
    | "performance"
    | "scalability"
    | "maintainability";
  description: string;
  probability: "high" | "medium" | "low";
  impact: "critical" | "high" | "medium" | "low";
  mitigation: string[];
}

export interface StackRecommendation {
  category:
    | "frontend"
    | "backend"
    | "database"
    | "infrastructure"
    | "devops"
    | "monitoring";
  recommendations: TechnologyRecommendation[];
}

export interface TechnologyRecommendation {
  name: string;
  version?: string;
  rationale: string[];
  pros: string[];
  cons: string[];
  alternatives: string[];
  learningCurve: "low" | "medium" | "high";
  communitSupport: "excellent" | "good" | "moderate" | "limited";
  cost: "free" | "freemium" | "paid";
}

export interface ConsensusResult {
  overallConsensus: number;
  architectureRecommendation: string;
  llmAnalyses: ArchitectureAnalysis[];
  consensusAreas: ConsensusArea[];
  divergenceAreas: DivergenceArea[];
  finalRecommendation: string;
  confidenceLevel: number;
}

export interface ConsensusArea {
  topic: string;
  agreement: number;
  details: string[];
}

export interface DivergenceArea {
  topic: string;
  perspectives: LLMPerspective[];
  resolution: string;
}

export interface LLMPerspective {
  provider: string;
  viewpoint: string;
  rationale: string[];
}

export interface TechSpecDocument {
  projectTitle: string;
  architectureOverview: string;
  systemArchitecture: ArchitectureAnalysis;
  technologyStack: StackRecommendation[];
  dataModel: DataModelSpec[];
  apiSpecification: APISpec[];
  deploymentArchitecture: DeploymentSpec;
  securityArchitecture: SecuritySpec;
  monitoringStrategy: MonitoringSpec;
  qualityScore: number;
}

export interface DataModelSpec {
  entityName: string;
  description: string;
  attributes: AttributeSpec[];
  relationships: RelationshipSpec[];
  indexes: IndexSpec[];
}

export interface AttributeSpec {
  name: string;
  type: string;
  required: boolean;
  unique: boolean;
  description: string;
  validation?: string[];
}

export interface RelationshipSpec {
  type: "one-to-one" | "one-to-many" | "many-to-many";
  targetEntity: string;
  description: string;
}

export interface IndexSpec {
  fields: string[];
  type: "primary" | "unique" | "composite";
  rationale: string;
}

export interface APISpec {
  endpoint: string;
  method: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  description: string;
  parameters: ParameterSpec[];
  requestBody?: any;
  responseSchema: any;
  authentication: boolean;
  rateLimit?: string;
}

export interface ParameterSpec {
  name: string;
  type: string;
  required: boolean;
  description: string;
  validation?: string[];
}

export interface DeploymentSpec {
  environment: "cloud" | "on-premise" | "hybrid";
  provider?: string;
  regions: string[];
  scalingStrategy: string;
  cicdPipeline: string[];
  infrastructureAsCode: boolean;
}

export interface SecuritySpec {
  authentication: string[];
  authorization: string[];
  dataEncryption: EncryptionSpec;
  threatMitigation: ThreatMitigationSpec[];
  complianceRequirements: string[];
}

export interface EncryptionSpec {
  atRest: boolean;
  inTransit: boolean;
  methods: string[];
}

export interface ThreatMitigationSpec {
  threat: string;
  mitigation: string[];
  priority: "critical" | "high" | "medium" | "low";
}

export interface MonitoringSpec {
  metrics: string[];
  logging: LoggingSpec;
  alerting: AlertSpec[];
  dashboards: string[];
}

export interface LoggingSpec {
  levels: string[];
  retention: string;
  aggregation: boolean;
}

export interface AlertSpec {
  name: string;
  condition: string;
  severity: "critical" | "high" | "medium" | "low";
  notification: string[];
}

// ============================================================================
// Stage 5: Implementation Playbook Types
// ============================================================================

export interface CodingPrompt {
  id: string;
  title: string;
  description: string;
  phase: "setup" | "implementation" | "testing" | "deployment";
  priority: number;
  promptText: string;
  expectedOutput: string;
  context: Record<string, any>;
  dependencies: string[];
  estimatedTime: string;
  complexity: "low" | "medium" | "high";
}

export interface DevelopmentWorkflow {
  id: string;
  name: string;
  description: string;
  phases: WorkflowPhase[];
  estimatedDuration: string;
  requiredSkills: string[];
}

export interface WorkflowPhase {
  id: string;
  name: string;
  order: number;
  tasks: WorkflowTask[];
  estimatedDuration: string;
  deliverables: string[];
}

export interface WorkflowTask {
  id: string;
  title: string;
  description: string;
  codingPromptIds: string[];
  dependencies: string[];
  estimatedTime: string;
  skills: string[];
  acceptanceCriteria: string[];
}

export interface TestingStrategy {
  unitTests: TestSpec[];
  integrationTests: TestSpec[];
  e2eTests: TestSpec[];
  performanceTests: TestSpec[];
  securityTests: TestSpec[];
  coverageTarget: number;
}

export interface TestSpec {
  id: string;
  name: string;
  description: string;
  type: "unit" | "integration" | "e2e" | "performance" | "security";
  priority: "critical" | "high" | "medium" | "low";
  testCases: TestCase[];
}

export interface TestCase {
  id: string;
  description: string;
  preconditions: string[];
  steps: string[];
  expectedResult: string;
  actualResult?: string;
  status?: "pass" | "fail" | "skip" | "pending";
}

export interface ImplementationPlaybook {
  projectTitle: string;
  overview: string;
  codingPrompts: CodingPrompt[];
  developmentWorkflow: DevelopmentWorkflow;
  testingStrategy: TestingStrategy;
  deploymentGuide: DeploymentGuide;
  bestPractices: BestPractice[];
  troubleshooting: TroubleshootingGuide[];
  qualityScore: number;
  contextIntegration: {
    allStagesIntegrated: boolean;
    completeness: number;
    gaps: string[];
  };
}

export interface DeploymentGuide {
  prerequisites: string[];
  steps: DeploymentStep[];
  rollbackProcedure: string[];
  postDeploymentValidation: string[];
  monitoring: string[];
}

export interface DeploymentStep {
  order: number;
  title: string;
  description: string;
  commands: string[];
  validation: string[];
  estimatedTime: string;
}

export interface BestPractice {
  category: string;
  title: string;
  description: string;
  rationale: string;
  examples: string[];
}

export interface TroubleshootingGuide {
  issue: string;
  symptoms: string[];
  possibleCauses: string[];
  solutions: Solution[];
}

export interface Solution {
  description: string;
  steps: string[];
  preventionTips: string[];
}

// ============================================================================
// Forge Project Types
// ============================================================================

export interface ForgeProject {
  id: string;
  name: string;
  description: string;
  currentStage: ForgeStage;
  status: ProjectStatus;
  priority: ProjectPriority;
  progressPercentage: number;
  ownerId: string;
  organizationId?: string;
  tags: string[];
  createdAt: string;
  updatedAt: string;
  forgeData: {
    ideaRefinement?: IdeaRefinementData;
    prdGeneration?: PRDGenerationData;
    uxRequirements?: UXRequirementsData;
    technicalAnalysis?: TechnicalAnalysisData;
    implementationPlaybook?: ImplementationPlaybookData;
  };
  collaborators: Collaborator[];
  artifacts: Artifact[];
  qualityTracking: QualityTracking;
}

export interface IdeaRefinementData {
  ideaData: IdeaData;
  refinedIdea?: RefinedIdea;
  qualityAssessment?: QualityAssessment;
  stageCompleted: boolean;
  completedAt?: string;
}

export interface PRDGenerationData {
  prdDocument?: PRDDocument;
  qualityAssessment?: QualityAssessment;
  stageCompleted: boolean;
  completedAt?: string;
}

export interface UXRequirementsData {
  uxDocument?: UXDocument;
  qualityAssessment?: QualityAssessment;
  stageCompleted: boolean;
  completedAt?: string;
}

export interface TechnicalAnalysisData {
  techSpecDocument?: TechSpecDocument;
  consensusResult?: ConsensusResult;
  qualityAssessment?: QualityAssessment;
  stageCompleted: boolean;
  completedAt?: string;
}

export interface ImplementationPlaybookData {
  playbook?: ImplementationPlaybook;
  qualityAssessment?: QualityAssessment;
  stageCompleted: boolean;
  completedAt?: string;
}

export interface Collaborator {
  userId: string;
  email: string;
  role: "owner" | "editor" | "viewer";
  addedAt: string;
}

export interface Artifact {
  id: string;
  name: string;
  type: "document" | "diagram" | "code" | "specification";
  stage: ForgeStage;
  filePath?: string;
  content?: string;
  createdAt: string;
  createdBy: string;
}

export interface QualityTracking {
  overallQuality: number;
  stageQualities: Record<ForgeStage, number>;
  qualityTrend: QualityTrendPoint[];
  issues: QualityIssue[];
}

export interface QualityTrendPoint {
  timestamp: string;
  stage: ForgeStage;
  score: number;
}

export interface QualityIssue {
  id: string;
  stage: ForgeStage;
  severity: "critical" | "high" | "medium" | "low";
  description: string;
  resolved: boolean;
  resolvedAt?: string;
}

// ============================================================================
// API Request/Response Types
// ============================================================================

export interface StageCompletionRequest {
  projectId: string;
  stage: ForgeStage;
  data: any;
}

export interface StageCompletionResponse {
  success: boolean;
  message: string;
  qualityAssessment: QualityAssessment;
  canProgress: boolean;
  nextStage?: ForgeStage;
}

export type ExportFormat = "json" | "markdown" | "pdf" | "zip";

export interface ExportRequest {
  projectId: string;
  format: ExportFormat;
  stages?: ForgeStage[];
  includeArtifacts?: boolean;
}

export interface ExportResponse {
  success: boolean;
  downloadUrl?: string;
  blob?: Blob;
  filename: string;
  expiresAt?: string;
}
