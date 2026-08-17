import api from '../../../services/api';
import {
  DependencyChainResponse,
  ProjectGraphResponse,
  RelationshipCreatePayload,
  RequirementRelationship,
  RequirementRelationshipsResponse,
  SuggestRelationshipsResponse,
} from '../../../types';

export const graphService = {
  createRelationship: async (
    projectId: string,
    payload: RelationshipCreatePayload
  ): Promise<RequirementRelationship> => {
    const response = await api.post<RequirementRelationship>(
      `/projects/${projectId}/graph/relationships`,
      payload
    );
    return response.data;
  },

  getProjectGraph: async (projectId: string): Promise<ProjectGraphResponse> => {
    const response = await api.get<ProjectGraphResponse>(
      `/projects/${projectId}/graph/relationships`
    );
    return response.data;
  },

  getRequirementRelationships: async (
    projectId: string,
    requirementId: string
  ): Promise<RequirementRelationshipsResponse> => {
    const response = await api.get<RequirementRelationshipsResponse>(
      `/projects/${projectId}/graph/requirements/${requirementId}`
    );
    return response.data;
  },

  deleteRelationship: async (projectId: string, relationshipId: string): Promise<void> => {
    await api.delete(`/projects/${projectId}/graph/relationships/${relationshipId}`);
  },

  queryDependencies: async (
    projectId: string,
    requirementId: string
  ): Promise<DependencyChainResponse> => {
    const response = await api.get<DependencyChainResponse>(
      `/projects/${projectId}/graph/requirements/${requirementId}/dependencies`
    );
    return response.data;
  },

  queryConflicts: async (
    projectId: string,
    requirementId: string
  ): Promise<RequirementRelationship[]> => {
    const response = await api.get<RequirementRelationship[]>(
      `/projects/${projectId}/graph/requirements/${requirementId}/conflicts`
    );
    return response.data;
  },

  suggestRelationships: async (projectId: string): Promise<SuggestRelationshipsResponse> => {
    const response = await api.post<SuggestRelationshipsResponse>(
      `/projects/${projectId}/graph/suggest-relationships`
    );
    return response.data;
  },
};
