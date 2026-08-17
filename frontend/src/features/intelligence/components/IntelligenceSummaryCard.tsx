import React from 'react';
import { ShieldAlert, GitFork, AlertTriangle, Sparkles, Loader2 } from 'lucide-react';
import { IntelligenceSummaryResponse } from '../../../types';

interface IntelligenceSummaryCardProps {
  summary: IntelligenceSummaryResponse | null;
  isScanning: boolean;
  onRunScan: () => void;
  onOpenWorkspace: () => void;
}

export const IntelligenceSummaryCard: React.FC<IntelligenceSummaryCardProps> = ({
  summary,
  isScanning,
  onRunScan,
  onOpenWorkspace,
}) => {
  if (!summary) return null;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-indigo-950/80 border border-indigo-800/60 flex items-center justify-center text-indigo-400">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white">Requirement Intelligence Engine</h3>
            <p className="text-xs text-slate-400">
              Automated conflict detection & dependency discovery analytics
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={onRunScan}
            disabled={isScanning}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 rounded-lg shadow-sm transition-all"
          >
            {isScanning ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
            <span>{isScanning ? 'Scanning Workspace...' : 'Run Intelligence Scan'}</span>
          </button>

          <button
            onClick={onOpenWorkspace}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-slate-200 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-lg transition-all"
          >
            <span>Review Suggestions</span>
          </button>
        </div>
      </div>

      {/* Analytics Badges Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
        <div className="p-3 bg-slate-950/60 border border-slate-800/80 rounded-lg">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-amber-400 mb-1">
            <ShieldAlert className="w-3.5 h-3.5" />
            <span>Active Conflicts</span>
          </div>
          <p className="text-lg font-bold text-white">{summary.total_conflicts}</p>
        </div>

        <div className="p-3 bg-slate-950/60 border border-slate-800/80 rounded-lg">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-indigo-400 mb-1">
            <GitFork className="w-3.5 h-3.5" />
            <span>Pending Dependencies</span>
          </div>
          <p className="text-lg font-bold text-white">{summary.unresolved_dependency_suggestions}</p>
        </div>

        <div className="p-3 bg-slate-950/60 border border-slate-800/80 rounded-lg">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-amber-500 mb-1">
            <AlertTriangle className="w-3.5 h-3.5" />
            <span>Orphan Specifications</span>
          </div>
          <p className="text-lg font-bold text-white">{summary.orphan_requirements_count}</p>
        </div>

        <div className="p-3 bg-slate-950/60 border border-slate-800/80 rounded-lg">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-emerald-400 mb-1">
            <Sparkles className="w-3.5 h-3.5" />
            <span>High Confidence Issues</span>
          </div>
          <p className="text-lg font-bold text-white">{summary.high_confidence_issues_count}</p>
        </div>
      </div>
    </div>
  );
};
