import React from 'react';
import { ArrowRight, TrendingUp, TrendingDown, Minus, Shield, Zap, Wrench, CheckCircle, Award } from 'lucide-react';
import { CodeImprovementEvaluation } from '../types/codeEvaluation.types';

interface ScoreDeltaCardsProps {
  evaluation: CodeImprovementEvaluation;
}

export const ScoreDeltaCards: React.FC<ScoreDeltaCardsProps> = ({ evaluation }) => {
  const { before_score, after_score, score_delta, before_health, after_health, category_scores } = evaluation;

  const renderHealthBadge = (health: string) => {
    const h = health.toLowerCase();
    if (h === 'healthy') {
      return (
        <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          HEALTHY
        </span>
      );
    }
    if (h === 'needs_attention') {
      return (
        <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
          NEEDS ATTENTION
        </span>
      );
    }
    return (
      <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-red-500/10 text-red-400 border border-red-500/20">
        AT RISK
      </span>
    );
  };

  const getDeltaBadge = (delta: number) => {
    if (delta > 0) {
      return (
        <div className="flex items-center gap-1 text-emerald-400 font-bold text-sm bg-emerald-500/10 px-3 py-1 rounded-full border border-emerald-500/20">
          <TrendingUp className="h-4 w-4" /> +{delta} Points
        </div>
      );
    }
    if (delta < 0) {
      return (
        <div className="flex items-center gap-1 text-red-400 font-bold text-sm bg-red-500/10 px-3 py-1 rounded-full border border-red-500/20">
          <TrendingDown className="h-4 w-4" /> {delta} Points
        </div>
      );
    }
    return (
      <div className="flex items-center gap-1 text-slate-400 font-bold text-sm bg-slate-800 px-3 py-1 rounded-full border border-slate-700">
        <Minus className="h-4 w-4" /> 0 Points Change
      </div>
    );
  };

  const getCategoryIcon = (category: string) => {
    switch (category.toLowerCase()) {
      case 'security':
        return <Shield className="h-4 w-4 text-emerald-400" />;
      case 'performance':
        return <Zap className="h-4 w-4 text-amber-400" />;
      case 'maintainability':
        return <Wrench className="h-4 w-4 text-indigo-400" />;
      case 'compliance':
        return <Award className="h-4 w-4 text-purple-400" />;
      default:
        return <CheckCircle className="h-4 w-4 text-blue-400" />;
    }
  };

  return (
    <div className="space-y-4">
      {/* Primary Score Comparison Banner */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 backdrop-blur-sm">
        <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4 flex items-center justify-between">
          <span>Overall Quality Evaluation Score</span>
          {getDeltaBadge(score_delta)}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-center">
          {/* BEFORE */}
          <div className="bg-slate-950/70 p-4 rounded-xl border border-slate-800/80 text-center space-y-1">
            <span className="text-xs font-medium text-slate-400 uppercase">BEFORE FIX</span>
            <div className="text-3xl font-extrabold text-slate-200">{before_score}/100</div>
            <div className="pt-1">{renderHealthBadge(before_health)}</div>
          </div>

          {/* ARROW */}
          <div className="flex flex-col items-center justify-center text-slate-500">
            <ArrowRight className="h-8 w-8 text-indigo-400 hidden md:block" />
            <span className="text-[11px] font-mono text-slate-400 mt-1">Re-Analysis Scan</span>
          </div>

          {/* AFTER */}
          <div className="bg-slate-950/70 p-4 rounded-xl border border-slate-800/80 text-center space-y-1">
            <span className="text-xs font-medium text-slate-400 uppercase">AFTER FIX</span>
            <div className="text-3xl font-extrabold text-emerald-400">{after_score}/100</div>
            <div className="pt-1">{renderHealthBadge(after_health)}</div>
          </div>
        </div>
      </div>

      {/* Category Breakdown Cards */}
      {category_scores && Object.keys(category_scores).length > 0 && (
        <div className="space-y-2">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 px-1">
            Category Breakdown Deltas
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
            {Object.entries(category_scores).map(([category, item]) => {
              const delta = item.delta;
              let deltaColor = 'text-slate-400';
              if (delta < 0) deltaColor = 'text-emerald-400 font-bold'; // fewer issues
              if (delta > 0) deltaColor = 'text-red-400 font-bold'; // more issues

              return (
                <div
                  key={category}
                  className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-3.5 flex items-center justify-between"
                >
                  <div className="flex items-center gap-2.5">
                    <div className="p-2 bg-slate-800/80 rounded-lg">{getCategoryIcon(category)}</div>
                    <div>
                      <div className="text-xs font-bold text-slate-200 capitalize">{category}</div>
                      <div className="text-[11px] text-slate-400">
                        {item.before} → {item.after} issues
                      </div>
                    </div>
                  </div>
                  <div className={`text-xs ${deltaColor}`}>
                    {delta < 0 ? `${delta} issues` : delta > 0 ? `+${delta} issues` : 'No change'}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
