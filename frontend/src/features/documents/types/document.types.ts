import { RequirementPriority, RequirementStatus, RequirementType } from '@/types';

export type DocumentFileType = 'pdf' | 'docx' | 'txt';
export type DocumentStatus = 'uploaded' | 'extracting' | 'extracted' | 'failed';

export interface Document {
  id: string;
  project_id: string;
  filename: string;
  file_type: DocumentFileType;
  file_size: number;
  status: DocumentStatus;
  error_message?: string;
  doc_metadata?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface TextSegment {
  location_label: string;
  text: string;
}

export interface DocumentTextResponse {
  document_id: string;
  filename: string;
  raw_text: string;
  total_segments: number;
  word_count: number;
  segments: TextSegment[];
  metadata: Record<string, any>;
}

export interface CandidateRequirement {
  candidate_id: string;
  original_req_id?: string;
  title: string;
  description: string;
  type: RequirementType;
  priority: RequirementPriority;
  source_document_id: string;
  source_section: string;
  source_snippet: string;
  location_label?: string;
  is_duplicate: boolean;
  duplicate_of_id?: string;
  similarity_score: number;

  // Client UI state
  accepted?: boolean;
  rejected?: boolean;
  selected?: boolean;
}

export interface ExtractionResponse {
  document_id: string;
  total_candidates: number;
  candidates: CandidateRequirement[];
}

export interface BatchAcceptItem {
  title: string;
  description: string;
  type: RequirementType;
  priority: RequirementPriority;
  status: RequirementStatus;
  source_document_id?: string;
  source_section?: string;
  source_snippet?: string;
  original_req_id?: string;
}

export interface BatchAcceptRequest {
  items: BatchAcceptItem[];
}

export interface BatchAcceptResponse {
  accepted_count: number;
  created_requirements: any[];
}
