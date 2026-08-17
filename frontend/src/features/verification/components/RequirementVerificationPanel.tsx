import React, { useState, useEffect } from 'react';
import { ShieldCheck, X, AlertTriangle, Loader2, Sparkles } from 'lucide-react';
import { verificationService } from '../api/verificationService';
import { Requirement, TestExecutionStatus, VerificationSpecificationResponse } from '../../../types';

interface RequirementVerificationPanelProps {
  isOpen: boolean;
  projectId: string;
  requirement: Requirement | null;
  onClose: () => void;
  onRefreshSummary: () => void;
}

export const RequirementVerificationPanel: React.FC<RequirementVerificationPanelProps> = ({
  isOpen,
  projectId,
  requirement,
  onClose,
  onRefreshSummary,
}) => {
  const [spec, setSpec] = useState<VerificationSpecificationResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isCompiling, setIsCompiling] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<string>('all');
  const [error, setError] = useState<string | null>(null);
  const [updatingTcId, setUpdatingTcId] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && requirement) {
      fetchVerification();
    }
  }, [isOpen, requirement]);

  const fetchVerification = async () => {
    if (!requirement) return;
    setIsLoading(true);
    setError(null);
    try {
      const data = await verificationService.getVerification(projectId, requirement.id);
      setSpec(data);
    } catch (err: any) {
      setError('Failed to fetch verification specification.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCompile = async () => {
    if (!requirement) return;
    setIsCompiling(true);
    setError(null);
    try {
      const data = await verificationService.compileRequirement(projectId, requirement.id);
      setSpec(data);
      onRefreshSummary();
    } catch (err: any) {
      setError('Failed to compile verification specification.');
    } finally {
      setIsCompiling(false);
    }
  };

  const handleUpdateTcStatus = async (tcId: string, status: TestExecutionStatus) => {
    setUpdatingTcId(tcId);
    try {
      await verificationService.updateTestCaseStatus(projectId, tcId, status);
      await fetchVerification();
      onRefreshSummary();
    } catch (err: any) {
      setError('Failed to update test case status.');
    } finally {
      setUpdatingTcId(null);
    }
  };

  if (!isOpen || !requirement) return null;

  const getReadinessBadge = (readiness: string) => {
    if (readiness === 'explicit_measurable') return 'text-emerald-400 bg-emerald-950/80 border-emerald-800';
    if (readiness === 'confidently_inferred') return 'text-indigo-400 bg-indigo-950/80 border-indigo-800';
    return 'text-red-400 bg-red-950/80 border-red-800';
  };

  const getStatusBadge = (status: string) => {
    if (status === 'verified') return 'text-emerald-400 bg-emerald-950/80 border-emerald-800';
    if (status === 'ready_for_verification') return 'text-indigo-400 bg-indigo-950/80 border-indigo-800';
    if (status === 'partially_ready') return 'text-amber-400 bg-amber-950/80 border-amber-800';
    return 'text-red-400 bg-red-950/80 border-red-800';
  };

  const filteredTestCases = spec
    ? spec.test_cases.filter((tc) => (activeTab === 'all' ? true : tc.test_type === activeTab))
    : [];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-xl shadow-2xl w-full max-w-4xl overflow-hidden flex flex-col max-h-[92vh] animate-in fade-in duration-200">
        {/* Header */}
        <div className="flex justify-between items-center px-6 py-4 border-b border-slate-800 shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-emerald-950/60 border border-emerald-800/60 flex items-center justify-center text-emerald-400">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-white truncate max-w-lg">
                Verification Compiler: {requirement.title}
              </h3>
              <p className="text-xs text-slate-400">
                Structured criteria, Given-When-Then acceptance tests & execution evidence
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 overflow-y-auto flex-1 space-y-5">
          {error && (
            <div className="p-3 bg-red-950/40 border border-red-800 rounded-lg text-red-300 text-xs flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {isLoading ? (
            <div className="flex items-center justify-center py-16 text-slate-400 text-xs">
              <Loader2 className="w-6 h-6 animate-spin text-emerald-400 mr-2" />
              <span>Compiling verification specification...</span>
            </div>
          ) : !spec ? (
            <div className="text-center py-12 space-y-3">
              <p className="text-slate-400 text-xs">No verification specification compiled yet for this requirement.</p>
              <button
                onClick={handleCompile}
                disabled={isCompiling}
                className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-500 rounded-lg shadow-sm"
              >
                {isCompiling ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
                <span>Compile Verification Spec</span>
              </button>
            </div>
          ) : (
            <div className="space-y-5">
              {/* Readiness & Execution Status Banner */}
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 p-4 bg-slate-950 border border-slate-800 rounded-xl">
                <div className="flex items-center gap-3">
                  <div>
                    <span className="text-[10px] text-slate-400 uppercase block font-semibold mb-0.5">Readiness:</span>
                    <span className={`text-xs font-bold px-2.5 py-1 rounded border uppercase ${getReadinessBadge(spec.readiness_status)}`}>
                      {spec.readiness_status.replace('_', ' ')}
                    </span>
                  </div>

                  <div>
                    <span className="text-[10px] text-slate-400 uppercase block font-semibold mb-0.5">Verification Evidence:</span>
                    <span className={`text-xs font-bold px-2.5 py-1 rounded border uppercase ${getStatusBadge(spec.verification_status)}`}>
                      {spec.verification_status.replace('_', ' ')}
                    </span>
                  </div>
                </div>

                <button
                  onClick={handleCompile}
                  disabled={isCompiling}
                  className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-white bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-lg transition-colors"
                >
                  {isCompiling ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5 text-emerald-400" />}
                  <span>Re-Compile Spec</span>
                </button>
              </div>

              {/* Extracted Criteria Grid */}
              <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl space-y-3">
                <h4 className="text-xs font-bold text-slate-300">Extracted Structured Criteria:</h4>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                  <div>
                    <span className="text-slate-400 text-[10px] block">Metric:</span>
                    <span className="font-semibold text-white">{spec.metric || 'N/A'}</span>
                  </div>
                  <div>
                    <span className="text-slate-400 text-[10px] block">Operator & Threshold:</span>
                    <span className="font-semibold text-white">{spec.operator || ''} {spec.threshold || 'N/A'} {spec.unit || ''}</span>
                  </div>
                  <div>
                    <span className="text-slate-400 text-[10px] block">Population / Sample:</span>
                    <span className="font-semibold text-white">{spec.population_sample || 'All Contexts'}</span>
                  </div>
                  <div>
                    <span className="text-slate-400 text-[10px] block">Verification Type:</span>
                    <span className="font-semibold text-white capitalize">{spec.verification_type}</span>
                  </div>
                </div>

                {spec.pass_condition && (
                  <div className="p-2.5 bg-slate-900 border border-slate-800 rounded text-xs text-slate-300">
                    <span className="font-semibold text-emerald-400">Pass Condition:</span> {spec.pass_condition}
                  </div>
                )}
              </div>

              {/* Acceptance Criteria (Given-When-Then) */}
              {spec.acceptance_criteria.length > 0 && (
                <div className="p-4 bg-indigo-950/30 border border-indigo-900/40 rounded-xl text-xs text-indigo-200 space-y-2">
                  <h4 className="font-bold text-indigo-300">Acceptance Criteria (Gherkin / Measurable):</h4>
                  {spec.acceptance_criteria.map((ac, idx) => (
                    <div key={idx} className="space-y-1 font-mono text-[11px] bg-indigo-950/60 p-2.5 rounded border border-indigo-900/60">
                      {ac.given && <p><span className="text-indigo-400 font-bold">GIVEN</span> {ac.given}</p>}
                      {ac.when && <p><span className="text-indigo-400 font-bold">WHEN</span> {ac.when}</p>}
                      {ac.then && <p><span className="text-indigo-400 font-bold">THEN</span> {ac.then}</p>}
                      {ac.criterion && <p><span className="text-indigo-400 font-bold">CRITERION:</span> {ac.criterion}</p>}
                    </div>
                  ))}
                </div>
              )}

              {/* Synthesized Test Case Suite */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold text-slate-300">Generated Test Case Suite ({spec.test_cases.length}):</h4>
                  <div className="flex items-center gap-1 text-xs">
                    {['all', 'positive', 'negative', 'boundary', 'performance', 'security'].map((t) => (
                      <button
                        key={t}
                        onClick={() => setActiveTab(t)}
                        className={`px-2 py-0.5 rounded capitalize ${activeTab === t ? 'bg-indigo-600 text-white font-bold' : 'bg-slate-800 text-slate-400'}`}
                      >
                        {t}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
                  {filteredTestCases.map((tc) => (
                    <div key={tc.id} className="p-3 bg-slate-950 border border-slate-800 rounded-xl space-y-2 text-xs">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-white">{tc.title}</span>
                        <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-slate-900 text-slate-400 border border-slate-800">
                          {tc.test_type}
                        </span>
                      </div>

                      <p className="text-slate-400 text-[11px]"><span className="font-semibold text-slate-300">Expected:</span> {tc.expected_result}</p>

                      {/* Execution Evidence Status Controls */}
                      <div className="flex items-center justify-end gap-2 pt-1 border-t border-slate-900 text-[11px]">
                        <span className="text-slate-500 font-medium mr-1">Execution Status:</span>
                        {(['untested', 'passed', 'failed', 'blocked'] as TestExecutionStatus[]).map((st) => (
                          <button
                            key={st}
                            onClick={() => handleUpdateTcStatus(tc.id, st)}
                            disabled={updatingTcId === tc.id}
                            className={`px-2.5 py-0.5 rounded font-semibold capitalize transition-all ${
                              tc.execution_status === st
                                ? st === 'passed'
                                  ? 'bg-emerald-600 text-white'
                                  : st === 'failed'
                                  ? 'bg-red-600 text-white'
                                  : st === 'blocked'
                                  ? 'bg-amber-600 text-white'
                                  : 'bg-slate-700 text-white'
                                : 'bg-slate-900 text-slate-400 hover:bg-slate-800'
                            }`}
                          >
                            {st}
                          </button>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end px-6 py-4 bg-slate-950/60 border-t border-slate-800 shrink-0">
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-medium text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
