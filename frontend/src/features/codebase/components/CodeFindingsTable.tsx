import React, { useState } from 'react';
import {
  Search,
  AlertTriangle,
  ShieldAlert,
  Info,
  ChevronLeft,
  ChevronRight,
  Code2,
  Sparkles,
  X,
  FileCode,
  CheckCircle,
} from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import {
  CodeReviewFinding,
  FindingCategory,
  FindingSeverity,
} from '../types/codeQuality.types';

interface CodeFindingsTableProps {
  findings: CodeReviewFinding[];
  totalFindings: number;
  currentPage: number;
  pageSize: number;
  isLoading: boolean;
  onPageChange: (page: number) => void;
  onFilterChange: (filters: {
    severity?: FindingSeverity;
    category?: FindingCategory;
    search?: string;
    sort_by?: string;
    sort_dir?: 'asc' | 'desc';
  }) => void;
  onOpenImprovementModal?: (findingId: string) => void;
}

export const CodeFindingsTable: React.FC<CodeFindingsTableProps> = ({
  findings,
  totalFindings,
  currentPage,
  pageSize,
  isLoading,
  onPageChange,
  onFilterChange,
  onOpenImprovementModal,
}) => {
  const [search, setSearch] = useState('');
  const [selectedSeverity, setSelectedSeverity] = useState<string>('all');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [sortBy, setSortBy] = useState<string>('severity');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');

  // Finding Detail Modal state
  const [inspectFinding, setInspectFinding] = useState<CodeReviewFinding | null>(
    null
  );

  const handleSearchChange = (val: string) => {
    setSearch(val);
    emitFilters(val, selectedSeverity, selectedCategory, sortBy, sortDir);
  };

  const handleSeverityChange = (val: string) => {
    setSelectedSeverity(val);
    emitFilters(search, val, selectedCategory, sortBy, sortDir);
  };

  const handleCategoryChange = (val: string) => {
    setSelectedCategory(val);
    emitFilters(search, selectedSeverity, val, sortBy, sortDir);
  };

  const handleSortChange = (field: string) => {
    const nextDir = sortBy === field && sortDir === 'desc' ? 'asc' : 'desc';
    setSortBy(field);
    setSortDir(nextDir);
    emitFilters(search, selectedSeverity, selectedCategory, field, nextDir);
  };

  const emitFilters = (
    q: string,
    sev: string,
    cat: string,
    sortField: string,
    sortDirection: 'asc' | 'desc'
  ) => {
    onFilterChange({
      search: q.trim() ? q.trim() : undefined,
      severity: sev !== 'all' ? (sev as FindingSeverity) : undefined,
      category: cat !== 'all' ? (cat as FindingCategory) : undefined,
      sort_by: sortField,
      sort_dir: sortDirection,
    });
  };

  const totalPages = Math.ceil(totalFindings / pageSize) || 1;

  const getSeverityBadge = (severity: FindingSeverity) => {
    switch (severity) {
      case 'critical':
        return (
          <Badge variant="error" size="sm">
            <ShieldAlert className="h-3 w-3" /> Critical
          </Badge>
        );
      case 'warning':
        return (
          <Badge variant="warning" size="sm">
            <AlertTriangle className="h-3 w-3" /> Warning
          </Badge>
        );
      case 'info':
        return (
          <Badge variant="primary" size="sm">
            <Info className="h-3 w-3" /> Info
          </Badge>
        );
      default:
        return <Badge variant="neutral" size="sm">{severity}</Badge>;
    }
  };

  const getCategoryBadge = (category: FindingCategory) => {
    const catMap: Record<FindingCategory, string> = {
      security: 'bg-red-50 text-red-700 dark:bg-red-950/40 dark:text-red-300 border-red-200 dark:border-red-800',
      performance: 'bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300 border-amber-200 dark:border-amber-800',
      maintainability: 'bg-indigo-50 text-indigo-700 dark:bg-indigo-950/40 dark:text-indigo-300 border-indigo-200 dark:border-indigo-800',
      compliance: 'bg-purple-50 text-purple-700 dark:bg-purple-950/40 dark:text-purple-300 border-purple-200 dark:border-purple-800',
      quality: 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800',
    };
    return (
      <span
        className={`px-2 py-0.5 rounded text-[10px] font-bold border uppercase tracking-wider ${
          catMap[category] || 'bg-slate-100 text-slate-700'
        }`}
      >
        {category}
      </span>
    );
  };

  return (
    <div className="space-y-4">
      {/* Filtering & Search Bar */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-12 items-center bg-slate-50/70 p-3 rounded-xl border border-slate-200 dark:border-slate-800 dark:bg-slate-900/50">
        {/* Search */}
        <div className="sm:col-span-4 relative">
          <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search rule ID, title, file..."
            value={search}
            onChange={(e) => handleSearchChange(e.target.value)}
            className="w-full rounded-lg border border-slate-200 bg-white pl-9 pr-3 py-1.5 text-xs text-slate-900 focus:border-indigo-500 focus:outline-none dark:border-slate-700 dark:bg-slate-900 dark:text-white"
          />
        </div>

        {/* Severity Select */}
        <div className="sm:col-span-3">
          <select
            value={selectedSeverity}
            onChange={(e) => handleSeverityChange(e.target.value)}
            className="w-full rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-xs text-slate-900 focus:border-indigo-500 focus:outline-none dark:border-slate-700 dark:bg-slate-900 dark:text-white"
          >
            <option value="all">All Severities</option>
            <option value="critical">Critical Only</option>
            <option value="warning">Warning Only</option>
            <option value="info">Info Only</option>
          </select>
        </div>

        {/* Category Select */}
        <div className="sm:col-span-3">
          <select
            value={selectedCategory}
            onChange={(e) => handleCategoryChange(e.target.value)}
            className="w-full rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-xs text-slate-900 focus:border-indigo-500 focus:outline-none dark:border-slate-700 dark:bg-slate-900 dark:text-white"
          >
            <option value="all">All Categories</option>
            <option value="security">Security</option>
            <option value="performance">Performance</option>
            <option value="maintainability">Maintainability</option>
            <option value="compliance">Compliance</option>
            <option value="quality">Quality</option>
          </select>
        </div>

        {/* Sort Button */}
        <div className="sm:col-span-2 flex justify-end">
          <Button
            size="sm"
            variant="secondary"
            onClick={() => handleSortChange(sortBy)}
            className="w-full text-xs font-semibold"
          >
            Sort: {sortBy.toUpperCase()} ({sortDir.toUpperCase()})
          </Button>
        </div>
      </div>

      {/* Findings Table */}
      <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-xs dark:border-slate-800 dark:bg-slate-900">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-50 text-slate-500 border-b border-slate-200 dark:bg-slate-950/50 dark:border-slate-800 dark:text-slate-400 font-semibold">
            <tr>
              <th className="px-4 py-3">Severity</th>
              <th className="px-4 py-3">Rule ID</th>
              <th className="px-4 py-3">Category</th>
              <th className="px-4 py-3">Finding Title & Location</th>
              <th className="px-4 py-3 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60">
            {isLoading ? (
              <tr>
                <td colSpan={5} className="p-8 text-center text-slate-400">
                  Loading code quality findings...
                </td>
              </tr>
            ) : findings.length === 0 ? (
              <tr>
                <td colSpan={5} className="p-8 text-center text-slate-400">
                  <div className="flex flex-col items-center gap-2">
                    <CheckCircle className="h-6 w-6 text-emerald-500" />
                    <span>No code findings matched your filter criteria.</span>
                  </div>
                </td>
              </tr>
            ) : (
              findings.map((f) => (
                <tr
                  key={f.id}
                  className="hover:bg-slate-50/70 transition-colors dark:hover:bg-slate-800/40"
                >
                  <td className="px-4 py-3 whitespace-nowrap">
                    {getSeverityBadge(f.severity)}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap font-mono font-bold text-slate-800 dark:text-slate-200">
                    {f.rule_id}
                  </td>
                  <td className="px-4 py-3 whitespace-nowrap">
                    {getCategoryBadge(f.category)}
                  </td>
                  <td className="px-4 py-3">
                    <div className="font-semibold text-slate-900 dark:text-white">
                      {f.title}
                    </div>
                    <div className="flex items-center gap-1.5 text-[11px] font-mono text-slate-500 dark:text-slate-400 mt-0.5">
                      <FileCode className="h-3 w-3 text-slate-400" />
                      <span>{f.file_path}</span>
                      {f.line_number && <span>(Line {f.line_number})</span>}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-right whitespace-nowrap">
                    <Button
                      size="sm"
                      variant="secondary"
                      onClick={() => setInspectFinding(f)}
                      className="text-xs"
                    >
                      <Sparkles className="h-3 w-3 mr-1 text-indigo-500" /> Details & AI Fix
                    </Button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Controls */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between pt-2">
          <div className="text-xs text-slate-500 dark:text-slate-400">
            Showing Page <span className="font-bold">{currentPage}</span> of{' '}
            <span className="font-bold">{totalPages}</span> ({totalFindings} total findings)
          </div>
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant="secondary"
              disabled={currentPage <= 1}
              onClick={() => onPageChange(currentPage - 1)}
            >
              <ChevronLeft className="h-4 w-4 mr-1" /> Previous
            </Button>
            <Button
              size="sm"
              variant="secondary"
              disabled={currentPage >= totalPages}
              onClick={() => onPageChange(currentPage + 1)}
            >
              Next <ChevronRight className="h-4 w-4 ml-1" />
            </Button>
          </div>
        </div>
      )}

      {/* Detail Modal */}
      {inspectFinding && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 p-4 backdrop-blur-xs">
          <div className="flex max-h-[85vh] w-full max-w-3xl flex-col rounded-2xl border border-slate-200 bg-white shadow-2xl dark:border-slate-800 dark:bg-slate-900 overflow-hidden">
            {/* Modal Header */}
            <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4 dark:border-slate-800">
              <div className="flex items-center gap-2.5">
                <span className="font-mono text-sm font-bold px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-200">
                  {inspectFinding.rule_id}
                </span>
                {getSeverityBadge(inspectFinding.severity)}
                {getCategoryBadge(inspectFinding.category)}
              </div>
              <button
                onClick={() => setInspectFinding(null)}
                className="p-1 rounded-lg text-slate-400 hover:bg-slate-100 hover:text-slate-700 dark:hover:bg-slate-800 dark:hover:text-slate-200"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="flex-1 overflow-y-auto p-6 space-y-5">
              <div>
                <h3 className="text-base font-bold text-slate-900 dark:text-white">
                  {inspectFinding.title}
                </h3>
                <div className="flex items-center gap-2 font-mono text-xs text-indigo-600 dark:text-indigo-400 mt-1">
                  <FileCode className="h-3.5 w-3.5" />
                  <span>{inspectFinding.file_path}</span>
                  {inspectFinding.line_number && (
                    <span>(Line {inspectFinding.line_number})</span>
                  )}
                </div>
              </div>

              {/* Description */}
              <div className="space-y-1">
                <div className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
                  Description
                </div>
                <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                  {inspectFinding.description}
                </p>
              </div>

              {/* Snippet */}
              {inspectFinding.snippet && (
                <div className="space-y-1">
                  <div className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider flex items-center gap-1">
                    <Code2 className="h-3.5 w-3.5 text-slate-500" /> Flagged Code Snippet
                  </div>
                  <pre className="p-3 bg-slate-950 text-slate-200 rounded-lg text-[11px] font-mono overflow-x-auto border border-slate-800">
                    {inspectFinding.snippet}
                  </pre>
                </div>
              )}

              {/* Suggestion */}
              <div className="p-3.5 bg-indigo-50/60 rounded-xl border border-indigo-100 dark:bg-indigo-950/30 dark:border-indigo-900/50 space-y-1">
                <div className="text-xs font-bold text-indigo-900 dark:text-indigo-200 uppercase tracking-wider">
                  Remediation Suggestion
                </div>
                <p className="text-xs text-indigo-800 dark:text-indigo-300">
                  {inspectFinding.suggestion}
                </p>
              </div>

              {/* Grounded AI Explanation */}
              {inspectFinding.ai_explanation && (
                <div className="p-4 bg-gradient-to-r from-purple-50/80 to-indigo-50/80 dark:from-purple-950/40 dark:to-indigo-950/40 rounded-xl border border-purple-200 dark:border-purple-800/60 space-y-2">
                  <div className="flex items-center gap-2 text-xs font-bold text-purple-900 dark:text-purple-200">
                    <Sparkles className="h-4 w-4 text-purple-600 dark:text-purple-400" />
                    Grounded AI Explanation & Requirements Context
                  </div>
                  <p className="text-xs text-purple-950 dark:text-purple-200 whitespace-pre-wrap leading-relaxed">
                    {inspectFinding.ai_explanation}
                  </p>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="border-t border-slate-200 px-6 py-3 dark:border-slate-800 flex items-center justify-between">
              {onOpenImprovementModal && inspectFinding ? (
                <Button
                  size="sm"
                  onClick={() => {
                    const fId = inspectFinding.id;
                    setInspectFinding(null);
                    onOpenImprovementModal(fId);
                  }}
                  className="bg-purple-600 hover:bg-purple-700 text-white font-bold"
                >
                  <Sparkles className="h-3.5 w-3.5 mr-1" /> Improve Code (AI Fix)
                </Button>
              ) : <div />}
              <Button size="sm" variant="secondary" onClick={() => setInspectFinding(null)}>
                Close
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
