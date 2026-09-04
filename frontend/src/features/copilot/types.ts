export type ConfidenceLevel = 'EXPLICIT' | 'INFERRED' | 'UNCERTAIN';

export type ReviewMode = 'qa' | 'security' | 'performance' | 'product' | 'architecture';

export interface CopilotChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  confidence?: ConfidenceLevel;
  evidence?: string[];
  referencedIds?: string[];
  caveats?: string;
  timestamp: Date;
}

export interface CopilotChatResponse {
  answer: string;
  confidence: ConfidenceLevel;
  evidence: string[];
  referenced_requirement_ids: string[];
  caveats?: string;
}

export interface DoctorIssue {
  severity: 'critical' | 'warning' | 'info';
  category: string;
  description: string;
  suggestion: string;
}

export interface RequirementDoctorResponse {
  requirement_id: string;
  requirement_title: string;
  overall_health: 'healthy' | 'needs_attention' | 'critical';
  health_score: number;
  issues: DoctorIssue[];
  improvement_hint?: string;
  confidence: ConfidenceLevel;
}

export interface ReviewFinding {
  requirement_id?: string;
  requirement_title?: string;
  severity: 'critical' | 'warning' | 'info';
  finding: string;
  recommendation: string;
  confidence: ConfidenceLevel;
}

export interface AIReviewResponse {
  project_id: string;
  mode: ReviewMode;
  total_requirements_reviewed: number;
  findings: ReviewFinding[];
  summary: string;
  timestamp: string;
}

export interface RefereeVote {
  choice: 'accept' | 'reject' | 'defer' | 'modify';
  reasoning: string;
  confidence: ConfidenceLevel;
  risk_if_accepted?: string;
  risk_if_rejected?: string;
}

export interface AIRefereeResponse {
  suggestion_id: string;
  referee_vote: RefereeVote;
  alternative_suggestion?: string;
}

export interface GapSuggestion {
  gap_type: string;
  title: string;
  description: string;
  rationale: string;
  confidence: ConfidenceLevel;
  related_requirement_ids: string[];
}

export interface GapFinderResponse {
  project_id: string;
  total_gaps_found: number;
  gaps: GapSuggestion[];
  coverage_score: number;
  summary: string;
}

export interface TestScenario {
  scenario_type: 'normal' | 'failure' | 'boundary' | 'edge';
  title: string;
  given: string;
  when: string;
  then: string;
  priority: 'high' | 'medium' | 'low';
  confidence: ConfidenceLevel;
}

export interface ScenarioGeneratorResponse {
  requirement_id: string;
  requirement_title: string;
  scenarios: TestScenario[];
  total_scenarios: number;
  status?: 'success' | 'insufficient_information';
  insufficient_info_reason?: string | null;
  missing_information?: string[] | null;
  clarification_questions?: string[] | null;
}

export interface TraceabilityLink {
  from_requirement_id: string;
  from_title: string;
  to_requirement_id: string;
  to_title: string;
  relationship_type: string;
  explanation: string;
  confidence: ConfidenceLevel;
}

export interface TraceabilityResponse {
  project_id: string;
  total_links: number;
  links: TraceabilityLink[];
  orphaned_requirement_ids: string[];
  coverage_percentage: number;
  summary: string;
}

export interface ProjectMemoryResponse {
  project_id: string;
  terminology: Record<string, string>;
  personas: Array<{ role: string; description: string }>;
  domain_context?: string;
  updated_at?: string;
}

export interface ProjectMemoryUpdate {
  terminology?: Record<string, string>;
  personas?: Array<{ role: string; description: string }>;
  domain_context?: string;
}
