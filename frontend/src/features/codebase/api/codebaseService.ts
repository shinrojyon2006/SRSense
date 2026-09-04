import api from '../../../services/api';
import {
  CodebaseSummary,
  CodeFileSummary,
  CodeFileDetail,
  CodeSymbol,
  CodeDependency,
  RequirementCodeLink,
  RequirementCodeLinkCreateInput,
} from '../types/codebase.types';

export const codebaseService = {
  uploadZip: async (projectId: string, file: File): Promise<CodebaseSummary> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post<CodebaseSummary>(
      `/projects/${projectId}/codebase/upload`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  },

  getSummary: async (projectId: string): Promise<CodebaseSummary | null> => {
    const response = await api.get<CodebaseSummary | null>(
      `/projects/${projectId}/codebase/`
    );
    return response.data;
  },

  listFiles: async (
    projectId: string,
    search?: string,
    language?: string
  ): Promise<CodeFileSummary[]> => {
    const params = new URLSearchParams();
    if (search) params.append('search', search);
    if (language && language !== 'all') params.append('language', language);

    const response = await api.get<CodeFileSummary[]>(
      `/projects/${projectId}/codebase/files?${params.toString()}`
    );
    return response.data;
  },

  getFileDetail: async (
    projectId: string,
    fileId: string
  ): Promise<CodeFileDetail> => {
    const response = await api.get<CodeFileDetail>(
      `/projects/${projectId}/codebase/files/${fileId}`
    );
    return response.data;
  },

  searchSymbols: async (
    projectId: string,
    query: string,
    symbolType?: string,
    language?: string
  ): Promise<CodeSymbol[]> => {
    const params = new URLSearchParams({ q: query });
    if (symbolType && symbolType !== 'all') params.append('symbol_type', symbolType);
    if (language && language !== 'all') params.append('language', language);

    const response = await api.get<CodeSymbol[]>(
      `/projects/${projectId}/codebase/symbols?${params.toString()}`
    );
    return response.data;
  },

  getDependencies: async (projectId: string): Promise<CodeDependency[]> => {
    const response = await api.get<CodeDependency[]>(
      `/projects/${projectId}/codebase/dependencies`
    );
    return response.data;
  },

  listLinks: async (
    projectId: string,
    requirementId?: string
  ): Promise<RequirementCodeLink[]> => {
    const params = new URLSearchParams();
    if (requirementId) params.append('requirement_id', requirementId);

    const response = await api.get<RequirementCodeLink[]>(
      `/projects/${projectId}/codebase/links?${params.toString()}`
    );
    return response.data;
  },

  createLink: async (
    projectId: string,
    data: RequirementCodeLinkCreateInput
  ): Promise<RequirementCodeLink> => {
    const response = await api.post<RequirementCodeLink>(
      `/projects/${projectId}/codebase/links`,
      data
    );
    return response.data;
  },

  deleteLink: async (projectId: string, linkId: string): Promise<void> => {
    await api.delete(`/projects/${projectId}/codebase/links/${linkId}`);
  },

  deleteCodebase: async (projectId: string): Promise<void> => {
    await api.delete(`/projects/${projectId}/codebase/`);
  },
};
