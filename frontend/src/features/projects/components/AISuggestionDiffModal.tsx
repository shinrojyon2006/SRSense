import React from 'react';
import { Modal } from '@/components/ui/Modal';
import { Button } from '@/components/ui/Button';
import { AIImprovementResultPayload } from '@/services/aiService';
import { Sparkles, Check } from 'lucide-react';

interface AISuggestionDiffModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAccept: (improvedTitle: string, improvedDescription: string) => Promise<void>;
  originalTitle: string;
  originalDescription: string;
  suggestion: AIImprovementResultPayload | null;
  isLoading?: boolean;
}

export const AISuggestionDiffModal: React.FC<AISuggestionDiffModalProps> = ({
  isOpen,
  onClose,
  onAccept,
  originalTitle,
  originalDescription,
  suggestion,
  isLoading = false,
}) => {
  if (!suggestion) return null;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="AI Specification Improvement Suggestion (EARS Standard)"
    >
      <div className="space-y-4">
        <div className="flex items-center gap-2 rounded-lg bg-indigo-50 p-3 text-xs text-indigo-700 dark:bg-indigo-950/40 dark:text-indigo-300">
          <Sparkles className="h-4 w-4 shrink-0" />
          <p>{suggestion.explanation}</p>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {/* Original */}
          <div className="space-y-1.5 rounded-xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950">
            <span className="text-[10px] font-extrabold uppercase tracking-wider text-slate-400">
              Original Draft
            </span>
            <p className="text-xs font-bold text-slate-900 dark:text-white">
              {originalTitle}
            </p>
            <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
              {originalDescription}
            </p>
          </div>

          {/* AI Improved EARS */}
          <div className="space-y-1.5 rounded-xl border border-emerald-200 bg-emerald-50/50 p-4 dark:border-emerald-900/50 dark:bg-emerald-950/30">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-extrabold uppercase tracking-wider text-emerald-600 dark:text-emerald-400">
                AI EARS Standard Refactoring
              </span>
              <Sparkles className="h-3.5 w-3.5 text-emerald-500" />
            </div>
            <p className="text-xs font-bold text-slate-900 dark:text-white">
              {suggestion.improved_title}
            </p>
            <p className="text-xs text-slate-800 dark:text-slate-200 font-medium leading-relaxed">
              {suggestion.improved_description}
            </p>
          </div>
        </div>

        <div className="flex items-center justify-between pt-4 border-t border-slate-100 dark:border-slate-800">
          <span className="text-[11px] text-slate-400 italic">
            Syntax: {suggestion.ears_template_used}
          </span>

          <div className="flex items-center gap-3">
            <Button variant="secondary" onClick={onClose} disabled={isLoading}>
              Keep Original
            </Button>
            <Button
              onClick={() => onAccept(suggestion.improved_title, suggestion.improved_description)}
              isLoading={isLoading}
            >
              <Check className="h-4 w-4 mr-1" /> Accept AI Suggestion
            </Button>
          </div>
        </div>
      </div>
    </Modal>
  );
};
