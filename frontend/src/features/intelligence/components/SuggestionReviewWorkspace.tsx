import React, { useState, useEffect } from 'react';
import { Sparkles, X, Check, Trash2, AlertCircle, ArrowRight, ShieldAlert, GitFork, Loader2 } from 'lucide-react';
import { intelligenceService } from '../api/intelligenceService';
import { Requirement, RequirementSuggestion } from '../../../types';

interface SuggestionReviewWorkspaceProps {
  isOpen: boolean;
  projectId: string;
  requirements: Requirement[];
  onClose: () => void;
  onRefreshSummary: () => void;
}

export const SuggestionReviewWorkspace: React.FC<SuggestionReviewWorkspaceProps> = ({
  isOpen,
  projectId,
  requirements,
  onClose,
  onRefreshSummary,
}) => {
  const [suggestions, setSuggestions] = useState<RequirementSuggestion[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [activeFilter, setActiveFilter] = useState<string>('suggested');
  const [error, setError] = useState<string | null>(null);
  const [processingId, setProcessingId] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      fetchSuggestions();
    }
  }, [isOpen, activeFilter]);

  const fetchSuggestions = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await intelligenceService.getSuggestions(projectId, {
        status: activeFilter !== 'all' ? activeFilter : undefined,
      });
      setSuggestions(data);
    } catch (err: any) {
      setError('Failed to load intelligence suggestions.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleAccept = async (sugId: string) => {
    setProcessingId(sugId);
    setError(null);
    try {
      await intelligenceService.acceptSuggestion(projectId, sugId);
      await fetchSuggestions();
      onRefreshSummary();
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to accept suggestion.');
    } finally {
      setProcessingId(null);
    }
  };

  const handleReject = async (sugId: string) => {
    setProcessingId(sugId);
    setError(null);
    try {
      await intelligenceService.rejectSuggestion(projectId, sugId, 'Rejected by reviewer');
      await fetchSuggestions();
      onRefreshSummary();
    } catch (err: any) {
      setError('Failed to reject suggestion.');
    } finally {
      setProcessingId(null);
    }
  };

  if (!isOpen) return null;

  const getReqTitle = (reqId: string) => {
    const found = requirements.find((r) => r.id === reqId);
    return found ? found.title : reqId;
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-xl shadow-2xl w-full max-w-4xl overflow-hidden flex flex-col max-h-[90vh] animate-in fade-in duration-200">
        {/* Header */}
        <div className="flex justify-between items-center px-6 py-4 border-b border-slate-800 shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-indigo-950/60 border border-indigo-800/60 flex items-center justify-center text-indigo-400">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-white">
                Conflict & Dependency Intelligence Workspace
              </h3>
              <p className="text-xs text-slate-400">
                Review automatically discovered suggestions and evidence before committing graph edges
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

        {/* Filter Bar */}
        <div className="flex items-center gap-2 px-6 py-3 bg-slate-950/60 border-b border-slate-800 text-xs shrink-0">
          <span className="text-slate-400 font-medium mr-2">Filter Status:</span>
          {['suggested', 'accepted', 'rejected', 'all'].map((f) => (
            <button
              key={f}
              onClick={() => setActiveFilter(f)}
              className={`px-3 py-1 rounded-lg capitalize font-medium transition-all ${
                activeFilter === f
                  ? 'bg-indigo-600 text-white font-semibold'
                  : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
              }`}
            >
              {f}
            </button>
          ))}
        </div>

        {/* Content Body */}
        <div className="p-6 overflow-y-auto flex-1 space-y-4">
          {error && (
            <div className="flex items-start gap-3 p-3 bg-red-950/40 border border-red-800 rounded-lg text-red-300 text-sm">
              <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {isLoading ? (
            <div className="flex items-center justify-center py-16 text-slate-400 text-sm">
              <Loader2 className="w-6 h-6 animate-spin text-indigo-400 mr-2" />
              <span>Loading intelligence suggestions...</span>
            </div>
          ) : suggestions.length === 0 ? (
            <div className="text-center py-16 text-slate-500 text-sm">
              No suggestions found matching filter status '<span className="text-slate-300 capitalize">{activeFilter}</span>'.
            </div>
          ) : (
            <div className="space-y-4">
              {suggestions.map((sug) => (
                <div
                  key={sug.id}
                  className="bg-slate-950 border border-slate-800 rounded-xl p-4 shadow-sm hover:border-slate-700 transition-all space-y-3"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                    <div className="flex items-center gap-2">
                      {sug.relationship_type === 'conflicts_with' ? (
                        <span className="flex items-center gap-1 text-xs font-bold text-amber-400 bg-amber-950/60 border border-amber-800/60 px-2.5 py-1 rounded-md">
                          <ShieldAlert className="w-3.5 h-3.5" /> Conflict
                        </span>
                      ) : (
                        <span className="flex items-center gap-1 text-xs font-bold text-indigo-400 bg-indigo-950/60 border border-indigo-800/60 px-2.5 py-1 rounded-md">
                          <GitFork className="w-3.5 h-3.5" /> Dependency
                        </span>
                      )}

                      {sug.conflict_category && (
                        <span className="text-xs text-slate-400 font-mono bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
                          {sug.conflict_category}
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-2 text-xs">
                      <span className="text-slate-400">Confidence:</span>
                      <span className="font-bold text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800/60">
                        {Math.round(sug.confidence_score * 100)}%
                      </span>
                    </div>
                  </div>

                  {/* Requirements Pair Display */}
                  <div className="flex items-center gap-3 p-3 bg-slate-900/80 border border-slate-800/60 rounded-lg text-xs">
                    <span className="font-bold text-white truncate max-w-xs">{getReqTitle(sug.source_id)}</span>
                    <ArrowRight className="w-4 h-4 text-slate-500 shrink-0" />
                    <span className="font-bold text-white truncate max-w-xs">{getReqTitle(sug.target_id)}</span>
                  </div>

                  {/* Evidence Explanation Banner */}
                  <div className="p-3 bg-indigo-950/30 border border-indigo-900/50 rounded-lg text-xs text-indigo-200">
                    <p className="font-semibold text-indigo-300 mb-1">Evidence & Technical Detail:</p>
                    <p>{sug.evidence_explanation}</p>

                    {sug.suggested_resolution && (
                      <p className="mt-1.5 text-slate-300 italic border-t border-indigo-900/40 pt-1.5">
                        Suggested Resolution: {sug.suggested_resolution}
                      </p>
                    )}
                  </div>

                  {/* Card Footer Actions */}
                  {sug.status === 'suggested' && (
                    <div className="flex items-center justify-end gap-2 pt-1">
                      <button
                        onClick={() => handleReject(sug.id)}
                        disabled={processingId === sug.id}
                        className="flex items-center gap-1 px-3 py-1.5 text-xs font-semibold text-slate-400 hover:text-red-400 bg-slate-900 hover:bg-red-950/40 border border-slate-800 rounded-lg transition-colors"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                        <span>Dismiss / Reject</span>
                      </button>

                      <button
                        onClick={() => handleAccept(sug.id)}
                        disabled={processingId === sug.id}
                        className="flex items-center gap-1 px-3 py-1.5 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 rounded-lg shadow-sm transition-colors"
                      >
                        {processingId === sug.id ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Check className="w-3.5 h-3.5" />}
                        <span>Accept & Add Edge</span>
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end px-6 py-4 bg-slate-950/60 border-t border-slate-800 shrink-0">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
