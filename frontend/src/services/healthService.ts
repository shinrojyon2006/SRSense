import api from './api';
import { HealthResponse } from '@/types';

export const healthService = {
  getHealth: async (): Promise<HealthResponse> => {
    const response = await api.get<HealthResponse>('/health');
    return response.data;
  },
};
