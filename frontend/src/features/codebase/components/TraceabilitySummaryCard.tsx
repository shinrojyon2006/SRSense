import React from 'react';
import { Network, CheckCircle, Layers, TestTube2, RotateCw } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { TraceabilitySummary } from '../types/traceability.types';

interface TraceabilitySummaryCardProps {
  summary: TraceabilitySummary | null;
  onDiscoverTests: () => void;
  isDiscovering: boolean;
}

export const TraceabilitySummaryCard: React.FC<TraceabilitySummaryCardProps> = ({
  summary,
  onDiscoverTests,
  isDiscovering,
}) => {
  if (!summary) return null;

  const renderHealthBadge = (health: string) => {
    const h = health.toUpperCase();
    if (h === 'HEALTHY') {
      return (
        <span className="px-3 py-1 rounded-full text-xs font-extrabold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          HEALTHY
        </span>
      );
    }
    if (h === 'NEEDS_ATTENTION') {
      return (
        <span className="px-3 py-1 rounded-full text-xs font-extrabold bg-amber-500/10 text-amber-400 border border-amber-500/20">
          NEEDS ATTENTION
        </span>
      );
    }
    return (
      <span className="px-3 py-1 rounded-full text-xs font-extrabold bg-red-500/10 text-red-400 border border-red-500/20">
        AT RISK
      </span>
    );
  };

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-3xl p-6 shadow-xl backdrop-blur-sm space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-indigo-950/60 text-indigo-400 rounded-2xl border border-indigo-800/50">
            <Network className="h-6 w-6" />
          </div>
          <div>
            <div className="flex items-center gap-2.5">
              <h3 className="text-base font-bold text-slate-100">
                Requirement → Code → Test Traceability Matrix
              </h3>
              {renderHealthBadge(summary.health_status)}
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Multi-Layer Engineering Coverage & Gap Intelligence Engine (Sprint 2.4)
            </p>
          </div>
        </div>

        <Button
          onClick={onDiscoverTests}
          disabled={isDiscovering}
          className="bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold shrink-0 px-4 py-2"
        >
          {isDiscovering ? (
            <>
              <RotateCw className="h-4 w-4 mr-2 animate-spin" /> Discovering Tests...
            </>
          ) : (
            <>
              <TestTube2 className="h-4 w-4 mr-2" /> Discover Tests & Link Matrix
            </>
          )}
        </Button>
      </div>

      {/* Grid Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
        {/* Score Gauge */}
        <div className="bg-slate-950/60 p-4 rounded-2xl border border-slate-800/80 flex flex-col justify-between">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
            Traceability Score
          </span>
          <div className="my-2 flex items-baseline gap-1">
            <span className="text-3xl font-extrabold text-indigo-400">
              {summary.traceability_score}
            </span>
            <span className="text-xs text-slate-500 font-bold">/ 100</span>
          </div>
          <span className="text-[10px] text-slate-500">Based on coverage & risk penalties</span>
        </div>

        {/* Requirements Total & Code */}
        <div className="bg-slate-950/60 p-4 rounded-2xl border border-slate-800/80 flex flex-col justify-between">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
            <Layers className="h-3.5 w-3.5 text-blue-400" /> Code Implementation
          </span>
          <div className="my-2 flex items-baseline gap-2">
            <span className="text-2xl font-extrabold text-slate-200">
              {summary.requirements_with_code}
            </span>
            <span className="text-xs text-slate-400">/ {summary.total_requirements} reqs</span>
          </div>
          <span className="text-[10px] text-emerald-400 font-semibold">
            {summary.code_coverage_pct}% Implemented
          </span>
        </div>

        {/* Test Coverage */}
        <div className="bg-slate-950/60 p-4 rounded-2xl border border-slate-800/80 flex flex-col justify-between">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
            <TestTube2 className="h-3.5 w-3.5 text-purple-400" /> Test Artifacts
          </span>
          <div className="my-2 flex items-baseline gap-2">
            <span className="text-2xl font-extrabold text-slate-200">
              {summary.requirements_with_tests}
            </span>
            <span className="text-xs text-slate-400">/ {summary.total_requirements} reqs</span>
          </div>
          <span className="text-[10px] text-purple-400 font-semibold">
            {summary.test_coverage_pct}% Tested
          </span>
        </div>

        {/* Fully Traced */}
        <div className="bg-slate-950/60 p-4 rounded-2xl border border-slate-800/80 flex flex-col justify-between">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
            <CheckCircle className="h-3.5 w-3.5 text-emerald-400" /> Fully Traced R→C→T
          </span>
          <div className="my-2 flex items-baseline gap-2">
            <span className="text-2xl font-extrabold text-emerald-400">
              {summary.fully_traced_count}
            </span>
            <span className="text-xs text-slate-400">/ {summary.total_requirements} reqs</span>
          </div>
          <span className="text-[10px] text-emerald-400 font-semibold">
            {summary.full_traceability_pct}% End-to-End Traced
          </span>
        </div>
      </div>

      {/* Progress Bars */}
      <div className="space-y-3 pt-2">
        <div>
          <div className="flex justify-between text-xs font-semibold text-slate-300 mb-1">
            <span>Full Traceability (Requirement → Code → Test)</span>
            <span className="text-emerald-400 font-bold">{summary.full_traceability_pct}%</span>
          </div>
          <div className="h-2 w-full bg-slate-950 rounded-full overflow-hidden border border-slate-800">
            <div
              className="h-full bg-gradient-to-r from-indigo-500 via-purple-500 to-emerald-400 transition-all duration-500"
              style={{ width: `${summary.full_traceability_pct}%` }}
            />
          </div>
        </div>
      </div>
    </div>
  );
};
