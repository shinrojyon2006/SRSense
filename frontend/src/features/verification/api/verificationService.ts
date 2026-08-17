import api from '../../../services/api';
import {
  ProjectVerificationSummaryResponse,
  TestCase,
  TestExecutionStatus,
  VerificationSpecificationResponse,
} from '../../../types';

export const verificationService = {
  compileRequirement: async (
    projectId: string,
    requirementId: string
  ): Promise<VerificationSpecificationResponse> => {
    const response = await api.post<VerificationSpecificationResponse>(
      `/projects/${projectId}/verification/requirements/${requirementId}/compile`
    );
    return response.data;
  },

  getVerification: async (
    projectId: string,
    requirementId: string
  ): Promise<VerificationSpecificationResponse> => {
    const response = await api.get<VerificationSpecificationResponse>(
      `/projects/${projectId}/verification/requirements/${requirementId}`
    );
    return response.data;
  },

  updateTestCaseStatus: async (
    projectId: string,
    testCaseId: string,
    execution_status: TestExecutionStatus
  ): Promise<TestCase> => {
    const response = await api.patch<TestCase>(
      `/projects/${projectId}/verification/test-cases/${testCaseId}`,
      { execution_status }
    );
    return response.data;
  },

  getSummary: async (
    projectId: string
  ): Promise<ProjectVerificationSummaryResponse> => {
    const response = await api.get<ProjectVerificationSummaryResponse>(
      `/projects/${projectId}/verification/summary`
    );
    return response.data;
  },
};
