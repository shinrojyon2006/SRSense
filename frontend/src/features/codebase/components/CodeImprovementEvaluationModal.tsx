import React from 'react';
import { X, Sparkles, AlertOctagon, CheckCircle, ShieldAlert, Scale, HelpCircle } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { CodeImprovementEvaluation, EvaluationResultClassification } from '../types/codeEvaluation.types';
import { ScoreDeltaCards } from './ScoreDeltaCards';
import { BeforeAfterComparison } from './BeforeAfterComparison';
import { FindingComparison } from './FindingComparison';

interface CodeImprovementEvaluationModalProps {
  isOpen: boolean;
  onClose: () => void;
  evaluation: CodeImprovementEvaluation | null;
  proposalTitle: string;
}

export const CodeImprovementEvaluationModal: React.FC<CodeImprovementEvaluationModalProps> = ({
  isOpen,
  onClose,
  evaluation,
  proposalTitle,
}) => {
  if (!isOpen || !evaluation) return null;

  const renderClassificationBadge = (classification: EvaluationResultClassification) => {
    switch (classification) {
      case 'improved':
        return (
          <div className="flex items-center gap-2 bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 px-3.5 py-1.5 rounded-full font-bold text-xs">
            <CheckCircle className="h-4 w-4" /> RESULT: IMPROVED
          </div>
        );
      case 'regressed':
        return (
          <div className="flex items-center gap-2 bg-red-500/10 text-red-400 border border-red-500/30 px-3.5 py-1.5 rounded-full font-bold text-xs">
            <AlertOctagon className="h-4 w-4" /> RESULT: REGRESSED
          </div>
        );
      case 'partially_improved':
        return (
          <div className="flex items-center gap-2 bg-amber-500/10 text-amber-400 border border-amber-500/30 px-3.5 py-1.5 rounded-full font-bold text-xs">
            <Scale className="h-4 w-4" /> RESULT: PARTIALLY IMPROVED
          </div>
        );
      case 'unchanged':
        return (
          <div className="flex items-center gap-2 bg-slate-800 text-slate-300 border border-slate-700 px-3.5 py-1.5 rounded-full font-bold text-xs">
            <HelpCircle className="h-4 w-4" /> RESULT: UNCHANGED
          </div>
        );
      default:
        return (
          <div className="flex items-center gap-2 bg-slate-800 text-slate-400 border border-slate-700 px-3.5 py-1.5 rounded-full font-bold text-xs">
            <HelpCircle className="h-4 w-4" /> RESULT: UNDETERMINED
          </div>
        );
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="bg-slate-950 border border-slate-800 rounded-3xl w-full max-w-4xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="p-6 border-b border-slate-800 flex items-center justify-between bg-slate-900/50">
          <div>
            <div className="flex items-center gap-3">
              <h2 className="text-lg font-bold text-slate-100">Engineering Improvement Evaluation</h2>
              {renderClassificationBadge(evaluation.result_classification)}
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Objective Before vs After verification scan for proposal: <span className="text-indigo-400 font-semibold">{proposalTitle}</span>
            </p>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose} className="rounded-full p-2 text-slate-400 hover:text-white">
            <X className="h-5 w-5" />
          </Button>
        </div>

        {/* Content Body */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1">
          {/* Regression Alert Banner if applicable */}
          {evaluation.regression_detected && (
            <div className="bg-red-950/70 border border-red-800 p-4 rounded-2xl space-y-2">
              <div className="flex items-center gap-2 text-red-400 font-bold text-sm">
                <ShieldAlert className="h-5 w-5 shrink-0" /> REGRESSION DETECTED
              </div>
              <ul className="space-y-1 text-xs text-red-200 list-disc list-inside">
                {evaluation.regression_details.map((detail, idx) => (
                  <li key={idx}>{detail}</li>
                ))}
              </ul>
            </div>
          )}

          {/* AI Grounded Technical Synthesis */}
          {evaluation.ai_explanation && (
            <div className="bg-indigo-950/30 border border-indigo-900/50 p-4 rounded-2xl space-y-2">
              <div className="flex items-center gap-2 text-indigo-400 font-bold text-xs uppercase tracking-wider">
                <Sparkles className="h-4 w-4" /> AI Grounded Evidence Synthesis
              </div>
              <p className="text-xs text-slate-300 leading-relaxed font-sans">
                {evaluation.ai_explanation}
              </p>
            </div>
          )}

          {/* Overall Score Delta Cards */}
          <ScoreDeltaCards evaluation={evaluation} />

          {/* Requirement Compliance & Test Impact */}
          <BeforeAfterComparison
            requirementImpact={evaluation.requirement_compliance_impact}
            testImpact={evaluation.test_impact}
          />

          {/* Finding Comparison Breakdown */}
          <FindingComparison
            resolved={evaluation.resolved_findings}
            remaining={evaluation.remaining_findings}
            newFindings={evaluation.new_findings}
            unchanged={evaluation.unchanged_findings}
          />
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-800 bg-slate-900/50 flex items-center justify-between text-xs text-slate-500">
          <div>Evaluated on {new Date(evaluation.created_at).toLocaleString()}</div>
          <Button variant="ghost" onClick={onClose}>
            Close Audit Report
          </Button>
        </div>
      </div>
    </div>
  );
};
