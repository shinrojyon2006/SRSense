import api from './api';
import { Requirement } from '@/types';

export interface AIAnalysisResultPayload {
  quality_score: number;
  ambiguity_tags: string[];
  passive_voice_instances: string[];
  missing_criteria: string[];
  summary_feedback: string;
}

export interface AIImprovementResultPayload {
  improved_title: string;
  improved_description: string;
  ears_template_used: string;
  explanation: string;
}

export interface SRSExportPayload {
  filename?: string;
  content?: string;
  srs_title?: string;
  total_requirements?: number;
  requirements?: any[];
}

export const aiService = {
  analyzeRequirement: async (
    projectId: string,
    requirementId: string
  ): Promise<Requirement> => {
    const response = await api.post<Requirement>(
      `/projects/${projectId}/requirements/${requirementId}/analyze`
    );
    return response.data;
  },

  improveRequirement: async (
    projectId: string,
    requirementId: string
  ): Promise<AIImprovementResultPayload> => {
    const response = await api.post<AIImprovementResultPayload>(
      `/projects/${projectId}/requirements/${requirementId}/improve`
    );
    return response.data;
  },

  analyzeDraft: async (
    title: string,
    description: string,
    type: string = 'functional'
  ): Promise<AIAnalysisResultPayload> => {
    const response = await api.post<AIAnalysisResultPayload>(
      '/ai/analyze-draft',
      { title, description, type }
    );
    return response.data;
  },

  exportSrsDocument: async (
    projectId: string,
    format: 'markdown' | 'json' = 'markdown'
  ): Promise<SRSExportPayload> => {
    const response = await api.get<SRSExportPayload>(
      `/projects/${projectId}/export`,
      { params: { format } }
    );
    return response.data;
  },
};
