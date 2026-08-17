import api from '../../../services/api';
import {
  BatchAcceptRequest,
  BatchAcceptResponse,
  ExtractionResponse,
} from '../types/document.types';

export const extractionService = {
  extractCandidates: async (
    projectId: string,
    documentId: string
  ): Promise<ExtractionResponse> => {
    const response = await api.post<ExtractionResponse>(
      `/projects/${projectId}/documents/${documentId}/extract-candidates`
    );
    return response.data;
  },

  batchAcceptCandidates: async (
    projectId: string,
    payload: BatchAcceptRequest
  ): Promise<BatchAcceptResponse> => {
    const response = await api.post<BatchAcceptResponse>(
      `/projects/${projectId}/extraction/batch-accept`,
      payload
    );
    return response.data;
  },
};
