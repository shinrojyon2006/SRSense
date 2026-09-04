import React from 'react';
import {
  Code,
  FileCode,
  FolderCode,
  Terminal,
  UploadCloud,
  CheckCircle2,
  Layers,
  Search,
  Trash2,
} from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { CodebaseSummary } from '../types/codebase.types';

interface CodebaseSummaryCardProps {
  summary: CodebaseSummary | null;
  isLoading?: boolean;
  onOpenUpload: () => void;
  onOpenExplorer: () => void;
  onDeleteCodebase: () => void;
}

const LANGUAGE_COLORS: Record<string, string> = {
  Python: 'bg-blue-500 text-white',
  TypeScript: 'bg-indigo-600 text-white',
  JavaScript: 'bg-amber-400 text-slate-900',
  Java: 'bg-orange-600 text-white',
  'C++': 'bg-cyan-600 text-white',
  C: 'bg-slate-600 text-white',
  HTML: 'bg-rose-500 text-white',
  CSS: 'bg-purple-500 text-white',
  SQL: 'bg-emerald-600 text-white',
  'Unknown / Unsupported': 'bg-slate-400 text-white',
};

export const CodebaseSummaryCard: React.FC<CodebaseSummaryCardProps> = ({
  summary,
  isLoading,
  onOpenUpload,
  onOpenExplorer,
  onDeleteCodebase,
}) => {
  if (isLoading) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs dark:border-slate-800 dark:bg-slate-900 animate-pulse">
        <div className="h-6 w-1/4 bg-slate-200 dark:bg-slate-800 rounded mb-4"></div>
        <div className="h-16 w-full bg-slate-100 dark:bg-slate-800/60 rounded"></div>
      </div>
    );
  }

  if (!summary) {
    return (
      <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50/50 p-6 dark:border-slate-800 dark:bg-slate-950/40">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-xl bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 dark:text-indigo-400">
              <FolderCode className="h-6 w-6" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                Code Intelligence Subsystem (Sprint 2.0)
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                Import and index your source code repository to enable multi-language AST inspection and Requirement ↔ Code traceability.
              </p>
            </div>
          </div>
          <Button onClick={onOpenUpload} className="shrink-0">
            <UploadCloud className="h-4 w-4 mr-1.5" /> Import Repository ZIP
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs dark:border-slate-800 dark:bg-slate-900 space-y-5">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-lg bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 dark:text-indigo-400">
            <Code className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                {summary.repo_name}
              </h3>
              <Badge
                variant={
                  summary.status === 'indexed'
                    ? 'success'
                    : summary.status === 'indexing'
                    ? 'warning'
                    : 'error'
                }
              >
                {summary.status.toUpperCase()}
              </Badge>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Source Code Intelligence & AST Index
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="secondary" onClick={onOpenExplorer}>
            <Search className="h-3.5 w-3.5 mr-1" /> Explore Codebase
          </Button>
          <Button variant="secondary" onClick={onOpenUpload} title="Re-index repository">
            <UploadCloud className="h-3.5 w-3.5 mr-1" /> Re-upload
          </Button>
          <Button
            variant="ghost"
            onClick={onDeleteCodebase}
            title="Remove indexed codebase"
            className="text-red-500 hover:text-red-600 dark:text-red-400"
          >
            <Trash2 className="h-3.5 w-3.5" />
          </Button>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="rounded-lg border border-slate-100 bg-slate-50 p-3 dark:border-slate-800/80 dark:bg-slate-950/60">
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-500 dark:text-slate-400">
            <FileCode className="h-3.5 w-3.5 text-indigo-500" /> Files Analyzed
          </div>
          <div className="mt-1 text-lg font-bold text-slate-900 dark:text-white">
            {summary.total_files}
          </div>
        </div>

        <div className="rounded-lg border border-slate-100 bg-slate-50 p-3 dark:border-slate-800/80 dark:bg-slate-950/60">
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-500 dark:text-slate-400">
            <Terminal className="h-3.5 w-3.5 text-blue-500" /> Total Lines
          </div>
          <div className="mt-1 text-lg font-bold text-slate-900 dark:text-white">
            {summary.total_lines.toLocaleString()}
          </div>
        </div>

        <div className="rounded-lg border border-slate-100 bg-slate-50 p-3 dark:border-slate-800/80 dark:bg-slate-950/60">
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-500 dark:text-slate-400">
            <Layers className="h-3.5 w-3.5 text-emerald-500" /> Classes / Structs
          </div>
          <div className="mt-1 text-lg font-bold text-slate-900 dark:text-white">
            {summary.total_classes}
          </div>
        </div>

        <div className="rounded-lg border border-slate-100 bg-slate-50 p-3 dark:border-slate-800/80 dark:bg-slate-950/60">
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-500 dark:text-slate-400">
            <CheckCircle2 className="h-3.5 w-3.5 text-purple-500" /> Functions / Methods
          </div>
          <div className="mt-1 text-lg font-bold text-slate-900 dark:text-white">
            {summary.total_functions}
          </div>
        </div>
      </div>

      {/* Languages Distribution */}
      {summary.languages_summary && Object.keys(summary.languages_summary).length > 0 && (
        <div className="space-y-2">
          <div className="text-xs font-semibold text-slate-700 dark:text-slate-300">
            Languages Detected ({Object.keys(summary.languages_summary).length})
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {Object.entries(summary.languages_summary).map(([lang, count]) => {
              const colorClass =
                LANGUAGE_COLORS[lang] || 'bg-slate-500 text-white';
              return (
                <span
                  key={lang}
                  className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium ${colorClass}`}
                >
                  <span>{lang}</span>
                  <span className="opacity-80 text-[10px]">({count} files)</span>
                </span>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
