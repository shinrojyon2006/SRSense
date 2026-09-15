export type EvaluationResultClassification =
  | 'improved'
  | 'unchanged'
  | 'regressed'
  | 'partially_improved'
  | 'undetermined';

export interface CategoryScoreDelta {
  before: number;
  after: number;
  delta: number;
}

export interface FindingComparisonItem {
  id?: string | null;
  rule_id: string;
  title: string;
  description: string;
  category: string;
  severity: string;
  file_path: string;
  line_number?: number | null;
  snippet?: string | null;
}

export interface RequirementComplianceImpact {
  status: 'MEASURED' | 'UNDETERMINED';
  linked_requirement_id?: string | null;
  requirement_title?: string | null;
  before_score?: number | null;
  after_score?: number | null;
  delta: number;
  explanation: string;
}

export interface TestImpact {
  execution_status: 'NOT EXECUTED' | 'EXECUTED';
  affected_tests: Array<{ type: string; description: string }>;
  tests_run_count: number;
  passed_count: number;
  failed_count: number;
  details: string;
}

export interface CodeImprovementEvaluation {
  id: string;
  project_id: string;
  codebase_id: string;
  proposal_id: string;
  before_report_id?: string | null;
  after_report_id?: string | null;

  before_score: number;
  after_score: number;
  score_delta: number;

  before_health: string;
  after_health: string;

  before_summary: Record<string, any>;
  after_summary: Record<string, any>;
  category_scores: Record<string, CategoryScoreDelta>;

  resolved_findings: FindingComparisonItem[];
  remaining_findings: FindingComparisonItem[];
  new_findings: FindingComparisonItem[];
  unchanged_findings: FindingComparisonItem[];

  requirement_compliance_impact: RequirementComplianceImpact;
  test_impact: TestImpact;

  regression_detected: boolean;
  regression_details: string[];

  result_classification: EvaluationResultClassification;
  ai_explanation?: string | null;
  created_at: string;
}
