/**
 * Global TypeScript Interface & Type Definitions.
 */

export interface HealthResponse {
  status: string;
  version: string;
  database: string;
}

export type ThemeMode = 'light' | 'dark';

export interface BaseComponentProps {
  className?: string;
  children?: React.ReactNode;
}

// ── Auth & User Types ────────────────────────────────────────

export type UserRole = 'admin' | 'developer' | 'analyst';

export interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  created_at: string;
  updated_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  name: string;
  email: string;
  password: string;
  password_confirmation: string;
  role?: UserRole;
}

// ── Project Types ─────────────────────────────────────────────

export type ProjectStatus = 'draft' | 'active' | 'completed' | 'archived';

export interface Project {
  id: string;
  title: string;
  description: string;
  status: ProjectStatus;
  requirement_count: number;
  owner_id: string;
  created_at: string;
  updated_at: string;
}

export interface ProjectCreateInput {
  title: string;
  description?: string;
  status?: ProjectStatus;
}

export interface ProjectUpdateInput {
  title?: string;
  description?: string;
  status?: ProjectStatus;
  requirement_count?: number;
}

// ── Requirement Types ─────────────────────────────────────────

export type RequirementType = 'business' | 'user' | 'functional' | 'non_functional' | 'system';
export type RequirementPriority = 'low' | 'medium' | 'high' | 'critical';
export type RequirementStatus = 'draft' | 'in_review' | 'approved' | 'rejected';

export interface AIAnalysisResult {
  quality_score: number;
  ambiguity_tags: string[];
  passive_voice_instances: string[];
  missing_criteria: string[];
  summary_feedback: string;
}

export interface Requirement {
  id: string;
  title: string;
  description: string;
  type: RequirementType;
  priority: RequirementPriority;
  status: RequirementStatus;
  version: string;
  source: string;
  quality_score?: number | null;
  analysis_result?: AIAnalysisResult | null;
  source_document_id?: string | null;
  source_section?: string | null;
  source_snippet?: string | null;
  original_req_id?: string | null;
  project_id: string;
  parent_id?: string | null;
  created_at: string;
  updated_at: string;
}

export interface RequirementCreateInput {
  title: string;
  description: string;
  type?: RequirementType;
  priority?: RequirementPriority;
  status?: RequirementStatus;
  version?: string;
  source?: string;
  parent_id?: string;
}

export interface RequirementUpdateInput {
  title?: string;
  description?: string;
  type?: RequirementType;
  priority?: RequirementPriority;
  status?: RequirementStatus;
  version?: string;
  source?: string;
  quality_score?: number;
  analysis_result?: AIAnalysisResult;
  parent_id?: string;
}

// ── Knowledge Graph Types (Sprint 1.5) ────────────────────────

export type RelationshipType = 'depends_on' | 'conflicts_with' | 'derived_from' | 'verified_by';

export interface RequirementRelationship {
  id: string;
  project_id: string;
  source_id: string;
  target_id: string;
  type: RelationshipType;
  metadata?: Record<string, any> | null;
  created_at: string;
  updated_at: string;
}

export interface RelationshipCreatePayload {
  source_id: string;
  target_id: string;
  type: RelationshipType;
  metadata?: Record<string, any>;
}

export interface GraphNode {
  id: string;
  title: string;
  type: RequirementType;
  priority: RequirementPriority;
  status: RequirementStatus;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  type: RelationshipType;
}

