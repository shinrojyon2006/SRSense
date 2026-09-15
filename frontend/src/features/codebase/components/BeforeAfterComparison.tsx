import React from 'react';
import { Target, TestTube2, AlertCircle } from 'lucide-react';
import { RequirementComplianceImpact, TestImpact } from '../types/codeEvaluation.types';

interface BeforeAfterComparisonProps {
  requirementImpact: RequirementComplianceImpact;
  testImpact: TestImpact;
}

export const BeforeAfterComparison: React.FC<BeforeAfterComparisonProps> = ({
  requirementImpact,
  testImpact,
}) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {/* Requirement Compliance Impact */}
      <div className="bg-slate-900/60 border border-slate-800/80 p-4 rounded-2xl space-y-3">
        <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-purple-400 border-b border-slate-800 pb-2">
          <Target className="h-4 w-4" /> Requirement Compliance Impact
        </div>

        {requirementImpact.status === 'MEASURED' ? (
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs font-semibold text-slate-200">
              <span>{requirementImpact.requirement_title || 'Linked Requirement'}</span>
              <span className="text-emerald-400 font-mono font-bold">
                {requirementImpact.before_score} → {requirementImpact.after_score} (+{requirementImpact.delta})
              </span>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed bg-slate-950/60 p-3 rounded-xl border border-slate-800/60">
              {requirementImpact.explanation}
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs font-bold text-slate-400">
              <span>COMPLIANCE IMPACT</span>
              <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-400 text-[10px]">
                UNDETERMINED
              </span>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed bg-slate-950/60 p-3 rounded-xl border border-slate-800/60">
              {requirementImpact.explanation}
            </p>
          </div>
        )}
      </div>

      {/* Test Execution Impact */}
      <div className="bg-slate-900/60 border border-slate-800/80 p-4 rounded-2xl space-y-3">
        <div className="flex items-center justify-between border-b border-slate-800 pb-2">
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-blue-400">
            <TestTube2 className="h-4 w-4" /> Automated Test Considerations
          </div>
          <span className="text-[10px] font-mono font-bold uppercase px-2.5 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20">
            {testImpact.execution_status}
          </span>
        </div>

        <div className="space-y-2">
          <div className="flex items-center gap-2 text-xs text-slate-400 bg-amber-950/30 border border-amber-900/50 p-2.5 rounded-xl">
            <AlertCircle className="h-4 w-4 text-amber-400 shrink-0" />
            <span>{testImpact.details}</span>
          </div>

          {testImpact.affected_tests && testImpact.affected_tests.length > 0 && (
            <div className="space-y-1">
              <span className="text-[11px] font-bold text-slate-400 uppercase">
                Recommended Test Suite Reruns:
              </span>
              <ul className="space-y-1">
                {testImpact.affected_tests.map((t, i) => (
                  <li
                    key={i}
                    className="text-xs text-slate-300 bg-slate-950/60 px-3 py-1.5 rounded-lg border border-slate-800/50 flex items-center justify-between"
                  >
                    <span className="font-mono text-[11px] text-indigo-400">{t.type}</span>
                    <span>{t.description}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
