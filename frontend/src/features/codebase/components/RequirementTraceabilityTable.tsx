import React, { useState } from 'react';
import {
  CheckCircle,
  AlertTriangle,
  FileCode,
  TestTube2,
  Sparkles,
  Search,
  Filter,
  Eye,
} from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { RequirementTraceabilityItem } from '../types/traceability.types';

interface RequirementTraceabilityTableProps {
  items: RequirementTraceabilityItem[];
  onSelectRequirement: (item: RequirementTraceabilityItem) => void;
  onSuggestTest: (item: RequirementTraceabilityItem) => void;
}

export const RequirementTraceabilityTable: React.FC<RequirementTraceabilityTableProps> = ({
  items,
  onSelectRequirement,
  onSuggestTest,
}) => {
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');

  const filtered = items.filter((item) => {
    const matchesSearch =
      item.title.toLowerCase().includes(search.toLowerCase()) ||
      (item.original_req_id && item.original_req_id.toLowerCase().includes(search.toLowerCase()));

    const matchesStatus = statusFilter === 'ALL' || item.status === statusFilter;

    return matchesSearch && matchesStatus;
  });

  const renderStatusBadge = (status: string) => {
    switch (status) {
      case 'FULLY_TRACED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-extrabold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <CheckCircle className="h-3 w-3" /> FULLY TRACED
          </span>
        );
      case 'IMPLEMENTED_NOT_TESTED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-extrabold bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <AlertTriangle className="h-3 w-3" /> IMPLEMENTED — NOT TESTED
          </span>
        );
      case 'TESTED_NOT_LINKED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-extrabold bg-purple-500/10 text-purple-400 border border-purple-500/20">
            TESTED — NOT LINKED
          </span>
        );
      case 'NO_IMPLEMENTATION':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-extrabold bg-red-500/10 text-red-400 border border-red-500/20">
            NO IMPLEMENTATION
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-extrabold bg-slate-800 text-slate-400 border border-slate-700">
            UNDETERMINED
          </span>
        );
    }
  };

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-3xl p-5 space-y-4">
      {/* Controls */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 border-b border-slate-800 pb-4">
        <div className="relative flex-1 w-full">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search requirement title or ID (e.g. REQ-001)..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-4 py-2 text-xs text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-indigo-500"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <Filter className="h-4 w-4 text-slate-400 shrink-0" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
          >
            <option value="ALL">All Statuses</option>
            <option value="FULLY_TRACED">Fully Traced</option>
            <option value="IMPLEMENTED_NOT_TESTED">Implemented — Not Tested</option>
            <option value="NO_IMPLEMENTATION">No Implementation</option>
            <option value="TESTED_NOT_LINKED">Tested — Not Linked</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="border-b border-slate-800 text-slate-400 uppercase tracking-wider font-mono text-[10px]">
              <th className="py-3 px-3">Req ID / Title</th>
              <th className="py-3 px-3">Type</th>
              <th className="py-3 px-3">Code Link</th>
              <th className="py-3 px-3">Test Link</th>
              <th className="py-3 px-3">Traceability Status</th>
              <th className="py-3 px-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 text-slate-200">
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-8 text-center text-slate-500 font-mono">
                  No requirement traceability items match filter criteria.
                </td>
              </tr>
            ) : (
              filtered.map((item) => (
                <tr key={item.requirement_id} className="hover:bg-slate-950/50 transition-colors">
                  <td className="py-3 px-3 max-w-xs">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-[11px] font-bold text-indigo-400 bg-indigo-950/60 px-2 py-0.5 rounded border border-indigo-800/40 shrink-0">
                        {item.original_req_id || item.requirement_id.slice(0, 8)}
                      </span>
                      <span className="font-semibold truncate text-slate-100">{item.title}</span>
                    </div>
                  </td>
                  <td className="py-3 px-3">
                    <span className="uppercase text-[10px] font-bold px-2 py-0.5 rounded bg-slate-800 text-slate-400">
                      {item.requirement_type}
                    </span>
                  </td>
                  <td className="py-3 px-3 font-mono text-[11px]">
                    {item.has_code ? (
                      <div className="flex items-center gap-1 text-emerald-400">
                        <FileCode className="h-3.5 w-3.5" />
                        <span>{item.linked_code_files.length} file(s)</span>
                      </div>
                    ) : (
                      <span className="text-slate-500">None</span>
                    )}
                  </td>
                  <td className="py-3 px-3 font-mono text-[11px]">
                    {item.has_test ? (
                      <div className="flex items-center gap-1 text-purple-400">
                        <TestTube2 className="h-3.5 w-3.5" />
                        <span>{item.linked_test_names.length} test(s)</span>
                      </div>
                    ) : (
                      <span className="text-slate-500">None</span>
                    )}
                  </td>
                  <td className="py-3 px-3">{renderStatusBadge(item.status)}</td>
                  <td className="py-3 px-3 text-right">
                    <div className="flex items-center justify-end gap-1.5">
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => onSelectRequirement(item)}
                        className="text-xs px-2.5 py-1 text-slate-300 hover:text-white"
                      >
                        <Eye className="h-3.5 w-3.5 mr-1" /> View Graph
                      </Button>

                      {item.status === 'IMPLEMENTED_NOT_TESTED' && (
                        <Button
                          size="sm"
                          onClick={() => onSuggestTest(item)}
                          className="bg-indigo-600 hover:bg-indigo-700 text-white text-[11px] font-bold px-2.5 py-1"
                        >
                          <Sparkles className="h-3.5 w-3.5 mr-1" /> Suggest Test
                        </Button>
                      )}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
