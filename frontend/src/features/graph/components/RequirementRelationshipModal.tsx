import React, { useState, useEffect } from 'react';
import { GitFork, X, Plus, Trash2, AlertCircle, FileText, ArrowRight, ShieldAlert, CheckCircle2, Loader2 } from 'lucide-react';
import { graphService } from '../api/graphService';
import {
  Requirement,
  RequirementRelationshipsResponse,
  RelationshipType,
} from '../../../types';

interface RequirementRelationshipModalProps {
  isOpen: boolean;
  projectId: string;
  requirement: Requirement | null;
  allRequirements: Requirement[];
  onClose: () => void;
}

export const RequirementRelationshipModal: React.FC<RequirementRelationshipModalProps> = ({
  isOpen,
  projectId,
  requirement,
  allRequirements,
  onClose,
}) => {
  const [relData, setRelData] = useState<RequirementRelationshipsResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Form State for creating new edge
  const [targetId, setTargetId] = useState<string>('');
  const [relType, setRelType] = useState<RelationshipType>('depends_on');

  useEffect(() => {
    if (isOpen && requirement) {
      fetchRelationships();
    }
  }, [isOpen, requirement]);

  const fetchRelationships = async () => {
    if (!requirement) return;
    setIsLoading(true);
    setError(null);
    try {
      const data = await graphService.getRequirementRelationships(projectId, requirement.id);
      setRelData(data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to load requirement relationships.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateRelationship = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!requirement || !targetId) return;

    setIsSubmitting(true);
    setError(null);

    try {
      await graphService.createRelationship(projectId, {
        source_id: requirement.id,
        target_id: targetId,
        type: relType,
      });
      setTargetId('');
      await fetchRelationships();
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to create relationship edge.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteEdge = async (relId: string) => {
    if (!requirement) return;
    try {
      await graphService.deleteRelationship(projectId, relId);
      await fetchRelationships();
    } catch (err: any) {
      setError('Failed to delete relationship edge.');
    }
  };

  if (!isOpen || !requirement) return null;

  const getReqTitle = (reqId: string) => {
    const found = allRequirements.find((r) => r.id === reqId);
    return found ? found.title : reqId;
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-xl shadow-2xl w-full max-w-3xl overflow-hidden flex flex-col max-h-[90vh] animate-in fade-in duration-200">
        {/* Header */}
        <div className="flex justify-between items-center px-6 py-4 border-b border-slate-800 shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-indigo-950/60 border border-indigo-800/60 flex items-center justify-center text-indigo-400">
              <GitFork className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-white truncate max-w-md">
                Requirement Knowledge Graph — {requirement.title}
              </h3>
              <p className="text-xs text-slate-400">
                Type: <span className="uppercase text-slate-300">{requirement.type}</span> • Priority:{' '}
                <span className="uppercase text-slate-300">{requirement.priority}</span>
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
        <div className="p-6 overflow-y-auto flex-1 space-y-6">
          {error && (
            <div className="flex items-start gap-3 p-3 bg-red-950/40 border border-red-800 rounded-lg text-red-300 text-sm">
              <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {/* Traceability Summary Card */}
          {requirement.source_snippet && (
            <div className="p-3 bg-slate-950/80 border border-slate-800 rounded-lg space-y-1">
              <div className="flex items-center gap-2 text-xs font-semibold text-indigo-400 uppercase tracking-wider">
                <FileText className="w-3.5 h-3.5" />
                <span>Document Traceability Context</span>
              </div>
              <p className="text-xs text-slate-300">
                Section: <span className="text-white font-medium">{requirement.source_section || 'General'}</span>
              </p>
              <p className="text-xs text-slate-400 italic font-mono bg-slate-900 p-2 rounded border border-slate-800">
                "{requirement.source_snippet}"
              </p>
            </div>
          )}

          {/* Create Relationship Form */}
          <form onSubmit={handleCreateRelationship} className="p-4 bg-slate-950/60 border border-slate-800 rounded-xl space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
              <Plus className="w-4 h-4 text-indigo-400" />
              <span>Add Graph Relationship Edge</span>
            </h4>

            <div className="grid grid-cols-1 md:grid-cols-12 gap-3">
              <div className="md:col-span-4">
                <label className="block text-xs text-slate-400 mb-1">Relationship Type</label>
                <select
                  value={relType}
                  onChange={(e) => setRelType(e.target.value as RelationshipType)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none capitalize"
                >
                  <option value="depends_on">depends_on (Dependency)</option>
                  <option value="conflicts_with">conflicts_with (Symmetric Conflict)</option>
                  <option value="derived_from">derived_from (Decomposition)</option>
                  <option value="verified_by">verified_by (QA Test Verification)</option>
                </select>
              </div>

              <div className="md:col-span-6">
                <label className="block text-xs text-slate-400 mb-1">Target Requirement Specification</label>
                <select
                  value={targetId}
                  onChange={(e) => setTargetId(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none"
                >
                  <option value="">Select target requirement...</option>
                  {allRequirements
                    .filter((r) => r.id !== requirement.id)
                    .map((r) => (
                      <option key={r.id} value={r.id}>
                        {r.title} ({r.type})
                      </option>
                    ))}
                </select>
              </div>

              <div className="md:col-span-2 flex items-end">
                <button
                  type="submit"
                  disabled={!targetId || isSubmitting}
                  className="w-full flex items-center justify-center gap-1 px-3 py-1.5 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 rounded-lg shadow-sm transition-all"
                >
                  {isSubmitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
                  <span>Connect</span>
                </button>
              </div>
            </div>
          </form>

          {/* Active Edges Breakdown */}
          {isLoading ? (
            <div className="flex items-center justify-center py-12 text-slate-400 text-sm">
              <Loader2 className="w-6 h-6 animate-spin text-indigo-400 mr-2" />
              <span>Loading graph relationships...</span>
            </div>
          ) : relData ? (
            <div className="space-y-4">
              {/* Conflicts (Symmetric) */}
              <div>
                <h5 className="text-xs font-bold uppercase tracking-wider text-amber-400 mb-2 flex items-center gap-1.5">
                  <ShieldAlert className="w-4 h-4" />
                  <span>Symmetric Conflicts ({relData.conflicts.length})</span>
                </h5>
                {relData.conflicts.length === 0 ? (
                  <p className="text-xs text-slate-500 italic">No contradictory specifications detected.</p>
                ) : (
                  <div className="space-y-2">
                    {relData.conflicts.map((edge) => {
                      const otherId = edge.source_id === requirement.id ? edge.target_id : edge.source_id;
                      return (
                        <div key={edge.id} className="flex items-center justify-between p-3 bg-amber-950/20 border border-amber-800/60 rounded-lg text-xs">
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-amber-300">Conflicts with</span>
                            <ArrowRight className="w-3.5 h-3.5 text-slate-500" />
                            <span className="text-slate-200 font-medium">{getReqTitle(otherId)}</span>
                          </div>
                          <button
                            onClick={() => handleDeleteEdge(edge.id)}
                            className="text-slate-400 hover:text-red-400 p-1 rounded transition-colors"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* Outgoing Dependencies */}
              <div>
                <h5 className="text-xs font-bold uppercase tracking-wider text-indigo-400 mb-2 flex items-center gap-1.5">
                  <ArrowRight className="w-4 h-4" />
                  <span>Outgoing Relationships ({relData.outgoing.length})</span>
                </h5>
                {relData.outgoing.length === 0 ? (
                  <p className="text-xs text-slate-500 italic">No outgoing dependencies or derivations.</p>
                ) : (
                  <div className="space-y-2">
                    {relData.outgoing.map((edge) => (
                      <div key={edge.id} className="flex items-center justify-between p-3 bg-slate-950 border border-slate-800 rounded-lg text-xs">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-indigo-300 font-semibold uppercase">{edge.type}</span>
                          <ArrowRight className="w-3.5 h-3.5 text-slate-500" />
                          <span className="text-slate-200 font-medium">{getReqTitle(edge.target_id)}</span>
                        </div>
                        <button
                          onClick={() => handleDeleteEdge(edge.id)}
                          className="text-slate-400 hover:text-red-400 p-1 rounded transition-colors"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Incoming Dependencies */}
              <div>
                <h5 className="text-xs font-bold uppercase tracking-wider text-emerald-400 mb-2 flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Incoming Relationships ({relData.incoming.length})</span>
                </h5>
                {relData.incoming.length === 0 ? (
                  <p className="text-xs text-slate-500 italic">No incoming dependencies.</p>
                ) : (
                  <div className="space-y-2">
                    {relData.incoming.map((edge) => (
                      <div key={edge.id} className="flex items-center justify-between p-3 bg-slate-950 border border-slate-800 rounded-lg text-xs">
                        <div className="flex items-center gap-2">
                          <span className="text-slate-200 font-medium">{getReqTitle(edge.source_id)}</span>
                          <ArrowRight className="w-3.5 h-3.5 text-slate-500" />
                          <span className="font-mono text-emerald-300 font-semibold uppercase">{edge.type}</span>
                        </div>
                        <button
                          onClick={() => handleDeleteEdge(edge.id)}
                          className="text-slate-400 hover:text-red-400 p-1 rounded transition-colors"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ) : null}
        </div>

        {/* Footer */}
        <div className="flex justify-end px-6 py-4 bg-slate-950/60 border-t border-slate-800 shrink-0">
          <button
            type="button"
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
