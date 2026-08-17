import api from '../../../services/api';
import { Document, DocumentTextResponse } from '../types/document.types';

export const documentService = {
  uploadDocument: async (projectId: string, file: File): Promise<Document> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post<Document>(
      `/projects/${projectId}/documents/upload`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  },

  getDocuments: async (projectId: string): Promise<Document[]> => {
    const response = await api.get<Document[]>(`/projects/${projectId}/documents`);
    return response.data;
  },

  getDocument: async (projectId: string, documentId: string): Promise<Document> => {
    const response = await api.get<Document>(`/projects/${projectId}/documents/${documentId}`);
    return response.data;
  },

  getDocumentText: async (projectId: string, documentId: string): Promise<DocumentTextResponse> => {
    const response = await api.get<DocumentTextResponse>(
      `/projects/${projectId}/documents/${documentId}/text`
    );
    return response.data;
  },

  deleteDocument: async (projectId: string, documentId: string): Promise<void> => {
    await api.delete(`/projects/${projectId}/documents/${documentId}`);
  },
};
