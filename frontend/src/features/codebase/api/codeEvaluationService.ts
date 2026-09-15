import api from '../../../services/api';
import { CodeImprovementEvaluation } from '../types/codeEvaluation.types';

export const codeEvaluationService = {
  evaluateImprovement: async (
    projectId: string,
    proposalId: string
  ): Promise<CodeImprovementEvaluation> => {
    const response = await api.post<CodeImprovementEvaluation>(
      `/projects/${projectId}/codebase/improvements/${proposalId}/evaluate`
    );
    return response.data;
  },

  getEvaluation: async (
    projectId: string,
    proposalId: string
  ): Promise<CodeImprovementEvaluation> => {
    const response = await api.get<CodeImprovementEvaluation>(
      `/projects/${projectId}/codebase/improvements/${proposalId}/evaluation`
    );
    return response.data;
  },
};
