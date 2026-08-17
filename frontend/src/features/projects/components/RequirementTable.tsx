import React from 'react';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Requirement } from '@/types';
import { Edit2, Trash2, ShieldCheck, AlertTriangle, Sparkles, Wand2, GitFork, Zap, FileCode2 } from 'lucide-react';

interface RequirementTableProps {
  requirements: Requirement[];
  onEdit: (req: Requirement) => void;
  onDelete: (req: Requirement) => void;
  onAnalyze: (req: Requirement) => void;
  onImprove: (req: Requirement) => void;
  onOpenRelationships?: (req: Requirement) => void;
  onSimulateImpact?: (req: Requirement) => void;
  onOpenVerification?: (req: Requirement) => void;
  analyzingId?: string | null;
  improvingId?: string | null;
}

export const RequirementTable: React.FC<RequirementTableProps> = ({
  requirements,
  onEdit,
  onDelete,
  onAnalyze,
  onImprove,
  onOpenRelationships,
  onSimulateImpact,
  onOpenVerification,
  analyzingId,
  improvingId,
}) => {
  const getTypeBadgeVariant = (type: string) => {
    switch (type) {
      case 'functional': return 'primary';
      case 'non_functional': return 'warning';
      case 'user': return 'success';
      case 'business': return 'neutral';
      case 'system': return 'error';
      default: return 'neutral';
    }
  };

  const getPriorityBadgeVariant = (priority: string) => {
    switch (priority) {
      case 'critical': return 'error';
      case 'high': return 'warning';
      case 'medium': return 'primary';
      case 'low': return 'neutral';
      default: return 'neutral';
    }
  };

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'approved': return 'success';
      case 'in_review': return 'warning';
      case 'rejected': return 'error';
      default: return 'neutral';
    }
  };

  if (requirements.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-300 p-12 text-center dark:border-slate-800">
        <p className="text-sm font-medium text-slate-600 dark:text-slate-400">
          No requirements specifications found in this workspace.
        </p>
        <p className="mt-1 text-xs text-slate-400">
          Click "Add Requirement" above to begin authoring specifications.
        </p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-xs dark:border-slate-800 dark:bg-slate-900">
      <table className="w-full text-left text-xs">
        <thead className="border-b border-slate-100 bg-slate-50/50 text-slate-500 dark:border-slate-800 dark:bg-slate-950/50 dark:text-slate-400">
          <tr>
            <th className="px-4 py-3 font-semibold">Title & Description</th>
            <th className="px-4 py-3 font-semibold">Type</th>
            <th className="px-4 py-3 font-semibold">Priority</th>
            <th className="px-4 py-3 font-semibold">Status</th>
            <th className="px-4 py-3 font-semibold">Quality Score</th>
            <th className="px-4 py-3 font-semibold text-right">AI, Simulator & Verification Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
          {requirements.map((req) => (
            <tr key={req.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/50 transition-colors">
              <td className="px-4 py-3 max-w-xs">
                <p className="font-bold text-slate-900 dark:text-white">{req.title}</p>
                <p className="mt-0.5 line-clamp-2 text-[11px] text-slate-500 dark:text-slate-400">
                  {req.description}
                </p>
              </td>

              <td className="px-4 py-3 capitalize">
                <Badge variant={getTypeBadgeVariant(req.type)} size="sm">
                  {req.type.replace('_', ' ')}
                </Badge>
              </td>

              <td className="px-4 py-3 capitalize">
                <Badge variant={getPriorityBadgeVariant(req.priority)} size="sm">
                  {req.priority}
                </Badge>
              </td>

              <td className="px-4 py-3 capitalize">
                <Badge variant={getStatusBadgeVariant(req.status)} size="sm">
                  {req.status.replace('_', ' ')}
                </Badge>
              </td>

              <td className="px-4 py-3">
                {req.quality_score !== null && req.quality_score !== undefined ? (
                  <div className="flex items-center gap-1.5 font-bold">
                    {req.quality_score >= 80 ? (
                      <span className="flex items-center gap-1 text-emerald-600 dark:text-emerald-400">
                        <ShieldCheck className="h-3.5 w-3.5" /> {req.quality_score}/100
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 text-amber-600 dark:text-amber-400">
                        <AlertTriangle className="h-3.5 w-3.5" /> {req.quality_score}/100
                      </span>
                    )}
                  </div>
                ) : (
                  <span className="text-[11px] text-slate-400 italic">Not Analyzed</span>
                )}
              </td>

              <td className="px-4 py-3 text-right">
                <div className="flex items-center justify-end gap-1">
                  {onOpenVerification && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onOpenVerification(req)}
                      title="Open Requirement Verification Compiler & Test Suite"
                    >
                      <FileCode2 className="h-3.5 w-3.5 text-emerald-400" />
                    </Button>
                  )}
                  {onSimulateImpact && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onSimulateImpact(req)}
                      title="Run Ephemeral What-If Change Impact Simulation"
                    >
                      <Zap className="h-3.5 w-3.5 text-rose-400" />
                    </Button>
                  )}
                  {onOpenRelationships && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onOpenRelationships(req)}
                      title="Manage Knowledge Graph Relationships"
                    >
                      <GitFork className="h-3.5 w-3.5 text-indigo-400" />
                    </Button>
                  )}
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onAnalyze(req)}
                    isLoading={analyzingId === req.id}
                    title="Run AI Quality Analysis"
                  >
                    <Sparkles className="h-3.5 w-3.5 text-indigo-500" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onImprove(req)}
                    isLoading={improvingId === req.id}
                    title="Suggest AI EARS Improvement"
                  >
                    <Wand2 className="h-3.5 w-3.5 text-emerald-500" />
                  </Button>
                  <Button variant="ghost" size="sm" onClick={() => onEdit(req)}>
                    <Edit2 className="h-3.5 w-3.5" />
                  </Button>
                  <Button variant="ghost" size="sm" className="text-red-500 hover:text-red-700" onClick={() => onDelete(req)}>
                    <Trash2 className="h-3.5 w-3.5" />
                  </Button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
