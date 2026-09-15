import React from 'react';
import { X, ArrowDown, FileCode, TestTube2, ShieldCheck, Sparkles, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { RequirementTraceabilityItem } from '../types/traceability.types';

interface RequirementTraceabilityDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  item: RequirementTraceabilityItem | null;
  onSuggestTest: (item: RequirementTraceabilityItem) => void;
}

export const RequirementTraceabilityDrawer: React.FC<RequirementTraceabilityDrawerProps> = ({
  isOpen,
  onClose,
  item,
  onSuggestTest,
}) => {
  if (!isOpen || !item) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/75 backdrop-blur-xs">
      <div className="bg-slate-950 border-l border-slate-800 w-full max-w-xl h-full flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="p-5 border-b border-slate-800 flex items-center justify-between bg-slate-900/50">
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs font-bold text-indigo-400 bg-indigo-950 px-2 py-0.5 rounded border border-indigo-800/50">
                {item.original_req_id || item.requirement_id.slice(0, 8)}
              </span>
              <h3 className="text-sm font-bold text-slate-100">{item.title}</h3>
            </div>
            <p className="text-xs text-slate-400 mt-1">Requirement → Code → Test Evidence Pipeline</p>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose} className="rounded-full p-2 text-slate-400 hover:text-white">
            <X className="h-5 w-5" />
          </Button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Risk Banner */}
          {item.risk && (
            <div className="p-3.5 bg-amber-950/40 border border-amber-800/60 rounded-2xl flex items-center gap-2.5 text-xs text-amber-300">
              <AlertCircle className="h-4 w-4 text-amber-400 shrink-0" />
              <span>{item.risk}</span>
            </div>
          )}

          {/* R -> C -> T Visual Pipeline */}
          <div className="space-y-4">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Traceability Pipeline Visualization
            </h4>

            {/* NODE 1: Requirement */}
            <div className="bg-slate-900 border border-indigo-500/40 p-4 rounded-2xl space-y-1">
              <div className="flex items-center justify-between text-xs font-bold text-indigo-400 uppercase tracking-wider">
                <span>1. Requirement Contract</span>
                <span className="text-[10px] bg-indigo-950 px-2 py-0.5 rounded border border-indigo-800">
                  {item.requirement_type}
                </span>
              </div>
              <div className="text-sm font-semibold text-slate-100">{item.title}</div>
            </div>

            <ArrowDown className="h-5 w-5 mx-auto text-indigo-400" />

            {/* NODE 2: Code Implementation */}
            <div className="bg-slate-900 border border-blue-500/40 p-4 rounded-2xl space-y-2">
              <div className="flex items-center justify-between text-xs font-bold text-blue-400 uppercase tracking-wider">
                <span className="flex items-center gap-1.5">
                  <FileCode className="h-4 w-4" /> 2. Code Implementation
                </span>
                <span className="text-[10px] font-mono">
                  {item.has_code ? `${item.linked_code_files.length} file(s)` : 'NO CODE'}
                </span>
              </div>

              {item.linked_code_files.length > 0 ? (
                <div className="space-y-1 font-mono text-xs">
                  {item.linked_code_files.map((file, idx) => (
                    <div key={idx} className="p-2 bg-slate-950 rounded-xl border border-slate-800 text-slate-300">
                      {file}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-3 bg-red-950/30 border border-red-900/40 rounded-xl text-xs text-red-300 italic">
                  No source code implementation linked to this requirement.
                </div>
              )}
            </div>

            <ArrowDown className="h-5 w-5 mx-auto text-purple-400" />

            {/* NODE 3: Test Artifact */}
            <div className="bg-slate-900 border border-purple-500/40 p-4 rounded-2xl space-y-2">
              <div className="flex items-center justify-between text-xs font-bold text-purple-400 uppercase tracking-wider">
                <span className="flex items-center gap-1.5">
                  <TestTube2 className="h-4 w-4" /> 3. Verification Test Artifact
                </span>
                <span className="text-[10px] font-mono">
                  {item.has_test ? `${item.linked_test_names.length} test(s)` : 'NO TEST'}
                </span>
              </div>

              {item.linked_test_names.length > 0 ? (
                <div className="space-y-1 font-mono text-xs">
                  {item.linked_test_names.map((testName, idx) => (
                    <div key={idx} className="p-2 bg-slate-950 rounded-xl border border-slate-800 text-slate-300">
                      {testName}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-3 bg-amber-950/30 border border-amber-900/40 rounded-xl text-xs text-amber-300 italic">
                  No automated test coverage artifact linked to this requirement.
                </div>
              )}
            </div>
          </div>

          {/* Evidence Explanations */}
          {item.evidence && item.evidence.length > 0 && (
            <div className="bg-slate-900/60 border border-slate-800 p-4 rounded-2xl space-y-2">
              <div className="flex items-center gap-2 text-xs font-bold text-slate-300 uppercase tracking-wider">
                <ShieldCheck className="h-4 w-4 text-emerald-400" /> Traceability Evidence
              </div>
              <div className="space-y-2">
                {item.evidence.map((ev, i) => (
                  <div key={i} className="p-3 bg-slate-950/80 rounded-xl border border-slate-800/80 text-xs text-slate-300">
                    <span className="font-bold text-indigo-400 uppercase text-[10px] block mb-1">
                      Signal: {ev.signal || 'EVIDENCE'}
                    </span>
                    <p className="leading-relaxed">{ev.explanation}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-800 bg-slate-900/50 flex items-center justify-between">
          <Button variant="ghost" onClick={onClose} className="text-xs">
            Close Drawer
          </Button>

          {item.status === 'IMPLEMENTED_NOT_TESTED' && (
            <Button
              onClick={() => {
                onClose();
                onSuggestTest(item);
              }}
              className="bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold"
            >
              <Sparkles className="h-4 w-4 mr-1.5" /> Suggest Test
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};
