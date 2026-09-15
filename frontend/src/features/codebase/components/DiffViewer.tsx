import React, { useState } from 'react';
import { Columns, FileText, Check, Copy } from 'lucide-react';
import { Button } from '@/components/ui/Button';

interface DiffViewerProps {
  currentCode: string;
  proposedCode: string;
  patchDiff: string;
  filePath: string;
}

export const DiffViewer: React.FC<DiffViewerProps> = ({
  currentCode,
  proposedCode,
  patchDiff,
  filePath,
}) => {
  const [viewMode, setViewMode] = useState<'side_by_side' | 'unified'>('side_by_side');
  const [copied, setCopied] = useState(false);

  const handleCopyDiff = () => {
    navigator.clipboard.writeText(patchDiff);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const renderUnifiedDiff = () => {
    const lines = patchDiff ? patchDiff.split('\n') : [];
    return (
      <div className="font-mono text-[11px] leading-relaxed overflow-x-auto bg-slate-950 p-4 rounded-xl border border-slate-800 text-slate-200">
        <div className="text-slate-400 font-bold mb-2 border-b border-slate-800 pb-1">
          {filePath} (Unified Git Diff)
        </div>
        {lines.map((line: string, idx: number) => {
          let bgClass = '';
          let textClass = 'text-slate-300';
          if (line.startsWith('+') && !line.startsWith('+++')) {
            bgClass = 'bg-emerald-950/60 text-emerald-300';
          } else if (line.startsWith('-') && !line.startsWith('---')) {
            bgClass = 'bg-red-950/60 text-red-300';
          } else if (line.startsWith('@@') || line.startsWith('---') || line.startsWith('+++')) {
            textClass = 'text-indigo-400 font-bold';
          }

          return (
            <div key={idx} className={`px-2 py-0.5 rounded-xs ${bgClass} ${textClass}`}>
              {line}
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div className="space-y-3">
      {/* Diff Toolbar */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5 bg-slate-100 dark:bg-slate-800/80 p-1 rounded-lg">
          <button
            onClick={() => setViewMode('side_by_side')}
            className={`px-3 py-1 rounded-md text-xs font-semibold flex items-center gap-1.5 transition-all ${
              viewMode === 'side_by_side'
                ? 'bg-white text-indigo-600 shadow-xs dark:bg-slate-700 dark:text-white'
                : 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white'
            }`}
          >
            <Columns className="h-3.5 w-3.5" /> Side-by-Side Comparison
          </button>
          <button
            onClick={() => setViewMode('unified')}
            className={`px-3 py-1 rounded-md text-xs font-semibold flex items-center gap-1.5 transition-all ${
              viewMode === 'unified'
                ? 'bg-white text-indigo-600 shadow-xs dark:bg-slate-700 dark:text-white'
                : 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white'
            }`}
          >
            <FileText className="h-3.5 w-3.5" /> Unified Patch Diff
          </button>
        </div>

        <Button size="sm" variant="ghost" onClick={handleCopyDiff} className="text-xs">
          {copied ? (
            <>
              <Check className="h-3.5 w-3.5 mr-1 text-emerald-500" /> Copied Diff
            </>
          ) : (
            <>
              <Copy className="h-3.5 w-3.5 mr-1" /> Copy Diff
            </>
          )}
        </Button>
      </div>

      {/* Content Area */}
      {viewMode === 'unified' ? (
        renderUnifiedDiff()
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Current Code */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between text-xs font-bold text-red-600 dark:text-red-400 uppercase tracking-wider px-1">
              <span>Current Code (Existing)</span>
              <span className="text-[10px] text-slate-400">Before Fix</span>
            </div>
            <pre className="p-4 bg-slate-950 text-red-200 rounded-xl text-[11px] font-mono overflow-x-auto border border-red-900/50 max-h-80">
              {currentCode || '// No current code snippet'}
            </pre>
          </div>

          {/* Proposed Code */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between text-xs font-bold text-emerald-600 dark:text-emerald-400 uppercase tracking-wider px-1">
              <span>Proposed Code (Refactored)</span>
              <span className="text-[10px] text-emerald-500 font-bold">Reviewable Fix</span>
            </div>
            <pre className="p-4 bg-slate-950 text-emerald-200 rounded-xl text-[11px] font-mono overflow-x-auto border border-emerald-900/50 max-h-80">
              {proposedCode || '// No proposed code generated'}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
};
