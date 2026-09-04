export type CodebaseStatus = 'pending' | 'indexing' | 'indexed' | 'failed';

export interface CodeSymbol {
  id: string;
  file_id: string;
  symbol_name: string;
  symbol_type: string; // 'class' | 'interface' | 'struct' | 'function' | 'method' | 'endpoint' | 'table' | 'view' | 'procedure'
  line_start?: number | null;
  line_end?: number | null;
  signature?: string | null;
  docstring?: string | null;
  parent_symbol_name?: string | null;
  metadata_json?: Record<string, any>;
}

export interface CodeFileSummary {
  id: string;
  path: string;
  filename: string;
  language: string;
  confidence: string;
  size_bytes: number;
  line_count: number;
  symbol_count: number;
  endpoint_count: number;
}

export interface CodeFileDetail {
  id: string;
  codebase_id: string;
  project_id: string;
  path: string;
  filename: string;
  language: string;
  confidence: string;
  size_bytes: number;
  line_count: number;
  imports: string[];
  exports: string[];
  endpoints: Array<{
    http_method: string;
    path: string;
    line_number?: number;
    handler_function?: string;
  }>;
  db_interactions: Array<{
    operation_type: string;
    matched_code: string;
    line_number?: number;
  }>;
  symbols: CodeSymbol[];
}

export interface CodeDependency {
  id: string;
  source_file_id: string;
  source_file_path?: string | null;
  target_file_id?: string | null;
  target_file_path?: string | null;
  target_module: string;
  dependency_type: string;
}

export interface CodebaseSummary {
  id: string;
  project_id: string;
  repo_name: string;
  status: CodebaseStatus;
  total_files: number;
  total_lines: number;
  total_classes: number;
  total_functions: number;
  languages_summary: Record<string, number>;
  supported_files_count: number;
  unsupported_files_count: number;
  error_message?: string | null;
  created_at: string;
  updated_at: string;
}

export interface RequirementCodeLink {
  id: string;
  project_id: string;
  requirement_id: string;
  requirement_title?: string | null;
  requirement_identifier?: string | null;
  file_id: string;
  file_path?: string | null;
  file_language?: string | null;
  symbol_id?: string | null;
  symbol_name?: string | null;
  symbol_type?: string | null;
  link_type: string;
  notes?: string | null;
  created_at: string;
}

export interface RequirementCodeLinkCreateInput {
  requirement_id: string;
  file_id: string;
  symbol_id?: string | null;
  link_type?: string;
  notes?: string | null;
}
