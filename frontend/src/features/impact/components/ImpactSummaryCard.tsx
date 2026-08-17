import React from 'react';
import { Activity, AlertTriangle, ShieldCheck, Zap } from 'lucide-react';
import { ProjectRiskSummaryResponse } from '../../../types';

interface ImpactSummaryCardProps {
  summary: ProjectRiskSummaryResponse | null;
  onOpenWhatIfModal: () => void;
}

export const ImpactSummaryCard: React.FC<ImpactSummaryCardProps> = ({
  summary,
  onOpenWhatIfModal,
}) => {
  if (!summary) return null;

  const getRiskColor = (score: number) => {
    if (score >= 70) return 'text-red-400 bg-red-950/60 border-red-800/60';
    if (score >= 36) return 'text-amber-400 bg-amber-950/60 border-amber-800/60';
    return 'text-emerald-400 bg-emerald-950/60 border-emerald-800/60';
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-rose-950/80 border border-rose-800/60 flex items-center justify-center text-rose-400">
            <Activity className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white">Change Impact & Risk Simulator</h3>
            <p className="text-xs text-slate-400">
              Graph propagation analysis & ephemeral What-If change predictions
            </p>
          </div>
        </div>

        <button
          onClick={onOpenWhatIfModal}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-white bg-rose-600 hover:bg-rose-500 rounded-lg shadow-sm transition-all"
        >
          <Zap className="w-3.5 h-3.5" />
          <span>Launch What-If Simulator</span>
        </button>
      </div>

      {/* Analytics Badges */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
        <div className="p-3 bg-slate-950/60 border border-slate-800/80 rounded-lg">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-400 mb-1">
            <Activity className="w-3.5 h-3.5" />
            <span>Avg Risk Score</span>
          </div>
          <p className="text-lg font-bold text-white">
            <span className={`px-2 py-0.5 rounded border text-sm ${getRiskColor(summary.average_project_risk_score)}`}>
              {summary.average_project_risk_score} / 100
            </span>
          </p>
        </div>

        <div className="p-3 bg-slate-950/60 border border-slate-800/80 rounded-lg">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-red-400 mb-1">
            <AlertTriangle className="w-3.5 h-3.5" />
            <span>High Risk Specs</span>
          </div>
          <p className="text-lg font-bold text-white">{summary.high_risk_requirements_count}</p>
        </div>

        <div className="p-3 bg-slate-950/60 border border-slate-800/80 rounded-lg">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-emerald-400 mb-1">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Low Risk Specs</span>
          </div>
          <p className="text-lg font-bold text-white">{summary.risk_level_breakdown['LOW'] || 0}</p>
        </div>

        <div className="p-3 bg-slate-950/60 border border-slate-800/80 rounded-lg">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-indigo-400 mb-1">
            <Zap className="w-3.5 h-3.5" />
            <span>Simulator Status</span>
          </div>
          <p className="text-xs font-semibold text-emerald-400 mt-1">Ready (Ephemeral Non-Persistent)</p>
        </div>
      </div>
    </div>
  );
};
