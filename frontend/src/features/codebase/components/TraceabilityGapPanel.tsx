import React, { useState } from 'react';
import { AlertCircle, AlertTriangle, Info, ShieldAlert, Sparkles, Filter } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { TraceabilityGapsList } from '../types/traceability.types';

interface TraceabilityGapPanelProps {
  gapsData?: TraceabilityGapsList | null;
  onSuggestTest?: (requirementId: string, reqTitle: string) => void;
}

export const TraceabilityGapPanel: React.FC<TraceabilityGapPanelProps> = ({
  gapsData,
  onSuggestTest,
}) => {
  const [severityFilter, setSeverityFilter] = useState<string>('ALL');

  if (!gapsData || gapsData.gaps.length === 0) {
    return (
      <div className="bg-slate-900/60 border border-slate-800 rounded-3xl p-8 text-center space-y-3">
        <div className="mx-auto w-12 h-12 rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
          <Info className="h-6 w-6" />
        </div>
        <h3 className="text-sm font-bold text-slate-100">No Traceability Gaps Detected</h3>
        <p className="text-xs text-slate-400 max-w-md mx-auto">
          All mapped requirements currently have corresponding implementation files and test artifacts.
        </p>
      </div>
    );
  }

  const filteredGaps = gapsData.gaps.filter(
    (gap) => severityFilter === 'ALL' || gap.severity === severityFilter
  );

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case 'CRITICAL':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-extrabold bg-red-500/15 text-red-400 border border-red-500/30">
            <ShieldAlert className="h-3 w-3" /> CRITICAL
          </span>
        );
      case 'HIGH':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-extrabold bg-orange-500/15 text-orange-400 border border-orange-500/30">
            <AlertTriangle className="h-3 w-3" /> HIGH
          </span>
        );
      case 'MEDIUM':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-extrabold bg-amber-500/15 text-amber-400 border border-amber-500/30">
            <AlertCircle className="h-3 w-3" /> MEDIUM
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-extrabold bg-slate-800 text-slate-300 border border-slate-700">
            LOW
          </span>
        );
    }
  };

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-3xl p-5 space-y-4">
      {/* Header & Filter */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
        <div>
          <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-amber-400" />
            Coverage & Traceability Gaps ({gapsData.total_gaps})
          </h3>
          <p className="text-xs text-slate-400">
            Identified requirements lacking implementation, missing test verification, or missing SLA/security tests.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-slate-400" />
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
          >
            <option value="ALL">All Severities</option>
            <option value="CRITICAL">Critical</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
            <option value="LOW">Low</option>
          </select>
        </div>
      </div>

      {/* Gap Cards */}
      <div className="space-y-3">
        {filteredGaps.map((gap, idx) => (
          <div
            key={`${gap.requirement_id}-${idx}`}
            className="bg-slate-950/70 border border-slate-800 rounded-2xl p-4 space-y-2 hover:border-slate-700 transition-colors"
          >
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <span className="font-mono text-[11px] font-bold text-indigo-400 bg-indigo-950/60 px-2 py-0.5 rounded border border-indigo-800/40">
                  {gap.original_req_id || gap.requirement_id.slice(0, 8)}
                </span>
                <h4 className="text-xs font-bold text-slate-100">{gap.title}</h4>
              </div>
              <div className="flex items-center gap-2">
                <span className="uppercase text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-slate-900 text-slate-400 border border-slate-800">
                  {gap.gap_type.replace(/_/g, ' ')}
                </span>
                {getSeverityBadge(gap.severity)}
              </div>
            </div>

            <p className="text-xs text-slate-300">{gap.description}</p>

            <div className="bg-slate-900/80 border border-slate-800/80 rounded-xl p-2.5 flex items-start justify-between gap-3 text-[11px]">
              <div className="text-slate-400">
                <strong className="text-slate-200">Recommendation: </strong>
                {gap.recommendation}
              </div>

              {onSuggestTest && gap.gap_type === 'IMPLEMENTED_NOT_TESTED' && (
                <Button
                  size="sm"
                  onClick={() => onSuggestTest(gap.requirement_id, gap.title)}
                  className="bg-indigo-600 hover:bg-indigo-700 text-white text-[10px] font-bold px-2.5 py-1 shrink-0"
                >
                  <Sparkles className="h-3 w-3 mr-1" /> Suggest Test
                </Button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
