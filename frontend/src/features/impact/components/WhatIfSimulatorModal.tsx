import React, { useState, useEffect } from 'react';
import { Zap, X, AlertTriangle, Loader2, FileText, CheckCircle } from 'lucide-react';
import { impactService } from '../api/impactService';
import { Requirement, RequirementPriority, RequirementStatus, RequirementType, WhatIfSimulationResponse } from '../../../types';

interface WhatIfSimulatorModalProps {
  isOpen: boolean;
  projectId: string;
  requirement: Requirement | null;
  requirements: Requirement[];
  onClose: () => void;
  onCommitChange?: (reqId: string, title: string, desc: string) => Promise<void>;
}

export const WhatIfSimulatorModal: React.FC<WhatIfSimulatorModalProps> = ({
  isOpen,
  projectId,
  requirement,
  requirements,
  onClose,
  onCommitChange,
}) => {
  const [targetId, setTargetId] = useState<string>('');
  const [proposedTitle, setProposedTitle] = useState<string>('');
  const [proposedDesc, setProposedDesc] = useState<string>('');
  const [proposedType, setProposedType] = useState<RequirementType>('functional');
  const [proposedPriority, setProposedPriority] = useState<RequirementPriority>('medium');
  const [proposedStatus, setProposedStatus] = useState<RequirementStatus>('draft');

  const [simulation, setSimulation] = useState<WhatIfSimulationResponse | null>(null);
  const [isSimulating, setIsSimulating] = useState<boolean>(false);
  const [isCommitting, setIsCommitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  useEffect(() => {
    if (requirement) {
      setTargetId(requirement.id);
      setProposedTitle(requirement.title);
      setProposedDesc(requirement.description);
      setProposedType(requirement.type);
      setProposedPriority(requirement.priority);
      setProposedStatus(requirement.status);
    } else if (requirements.length > 0) {
      const first = requirements[0];
      setTargetId(first.id);
      setProposedTitle(first.title);
      setProposedDesc(first.description);
      setProposedType(first.type);
      setProposedPriority(first.priority);
      setProposedStatus(first.status);
    }
    setSimulation(null);
    setError(null);
    setSuccessMsg(null);
  }, [isOpen, requirement, requirements]);

  const handleSelectRequirement = (id: string) => {
    setTargetId(id);
    const found = requirements.find((r) => r.id === id);
    if (found) {
      setProposedTitle(found.title);
      setProposedDesc(found.description);
      setProposedType(found.type);
      setProposedPriority(found.priority);
      setProposedStatus(found.status);
    }
  };

  const handleRunSimulation = async () => {
    if (!proposedTitle.trim() || !proposedDesc.trim()) return;
    setIsSimulating(true);
    setError(null);
    setSuccessMsg(null);
    try {
      const res = await impactService.simulateWhatIf(projectId, {
        requirement_id: targetId || undefined,
        proposed_title: proposedTitle,
        proposed_description: proposedDesc,
        proposed_type: proposedType,
        proposed_priority: proposedPriority,
        proposed_status: proposedStatus,
      });
      setSimulation(res);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'What-If simulation failed.');
    } finally {
      setIsSimulating(false);
    }
  };

  const handleCommit = async () => {
    if (!targetId || !onCommitChange) return;
    setIsCommitting(true);
    setError(null);
    try {
      await onCommitChange(targetId, proposedTitle, proposedDesc);
      setSuccessMsg('Requirement edits committed successfully.');
      setTimeout(() => {
        onClose();
      }, 1000);
    } catch (err: any) {
      setError('Failed to commit requirement edits.');
    } finally {
      setIsCommitting(false);
    }
  };

  if (!isOpen) return null;

  const getRiskBadge = (score: number) => {
    if (score >= 70) return 'text-red-400 bg-red-950/80 border-red-800';
    if (score >= 36) return 'text-amber-400 bg-amber-950/80 border-amber-800';
    return 'text-emerald-400 bg-emerald-950/80 border-emerald-800';
  };

  const getChangeTypeBadge = (ct: string) => {
    if (ct === 'behavioral') return 'text-rose-400 bg-rose-950/80 border-rose-800';
    if (ct === 'metadata') return 'text-amber-400 bg-amber-950/80 border-amber-800';
    return 'text-slate-400 bg-slate-800 border-slate-700';
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-xl shadow-2xl w-full max-w-5xl overflow-hidden flex flex-col max-h-[92vh] animate-in fade-in duration-200">
        {/* Header */}
        <div className="flex justify-between items-center px-6 py-4 border-b border-slate-800 shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-rose-950/60 border border-rose-800/60 flex items-center justify-center text-rose-400">
              <Zap className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-white">What-If Change Impact Simulator</h3>
              <p className="text-xs text-slate-400">
                Test draft requirement edits in memory without persisting changes to PostgreSQL
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

        {/* Content Body: Split Layout */}
        <div className="p-6 overflow-y-auto flex-1 grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left Column: Draft Proposed Form */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-bold text-white">1. Select Specification & Propose Draft Edit</h4>
              <span className="text-[10px] uppercase font-mono text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800">
                Ephemeral Mode
              </span>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-1">Target Specification:</label>
              <select
                value={targetId}
                onChange={(e) => handleSelectRequirement(e.target.value)}
                className="w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-xs text-white focus:border-rose-500 focus:outline-none"
              >
                {requirements.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.title}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-1">Proposed Title:</label>
              <input
                type="text"
                value={proposedTitle}
                onChange={(e) => setProposedTitle(e.target.value)}
                className="w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-xs text-white focus:border-rose-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-400 mb-1">Proposed Description / Constraints:</label>
              <textarea
                rows={4}
                value={proposedDesc}
                onChange={(e) => setProposedDesc(e.target.value)}
                className="w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-xs text-white focus:border-rose-500 focus:outline-none font-mono"
              />
            </div>

            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Type:</label>
                <select
                  value={proposedType}
                  onChange={(e) => setProposedType(e.target.value as RequirementType)}
                  className="w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-xs text-white"
                >
                  <option value="functional">Functional</option>
                  <option value="non_functional">Non-Functional</option>
                  <option value="system">System</option>
                  <option value="user">User</option>
                  <option value="business">Business</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Priority:</label>
                <select
                  value={proposedPriority}
                  onChange={(e) => setProposedPriority(e.target.value as RequirementPriority)}
                  className="w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-xs text-white"
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="critical">Critical</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Status:</label>
                <select
                  value={proposedStatus}
                  onChange={(e) => setProposedStatus(e.target.value as RequirementStatus)}
                  className="w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 text-xs text-white"
                >
                  <option value="draft">Draft</option>
                  <option value="in_review">In Review</option>
                  <option value="approved">Approved</option>
                </select>
              </div>
            </div>

            <button
              onClick={handleRunSimulation}
              disabled={isSimulating}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 text-xs font-bold text-white bg-rose-600 hover:bg-rose-500 rounded-lg shadow-sm transition-all"
            >
              {isSimulating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />}
              <span>{isSimulating ? 'Simulating Impact...' : 'Run What-If Simulation'}</span>
            </button>
          </div>

          {/* Right Column: Real-time Analysis & Risk Gauges */}
          <div className="space-y-4 border-t lg:border-t-0 lg:border-l border-slate-800 pt-4 lg:pt-0 lg:pl-6">
            <h4 className="text-sm font-bold text-white">2. Simulation Analysis & Downstream Impact</h4>

            {error && (
              <div className="p-3 bg-red-950/40 border border-red-800 rounded-lg text-red-300 text-xs flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {successMsg && (
              <div className="p-3 bg-emerald-950/40 border border-emerald-800 rounded-lg text-emerald-300 text-xs flex items-center gap-2">
                <CheckCircle className="w-4 h-4 shrink-0" />
                <span>{successMsg}</span>
              </div>
            )}

            {!simulation ? (
              <div className="flex flex-col items-center justify-center py-20 text-slate-500 text-xs text-center space-y-2">
                <FileText className="w-8 h-8 text-slate-600" />
                <p>Click "Run What-If Simulation" to compute downstream impact and risk score.</p>
              </div>
            ) : (
              <div className="space-y-4 animate-in fade-in duration-150">
                {/* Risk Gauge Header */}
                <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl flex items-center justify-between">
                  <div>
                    <span className="text-xs text-slate-400 block mb-0.5">Predicted Risk Score:</span>
                    <span className={`text-xl font-bold px-2.5 py-1 rounded border ${getRiskBadge(simulation.risk_score)}`}>
                      {simulation.risk_score} / 100 ({simulation.risk_level})
                    </span>
                  </div>

                  <div>
                    <span className="text-xs text-slate-400 block mb-0.5">Change Classification:</span>
                    <span className={`text-xs font-bold uppercase px-2.5 py-1 rounded border ${getChangeTypeBadge(simulation.change_type)}`}>
                      {simulation.change_type}
                    </span>
                  </div>
                </div>

                {/* Direct & Transitive Affected Counts */}
                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div className="p-3 bg-slate-950/60 border border-slate-800 rounded-lg">
                    <span className="text-slate-400 font-medium">Direct Affected (Depth 1):</span>
                    <p className="text-base font-bold text-white mt-0.5">{simulation.direct_affected_count}</p>
                  </div>
                  <div className="p-3 bg-slate-950/60 border border-slate-800 rounded-lg">
                    <span className="text-slate-400 font-medium">Transitive (Depth &gt; 1):</span>
                    <p className="text-base font-bold text-white mt-0.5">{simulation.transitive_affected_count}</p>
                  </div>
                </div>

                {/* Affected List */}
                {simulation.direct_affected_requirements.length > 0 && (
                  <div className="space-y-2">
                    <h5 className="text-xs font-bold text-slate-300">Impacted Specifications:</h5>
                    <div className="space-y-1.5 max-h-36 overflow-y-auto pr-1 text-xs">
                      {simulation.direct_affected_requirements.map((item) => (
                        <div key={item.requirement_id} className="p-2 bg-slate-950 border border-slate-800 rounded flex items-center justify-between">
                          <span className="font-semibold text-white truncate max-w-xs">{item.title}</span>
                          <span className="text-[10px] text-slate-400 font-mono">Depth {item.depth}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Evidence Notes */}
                <div className="p-3 bg-rose-950/20 border border-rose-900/40 rounded-lg text-xs space-y-1 text-rose-200">
                  <p className="font-bold text-rose-300">Evidence & Reasoning:</p>
                  {simulation.evidence_reasoning.map((note, idx) => (
                    <p key={idx} className="flex items-start gap-1">
                      <span className="text-rose-400">•</span> <span>{note}</span>
                    </p>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-between items-center px-6 py-4 bg-slate-950/60 border-t border-slate-800 shrink-0">
          <span className="text-xs text-slate-500 italic">
            What-If runs entirely in memory. Zero database rows are modified.
          </span>

          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="px-4 py-2 text-xs font-medium text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors"
            >
              Close
            </button>

            {onCommitChange && targetId && (
              <button
                onClick={handleCommit}
                disabled={isCommitting || !proposedTitle.trim()}
                className="flex items-center gap-1.5 px-4 py-2 text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 rounded-lg shadow-sm transition-colors"
              >
                {isCommitting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <CheckCircle className="w-3.5 h-3.5" />}
                <span>Commit Edits to Requirement</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
