import React, { useEffect, useState } from 'react';
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Info,
  Loader2,
  Sparkles,
  X,
  XCircle,
} from 'lucide-react';
import { copilotService } from '../api/copilotService';
import { RequirementDoctorResponse } from '../types';

interface DoctorModalProps {
  isOpen: boolean;
  onClose: () => void;
  projectId: string;
  requirementId: string | null;
  requirementTitle?: string;
  onApplyImprovement?: () => void;
}

export const DoctorModal: React.FC<DoctorModalProps> = ({
  isOpen,
  onClose,
  projectId,
  requirementId,
  requirementTitle,
  onApplyImprovement,
}) => {
  const [data, setData] = useState<RequirementDoctorResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen || !requirementId) return;

    const fetchDiagnosis = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const res = await copilotService.getDoctorDiagnosis(projectId, requirementId);
        setData(res);
      } catch (err: any) {
        setError(err?.response?.data?.detail || 'Failed to run Requirement Doctor.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchDiagnosis();
  }, [isOpen, projectId, requirementId]);

  if (!isOpen) return null;

  const getHealthBadge = (health: string, score: number) => {
    if (health === 'healthy') {
      return (
        <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          <CheckCircle2 className="w-3.5 h-3.5" /> Healthy ({score}/100)
        </span>
      );
    }
    if (health === 'needs_attention') {
      return (
        <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
          <AlertTriangle className="w-3.5 h-3.5" /> Needs Attention ({score}/100)
        </span>
      );
    }
    return (
      <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
        <XCircle className="w-3.5 h-3.5" /> Critical ({score}/100)
      </span>
    );
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical':
        return <XCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />;
      case 'warning':
        return <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />;
      default:
        return <Info className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />;
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-xs animate-in fade-in duration-150">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/50">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
              <Activity className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                Requirement Doctor
              </h3>
              <p className="text-xs text-slate-400 truncate max-w-md">
                {requirementTitle || data?.requirement_title || 'Diagnosing specification health'}
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
        <div className="p-6 overflow-y-auto space-y-6">
          {isLoading && (
            <div className="py-16 flex flex-col items-center justify-center gap-3 text-slate-400">
              <Loader2 className="w-8 h-8 animate-spin text-indigo-500" />
              <p className="text-sm">Analyzing requirement syntax and quality metrics...</p>
            </div>
          )}

          {error && (
            <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-sm flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 shrink-0" />
              <div>
                <p className="font-semibold">Diagnosis Failed</p>
                <p className="text-xs text-rose-300/80 mt-0.5">{error}</p>
              </div>
            </div>
          )}

          {!isLoading && !error && data && (
            <>
              {/* Overall Health Score Card */}
              <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 flex items-center justify-between">
                <div>
                  <span className="text-xs text-slate-400 block mb-1">Health Assessment</span>
                  <div className="flex items-center gap-3">
                    {getHealthBadge(data.overall_health, data.health_score)}
                    <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                      {data.confidence} CONFIDENCE
                    </span>
                  </div>
                </div>

                {data.health_score < 80 && onApplyImprovement && (
                  <button
                    onClick={() => {
                      onClose();
                      onApplyImprovement();
                    }}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white transition-colors shadow-sm"
                  >
                    <Sparkles className="w-3.5 h-3.5" />
                    AI Improve
                  </button>
                )}
              </div>

              {/* Priority Fix Banner */}
              {data.improvement_hint && (
                <div className="p-3.5 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs flex items-start gap-2.5">
                  <Sparkles className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
                  <div>
                    <span className="font-semibold block text-indigo-200">Doctor Recommendation</span>
                    <p className="text-indigo-300/90 mt-0.5">{data.improvement_hint}</p>
                  </div>
                </div>
              )}

              {/* Issues List */}
              <div className="space-y-3">
                <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                  Diagnostic Findings ({data.issues.length})
                </h4>

                {data.issues.length === 0 ? (
                  <div className="p-4 rounded-xl bg-slate-950/40 border border-slate-800/80 text-center text-slate-400 text-xs">
                    <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto mb-2 opacity-80" />
                    No structural or syntax defects identified in this requirement.
                  </div>
                ) : (
                  <div className="space-y-2.5">
                    {data.issues.map((issue, idx) => (
                      <div
                        key={idx}
                        className="p-3.5 rounded-xl bg-slate-950/40 border border-slate-800/80 flex items-start gap-3"
                      >
                        {getSeverityIcon(issue.severity)}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-xs font-bold text-white">{issue.category}</span>
                            <span className="text-[10px] uppercase font-mono px-1.5 py-0.2 rounded bg-slate-800 text-slate-400">
                              {issue.severity}
                            </span>
                          </div>
                          <p className="text-xs text-slate-300">{issue.description}</p>
                          <p className="text-xs text-indigo-400/90 mt-1 flex items-start gap-1">
                            <span className="font-semibold text-indigo-300">Suggestion:</span>
                            <span>{issue.suggestion}</span>
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </>
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
