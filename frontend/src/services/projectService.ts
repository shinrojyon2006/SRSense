import api from './api';
import { Project, ProjectCreateInput, ProjectUpdateInput } from '@/types';

export const projectService = {
  getProjects: async (search?: string): Promise<Project[]> => {
    const params = search ? { search } : {};
    const response = await api.get<Project[]>('/projects', { params });
    return response.data;
  },

  getProject: async (id: string): Promise<Project> => {
    const response = await api.get<Project>(`/projects/${id}`);
    return response.data;
  },

  createProject: async (data: ProjectCreateInput): Promise<Project> => {
    const response = await api.post<Project>('/projects', data);
    return response.data;
  },

  updateProject: async (id: string, data: ProjectUpdateInput): Promise<Project> => {
    const response = await api.put<Project>(`/projects/${id}`, data);
    return response.data;
  },

  deleteProject: async (id: string): Promise<void> => {
    await api.delete(`/projects/${id}`);
  },
};
