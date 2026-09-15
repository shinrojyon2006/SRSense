import React, { useState } from 'react';
import { CheckCircle2, AlertTriangle, AlertCircle, HelpCircle } from 'lucide-react';
import { FindingComparisonItem } from '../types/codeEvaluation.types';

interface FindingComparisonProps {
  resolved: FindingComparisonItem[];
  remaining: FindingComparisonItem[];
  newFindings: FindingComparisonItem[];
  unchanged: FindingComparisonItem[];
}

export const FindingComparison: React.FC<FindingComparisonProps> = ({
  resolved,
  remaining,
  newFindings,
  unchanged,
}) => {
  const [activeTab, setActiveTab] = useState<'resolved' | 'remaining' | 'new' | 'unchanged'>('resolved');

  const renderFindingList = (items: FindingComparisonItem[], emptyText: string) => {
    if (items.length === 0) {
      return (
        <div className="p-6 text-center text-slate-500 text-xs font-mono bg-slate-950/40 rounded-xl border border-slate-800/50">
          {emptyText}
        </div>
      );
    }

    return (
      <div className="space-y-2.5 max-h-72 overflow-y-auto pr-1">
        {items.map((item, idx) => (
          <div
            key={idx}
            className="p-3.5 bg-slate-950/80 rounded-xl border border-slate-800/80 space-y-1.5"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono font-bold text-indigo-400 bg-indigo-950/60 px-2 py-0.5 rounded-md border border-indigo-800/50">
                  {item.rule_id}
                </span>
                <span className="text-xs font-semibold text-slate-200">{item.title}</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded-full bg-slate-800 text-slate-300">
                  {item.category}
                </span>
                <span
                  className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded-full ${
                    item.severity === 'critical'
                      ? 'bg-red-500/20 text-red-400 border border-red-500/30'
                      : item.severity === 'warning'
                      ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                      : 'bg-slate-700 text-slate-300'
                  }`}
                >
                  {item.severity}
                </span>
              </div>
            </div>

            <p className="text-xs text-slate-400 leading-relaxed">{item.description}</p>

            <div className="text-[11px] font-mono text-slate-500 flex items-center gap-2 pt-1 border-t border-slate-900">
              <span>{item.file_path}</span>
              {item.line_number && <span>Line {item.line_number}</span>}
            </div>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="space-y-3 bg-slate-900/60 border border-slate-800/80 p-4 rounded-2xl">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300">
          Static Scan Finding Comparison
        </h4>
        <div className="flex gap-1.5 bg-slate-950 p-1 rounded-xl border border-slate-800">
          <button
            onClick={() => setActiveTab('resolved')}
            className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 ${
              activeTab === 'resolved'
                ? 'bg-emerald-600 text-white shadow-xs'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <CheckCircle2 className="h-3.5 w-3.5 text-emerald-300" /> Resolved ({resolved.length})
          </button>

          <button
            onClick={() => setActiveTab('remaining')}
            className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 ${
              activeTab === 'remaining'
                ? 'bg-amber-600 text-white shadow-xs'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <AlertTriangle className="h-3.5 w-3.5 text-amber-300" /> Remaining ({remaining.length})
          </button>

          <button
            onClick={() => setActiveTab('new')}
            className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 ${
              activeTab === 'new'
                ? 'bg-red-600 text-white shadow-xs'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <AlertCircle className="h-3.5 w-3.5 text-red-300" /> New ({newFindings.length})
          </button>

          <button
            onClick={() => setActiveTab('unchanged')}
            className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 ${
              activeTab === 'unchanged'
                ? 'bg-slate-700 text-white shadow-xs'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <HelpCircle className="h-3.5 w-3.5 text-slate-300" /> Unchanged ({unchanged.length})
          </button>
        </div>
      </div>

      <div>
        {activeTab === 'resolved' &&
          renderFindingList(resolved, 'No findings were resolved by this change.')}
        {activeTab === 'remaining' &&
          renderFindingList(remaining, 'No target findings remain open.')}
        {activeTab === 'new' &&
          renderFindingList(newFindings, 'Zero new findings were introduced. Code state is clean!')}
        {activeTab === 'unchanged' &&
          renderFindingList(unchanged, 'No relevant unchanged findings detected.')}
      </div>
    </div>
  );
};
