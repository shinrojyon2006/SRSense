import React, { useEffect, useRef, useState } from 'react';
import {
  AlertTriangle,
  Bot,
  Brain,
  CheckCircle2,
  ChevronRight,
  GitBranch,
  Loader2,
  RefreshCw,
  Save,
  Send,
  Shield,
  X,
} from 'lucide-react';
import { copilotService } from '../api/copilotService';
import {
  AIReviewResponse,
  ConfidenceLevel,
  CopilotChatMessage,
  GapFinderResponse,
  ProjectMemoryResponse,
  ReviewMode,
  TraceabilityResponse,
} from '../types';

interface CopilotPanelProps {
  isOpen: boolean;
  onClose: () => void;
  projectId: string;
  projectName?: string;
  onSelectRequirement?: (reqId: string) => void;
}

type TabType = 'chat' | 'review' | 'gaps' | 'traceability' | 'memory';

export const CopilotPanel: React.FC<CopilotPanelProps> = ({
  isOpen,
  onClose,
  projectId,
  projectName = 'Project',
  onSelectRequirement,
}) => {
  const [activeTab, setActiveTab] = useState<TabType>('chat');

  // ── Chat State ──────────────────────────────────────────────────────────
  const [messages, setMessages] = useState<CopilotChatMessage[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: `Hello! I am your Engineering AI Copilot for **${projectName}**. You can ask me about requirement counts, vague/ambiguous terms, quality scores, NFRs, or run deep specialized reviews across your specifications.`,
      confidence: 'EXPLICIT',
      timestamp: new Date(),
    },
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isSending, setIsSending] = useState(false);
  const chatBottomRef = useRef<HTMLDivElement>(null);

  // ── Review State ────────────────────────────────────────────────────────
  const [selectedMode, setSelectedMode] = useState<ReviewMode>('qa');
  const [reviewData, setReviewData] = useState<AIReviewResponse | null>(null);
  const [isReviewing, setIsReviewing] = useState(false);
  const [reviewError, setReviewError] = useState<string | null>(null);

  // ── Gap Finder State ────────────────────────────────────────────────────
  const [gapData, setGapData] = useState<GapFinderResponse | null>(null);
  const [isFindingGaps, setIsFindingGaps] = useState(false);
  const [gapError, setGapError] = useState<string | null>(null);

  // ── Traceability State ──────────────────────────────────────────────────
  const [traceData, setTraceData] = useState<TraceabilityResponse | null>(null);
  const [isTracing, setIsTracing] = useState(false);
  const [traceError, setTraceError] = useState<string | null>(null);

  // ── Project Memory State ────────────────────────────────────────────────
  const [memoryData, setMemoryData] = useState<ProjectMemoryResponse | null>(null);
  const [isLoadingMemory, setIsLoadingMemory] = useState(false);
  const [isSavingMemory, setIsSavingMemory] = useState(false);
  const [domainContextInput, setDomainContextInput] = useState('');
  const [newTermKey, setNewTermKey] = useState('');
  const [newTermVal, setNewTermVal] = useState('');
  const [memorySavedMsg, setMemorySavedMsg] = useState(false);

  useEffect(() => {
    if (chatBottomRef.current) {
      chatBottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isSending]);

  // Handle Send Chat
  const handleSendMessage = async () => {
    const q = inputMessage.trim();
    if (!q || isSending) return;

    const userMsg: CopilotChatMessage = {
      id: String(Date.now()),
      role: 'user',
      content: q,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputMessage('');
    setIsSending(true);

    try {
      const res = await copilotService.chat(projectId, q);
      const assistantMsg: CopilotChatMessage = {
        id: String(Date.now() + 1),
        role: 'assistant',
        content: res.answer,
        confidence: res.confidence,
        evidence: res.evidence,
        referencedIds: res.referenced_requirement_ids,
        caveats: res.caveats,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      const errorMsg: CopilotChatMessage = {
        id: String(Date.now() + 1),
        role: 'assistant',
        content:
          err?.response?.data?.detail ||
          'Failed to communicate with Engineering AI Copilot.',
        confidence: 'UNCERTAIN',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsSending(false);
    }
  };

  // Handle Review
  const handleRunReview = async (mode: ReviewMode) => {
    setSelectedMode(mode);
    setIsReviewing(true);
    setReviewError(null);
    try {
      const res = await copilotService.runReview(projectId, mode);
      setReviewData(res);
    } catch (err: any) {
      setReviewError(err?.response?.data?.detail || 'Review failed.');
    } finally {
      setIsReviewing(false);
    }
  };

  // Handle Gap Finder
  const handleFindGaps = async () => {
    setIsFindingGaps(true);
    setGapError(null);
    try {
      const res = await copilotService.findGaps(projectId);
      setGapData(res);
    } catch (err: any) {
      setGapError(err?.response?.data?.detail || 'Gap analysis failed.');
    } finally {
      setIsFindingGaps(false);
    }
  };

  // Handle Traceability
  const handleGetTraceability = async () => {
    setIsTracing(true);
    setTraceError(null);
    try {
      const res = await copilotService.getTraceability(projectId);
      setTraceData(res);
    } catch (err: any) {
      setTraceError(err?.response?.data?.detail || 'Traceability analysis failed.');
    } finally {
      setIsTracing(false);
    }
  };

  // Handle Memory Load
  const handleLoadMemory = async () => {
    setIsLoadingMemory(true);
    try {
      const res = await copilotService.getMemory(projectId);
      setMemoryData(res);
      setDomainContextInput(res.domain_context || '');
    } catch (err) {
      // Memory load failed
    } finally {
      setIsLoadingMemory(false);
    }
  };

  // Handle Memory Save
  const handleSaveMemory = async () => {
    if (!memoryData) return;
    setIsSavingMemory(true);
    try {
      const res = await copilotService.updateMemory(projectId, {
        domain_context: domainContextInput,
        terminology: memoryData.terminology,
        personas: memoryData.personas,
      });
      setMemoryData(res);
      setMemorySavedMsg(true);
      setTimeout(() => setMemorySavedMsg(false), 2500);
    } catch (err) {
      // Error saving
    } finally {
      setIsSavingMemory(false);
    }
  };

  const handleAddTerm = () => {
    if (!newTermKey.trim() || !newTermVal.trim() || !memoryData) return;
    setMemoryData({
      ...memoryData,
      terminology: {
        ...memoryData.terminology,
        [newTermKey.trim()]: newTermVal.trim(),
      },
    });
    setNewTermKey('');
    setNewTermVal('');
  };

  const handleDeleteTerm = (key: string) => {
    if (!memoryData) return;
    const next = { ...memoryData.terminology };
    delete next[key];
    setMemoryData({ ...memoryData, terminology: next });
  };

  useEffect(() => {
    if (!isOpen) return;
    if (activeTab === 'review' && !reviewData) handleRunReview('qa');
    if (activeTab === 'gaps' && !gapData) handleFindGaps();
    if (activeTab === 'traceability' && !traceData) handleGetTraceability();
    if (activeTab === 'memory' && !memoryData) handleLoadMemory();
  }, [isOpen, activeTab]);

  if (!isOpen) return null;

  const getConfidenceBadge = (confidence?: ConfidenceLevel) => {
    if (!confidence) return null;
    if (confidence === 'EXPLICIT') {
      return (
        <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          Explicit
        </span>
      );
    }
    if (confidence === 'INFERRED') {
      return (
        <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">
          Inferred
        </span>
      );
    }
    return (
      <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">
        Uncertain
      </span>
    );
  };

  return (
    <div className="fixed inset-y-0 right-0 z-40 w-full max-w-2xl bg-slate-900 border-l border-slate-800 shadow-2xl flex flex-col animate-in slide-in-from-right duration-200">
      {/* Header */}
      <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/90 shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-purple-600 flex items-center justify-center text-white shadow-lg shadow-indigo-500/20">
            <Bot className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-white">Engineering AI Copilot</h3>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                Sprint 1.9
              </span>
            </div>
            <p className="text-xs text-slate-400">Scoped reasoning over actual project specifications</p>
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Navigation Tabs */}
      <div className="px-6 border-b border-slate-800 flex gap-2 overflow-x-auto bg-slate-950/40 shrink-0">
        <button
          onClick={() => setActiveTab('chat')}
          className={`px-3.5 py-2.5 text-xs font-semibold border-b-2 transition-colors flex items-center gap-1.5 whitespace-nowrap ${
            activeTab === 'chat'
              ? 'border-indigo-500 text-indigo-400 bg-indigo-500/5'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Bot className="w-3.5 h-3.5" /> Chat
        </button>
        <button
          onClick={() => setActiveTab('review')}
          className={`px-3.5 py-2.5 text-xs font-semibold border-b-2 transition-colors flex items-center gap-1.5 whitespace-nowrap ${
            activeTab === 'review'
              ? 'border-indigo-500 text-indigo-400 bg-indigo-500/5'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Shield className="w-3.5 h-3.5" /> AI Review Modes
        </button>
        <button
          onClick={() => setActiveTab('gaps')}
          className={`px-3.5 py-2.5 text-xs font-semibold border-b-2 transition-colors flex items-center gap-1.5 whitespace-nowrap ${
            activeTab === 'gaps'
              ? 'border-indigo-500 text-indigo-400 bg-indigo-500/5'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <AlertTriangle className="w-3.5 h-3.5" /> Gap Finder
        </button>
        <button
          onClick={() => setActiveTab('traceability')}
          className={`px-3.5 py-2.5 text-xs font-semibold border-b-2 transition-colors flex items-center gap-1.5 whitespace-nowrap ${
            activeTab === 'traceability'
              ? 'border-indigo-500 text-indigo-400 bg-indigo-500/5'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <GitBranch className="w-3.5 h-3.5" /> Traceability
        </button>
        <button
          onClick={() => setActiveTab('memory')}
          className={`px-3.5 py-2.5 text-xs font-semibold border-b-2 transition-colors flex items-center gap-1.5 whitespace-nowrap ${
            activeTab === 'memory'
              ? 'border-indigo-500 text-indigo-400 bg-indigo-500/5'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Brain className="w-3.5 h-3.5" /> Project Memory
        </button>
      </div>

      {/* Body Area */}
      <div className="flex-1 overflow-y-auto p-6">
        {/* ── TAB 1: CHAT ───────────────────────────────────────────────── */}
        {activeTab === 'chat' && (
          <div className="flex flex-col h-full space-y-4">
            <div className="flex-1 space-y-3 overflow-y-auto pr-1">
              {messages.map((m) => (
                <div
                  key={m.id}
                  className={`flex gap-3 ${
                    m.role === 'user' ? 'justify-end' : 'justify-start'
                  }`}
                >
                  {m.role === 'assistant' && (
                    <div className="w-7 h-7 rounded-lg bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 shrink-0 mt-0.5">
                      <Bot className="w-4 h-4" />
                    </div>
                  )}

                  <div
                    className={`max-w-[85%] rounded-2xl p-3.5 text-xs space-y-2 leading-relaxed ${
                      m.role === 'user'
                        ? 'bg-indigo-600 text-white rounded-br-none'
                        : 'bg-slate-950 border border-slate-800 text-slate-200 rounded-bl-none shadow-sm'
                    }`}
                  >
                    <p className="whitespace-pre-wrap">{m.content}</p>

                    {m.role === 'assistant' && (
                      <div className="pt-2 border-t border-slate-800/80 space-y-1.5">
                        <div className="flex items-center justify-between text-[10px] text-slate-500">
                          {getConfidenceBadge(m.confidence)}
                          <span>{m.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                        </div>

                        {m.evidence && m.evidence.length > 0 && (
                          <div className="text-[11px] text-slate-400 bg-slate-900/80 p-2 rounded border border-slate-800/50">
                            <span className="font-semibold text-slate-300 block mb-0.5">Evidence Base:</span>
                            {m.evidence.map((ev, idx) => (
                              <p key={idx} className="flex items-start gap-1 text-[10px]">
                                <span className="text-indigo-400">•</span>
                                <span>{ev}</span>
                              </p>
                            ))}
                          </div>
                        )}

                        {m.referencedIds && m.referencedIds.length > 0 && onSelectRequirement && (
                          <div className="flex items-center gap-1.5 flex-wrap pt-1">
                            <span className="text-[10px] text-slate-400">Referenced:</span>
                            {m.referencedIds.map((rId) => (
                              <button
                                key={rId}
                                onClick={() => onSelectRequirement(rId)}
                                className="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-300 hover:bg-indigo-500/20 border border-indigo-500/30 transition-colors"
                              >
                                View Specification
                              </button>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {isSending && (
                <div className="flex gap-3 items-center text-slate-400 text-xs">
                  <div className="w-7 h-7 rounded-lg bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 shrink-0">
                    <Loader2 className="w-4 h-4 animate-spin" />
                  </div>
                  <span>Reasoning over project requirements...</span>
                </div>
              )}
              <div ref={chatBottomRef} />
            </div>

            {/* Chat Input */}
            <div className="pt-2 border-t border-slate-800 flex gap-2 shrink-0">
              <input
                type="text"
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
                placeholder="Ask about project requirements, quality, NFRs, dependencies..."
                className="flex-1 rounded-xl bg-slate-950 border border-slate-800 px-3.5 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
              />
              <button
                onClick={handleSendMessage}
                disabled={isSending || !inputMessage.trim()}
                className="px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white transition-colors flex items-center justify-center"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* ── TAB 2: AI REVIEW MODES ────────────────────────────────────── */}
        {activeTab === 'review' && (
          <div className="space-y-5">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-400">Select specialized engineering lens:</span>
              <button
                onClick={() => handleRunReview(selectedMode)}
                disabled={isReviewing}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 transition-colors"
              >
                {isReviewing ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5" />}
                Re-scan
              </button>
            </div>

            {/* Lens Selector */}
            <div className="grid grid-cols-5 gap-2">
              {(['qa', 'security', 'performance', 'product', 'architecture'] as ReviewMode[]).map((mode) => (
                <button
                  key={mode}
                  onClick={() => handleRunReview(mode)}
                  className={`p-2.5 rounded-xl border text-xs font-semibold capitalize transition-all text-center ${
                    selectedMode === mode
                      ? 'bg-indigo-600 border-indigo-500 text-white shadow-md'
                      : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-white hover:border-slate-700'
                  }`}
                >
                  {mode}
                </button>
              ))}
            </div>

            {isReviewing && (
              <div className="py-16 flex flex-col items-center justify-center gap-2 text-slate-400 text-xs">
                <Loader2 className="w-6 h-6 animate-spin text-indigo-500" />
                <span>Running {selectedMode.toUpperCase()} lens analysis...</span>
              </div>
            )}

            {reviewError && (
              <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs">
                {reviewError}
              </div>
            )}

            {!isReviewing && reviewData && (
              <div className="space-y-4 animate-in fade-in duration-150">
                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-xs space-y-1">
                  <span className="font-bold text-white block">Review Summary</span>
                  <p className="text-slate-300">{reviewData.summary}</p>
                </div>

                <div className="space-y-2.5">
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                    Findings ({reviewData.findings.length})
                  </h4>

                  {reviewData.findings.length === 0 ? (
                    <div className="p-4 rounded-xl bg-slate-950/40 border border-slate-800 text-center text-xs text-slate-400">
                      <CheckCircle2 className="w-6 h-6 text-emerald-400 mx-auto mb-1.5 opacity-80" />
                      No defects found under the {selectedMode.toUpperCase()} lens.
                    </div>
                  ) : (
                    reviewData.findings.map((f, idx) => (
                      <div
                        key={idx}
                        className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2 text-xs"
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-white truncate max-w-xs">
                            {f.requirement_title || 'Project-Wide Finding'}
                          </span>
                          <div className="flex items-center gap-1.5">
                            <span
                              className={`text-[10px] font-mono uppercase px-1.5 py-0.2 rounded ${
                                f.severity === 'critical'
                                  ? 'bg-rose-500/20 text-rose-300'
                                  : f.severity === 'warning'
                                  ? 'bg-amber-500/20 text-amber-300'
                                  : 'bg-blue-500/20 text-blue-300'
                              }`}
                            >
                              {f.severity}
                            </span>
                            {getConfidenceBadge(f.confidence)}
                          </div>
                        </div>

                        <p className="text-slate-300">{f.finding}</p>

                        <div className="p-2.5 rounded bg-slate-900 border border-slate-800 text-slate-400 flex items-start gap-1.5">
                          <span className="font-bold text-indigo-300 shrink-0">Recommendation:</span>
                          <span className="text-slate-300">{f.recommendation}</span>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {/* ── TAB 3: GAP FINDER ─────────────────────────────────────────── */}
        {activeTab === 'gaps' && (
          <div className="space-y-5">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-400">Identify missing requirements and specification blind spots:</span>
              <button
                onClick={handleFindGaps}
                disabled={isFindingGaps}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 transition-colors"
              >
                {isFindingGaps ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5" />}
                Scan Gaps
              </button>
            </div>

            {isFindingGaps && (
              <div className="py-16 flex flex-col items-center justify-center gap-2 text-slate-400 text-xs">
                <Loader2 className="w-6 h-6 animate-spin text-indigo-500" />
                <span>Scanning requirements for structural blind spots...</span>
              </div>
            )}

            {gapError && (
              <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs">
                {gapError}
              </div>
            )}

            {!isFindingGaps && gapData && (
              <div className="space-y-4 animate-in fade-in duration-150">
                {/* Score Header */}
                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between">
                  <div>
                    <span className="text-xs text-slate-400 block mb-1">Specification Coverage Score</span>
                    <span className="text-xl font-bold text-white">
                      {gapData.coverage_score}%{' '}
                      <span className="text-xs font-normal text-slate-400">
                        ({gapData.total_gaps_found} gap categories detected)
                      </span>
                    </span>
                  </div>
                  <div className="w-12 h-12 rounded-full border-2 border-indigo-500/40 flex items-center justify-center text-xs font-mono font-bold text-indigo-400">
                    {gapData.coverage_score}%
                  </div>
                </div>

                <div className="space-y-2.5">
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                    Recommended Additions ({gapData.gaps.length})
                  </h4>

                  {gapData.gaps.length === 0 ? (
                    <div className="p-4 rounded-xl bg-slate-950/40 border border-slate-800 text-center text-xs text-slate-400">
                      <CheckCircle2 className="w-6 h-6 text-emerald-400 mx-auto mb-1.5 opacity-80" />
                      Requirements suite is well-rounded. No major category blind spots found.
                    </div>
                  ) : (
                    gapData.gaps.map((gap, idx) => (
                      <div
                        key={idx}
                        className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2 text-xs"
                      >
                        <div className="flex items-center justify-between">
                          <h5 className="font-bold text-white">{gap.title}</h5>
                          {getConfidenceBadge(gap.confidence)}
                        </div>

                        <p className="text-slate-300">{gap.description}</p>

                        <div className="p-2.5 rounded bg-indigo-500/5 border border-indigo-500/20 text-indigo-300 text-[11px]">
                          <span className="font-bold text-indigo-200">Rationale: </span>
                          <span>{gap.rationale}</span>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {/* ── TAB 4: TRACEABILITY ───────────────────────────────────────── */}
        {activeTab === 'traceability' && (
          <div className="space-y-5">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-400">Dependency chain reasoning and orphan analysis:</span>
              <button
                onClick={handleGetTraceability}
                disabled={isTracing}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 transition-colors"
              >
                {isTracing ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5" />}
                Analyze
              </button>
            </div>

            {isTracing && (
              <div className="py-16 flex flex-col items-center justify-center gap-2 text-slate-400 text-xs">
                <Loader2 className="w-6 h-6 animate-spin text-indigo-500" />
                <span>Tracing requirement relationships...</span>
              </div>
            )}

            {traceError && (
              <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs">
                {traceError}
              </div>
            )}

            {!isTracing && traceData && (
              <div className="space-y-4 animate-in fade-in duration-150">
                {/* Stats Bar */}
                <div className="grid grid-cols-3 gap-3 text-xs">
                  <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                    <span className="text-slate-400 block text-[11px]">Total Links</span>
                    <span className="text-lg font-bold text-white">{traceData.total_links}</span>
                  </div>
                  <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                    <span className="text-slate-400 block text-[11px]">Orphan Count</span>
                    <span className="text-lg font-bold text-amber-400">{traceData.orphaned_requirement_ids.length}</span>
                  </div>
                  <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                    <span className="text-slate-400 block text-[11px]">Coverage</span>
                    <span className="text-lg font-bold text-emerald-400">{traceData.coverage_percentage}%</span>
                  </div>
                </div>

                {/* Explanations */}
                <div className="space-y-2.5">
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                    Relationship Explanations ({traceData.links.length})
                  </h4>

                  {traceData.links.length === 0 ? (
                    <div className="p-4 rounded-xl bg-slate-950/40 border border-slate-800 text-center text-xs text-slate-400">
                      No dependency links established yet. Connect specifications via the Knowledge Graph.
                    </div>
                  ) : (
                    traceData.links.map((link, idx) => (
                      <div
                        key={idx}
                        className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2 text-xs"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-1.5 font-bold text-white">
                            <span className="truncate max-w-[140px]">{link.from_title}</span>
                            <ChevronRight className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                            <span className="truncate max-w-[140px] text-indigo-300">{link.to_title}</span>
                          </div>
                          <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">
                            {link.relationship_type}
                          </span>
                        </div>

                        <p className="text-slate-300 text-[11px] bg-slate-900/60 p-2.5 rounded border border-slate-800/80">
                          {link.explanation}
                        </p>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {/* ── TAB 5: PROJECT MEMORY ─────────────────────────────────────── */}
        {activeTab === 'memory' && (
          <div className="space-y-5">
            <div className="flex items-center justify-between">
              <span className="text-xs text-slate-400">
                Shared domain terminology & vocabulary for this project:
              </span>
              <button
                onClick={handleSaveMemory}
                disabled={isSavingMemory}
                className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white transition-colors shadow-sm"
              >
                {isSavingMemory ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
                Save Changes
              </button>
            </div>

            {memorySavedMsg && (
              <div className="p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4" /> Memory updated successfully.
              </div>
            )}

            {isLoadingMemory ? (
              <div className="py-16 flex flex-col items-center justify-center gap-2 text-slate-400 text-xs">
                <Loader2 className="w-6 h-6 animate-spin text-indigo-500" />
                <span>Loading project memory...</span>
              </div>
            ) : (
              <div className="space-y-5">
                {/* Domain Context */}
                <div className="space-y-1.5">
                  <label className="block text-xs font-bold text-slate-300">
                    Domain Background & Project Context:
                  </label>
                  <textarea
                    rows={3}
                    value={domainContextInput}
                    onChange={(e) => setDomainContextInput(e.target.value)}
                    placeholder="e.g. Healthcare portal subject to HIPAA compliance, handling encrypted EHR records..."
                    className="w-full rounded-xl bg-slate-950 border border-slate-800 p-3 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500 font-mono"
                  />
                </div>

                {/* Terminology List */}
                <div className="space-y-2.5">
                  <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                    Domain Vocabulary & Acronyms
                  </h4>

                  <div className="flex gap-2">
                    <input
                      type="text"
                      placeholder="Term (e.g. SLA)"
                      value={newTermKey}
                      onChange={(e) => setNewTermKey(e.target.value)}
                      className="w-1/3 rounded-lg bg-slate-950 border border-slate-800 px-3 py-1.5 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500"
                    />
                    <input
                      type="text"
                      placeholder="Definition / Meaning"
                      value={newTermVal}
                      onChange={(e) => setNewTermVal(e.target.value)}
                      className="flex-1 rounded-lg bg-slate-950 border border-slate-800 px-3 py-1.5 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500"
                    />
                    <button
                      onClick={handleAddTerm}
                      className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold transition-colors"
                    >
                      Add
                    </button>
                  </div>

                  <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
                    {memoryData && Object.keys(memoryData.terminology || {}).length === 0 ? (
                      <p className="text-xs text-slate-500 italic">No custom terminology defined yet.</p>
                    ) : (
                      Object.entries(memoryData?.terminology || {}).map(([key, val]) => (
                        <div
                          key={key}
                          className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800 flex items-center justify-between text-xs"
                        >
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-indigo-400">{key}:</span>
                            <span className="text-slate-300">{val}</span>
                          </div>
                          <button
                            onClick={() => handleDeleteTerm(key)}
                            className="text-slate-500 hover:text-rose-400 p-1 transition-colors"
                          >
                            <X className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
