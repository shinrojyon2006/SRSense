export type CodeHealthStatus = 'healthy' | 'needs_attention' | 'at_risk';

export type FindingCategory =
  | 'security'
  | 'performance'
  | 'maintainability'
  | 'compliance'
  | 'quality';

export type FindingSeverity = 'critical' | 'warning' | 'info';

export interface CodeReviewFinding {
  id: string;
  report_id: string;
  file_id?: string | null;
  file_path: string;
  line_number?: number | null;
  category: FindingCategory;
  severity: FindingSeverity;
  title: string;
  description: string;
  rule_id: string;
  suggestion: string;
  ai_explanation?: string | null;
  snippet?: string | null;
  linked_requirement_id?: string | null;
  created_at: string;
}

export interface CodeReviewReport {
  id: string;
  project_id: string;
  codebase_id: string;
  overall_score: number;
  health_status: CodeHealthStatus;
  summary: string;
  total_files_analyzed: number;
  total_issues_count: number;
  critical_count: number;
  warning_count: number;
  info_count: number;
  category_counts: Record<string, number>;
  findings_preview?: CodeReviewFinding[];
  created_at: string;
}

export interface CodeReviewFindingsList {
  total_findings: number;
  report_id: string;
  page: number;
  page_size: number;
  findings: CodeReviewFinding[];
}

export interface CodeReviewFindingsQueryParams {
  severity?: FindingSeverity;
  category?: FindingCategory;
  file_path?: string;
  search?: string;
  sort_by?: string;
  sort_dir?: 'asc' | 'desc';
  page?: number;
  page_size?: number;
}
