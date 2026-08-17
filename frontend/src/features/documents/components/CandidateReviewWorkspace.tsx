import React, { useState } from 'react';
import {
  CheckCircle2,
  XCircle,
  AlertTriangle,
  FileText,
  CheckSquare,
  Square,
  Sparkles,
  ArrowLeft,
  Loader2,
  AlertCircle,
} from 'lucide-react';
import { extractionService } from '../api/extractionService';
import { CandidateRequirement, Document } from '../types/document.types';
import { RequirementPriority, RequirementType } from '@/types';

interface CandidateReviewWorkspaceProps {
  projectId: string;
  document: Document;
  initialCandidates: CandidateRequirement[];
  onClose: () => void;
  onAcceptSuccess: () => void;
}

export const CandidateReviewWorkspace: React.FC<CandidateReviewWorkspaceProps> = ({
  projectId,
  document,
  initialCandidates,
  onClose,
  onAcceptSuccess,
}) => {
  const [candidates, setCandidates] = useState<CandidateRequirement[]>(
    initialCandidates.map((c) => ({ ...c, selected: false, accepted: false, rejected: false }))
  );
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Toggle selection
  const toggleSelectCandidate = (candidateId: string) => {
    setCandidates((prev) =>
      prev.map((c) => (c.candidate_id === candidateId ? { ...c, selected: !c.selected } : c))
    );
  };

  const toggleSelectAll = () => {
    const allSelected = candidates.every((c) => c.selected);
    setCandidates((prev) => prev.map((c) => ({ ...c, selected: !allSelected })));
  };

  // Inline Field Updates
  const updateCandidateField = (
    candidateId: string,
    field: keyof CandidateRequirement,
    value: any
  ) => {
    setCandidates((prev) =>
      prev.map((c) => (c.candidate_id === candidateId ? { ...c, [field]: value } : c))
    );
  };

  // Mark single candidate as accepted or rejected locally
  const markCandidateStatus = (candidateId: string, status: 'accept' | 'reject') => {
    setCandidates((prev) =>
      prev.map((c) => {
        if (c.candidate_id === candidateId) {
          return {
            ...c,
            accepted: status === 'accept',
            rejected: status === 'reject',
          };
        }
        return c;
      })
    );
  };

  // Mark selected candidates
  const markSelectedStatus = (status: 'accept' | 'reject') => {
    setCandidates((prev) =>
      prev.map((c) => {
        if (c.selected) {
          return {
            ...c,
            accepted: status === 'accept',
            rejected: status === 'reject',
          };
        }
        return c;
      })
    );
  };

  // Submit accepted candidates via batch-accept API
  const handleBatchAcceptSubmit = async () => {
    const acceptedCandidates = candidates.filter((c) => c.accepted);
    if (acceptedCandidates.length === 0) {
      setError('Please accept at least one requirement candidate to commit.');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const items = acceptedCandidates.map((c) => ({
        title: c.title,
        description: c.description,
        type: c.type,
        priority: c.priority,
        status: 'approved' as const,
        source_document_id: c.source_document_id,
        source_section: c.source_section,
        source_snippet: c.source_snippet,
        original_req_id: c.original_req_id,
      }));

      await extractionService.batchAcceptCandidates(projectId, { items });
      onAcceptSuccess();
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Failed to persist accepted candidates.';
      setError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const selectedCount = candidates.filter((c) => c.selected).length;
  const acceptedCount = candidates.filter((c) => c.accepted).length;

  return (
    <div className="fixed inset-0 z-50 bg-slate-950 flex flex-col overflow-hidden">
      {/* Top Navbar */}
      <header className="bg-slate-900 border-b border-slate-800 px-6 py-4 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-4">
          <button
            onClick={onClose}
            className="flex items-center gap-1.5 text-sm text-slate-400 hover:text-white bg-slate-800 px-3 py-1.5 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Workspace</span>
          </button>
          <div>
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-amber-400" />
              <span>Candidate Review Workspace</span>
            </h2>
            <p className="text-xs text-slate-400">
              Source: <span className="text-slate-200 font-medium">{document.filename}</span> •{' '}
              {candidates.length} Candidate Statements Extracted
            </p>
          </div>
        </div>

        {/* Global Action Bar */}
        <div className="flex items-center gap-3">
          <button
            onClick={toggleSelectAll}
            className="flex items-center gap-1.5 text-xs text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 px-3 py-2 rounded-lg border border-slate-700 transition-colors"
          >
            {candidates.every((c) => c.selected) ? (
              <CheckSquare className="w-4 h-4 text-indigo-400" />
            ) : (
              <Square className="w-4 h-4 text-slate-400" />
            )}
            <span>Select All ({candidates.length})</span>
          </button>

          {selectedCount > 0 && (
            <>
              <button
                onClick={() => markSelectedStatus('accept')}
                className="flex items-center gap-1.5 text-xs text-emerald-300 hover:text-white bg-emerald-950/60 hover:bg-emerald-900/60 border border-emerald-800 px-3 py-2 rounded-lg transition-colors"
              >
                <CheckCircle2 className="w-4 h-4" />
                <span>Accept Selected ({selectedCount})</span>
              </button>
              <button
                onClick={() => markSelectedStatus('reject')}
                className="flex items-center gap-1.5 text-xs text-red-300 hover:text-white bg-red-950/60 hover:bg-red-900/60 border border-red-800 px-3 py-2 rounded-lg transition-colors"
              >
                <XCircle className="w-4 h-4" />
                <span>Reject Selected ({selectedCount})</span>
              </button>
            </>
          )}

          <button
            onClick={handleBatchAcceptSubmit}
            disabled={acceptedCount === 0 || isSubmitting}
            className="flex items-center gap-2 px-5 py-2 text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 rounded-lg shadow-lg shadow-indigo-950/50 transition-all"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Commiting...</span>
              </>
            ) : (
              <>
                <CheckCircle2 className="w-4 h-4" />
                <span>Commit Accepted ({acceptedCount})</span>
              </>
            )}
          </button>
        </div>
      </header>

      {/* Main Review Body */}
      <main className="flex-1 overflow-y-auto p-6 bg-slate-950 space-y-4">
        {error && (
          <div className="flex items-start gap-3 p-4 bg-red-950/40 border border-red-800 rounded-xl text-red-300 text-sm max-w-4xl mx-auto">
            <AlertCircle className="w-5 h-5 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {candidates.length === 0 ? (
          <div className="text-center py-20 text-slate-400">
            <FileText className="w-12 h-12 mx-auto mb-3 text-slate-600" />
            <p className="text-lg font-medium text-slate-300">No candidate statements found.</p>
            <p className="text-sm text-slate-500">
              The document did not contain explicit requirement patterns or modal verbs.
            </p>
          </div>
        ) : (
          <div className="max-w-5xl mx-auto space-y-4 pb-12">
            {candidates.map((candidate, idx) => (
              <div
                key={candidate.candidate_id}
                className={`bg-slate-900 border rounded-xl transition-all ${
                  candidate.accepted
                    ? 'border-emerald-700/80 bg-emerald-950/10'
                    : candidate.rejected
                    ? 'border-red-900/60 bg-red-950/10 opacity-60'
                    : candidate.is_duplicate
                    ? 'border-amber-700/80 bg-amber-950/10'
                    : 'border-slate-800 hover:border-slate-700'
                }`}
              >
                {/* Candidate Top Header */}
                <div className="px-5 py-3 border-b border-slate-800/80 flex items-center justify-between bg-slate-950/40">
                  <div className="flex items-center gap-3">
                    <button
                      type="button"
                      onClick={() => toggleSelectCandidate(candidate.candidate_id)}
                      className="text-slate-400 hover:text-indigo-400 transition-colors"
                    >
                      {candidate.selected ? (
                        <CheckSquare className="w-5 h-5 text-indigo-400" />
                      ) : (
                        <Square className="w-5 h-5" />
                      )}
                    </button>
                    <span className="font-mono text-xs text-indigo-300 font-semibold bg-indigo-950/80 px-2 py-0.5 rounded border border-indigo-800">
                      Candidate #{idx + 1}
                    </span>
                    {candidate.original_req_id && (
                      <span className="font-mono text-xs text-amber-300 font-semibold bg-amber-950/80 px-2 py-0.5 rounded border border-amber-800">
                        {candidate.original_req_id}
                      </span>
                    )}

                    {candidate.is_duplicate && (
                      <div className="flex items-center gap-1.5 text-xs text-amber-300 bg-amber-950/60 border border-amber-800 px-2.5 py-0.5 rounded-full">
                        <AlertTriangle className="w-3.5 h-3.5" />
                        <span>
                          Potential Duplicate ({Math.round(candidate.similarity_score * 100)}% Match)
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => markCandidateStatus(candidate.candidate_id, 'accept')}
                      className={`flex items-center gap-1 text-xs px-3 py-1.5 rounded-lg font-medium transition-all ${
                        candidate.accepted
                          ? 'bg-emerald-600 text-white font-semibold shadow-md'
                          : 'bg-slate-800 text-slate-300 hover:bg-emerald-950/80 hover:text-emerald-300 border border-slate-700'
                      }`}
                    >
                      <CheckCircle2 className="w-4 h-4" />
                      <span>{candidate.accepted ? 'Accepted' : 'Accept'}</span>
                    </button>

                    <button
                      type="button"
                      onClick={() => markCandidateStatus(candidate.candidate_id, 'reject')}
                      className={`flex items-center gap-1 text-xs px-3 py-1.5 rounded-lg font-medium transition-all ${
                        candidate.rejected
                          ? 'bg-red-700 text-white font-semibold shadow-md'
                          : 'bg-slate-800 text-slate-300 hover:bg-red-950/80 hover:text-red-300 border border-slate-700'
                      }`}
                    >
                      <XCircle className="w-4 h-4" />
                      <span>{candidate.rejected ? 'Rejected' : 'Reject'}</span>
                    </button>
                  </div>
                </div>

                {/* Candidate Content Body */}
                <div className="p-5 space-y-4">
                  {/* Title & Controls Row */}
                  <div className="grid grid-cols-1 md:grid-cols-12 gap-3">
                    <div className="md:col-span-6">
                      <label className="block text-xs font-semibold text-slate-400 mb-1">
                        Title
                      </label>
                      <input
                        type="text"
                        value={candidate.title}
                        onChange={(e) =>
                          updateCandidateField(candidate.candidate_id, 'title', e.target.value)
                        }
                        className="w-full bg-slate-950 border border-slate-700 focus:border-indigo-500 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none"
                      />
                    </div>

                    <div className="md:col-span-3">
                      <label className="block text-xs font-semibold text-slate-400 mb-1">
                        Type
                      </label>
                      <select
                        value={candidate.type}
                        onChange={(e) =>
                          updateCandidateField(
                            candidate.candidate_id,
                            'type',
                            e.target.value as RequirementType
                          )
                        }
                        className="w-full bg-slate-950 border border-slate-700 focus:border-indigo-500 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none capitalize"
                      >
                        <option value="functional">Functional</option>
                        <option value="non_functional">Non-Functional</option>
                        <option value="user">User</option>
                        <option value="business">Business</option>
                        <option value="system">System</option>
                      </select>
                    </div>

                    <div className="md:col-span-3">
                      <label className="block text-xs font-semibold text-slate-400 mb-1">
                        Priority
                      </label>
                      <select
                        value={candidate.priority}
                        onChange={(e) =>
                          updateCandidateField(
                            candidate.candidate_id,
                            'priority',
                            e.target.value as RequirementPriority
                          )
                        }
                        className="w-full bg-slate-950 border border-slate-700 focus:border-indigo-500 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none capitalize"
                      >
                        <option value="low">Low</option>
                        <option value="medium">Medium</option>
                        <option value="high">High</option>
                        <option value="critical">Critical</option>
                      </select>
                    </div>
                  </div>

                  {/* Description Textarea */}
                  <div>
                    <label className="block text-xs font-semibold text-slate-400 mb-1">
                      Requirement Statement
                    </label>
                    <textarea
                      rows={2}
                      value={candidate.description}
                      onChange={(e) =>
                        updateCandidateField(candidate.candidate_id, 'description', e.target.value)
                      }
                      className="w-full bg-slate-950 border border-slate-700 focus:border-indigo-500 rounded-lg p-3 text-sm text-slate-200 focus:outline-none resize-y"
                    />
                  </div>

                  {/* Traceability Metadata Footer */}
                  <div className="p-3 bg-slate-950/80 border border-slate-800 rounded-lg flex flex-col md:flex-row md:items-center justify-between gap-2 text-xs text-slate-400">
                    <div className="flex items-center gap-2">
                      <FileText className="w-4 h-4 text-indigo-400 shrink-0" />
                      <span>
                        Source: <span className="text-slate-200">{document.filename}</span> •{' '}
                        Section: <span className="text-slate-200">{candidate.source_section}</span>
                      </span>
                    </div>
                    <div className="truncate max-w-md italic text-slate-500">
                      Snippet: "{candidate.source_snippet}"
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
};
