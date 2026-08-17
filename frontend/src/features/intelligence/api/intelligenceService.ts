import api from '../../../services/api';
import {
  IntelligenceSummaryResponse,
  RequirementSuggestion,
  ScanResponse,
} from '../../../types';

export const intelligenceService = {
  runScan: async (projectId: string): Promise<ScanResponse> => {
    const response = await api.post<ScanResponse>(
      `/projects/${projectId}/intelligence/scan`
    );
    return response.data;
  },

  getSummary: async (projectId: string): Promise<IntelligenceSummaryResponse> => {
    const response = await api.get<IntelligenceSummaryResponse>(
      `/projects/${projectId}/intelligence/summary`
    );
    return response.data;
  },

  getSuggestions: async (
    projectId: string,
    params?: { status?: string; type?: string; min_confidence?: number }
  ): Promise<RequirementSuggestion[]> => {
    const response = await api.get<RequirementSuggestion[]>(
      `/projects/${projectId}/intelligence/suggestions`,
      { params }
    );
    return response.data;
  },

  acceptSuggestion: async (
    projectId: string,
    suggestionId: string
  ): Promise<RequirementSuggestion> => {
    const response = await api.post<RequirementSuggestion>(
      `/projects/${projectId}/intelligence/suggestions/${suggestionId}/accept`
    );
    return response.data;
  },

  rejectSuggestion: async (
    projectId: string,
    suggestionId: string,
    reason?: string
  ): Promise<RequirementSuggestion> => {
    const response = await api.post<RequirementSuggestion>(
      `/projects/${projectId}/intelligence/suggestions/${suggestionId}/reject`,
      { reason }
    );
    return response.data;
  },
};
