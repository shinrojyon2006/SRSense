import api from '../../../services/api';
import {
  AIRefereeResponse,
  AIReviewResponse,
  CopilotChatResponse,
  GapFinderResponse,
  ProjectMemoryResponse,
  ProjectMemoryUpdate,
  RequirementDoctorResponse,
  ReviewMode,
  ScenarioGeneratorResponse,
  TraceabilityResponse,
} from '../types';

export const copilotService = {
  chat: async (
    projectId: string,
    message: string,
    contextRequirementIds?: string[]
  ): Promise<CopilotChatResponse> => {
    const res = await api.post<CopilotChatResponse>(
      `/projects/${projectId}/copilot/chat`,
      {
        message,
        context_requirement_ids: contextRequirementIds,
      }
    );
    return res.data;
  },

  getDoctorDiagnosis: async (
    projectId: string,
    requirementId: string
  ): Promise<RequirementDoctorResponse> => {
    const res = await api.get<RequirementDoctorResponse>(
      `/projects/${projectId}/copilot/doctor/${requirementId}`
    );
    return res.data;
  },

  runReview: async (
    projectId: string,
    mode: ReviewMode
  ): Promise<AIReviewResponse> => {
    const res = await api.post<AIReviewResponse>(
      `/projects/${projectId}/copilot/review?mode=${mode}`
    );
    return res.data;
  },

  refereeSuggestion: async (
    projectId: string,
    suggestionId: string
  ): Promise<AIRefereeResponse> => {
    const res = await api.get<AIRefereeResponse>(
      `/projects/${projectId}/copilot/referee/${suggestionId}`
    );
    return res.data;
  },

  findGaps: async (projectId: string): Promise<GapFinderResponse> => {
    const res = await api.get<GapFinderResponse>(
      `/projects/${projectId}/copilot/gaps`
    );
    return res.data;
  },

  generateScenarios: async (
    projectId: string,
    requirementId: string
  ): Promise<ScenarioGeneratorResponse> => {
    const res = await api.post<ScenarioGeneratorResponse>(
      `/projects/${projectId}/copilot/scenarios/${requirementId}`
    );
    return res.data;
  },

  getTraceability: async (projectId: string): Promise<TraceabilityResponse> => {
    const res = await api.get<TraceabilityResponse>(
      `/projects/${projectId}/copilot/traceability`
    );
    return res.data;
  },

  getMemory: async (projectId: string): Promise<ProjectMemoryResponse> => {
    const res = await api.get<ProjectMemoryResponse>(
      `/projects/${projectId}/copilot/memory`
    );
    return res.data;
  },

  updateMemory: async (
    projectId: string,
    update: ProjectMemoryUpdate
  ): Promise<ProjectMemoryResponse> => {
    const res = await api.put<ProjectMemoryResponse>(
      `/projects/${projectId}/copilot/memory`,
      update
    );
    return res.data;
  },
};
