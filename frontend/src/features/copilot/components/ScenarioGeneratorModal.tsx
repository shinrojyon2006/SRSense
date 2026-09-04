import React, { useEffect, useState } from 'react';
import {
  AlertTriangle,
  Beaker,
  CheckCircle2,
  Copy,
  Loader2,
  X,
} from 'lucide-react';
import { copilotService } from '../api/copilotService';
import { ScenarioGeneratorResponse, TestScenario } from '../types';

interface ScenarioGeneratorModalProps {
  isOpen: boolean;
  onClose: () => void;
  projectId: string;
  requirementId: string | null;
  requirementTitle?: string;
}

export const ScenarioGeneratorModal: React.FC<ScenarioGeneratorModalProps> = ({
  isOpen,
  onClose,
  projectId,
  requirementId,
  requirementTitle,
}) => {
  const [data, setData] = useState<ScenarioGeneratorResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copiedIdx, setCopiedIdx] = useState<number | null>(null);

  useEffect(() => {
    if (!isOpen || !requirementId) return;

    const fetchScenarios = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const res = await copilotService.generateScenarios(projectId, requirementId);
        setData(res);
      } catch (err: any) {
        setError(err?.response?.data?.detail || 'Failed to generate test scenarios.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchScenarios();
  }, [isOpen, projectId, requirementId]);

  if (!isOpen) return null;

  const getScenarioBadge = (type: string) => {
    switch (type) {
      case 'normal':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
      case 'boundary':
        return 'bg-blue-500/10 text-blue-400 border-blue-500/20';
      case 'failure':
        return 'bg-rose-500/10 text-rose-400 border-rose-500/20';
      case 'edge':
        return 'bg-purple-500/10 text-purple-400 border-purple-500/20';
      default:
        return 'bg-slate-800 text-slate-400 border-slate-700';
    }
  };

  const copyToClipboard = (scenario: TestScenario, idx: number) => {
    const text = `Scenario: ${scenario.title}\n  Given ${scenario.given}\n  When ${scenario.when}\n  Then ${scenario.then}`;
    navigator.clipboard.writeText(text);
    setCopiedIdx(idx);
    setTimeout(() => setCopiedIdx(null), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-xs animate-in fade-in duration-150">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-3xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/50">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400">
              <Beaker className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                Scenario Generator (Given-When-Then)
              </h3>
              <p className="text-xs text-slate-400 truncate max-w-md">
                {requirementTitle || data?.requirement_title || 'Generating test cases'}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto space-y-4">
          {isLoading && (
            <div className="py-16 flex flex-col items-center justify-center gap-3 text-slate-400">
              <Loader2 className="w-8 h-8 animate-spin text-purple-500" />
              <p className="text-sm">Synthesizing Given-When-Then test cases...</p>
            </div>
          )}

          {error && (
            <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-sm flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 shrink-0" />
              <div>
                <p className="font-semibold">Scenario Generation Failed</p>
                <p className="text-xs text-rose-300/80 mt-0.5">{error}</p>
              </div>
            </div>
          )}

          {!isLoading && !error && data && data.insufficient_info_reason && (
            <div className="space-y-4">
              <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-200 space-y-3">
                <div className="flex items-start gap-3">
                  <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
                  <div>
                    <h4 className="text-sm font-bold text-amber-300">
                      {data.insufficient_info_reason}
                    </h4>
                    <p className="text-xs text-amber-200/80 mt-1">
                      To prevent AI hallucination of imaginary system parameters, test scenarios cannot be generated until the requirement specifies concrete operations, quantitative metrics, or triggers.
                    </p>
                  </div>
                </div>

                {data.missing_information && data.missing_information.length > 0 && (
                  <div className="pt-2 border-t border-amber-500/20 space-y-1.5">
                    <p className="text-[11px] font-semibold uppercase tracking-wider text-amber-400">
                      Missing Required Information:
                    </p>
                    <ul className="space-y-1 text-xs text-amber-200/90 pl-1">
                      {data.missing_information.map((item, idx) => (
                        <li key={idx} className="flex items-start gap-2">
                          <span className="text-amber-400 font-bold">•</span>
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {data.clarification_questions && data.clarification_questions.length > 0 && (
                  <div className="pt-2 border-t border-amber-500/20 space-y-1.5">
                    <p className="text-[11px] font-semibold uppercase tracking-wider text-amber-400">
                      Recommended Clarification Questions:
                    </p>
                    <ul className="space-y-1 text-xs text-slate-300 pl-1">
                      {data.clarification_questions.map((q, idx) => (
                        <li key={idx} className="flex items-start gap-2 font-mono text-[11px]">
                          <span className="text-purple-400">Q{idx + 1}:</span>
                          <span>{q}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          )}

          {!isLoading && !error && data && !data.insufficient_info_reason && (
            <div className="space-y-4">
              <div className="flex items-center justify-between text-xs text-slate-400 pb-1">
                <span>Generated {data.total_scenarios} test scenario(s)</span>
                <span className="text-[10px] text-slate-500">BDD / Gherkin Compatible</span>
              </div>

              {data.scenarios.map((sc, idx) => (
                <div
                  key={idx}
                  className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2.5 relative group"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span
                        className={`text-[10px] uppercase font-mono px-2 py-0.5 rounded border ${getScenarioBadge(
                          sc.scenario_type
                        )}`}
                      >
                        {sc.scenario_type}
                      </span>
                      <h4 className="text-xs font-bold text-white">{sc.title}</h4>
                    </div>

                    <button
                      onClick={() => copyToClipboard(sc, idx)}
                      className="p-1 rounded text-slate-400 hover:text-white hover:bg-slate-800 transition-colors text-xs flex items-center gap-1"
                      title="Copy Gherkin snippet"
                    >
                      {copiedIdx === idx ? (
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                      ) : (
                        <Copy className="w-3.5 h-3.5" />
                      )}
                    </button>
                  </div>

                  <div className="space-y-1.5 font-mono text-xs text-slate-300 bg-slate-900/80 p-3 rounded-lg border border-slate-800/80">
                    <p className="flex items-start gap-2">
                      <span className="text-purple-400 font-bold w-12 shrink-0">Given</span>
                      <span className="text-slate-300">{sc.given}</span>
                    </p>
                    <p className="flex items-start gap-2">
                      <span className="text-blue-400 font-bold w-12 shrink-0">When</span>
                      <span className="text-slate-300">{sc.when}</span>
                    </p>
                    <p className="flex items-start gap-2">
                      <span className="text-emerald-400 font-bold w-12 shrink-0">Then</span>
                      <span className="text-slate-300">{sc.then}</span>
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3.5 border-t border-slate-800 bg-slate-950/60 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-white transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
