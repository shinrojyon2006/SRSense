export interface CodeTestArtifact {
  id: string;
  project_id: string;
  codebase_id: string;
  file_path: string;
  test_name: string;
  test_framework?: string | null;
  test_type: string;
  line_start?: number | null;
  line_end?: number | null;
  status?: string | null;
  created_at: string;
}

export interface RequirementTestLink {
  id: string;
  project_id: string;
  requirement_id: string;
  test_artifact_id: string;
  relationship_type: 'DIRECT' | 'INFERRED' | 'AI_PROPOSED';
  confidence: number;
  evidence: Record<string, any>;
  verified: boolean;
  created_at: string;
}

export interface RequirementTraceabilityItem {
  requirement_id: string;
  original_req_id?: string | null;
  title: string;
  requirement_type: string;
  has_code: boolean;
  has_test: boolean;
  status:
    | 'FULLY_TRACED'
    | 'IMPLEMENTED_NOT_TESTED'
    | 'TESTED_NOT_LINKED'
    | 'NO_IMPLEMENTATION'
    | 'PARTIALLY_TRACED'
    | 'UNDETERMINED';
  confidence: number;
  linked_code_files: string[];
  linked_test_names: string[];
  evidence: Record<string, any>[];
  risk?: string | null;
}

export interface TraceabilitySummary {
  total_requirements: number;
  requirements_with_code: number;
  requirements_without_code: number;
  requirements_with_tests: number;
  requirements_without_tests: number;
  fully_traced_count: number;
  partially_traced_count: number;
  untraced_count: number;
  code_coverage_pct: number;
  test_coverage_pct: number;
  full_traceability_pct: number;
  traceability_score: number;
  health_status: 'HEALTHY' | 'NEEDS_ATTENTION' | 'AT_RISK' | string;
}

export interface TraceabilityGap {
  requirement_id: string;
  original_req_id?: string | null;
  title: string;
  gap_type:
    | 'NO_IMPLEMENTATION'
    | 'IMPLEMENTED_NOT_TESTED'
    | 'WEAK_TRACEABILITY'
    | 'MISSING_SLA_TEST'
    | 'MISSING_SECURITY_TEST';
  description: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  recommendation: string;
}

export interface TraceabilityGapsList {
  total_gaps: number;
  gaps: TraceabilityGap[];
}

export interface TestProposal {
  requirement_id: string;
  requirement_title: string;
  test_title: string;
  purpose: string;
  test_type: string;
  suggested_framework: string;
  preconditions: string[];
  inputs: string[];
  steps: string[];
  expected_result: string;
  validated_behavior: string;
  edge_cases: string[];
  code_snippet_proposal: string;
  confidence: number;
  status: 'PROPOSAL_GENERATED' | 'INSUFFICIENT_CONTEXT';
  missing_context_explanation?: string | null;
}
