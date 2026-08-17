import api from '../../../services/api';
import {
  ImpactReportResponse,
  ProjectRiskSummaryResponse,
  WhatIfSimulationRequest,
  WhatIfSimulationResponse,
} from '../../../types';

export const impactService = {
  simulateWhatIf: async (
    projectId: string,
    data: WhatIfSimulationRequest
  ): Promise<WhatIfSimulationResponse> => {
    const response = await api.post<WhatIfSimulationResponse>(
      `/projects/${projectId}/impact/simulate`,
      data
    );
    return response.data;
  },

  getImpactAnalysis: async (
    projectId: string,
    requirementId: string
  ): Promise<WhatIfSimulationResponse> => {
    const response = await api.get<WhatIfSimulationResponse>(
      `/projects/${projectId}/impact/requirements/${requirementId}`
    );
    return response.data;
  },

  generateReport: async (
    projectId: string,
    requirementId: string
  ): Promise<ImpactReportResponse> => {
    const response = await api.post<ImpactReportResponse>(
      `/projects/${projectId}/impact/requirements/${requirementId}/report`
    );
    return response.data;
  },

  getSummary: async (projectId: string): Promise<ProjectRiskSummaryResponse> => {
    const response = await api.get<ProjectRiskSummaryResponse>(
      `/projects/${projectId}/impact/summary`
    );
    return response.data;
  },
};
