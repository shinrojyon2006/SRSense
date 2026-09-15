export type ImprovementStatus =
  | 'proposed'
  | 'approved'
  | 'rejected'
  | 'applied'
  | 'failed'
  | 'stale';

export interface AffectedRequirement {
  requirement_id: string;
  title: string;
  grounding_status?: string;
}

export interface TestConsideration {
  type: string;
  description: string;
}

export interface CodeImprovementProposal {
  id: string;
  project_id: string;
  codebase_id: string;
  finding_id?: string | null;
  linked_requirement_id?: string | null;
  rule_id: string;
  title: string;
  problem_summary: string;
  root_cause: string;
  recommendation: string;
  file_id?: string | null;
  file_path: string;
  current_code: string;
  proposed_code: string;
  patch_diff: string;
  affected_files: string[];
  affected_requirements: AffectedRequirement[];
  affected_tests: TestConsideration[];
  risks?: string | null;
  confidence: number;
  uncertainty?: string | null;
  status: ImprovementStatus;
  error_message?: string | null;
  created_at: string;
  reviewed_at?: string | null;
  applied_at?: string | null;
}

export interface CodeImprovementCreatePayload {
  finding_id?: string;
  file_id?: string;
  rule_id?: string;
}

export interface CodeImprovementList {
  total: number;
  items: CodeImprovementProposal[];
}
