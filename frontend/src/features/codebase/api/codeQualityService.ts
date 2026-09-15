import api from '../../../services/api';
import {
  CodeReviewReport,
  CodeReviewFindingsList,
  CodeReviewFindingsQueryParams,
} from '../types/codeQuality.types';

export const codeQualityService = {
  triggerReview: async (projectId: string): Promise<CodeReviewReport> => {
    const response = await api.post<CodeReviewReport>(
      `/projects/${projectId}/codebase/review`
    );
    return response.data;
  },

  getLatestReview: async (projectId: string): Promise<CodeReviewReport | null> => {
    const response = await api.get<CodeReviewReport | null>(
      `/projects/${projectId}/codebase/review`
    );
    return response.data;
  },

  getFindings: async (
    projectId: string,
    params?: CodeReviewFindingsQueryParams
  ): Promise<CodeReviewFindingsList> => {
    const query = new URLSearchParams();
    if (params?.severity) query.append('severity', params.severity);
    if (params?.category) query.append('category', params.category);
    if (params?.file_path) query.append('file_path', params.file_path);
    if (params?.search) query.append('search', params.search);
    if (params?.sort_by) query.append('sort_by', params.sort_by);
    if (params?.sort_dir) query.append('sort_dir', params.sort_dir);
    if (params?.page) query.append('page', params.page.toString());
    if (params?.page_size) query.append('page_size', params.page_size.toString());

    const queryString = query.toString();
    const url = `/projects/${projectId}/codebase/findings${queryString ? `?${queryString}` : ''}`;
    const response = await api.get<CodeReviewFindingsList>(url);
    return response.data;
  },
};
