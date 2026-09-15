import api from '../../../services/api';
import {
  CodeImprovementProposal,
  CodeImprovementCreatePayload,
  CodeImprovementList,
  ImprovementStatus,
} from '../types/codeImprovement.types';

export const codeImprovementService = {
  createProposal: async (
    projectId: string,
    payload: CodeImprovementCreatePayload
  ): Promise<CodeImprovementProposal> => {
    const response = await api.post<CodeImprovementProposal>(
      `/projects/${projectId}/codebase/improvements`,
      payload
    );
    return response.data;
  },

  getProposal: async (
    projectId: string,
    improvementId: string
  ): Promise<CodeImprovementProposal> => {
    const response = await api.get<CodeImprovementProposal>(
      `/projects/${projectId}/codebase/improvements/${improvementId}`
    );
    return response.data;
  },

  listProposals: async (
    projectId: string,
    status?: ImprovementStatus,
    findingId?: string
  ): Promise<CodeImprovementList> => {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    if (findingId) params.append('finding_id', findingId);

    const queryString = params.toString();
    const url = `/projects/${projectId}/codebase/improvements${queryString ? `?${queryString}` : ''}`;
    const response = await api.get<CodeImprovementList>(url);
    return response.data;
  },

  approveAndApply: async (
    projectId: string,
    improvementId: string
  ): Promise<CodeImprovementProposal> => {
    const response = await api.post<CodeImprovementProposal>(
      `/projects/${projectId}/codebase/improvements/${improvementId}/approve`
    );
    return response.data;
  },

  rejectProposal: async (
    projectId: string,
    improvementId: string
  ): Promise<CodeImprovementProposal> => {
    const response = await api.post<CodeImprovementProposal>(
      `/projects/${projectId}/codebase/improvements/${improvementId}/reject`
    );
    return response.data;
  },
};
