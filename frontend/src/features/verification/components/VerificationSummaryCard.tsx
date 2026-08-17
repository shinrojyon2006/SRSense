import React from 'react';
import { ShieldCheck, CheckSquare, AlertTriangle, FileCode2 } from 'lucide-react';
import { ProjectVerificationSummaryResponse } from '../../../types';

interface VerificationSummaryCardProps {
  summary: ProjectVerificationSummaryResponse | null;
}

export const VerificationSummaryCard: React.FC<VerificationSummaryCardProps> = ({ summary }) => {
  if (!summary) return null;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg bg-emerald-950/80 border border-emerald-800/60 flex items-center justify-center text-emerald-400">
          <ShieldCheck className="w-5 h-5" />
        </div>
        <div>
          <h3 className="text-sm font-bold text-white">Requirement Verification Compiler</h3>
          <p className="text-xs text-slate-400">
            Automated test case synthesis & execution evidence coverage metrics
          </p>
        </div>
      </div>

      {/* 3 Coverage Percentage Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
        <div className="p-3 bg-slate-950/60 border border-slate-800/80 rounded-lg">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-semibold text-indigo-400 flex items-center gap-1">
              <FileCode2 className="w-3.5 h-3.5" /> Verification Readiness
            </span>
            <span className="text-xs font-bold text-indigo-300">
              {summary.verification_readiness_percentage}%
            </span>
          </div>
          <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
            <div
              className="bg-indigo-500 h-1.5 rounded-full"
              style={{ width: `${summary.verification_readiness_percentage}%` }}
            />
          </div>
          <p className="text-[10px] text-slate-500 mt-1">Explicit & measurable specs</p>
        </div>

        <div className="p-3 bg-slate-950/60 border border-slate-800/80 rounded-lg">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-semibold text-amber-400 flex items-center gap-1">
              <CheckSquare className="w-3.5 h-3.5" /> Test Gen Coverage
            </span>
            <span className="text-xs font-bold text-amber-300">
              {summary.test_generation_coverage_percentage}%
            </span>
          </div>
          <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
            <div
              className="bg-amber-500 h-1.5 rounded-full"
              style={{ width: `${summary.test_generation_coverage_percentage}%` }}
            />
          </div>
          <p className="text-[10px] text-slate-500 mt-1">Synthesized test suites</p>
        </div>

        <div className="p-3 bg-slate-950/60 border border-slate-800/80 rounded-lg">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-semibold text-emerald-400 flex items-center gap-1">
              <ShieldCheck className="w-3.5 h-3.5" /> Actual Verified
            </span>
            <span className="text-xs font-bold text-emerald-300">
              {summary.actual_verification_coverage_percentage}%
            </span>
          </div>
          <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
            <div
              className="bg-emerald-500 h-1.5 rounded-full"
              style={{ width: `${summary.actual_verification_coverage_percentage}%` }}
            />
          </div>
          <p className="text-[10px] text-slate-500 mt-1">Passing test execution evidence</p>
        </div>
      </div>

      {/* Verification Status Counters */}
      <div className="grid grid-cols-4 gap-2 pt-1 text-center text-xs">
        <div className="p-2 bg-slate-950 border border-slate-800/60 rounded">
          <span className="text-slate-400 block text-[10px]">Verified</span>
          <span className="font-bold text-emerald-400">{summary.status_breakdown['verified'] || 0}</span>
        </div>

        <div className="p-2 bg-slate-950 border border-slate-800/60 rounded">
          <span className="text-slate-400 block text-[10px]">Ready</span>
          <span className="font-bold text-indigo-400">{summary.status_breakdown['ready_for_verification'] || 0}</span>
        </div>

        <div className="p-2 bg-slate-950 border border-slate-800/60 rounded">
          <span className="text-slate-400 block text-[10px]">Partially Ready</span>
          <span className="font-bold text-amber-400">{summary.status_breakdown['partially_ready'] || 0}</span>
        </div>

        <div className="p-2 bg-slate-950 border border-slate-800/60 rounded">
          <span className="text-slate-400 block text-[10px]">Unverified / Gap</span>
          <span className="font-bold text-red-400">{summary.status_breakdown['unverified'] || 0}</span>
        </div>
      </div>

      {summary.unverified_requirements_gaps.length > 0 && (
        <div className="p-2.5 bg-amber-950/30 border border-amber-900/50 rounded-lg text-xs text-amber-300 flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
            <span>{summary.unverified_requirements_gaps.length} specification(s) have non-measurable verification gaps.</span>
          </div>
        </div>
      )}
    </div>
  );
};
