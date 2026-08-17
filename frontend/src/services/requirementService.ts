import api from './api';
import {
  Requirement,
  RequirementCreateInput,
  RequirementPriority,
  RequirementStatus,
  RequirementType,
  RequirementUpdateInput,
} from '@/types';

export const requirementService = {
  getRequirements: async (
    projectId: string,
    params?: {
      search?: string;
      type?: RequirementType;
      priority?: RequirementPriority;
      status?: RequirementStatus;
    }
  ): Promise<Requirement[]> => {
    const response = await api.get<Requirement[]>(
      `/projects/${projectId}/requirements`,
      { params }
    );
    return response.data;
  },

  getRequirement: async (
    projectId: string,
    requirementId: string
  ): Promise<Requirement> => {
    const response = await api.get<Requirement>(
      `/projects/${projectId}/requirements/${requirementId}`
    );
    return response.data;
  },

  createRequirement: async (
    projectId: string,
    data: RequirementCreateInput
  ): Promise<Requirement> => {
    const response = await api.post<Requirement>(
      `/projects/${projectId}/requirements`,
      data
    );
    return response.data;
  },

  updateRequirement: async (
    projectId: string,
    requirementId: string,
    data: RequirementUpdateInput
  ): Promise<Requirement> => {
    const response = await api.put<Requirement>(
      `/projects/${projectId}/requirements/${requirementId}`,
      data
    );
    return response.data;
  },

  deleteRequirement: async (
    projectId: string,
    requirementId: string
  ): Promise<void> => {
    await api.delete(`/projects/${projectId}/requirements/${requirementId}`);
  },
};
