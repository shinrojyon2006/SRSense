import React, { useState } from 'react';
import { Sparkles, Copy, Check, X, ShieldAlert, Code2, ListChecks, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { TestProposal } from '../types/traceability.types';

interface TestSuggestionModalProps {
  proposal: TestProposal | null;
  loading: boolean;
  onClose: () => void;
}

export const TestSuggestionModal: React.FC<TestSuggestionModalProps> = ({
  proposal,
  loading,
  onClose,
}) => {
  const [copied, setCopied] = useState(false);

  if (!proposal && !loading) return null;

  const handleCopy = () => {
    if (!proposal) return;
    const content = `// Test Proposal: ${proposal.test_title}
// Purpose: ${proposal.purpose}
// Requirement: ${proposal.requirement_title}
// Framework: ${proposal.suggested_framework} (${proposal.test_type})

${proposal.code_snippet_proposal}`;

    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-slate-900 border border-slate-800 rounded-3xl w-full max-w-3xl max-h-[85vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-950/50">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              <Sparkles className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-100">AI Test Proposal Generator</h3>
              <p className="text-xs text-slate-400">Bounded test code suggestion for missing coverage</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto space-y-5">
          {loading ? (
            <div className="py-16 text-center space-y-3">
              <Sparkles className="h-8 w-8 text-indigo-400 animate-spin mx-auto" />
              <p className="text-sm text-slate-300 font-medium">Generating test proposal from requirement context...</p>
              <p className="text-xs text-slate-500">Analyzing implementation logic & edge cases</p>
            </div>
          ) : proposal ? (
            <>
              {/* Safety Warning Banner */}
              <div className="bg-amber-500/10 border border-amber-500/20 rounded-2xl p-3.5 flex items-start gap-3">
                <ShieldAlert className="h-5 w-5 text-amber-400 shrink-0 mt-0.5" />
                <div className="text-xs text-amber-200 space-y-1">
                  <p className="font-bold">PROPOSAL ONLY — NON-AUTONOMOUS SAFETY NOTICE</p>
                  <p className="text-amber-300/80">
                    SRSense generates test code suggestions strictly for developer reference. It will NEVER automatically modify your codebase or write files to disk.
                  </p>
                </div>
              </div>

              {/* Requirement & Proposal Summary */}
              <div className="bg-slate-950 border border-slate-800 rounded-2xl p-4 space-y-3">
                <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-2.5">
                  <span className="text-xs font-bold text-slate-200 truncate">
                    Req: {proposal.requirement_title}
                  </span>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-800">
                      {proposal.test_type}
                    </span>
                    <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                      {proposal.suggested_framework}
                    </span>
                  </div>
                </div>

                <div>
                  <h4 className="text-sm font-extrabold text-indigo-400">{proposal.test_title}</h4>
                  <p className="text-xs text-slate-300 mt-1">{proposal.purpose}</p>
                </div>
              </div>

              {/* Test Steps & Validated Behavior */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Steps & Preconditions */}
                <div className="bg-slate-950/70 border border-slate-800 rounded-2xl p-4 space-y-3 text-xs">
                  <h5 className="font-bold text-slate-200 flex items-center gap-1.5">
                    <ListChecks className="h-4 w-4 text-emerald-400" /> Test Execution Flow
                  </h5>
                  {proposal.preconditions.length > 0 && (
                    <div>
                      <span className="text-[11px] font-semibold text-slate-400 block mb-1">Preconditions:</span>
                      <ul className="list-disc list-inside space-y-0.5 text-slate-300">
                        {proposal.preconditions.map((p, i) => (
                          <li key={i}>{p}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  <div>
                    <span className="text-[11px] font-semibold text-slate-400 block mb-1">Test Steps:</span>
                    <ol className="list-decimal list-inside space-y-1 text-slate-300">
                      {proposal.steps.map((s, i) => (
                        <li key={i}>{s}</li>
                      ))}
                    </ol>
                  </div>
                </div>

                {/* Validated Behavior & Edge Cases */}
                <div className="bg-slate-950/70 border border-slate-800 rounded-2xl p-4 space-y-3 text-xs">
                  <h5 className="font-bold text-slate-200 flex items-center gap-1.5">
                    <ArrowRight className="h-4 w-4 text-purple-400" /> Expected Outcome & Edge Cases
                  </h5>
                  <div>
                    <span className="text-[11px] font-semibold text-slate-400 block mb-1">Validated Behavior:</span>
                    <p className="text-emerald-400 font-mono text-[11px] bg-emerald-950/40 p-2 rounded-xl border border-emerald-800/40">
                      {proposal.validated_behavior}
                    </p>
                  </div>
                  {proposal.edge_cases.length > 0 && (
                    <div>
                      <span className="text-[11px] font-semibold text-slate-400 block mb-1">Edge Cases Addressed:</span>
                      <ul className="list-disc list-inside space-y-0.5 text-amber-300/90">
                        {proposal.edge_cases.map((e, i) => (
                          <li key={i}>{e}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>

              {/* Proposed Code Snippet */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <h5 className="text-xs font-bold text-slate-200 flex items-center gap-1.5">
                    <Code2 className="h-4 w-4 text-indigo-400" /> Code Snippet Proposal
                  </h5>
                  <Button
                    size="sm"
                    onClick={handleCopy}
                    className="bg-indigo-600 hover:bg-indigo-700 text-white text-[11px] font-bold px-3 py-1"
                  >
                    {copied ? (
                      <>
                        <Check className="h-3.5 w-3.5 mr-1" /> Copied!
                      </>
                    ) : (
                      <>
                        <Copy className="h-3.5 w-3.5 mr-1" /> [COPY TEST PROPOSAL]
                      </>
                    )}
                  </Button>
                </div>
                <pre className="bg-slate-950 border border-slate-800 rounded-2xl p-4 text-xs font-mono text-slate-200 overflow-x-auto max-h-60">
                  <code>{proposal.code_snippet_proposal}</code>
                </pre>
              </div>
            </>
          ) : null}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-slate-800 bg-slate-950/50">
          <span className="text-xs text-slate-500">SRSense Traceability & Test Intelligence</span>
          <div className="flex items-center gap-2">
            {proposal && (
              <Button
                size="sm"
                onClick={handleCopy}
                className="bg-indigo-600 hover:bg-indigo-700 text-white text-xs px-3 py-1.5"
              >
                {copied ? 'Copied' : '[COPY TEST PROPOSAL]'}
              </Button>
            )}
            <Button size="sm" variant="ghost" onClick={onClose} className="text-xs text-slate-400">
              Close
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};
