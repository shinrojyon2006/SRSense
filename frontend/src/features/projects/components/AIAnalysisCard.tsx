import React from 'react';
import { Badge } from '@/components/ui/Badge';
import { AIAnalysisResult } from '@/types';
import { ShieldCheck, AlertTriangle, AlertCircle, Sparkles } from 'lucide-react';

interface AIAnalysisCardProps {
  analysis: AIAnalysisResult;
  score: number;
}

export const AIAnalysisCard: React.FC<AIAnalysisCardProps> = ({ analysis, score }) => {
  const getScoreColor = (val: number) => {
    if (val >= 85) return 'text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/40 border-emerald-200 dark:border-emerald-800';
    if (val >= 70) return 'text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/40 border-amber-200 dark:border-amber-800';
    return 'text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-950/40 border-red-200 dark:border-red-800';
  };

  return (
    <div className="space-y-3 rounded-xl border border-slate-200 bg-slate-50/50 p-4 dark:border-slate-800 dark:bg-slate-950/50">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-indigo-500" />
          <h4 className="text-xs font-bold text-slate-900 dark:text-white">
            AI Requirement Quality Inspection
          </h4>
        </div>

        <div className={`flex items-center gap-1.5 rounded-lg border px-3 py-1 text-xs font-extrabold ${getScoreColor(score)}`}>
          {score >= 80 ? <ShieldCheck className="h-4 w-4" /> : <AlertTriangle className="h-4 w-4" />}
          Quality Score: {score}/100
        </div>
      </div>

      <p className="text-xs text-slate-600 dark:text-slate-400 font-medium">
        {analysis.summary_feedback}
      </p>

      {/* Ambiguity Tags */}
      {analysis.ambiguity_tags && analysis.ambiguity_tags.length > 0 && (
        <div className="space-y-1">
          <p className="text-[11px] font-semibold text-slate-500 dark:text-slate-400">
            Detected Ambiguities:
          </p>
          <div className="flex flex-wrap gap-1.5">
            {analysis.ambiguity_tags.map((tag, idx) => (
              <Badge key={idx} variant="warning" size="sm">
                {tag}
              </Badge>
            ))}
          </div>
        </div>
      )}

      {/* Passive Voice Warnings */}
      {analysis.passive_voice_instances && analysis.passive_voice_instances.length > 0 && (
        <div className="space-y-1">
          <p className="text-[11px] font-semibold text-slate-500 dark:text-slate-400">
            Passive Voice Flags:
          </p>
          <div className="flex flex-wrap gap-1.5">
            {analysis.passive_voice_instances.map((inst, idx) => (
              <Badge key={idx} variant="error" size="sm">
                {inst}
              </Badge>
            ))}
          </div>
        </div>
      )}

      {/* Missing Criteria Alerts */}
      {analysis.missing_criteria && analysis.missing_criteria.length > 0 && (
        <div className="space-y-1">
          <p className="text-[11px] font-semibold text-slate-500 dark:text-slate-400">
            Structure & Criteria Deficiencies:
          </p>
          <ul className="space-y-1 text-xs text-red-600 dark:text-red-400">
            {analysis.missing_criteria.map((crit, idx) => (
              <li key={idx} className="flex items-center gap-1.5 text-[11px]">
                <AlertCircle className="h-3 w-3 shrink-0" /> {crit}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