export interface ProjectGraphResponse {
  project_id: string;
  total_nodes: number;
  total_edges: number;
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface RequirementRelationshipsResponse {
  requirement_id: string;
  outgoing: RequirementRelationship[];
  incoming: RequirementRelationship[];
  conflicts: RequirementRelationship[];
}

export interface DependencyChainResponse {
  root_requirement_id: string;
  upstream_dependencies: RequirementRelationship[];
  impacted_downstream: RequirementRelationship[];
}

export interface SuggestedRelationshipItem {
  source_id: string;
  target_id: string;
  type: RelationshipType;
  reason: string;
  confidence_score: number;
}

export interface SuggestRelationshipsResponse {
  project_id: string;
  total_suggestions: number;
  suggestions: SuggestedRelationshipItem[];
}

// ── Intelligence Types (Sprint 1.6) ───────────────────────────

export type SuggestionStatus = 'suggested' | 'accepted' | 'rejected' | 'dismissed';

export interface RequirementSuggestion {
  id: string;
  project_id: string;
  source_id: string;
  target_id: string;
  relationship_type: RelationshipType;
  status: SuggestionStatus;
  confidence_score: number;
  conflict_category?: string | null;
  evidence_explanation: string;
  suggested_resolution?: string | null;
  source_hash: string;
  target_hash: string;
  detector_version: string;
  dismissal_reason?: string | null;
  rejected_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface IntelligenceSummaryResponse {
  project_id: string;
  total_conflicts: number;
  unresolved_dependency_suggestions: number;
  orphan_requirements_count: number;
  high_confidence_issues_count: number;
  confidence_distribution: Record<string, number>;
}

export interface ScanResponse {
  project_id: string;
  scanned_requirements_count: number;
  new_suggestions_created: number;
  existing_suggestions_updated: number;
  reconsidered_suggestions_count: number;
  total_suggestions: number;
  suggestions: RequirementSuggestion[];
}

// ── Impact & Risk Simulator Types (Sprint 1.7) ─────────────────

export type ChangeType = 'cosmetic' | 'metadata' | 'behavioral';

export interface WhatIfSimulationRequest {
  requirement_id?: string;
  proposed_title: string;
  proposed_description: string;
  proposed_type?: RequirementType;
  proposed_priority?: RequirementPriority;
  proposed_status?: RequirementStatus;
  max_depth?: number;
}

export interface ImpactedRequirementItem {
  requirement_id: string;
  title: string;
  type: RequirementType;
  priority: RequirementPriority;
  depth: number;
  path: string[];
  impact_reason: string;
}

export interface WhatIfSimulationResponse {
  project_id: string;
  target_requirement_id?: string | null;
  change_type: ChangeType;
  risk_score: number;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  direct_affected_count: number;
  transitive_affected_count: number;
  direct_affected_requirements: ImpactedRequirementItem[];
  transitive_affected_requirements: ImpactedRequirementItem[];
  new_conflicts_triggered: Record<string, any>[];
  conflicts_resolved: Record<string, any>[];
  evidence_reasoning: string[];
  is_ephemeral: boolean;
}

export interface ImpactReportResponse {
  id: string;
  project_id: string;
  requirement_id: string;
  change_type: ChangeType;
  risk_score: number;
  risk_level: string;
  direct_affected_count: number;
  transitive_affected_count: number;
  conflicts_count: number;
  report_data: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface ProjectRiskSummaryResponse {
  project_id: string;
  average_project_risk_score: number;
  high_risk_requirements_count: number;
  risk_level_breakdown: Record<string, number>;
  top_high_risk_requirements: Record<string, any>[];
}

// ── Requirement-to-Verification Compiler Types (Sprint 1.8) ───

export type VerificationType =
  | 'functional'
  | 'performance'
  | 'security'
  | 'usability'
  | 'reliability'
  | 'availability'
  | 'data_validation'
  | 'boundary_constraint'
  | 'integration';

export type VerificationReadiness =
  | 'explicit_measurable'
  | 'confidently_inferred'
  | 'verification_gap';

export type VerificationStatus =
  | 'unverified'
  | 'partially_ready'
  | 'ready_for_verification'
  | 'verified';

export type TestCaseType = 'positive' | 'negative' | 'boundary' | 'performance' | 'security';

export type TestExecutionStatus = 'untested' | 'passed' | 'failed' | 'blocked';

export interface TestCase {
  id: string;
  project_id: string;
  requirement_id: string;
  verification_spec_id?: string | null;
  test_type: TestCaseType;
  title: string;
  preconditions?: string | null;
  steps: string[];
  expected_result: string;
  execution_status: TestExecutionStatus;
  created_at: string;
  updated_at: string;
}

export interface VerificationSpecificationResponse {
  id: string;
  project_id: string;
  requirement_id: string;
  metric?: string | null;
  operator?: string | null;
  threshold?: string | null;
  unit?: string | null;
  population_sample?: string | null;
  condition?: string | null;
  expected_result?: string | null;
  verification_type: VerificationType;
  readiness_status: VerificationReadiness;
  verification_status: VerificationStatus;
  confidence_score: number;
  pass_condition?: string | null;
  missing_elements: string[];
  acceptance_criteria: Record<string, any>[];
  test_cases: TestCase[];
  created_at: string;
  updated_at: string;
}

export interface ProjectVerificationSummaryResponse {
  project_id: string;
  total_requirements_count: number;
  verification_readiness_percentage: number;
  test_generation_coverage_percentage: number;
  actual_verification_coverage_percentage: number;
  status_breakdown: Record<string, number>;
  readiness_breakdown: Record<string, number>;
  unverified_requirements_gaps: Record<string, any>[];
}
