import api from '../../../services/api';
import {
  RequirementTraceabilityItem,
  TraceabilitySummary,
  TraceabilityGapsList,
  CodeTestArtifact,
  TestProposal,
  RequirementTestLink,
} from '../types/traceability.types';

export const traceabilityService = {
  getRequirementTraceability: async (
    projectId: string
  ): Promise<RequirementTraceabilityItem[]> => {
    const response = await api.get<RequirementTraceabilityItem[]>(
      `/projects/${projectId}/traceability/requirements`
    );
    return response.data;
  },

  getTraceabilitySummary: async (
    projectId: string
  ): Promise<TraceabilitySummary> => {
    const response = await api.get<TraceabilitySummary>(
      `/projects/${projectId}/traceability/summary`
    );
    return response.data;
  },

  getTraceabilityGaps: async (
    projectId: string
  ): Promise<TraceabilityGapsList> => {
    const response = await api.get<TraceabilityGapsList>(
      `/projects/${projectId}/traceability/gaps`
    );
    return response.data;
  },

  getRequirementDetail: async (
    projectId: string,
    requirementId: string
  ): Promise<RequirementTraceabilityItem> => {
    const response = await api.get<RequirementTraceabilityItem>(
      `/projects/${projectId}/traceability/requirements/${requirementId}`
    );
    return response.data;
  },

  discoverTests: async (projectId: string): Promise<CodeTestArtifact[]> => {
    const response = await api.post<CodeTestArtifact[]>(
      `/projects/${projectId}/traceability/tests/discover`
    );
    return response.data;
  },

  suggestTestProposal: async (
    projectId: string,
    requirementId: string
  ): Promise<TestProposal> => {
    const response = await api.post<TestProposal>(
      `/projects/${projectId}/traceability/tests/suggest`,
      { requirement_id: requirementId }
    );
    return response.data;
  },

  createLink: async (
    projectId: string,
    requirementId: string,
    testArtifactId: string
  ): Promise<RequirementTestLink> => {
    const response = await api.post<RequirementTestLink>(
      `/projects/${projectId}/traceability/links`,
      { requirement_id: requirementId, test_artifact_id: testArtifactId }
    );
    return response.data;
  },

  deleteLink: async (projectId: string, linkId: string): Promise<void> => {
    await api.delete(`/projects/${projectId}/traceability/links/${linkId}`);
  },
};
