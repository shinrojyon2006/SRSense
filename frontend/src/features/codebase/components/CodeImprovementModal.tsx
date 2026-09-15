import React, { useState, useEffect } from 'react';
import {
  Sparkles,
  ShieldCheck,
  AlertTriangle,
  X,
  CheckCircle,
  FileCode,
  Layers,
  Check,
  RotateCw,
  Info,
  BarChart2,
} from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { codeImprovementService } from '../api/codeImprovementService';
import { codeEvaluationService } from '../api/codeEvaluationService';
import { CodeImprovementProposal } from '../types/codeImprovement.types';
import { CodeImprovementEvaluation } from '../types/codeEvaluation.types';
import { DiffViewer } from './DiffViewer';
import { CodeImprovementEvaluationModal } from './CodeImprovementEvaluationModal';

interface CodeImprovementModalProps {
  isOpen: boolean;
  projectId: string;
  findingId?: string;
  proposalId?: string;
  onClose: () => void;
  onAppliedSuccess?: () => void;
}

export const CodeImprovementModal: React.FC<CodeImprovementModalProps> = ({
  isOpen,
  projectId,
  findingId,
  proposalId,
  onClose,
  onAppliedSuccess,
}) => {
  const [proposal, setProposal] = useState<CodeImprovementProposal | null>(null);
  const [evaluation, setEvaluation] = useState<CodeImprovementEvaluation | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isApplying, setIsApplying] = useState<boolean>(false);
  const [isRejecting, setIsRejecting] = useState<boolean>(false);
  const [isEvaluating, setIsEvaluating] = useState<boolean>(false);
  const [isEvalModalOpen, setIsEvalModalOpen] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && projectId) {
      if (proposalId) {
        loadProposalDetail(proposalId);
      } else if (findingId) {
        generateNewProposal(findingId);
      }
    }
  }, [isOpen, projectId, findingId, proposalId]);

  const loadProposalDetail = async (propId: string) => {
    try {
      setIsLoading(true);
      setErrorMsg(null);
      const data = await codeImprovementService.getProposal(projectId, propId);
      setProposal(data);
      if (data.status === 'applied') {
        checkExistingEvaluation(data.id);
      }
    } catch (err: any) {
      console.error('Failed to load improvement proposal:', err);
      setErrorMsg('Failed to load code improvement proposal.');
    } finally {
      setIsLoading(false);
    }
  };

  const checkExistingEvaluation = async (propId: string) => {
    try {
      const evalData = await codeEvaluationService.getEvaluation(projectId, propId);
      setEvaluation(evalData);
    } catch {
      // evaluation not run yet
    }
  };

  const generateNewProposal = async (fId: string) => {
    try {
      setIsLoading(true);
      setErrorMsg(null);
      const data = await codeImprovementService.createProposal(projectId, {
        finding_id: fId,
      });
      setProposal(data);
    } catch (err: any) {
      console.error('Failed to generate improvement proposal:', err);
      setErrorMsg(
        err.response?.data?.detail || 'Failed to generate AI code improvement proposal.'
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleApproveAndApply = async () => {
    if (!proposal) return;
    try {
      setIsApplying(true);
      setErrorMsg(null);
      setSuccessMsg(null);
      const updated = await codeImprovementService.approveAndApply(
        projectId,
        proposal.id
      );
      setProposal(updated);
      setSuccessMsg('Improvement successfully approved and applied to codebase!');
      if (onAppliedSuccess) onAppliedSuccess();
    } catch (err: any) {
      console.error('Failed to apply improvement:', err);
      setErrorMsg(
        err.response?.data?.detail || 'Failed to apply patch to codebase.'
      );
    } finally {
      setIsApplying(false);
    }
  };

  const handleEvaluateImprovement = async () => {
    if (!proposal) return;
    try {
      setIsEvaluating(true);
      setErrorMsg(null);
      const evalResult = await codeEvaluationService.evaluateImprovement(projectId, proposal.id);
      setEvaluation(evalResult);
      setIsEvalModalOpen(true);
    } catch (err: any) {
      console.error('Failed to evaluate improvement:', err);
      setErrorMsg(
        err.response?.data?.detail || 'Failed to trigger post-patch code evaluation.'
      );
    } finally {
      setIsEvaluating(false);
    }
  };

  const handleReject = async () => {
    if (!proposal) return;
    try {
      setIsRejecting(true);
      setErrorMsg(null);
      const updated = await codeImprovementService.rejectProposal(
        projectId,
        proposal.id
      );
      setProposal(updated);
    } catch (err: any) {
      console.error('Failed to reject improvement:', err);
      setErrorMsg('Failed to reject proposal.');
    } finally {
      setIsRejecting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <>
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/75 p-4 sm:p-6 backdrop-blur-xs">
        <div className="flex h-[90vh] w-full max-w-5xl flex-col rounded-2xl border border-slate-200 bg-white shadow-2xl dark:border-slate-800 dark:bg-slate-900 overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4 dark:border-slate-800">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-xl bg-purple-50 dark:bg-purple-950/50 text-purple-600 dark:text-purple-400">
                <Sparkles className="h-5 w-5" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-base font-bold text-slate-900 dark:text-white">
                    AI Code Improvement Workspace
                  </h2>
                  {proposal && (
                    <Badge
                      variant={
                        proposal.status === 'applied'
                          ? 'success'
                          : proposal.status === 'rejected' || proposal.status === 'stale'
                          ? 'neutral'
                          : proposal.status === 'failed'
                          ? 'error'
                          : 'warning'
                      }
                    >
                      {proposal.status.toUpperCase()}
                    </Badge>
                  )}
                </div>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Bounded Context Refactoring, Requirement Grounding & Safe Non-Silent Patch Application
                </p>
              </div>
            </div>

            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:bg-slate-100 hover:text-slate-700 dark:hover:bg-slate-800 dark:hover:text-slate-200 transition-colors"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Body */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {isLoading ? (
              <div className="p-16 text-center text-xs text-slate-400 space-y-2">
                <RotateCw className="h-6 w-6 animate-spin mx-auto text-indigo-500" />
                <div>Generating AI Code Improvement Proposal & Patch Diff...</div>
              </div>
            ) : errorMsg ? (
              <div className="p-4 rounded-xl border border-red-200 bg-red-50 text-red-700 text-xs dark:border-red-900 dark:bg-red-950/40 dark:text-red-300">
                {errorMsg}
              </div>
            ) : !proposal ? (
              <div className="p-12 text-center text-xs text-slate-400">No proposal data found.</div>
            ) : (
              <div className="space-y-6">
                {successMsg && (
                  <div className="p-4 rounded-xl border border-emerald-200 bg-emerald-50 text-emerald-800 text-xs dark:border-emerald-900/60 dark:bg-emerald-950/40 dark:text-emerald-300 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <CheckCircle className="h-4 w-4 text-emerald-600" /> {successMsg}
                    </div>
                    <Button
                      size="sm"
                      onClick={handleEvaluateImprovement}
                      disabled={isEvaluating}
                      className="bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold"
                    >
                      {isEvaluating ? (
                        <>
                          <RotateCw className="h-3.5 w-3.5 mr-1 animate-spin" /> Evaluating...
                        </>
                      ) : (
                        <>
                          <BarChart2 className="h-3.5 w-3.5 mr-1" /> Evaluate Improvement
                        </>
                      )}
                    </Button>
                  </div>
                )}

                {/* Proposal Header & File Info */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 rounded-xl bg-slate-50/80 border border-slate-200 dark:bg-slate-950/40 dark:border-slate-800">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-indigo-100 dark:bg-indigo-950 text-indigo-700 dark:text-indigo-300">
                        Rule: {proposal.rule_id}
                      </span>
                      <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                        {proposal.title}
                      </h3>
                    </div>
                    <div className="flex items-center gap-2 font-mono text-xs text-slate-500 dark:text-slate-400 mt-1">
                      <FileCode className="h-3.5 w-3.5 text-slate-400" />
                      <span>File: {proposal.file_path}</span>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 shrink-0">
                    <div className="text-right">
                      <div className="text-[10px] text-slate-400 uppercase tracking-wider">
                        Confidence Score
                      </div>
                      <div className="text-sm font-extrabold text-indigo-600 dark:text-indigo-400">
                        {proposal.confidence}%
                      </div>
                    </div>
                  </div>
                </div>

                {/* Problem & Root Cause Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-4 rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900 space-y-1">
                    <div className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                      Problem Summary
                    </div>
                    <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                      {proposal.problem_summary}
                    </p>
                  </div>

                  <div className="p-4 rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900 space-y-1">
                    <div className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                      Root Cause Analysis
                    </div>
                    <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                      {proposal.root_cause}
                    </p>
                  </div>
                </div>

                {/* Linked Requirement Grounding Panel */}
                <div className="p-4 rounded-xl border border-indigo-200 bg-indigo-50/50 dark:border-indigo-900/60 dark:bg-indigo-950/30 space-y-2">
                  <div className="flex items-center gap-2 text-xs font-bold text-indigo-900 dark:text-indigo-200">
                    <ShieldCheck className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
                    Requirement-Grounded Impact & Refactoring Context
                  </div>
                  <p className="text-xs text-indigo-950 dark:text-indigo-200 leading-relaxed">
                    {proposal.recommendation}
                  </p>
                  {proposal.uncertainty && (
                    <div className="text-[11px] text-amber-700 dark:text-amber-300 italic flex items-center gap-1 mt-1">
                      <Info className="h-3.5 w-3.5 shrink-0" />
                      <span>{proposal.uncertainty}</span>
                    </div>
                  )}
                </div>

                {/* Code Comparison & Diff Viewer */}
                <div className="space-y-2">
                  <div className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider">
                    Reviewable Code Refactoring & Git Diff
                  </div>
                  <DiffViewer
                    currentCode={proposal.current_code}
                    proposedCode={proposal.proposed_code}
                    patchDiff={proposal.patch_diff}
                    filePath={proposal.file_path}
                  />
                </div>

                {/* Affected Artifacts & Test Considerations */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Affected Files & Requirements */}
                  <div className="p-4 rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900 space-y-3">
                    <div className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                      <Layers className="h-4 w-4 text-slate-500" /> Affected Artifacts
                    </div>
                    <div className="space-y-2 text-xs">
                      <div>
                        <span className="font-semibold text-slate-500 dark:text-slate-400">
                          Affected Files:
                        </span>
                        <div className="mt-1 font-mono text-[11px] text-slate-800 dark:text-slate-200 bg-slate-50 dark:bg-slate-950/40 p-2 rounded border border-slate-100 dark:border-slate-800">
                          {proposal.affected_files.join(', ')}
                        </div>
                      </div>
                      {proposal.affected_requirements.length > 0 && (
                        <div>
                          <span className="font-semibold text-slate-500 dark:text-slate-400">
                            Linked Requirements:
                          </span>
                          <div className="mt-1 space-y-1">
                            {proposal.affected_requirements.map((req, idx) => (
                              <div
                                key={idx}
                                className="p-2 rounded bg-indigo-50/50 dark:bg-indigo-950/30 border border-indigo-100 dark:border-indigo-900/40 text-[11px] font-semibold text-indigo-900 dark:text-indigo-200"
                              >
                                {req.title}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Suggested Test Considerations */}
                  <div className="p-4 rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900 space-y-3">
                    <div className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                      <CheckCircle className="h-4 w-4 text-emerald-500" /> Test Considerations
                    </div>
                    <div className="space-y-2 text-xs">
                      {proposal.affected_tests.map((t, idx) => (
                        <div
                          key={idx}
                          className="p-2.5 rounded-lg border border-slate-100 bg-slate-50/50 dark:border-slate-800 dark:bg-slate-950/40 text-xs"
                        >
                          <div className="font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wide text-[10px]">
                            {t.type}
                          </div>
                          <div className="text-slate-600 dark:text-slate-300 text-[11px] mt-0.5">
                            {t.description}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Footer & Action Bar */}
          {proposal && (
            <div className="border-t border-slate-200 px-6 py-4 dark:border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-3 bg-slate-50/60 dark:bg-slate-950/40">
              <div className="text-xs text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
                <AlertTriangle className="h-4 w-4 text-amber-500 shrink-0" />
                <span>
                  Safety Check: Patch is reviewed before applying. Source code is never silently modified.
                </span>
              </div>

              <div className="flex items-center gap-2 shrink-0">
                {proposal.status === 'applied' && (
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={handleEvaluateImprovement}
                    disabled={isEvaluating}
                    className="border border-indigo-500 text-indigo-400 hover:bg-indigo-950/50 font-bold"
                  >
                    {isEvaluating ? (
                      <>
                        <RotateCw className="h-4 w-4 mr-1.5 animate-spin" /> Evaluating...
                      </>
                    ) : (
                      <>
                        <BarChart2 className="h-4 w-4 mr-1.5" /> Evaluate Improvement
                      </>
                    )}
                  </Button>
                )}

                <Button
                  variant="secondary"
                  size="sm"
                  onClick={handleReject}
                  disabled={isRejecting || proposal.status === 'applied' || proposal.status === 'rejected'}
                >
                  {isRejecting ? 'Rejecting...' : 'Reject Proposal'}
                </Button>

                <Button
                  size="sm"
                  onClick={handleApproveAndApply}
                  disabled={isApplying || proposal.status === 'applied'}
                  className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold"
                >
                  {isApplying ? (
                    <>
                      <RotateCw className="h-4 w-4 mr-1.5 animate-spin" /> Applying Patch...
                    </>
                  ) : proposal.status === 'applied' ? (
                    <>
                      <Check className="h-4 w-4 mr-1.5" /> Patch Applied
                    </>
                  ) : (
                    <>
                      <Check className="h-4 w-4 mr-1.5" /> Approve & Apply Patch
                    </>
                  )}
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Evaluation Result Modal */}
      {isEvalModalOpen && (
        <CodeImprovementEvaluationModal
          isOpen={isEvalModalOpen}
          onClose={() => setIsEvalModalOpen(false)}
          evaluation={evaluation}
          proposalTitle={proposal?.title || ''}
        />
      )}
    </>
  );
};

