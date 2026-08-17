import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { projectService } from '@/services/projectService';
import { requirementService } from '@/services/requirementService';
import { aiService, AIImprovementResultPayload } from '@/services/aiService';
import { documentService } from '../../documents/api/documentService';
import { extractionService } from '../../documents/api/extractionService';
import { intelligenceService } from '../../intelligence/api/intelligenceService';
import { impactService } from '../../impact/api/impactService';
import { verificationService } from '../../verification/api/verificationService';
import { Document, CandidateRequirement } from '../../documents/types/document.types';
import { DocumentUploadModal } from '../../documents/components/DocumentUploadModal';
import { ExtractionPreviewModal } from '../../documents/components/ExtractionPreviewModal';
import { CandidateReviewWorkspace } from '../../documents/components/CandidateReviewWorkspace';
import { DocumentListCard } from '../../documents/components/DocumentListCard';
import { RequirementRelationshipModal } from '../../graph/components/RequirementRelationshipModal';
import { IntelligenceSummaryCard } from '../../intelligence/components/IntelligenceSummaryCard';
import { SuggestionReviewWorkspace } from '../../intelligence/components/SuggestionReviewWorkspace';
import { ImpactSummaryCard } from '../../impact/components/ImpactSummaryCard';
import { WhatIfSimulatorModal } from '../../impact/components/WhatIfSimulatorModal';
import { VerificationSummaryCard } from '../../verification/components/VerificationSummaryCard';
import { RequirementVerificationPanel } from '../../verification/components/RequirementVerificationPanel';

import {
  Project,
  Requirement,
  RequirementCreateInput,
  IntelligenceSummaryResponse,
  ProjectRiskSummaryResponse,
  ProjectVerificationSummaryResponse,
} from '@/types';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Modal } from '@/components/ui/Modal';
import { RequirementTable } from '../components/RequirementTable';
import { RequirementModal } from '../components/RequirementModal';
import { AIAnalysisCard } from '../components/AIAnalysisCard';
import { AISuggestionDiffModal } from '../components/AISuggestionDiffModal';
import { ArrowLeft, Plus, Search, Layers, AlertCircle, Download, FileText } from 'lucide-react';

export const ProjectDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [project, setProject] = useState<Project | null>(null);
  const [requirements, setRequirements] = useState<Requirement[]>([]);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [intelSummary, setIntelSummary] = useState<IntelligenceSummaryResponse | null>(null);
  const [impactSummary, setImpactSummary] = useState<ProjectRiskSummaryResponse | null>(null);
  const [verifSummary, setVerifSummary] = useState<ProjectVerificationSummaryResponse | null>(null);
  const [selectedReqForAnalysis, setSelectedReqForAnalysis] = useState<Requirement | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isScanning, setIsScanning] = useState(false);
  const [error, setError] = useState('');

  // Filters
  const [search, setSearch] = useState('');
  const [selectedType, setSelectedType] = useState<string>('all');
  const [selectedPriority, setSelectedPriority] = useState<string>('all');
  const [selectedStatus, setSelectedStatus] = useState<string>('all');

  // Modals
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingReq, setEditingReq] = useState<Requirement | null>(null);
  const [deletingReq, setDeletingReq] = useState<Requirement | null>(null);
  const [improvingReq, setImprovingReq] = useState<Requirement | null>(null);
  const [aiSuggestion, setAiSuggestion] = useState<AIImprovementResultPayload | null>(null);

  // Ingestion State & Modals
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [isPreviewModalOpen, setIsPreviewModalOpen] = useState(false);
  const [previewDoc, setPreviewDoc] = useState<Document | null>(null);
  const [isReviewWorkspaceOpen, setIsReviewWorkspaceOpen] = useState(false);
  const [extractedCandidates, setExtractedCandidates] = useState<CandidateRequirement[]>([]);
  const [activeExtractDoc, setActiveExtractDoc] = useState<Document | null>(null);

  // Graph, Intelligence, Impact & Verification Modal States
  const [isGraphModalOpen, setIsGraphModalOpen] = useState(false);
  const [graphReq, setGraphReq] = useState<Requirement | null>(null);
  const [isIntelWorkspaceOpen, setIsIntelWorkspaceOpen] = useState(false);
  const [isImpactSimulatorOpen, setIsImpactSimulatorOpen] = useState(false);
  const [simulatingReq, setSimulatingReq] = useState<Requirement | null>(null);
  const [isVerifPanelOpen, setIsVerifPanelOpen] = useState(false);
  const [verifReq, setVerifReq] = useState<Requirement | null>(null);

  const [analyzingId, setAnalyzingId] = useState<string | null>(null);
  const [improvingId, setImprovingId] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchProjectAndRequirements = useCallback(async () => {
    if (!id) return;
    try {
      setIsLoading(true);
      setError('');

      const params: any = {};
      if (search) params.search = search;
      if (selectedType !== 'all') params.type = selectedType;
      if (selectedPriority !== 'all') params.priority = selectedPriority;
      if (selectedStatus !== 'all') params.status = selectedStatus;

      // 1. Fetch core Project & Requirements workspace
      const [projData, reqsData] = await Promise.all([
        projectService.getProject(id),
        requirementService.getRequirements(id, params),
      ]);

      setProject(projData);
      setRequirements(reqsData);

      if (selectedReqForAnalysis) {
        const updatedReq = reqsData.find((r) => r.id === selectedReqForAnalysis.id);
        if (updatedReq) setSelectedReqForAnalysis(updatedReq);
      }

      // 2. Fetch secondary panel summaries independently without blocking requirements workspace
      documentService.getDocuments(id).then(setDocuments).catch(() => setDocuments([]));
      intelligenceService.getSummary(id).then(setIntelSummary).catch(() => setIntelSummary(null));
      impactService.getSummary(id).then(setImpactSummary).catch(() => setImpactSummary(null));
      verificationService.getSummary(id).then(setVerifSummary).catch(() => setVerifSummary(null));
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to load project requirements workspace');
    } finally {
      setIsLoading(false);
    }
  }, [id, search, selectedType, selectedPriority, selectedStatus, selectedReqForAnalysis?.id]);

  useEffect(() => {
    fetchProjectAndRequirements();
  }, [fetchProjectAndRequirements]);

  const handleRunIntelligenceScan = async () => {
    if (!id) return;
    try {
      setIsScanning(true);
      await intelligenceService.runScan(id);
      await fetchProjectAndRequirements();
    } catch (err: any) {
      setError('Intelligence scan failed.');
    } finally {
      setIsScanning(false);
    }
  };

  const handleCreateOrUpdate = async (data: RequirementCreateInput) => {
    if (!id) return;
    try {
      setIsSubmitting(true);
      if (editingReq) {
        await requirementService.updateRequirement(id, editingReq.id, data);
      } else {
        await requirementService.createRequirement(id, data);
      }
      await fetchProjectAndRequirements();
      setEditingReq(null);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCommitSimulatorEdits = async (reqId: string, title: string, description: string) => {
    if (!id) return;
    await requirementService.updateRequirement(id, reqId, { title, description });
    await fetchProjectAndRequirements();
  };

  const handleDelete = async () => {
    if (!id || !deletingReq) return;
    try {
      setIsSubmitting(true);
      await requirementService.deleteRequirement(id, deletingReq.id);
      await fetchProjectAndRequirements();
      setDeletingReq(null);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleAnalyze = async (req: Requirement) => {
    if (!id) return;
    try {
      setAnalyzingId(req.id);
      const updated = await aiService.analyzeRequirement(id, req.id);
      setSelectedReqForAnalysis(updated);
      await fetchProjectAndRequirements();
    } catch (err: any) {
      setError('AI Analysis failed for requirement.');
    } finally {
      setAnalyzingId(null);
    }
  };

  const handleImprove = async (req: Requirement) => {
    if (!id) return;
    try {
      setImprovingId(req.id);
      const suggestion = await aiService.improveRequirement(id, req.id);
      setImprovingReq(req);
      setAiSuggestion(suggestion);
    } catch (err: any) {
      setError('AI Improvement suggestion failed.');
    } finally {
      setImprovingId(null);
    }
  };

  const handleAcceptSuggestion = async (improvedTitle: string, improvedDescription: string) => {
    if (!id || !improvingReq) return;
    try {
      setIsSubmitting(true);
      await requirementService.updateRequirement(id, improvingReq.id, {
        title: improvedTitle,
        description: improvedDescription,
      });
      await fetchProjectAndRequirements();
      setImprovingReq(null);
      setAiSuggestion(null);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleExportSrs = async (format: 'markdown' | 'json') => {
    if (!id || !project) return;
    try {
      const data = await aiService.exportSrsDocument(id, format);
      const blob = new Blob([format === 'json' ? JSON.stringify(data, null, 2) : data.content || ''], {
        type: format === 'json' ? 'application/json' : 'text/markdown',
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = data.filename || `SRS_${project.title}.${format === 'json' ? 'json' : 'md'}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err: any) {
      setError('Failed to export SRS document.');
    }
  };

  // Ingestion Handlers
  const handleUploadSuccess = (doc: Document) => {
    setIsUploadModalOpen(false);
    setPreviewDoc(doc);
    setIsPreviewModalOpen(true);
    fetchProjectAndRequirements();
  };

  const handleStartExtraction = async (docId: string) => {
    if (!id) return;
    try {
      setIsLoading(true);
      const doc = documents.find((d) => d.id === docId) || previewDoc;
      if (doc) setActiveExtractDoc(doc);

      const res = await extractionService.extractCandidates(id, docId);
      setExtractedCandidates(res.candidates);
      setIsPreviewModalOpen(false);
      setIsReviewWorkspaceOpen(true);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Requirement extraction failed.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteDocument = async (docId: string) => {
    if (!id) return;
    try {
      await documentService.deleteDocument(id, docId);
      await fetchProjectAndRequirements();
    } catch (err: any) {
      setError('Failed to delete document.');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header & Navigation */}
      <div>
        <button
          onClick={() => navigate('/projects')}
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white mb-2 transition-colors"
        >
          <ArrowLeft className="h-3.5 w-3.5" /> Back to Projects
        </button>

        {project && (
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between rounded-xl border border-slate-200 bg-white p-6 shadow-xs dark:border-slate-800 dark:bg-slate-900">
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-xl font-bold text-slate-900 dark:text-white">
                  {project.title}
                </h1>
                <Badge variant={project.status === 'active' ? 'success' : 'neutral'}>
                  {project.status}
                </Badge>
              </div>
              <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                {project.description || 'No description provided.'}
              </p>
            </div>

            <div className="flex items-center gap-2">
              <div className="flex items-center gap-1.5 rounded-lg border border-slate-100 bg-slate-50 px-3 py-2 text-xs font-medium dark:border-slate-800 dark:bg-slate-950">
                <Layers className="h-4 w-4 text-indigo-500" />
                <span className="text-slate-600 dark:text-slate-300">
                  {project.requirement_count} Specifications
                </span>
              </div>

              <Button
                variant="secondary"
                onClick={() => setIsUploadModalOpen(true)}
                title="Ingest SRS Document (PDF, DOCX, TXT)"
              >
                <FileText className="h-4 w-4 mr-1 text-indigo-400" /> Ingest SRS Document
              </Button>

              <Button variant="secondary" onClick={() => handleExportSrs('markdown')} title="Export SRS Markdown">
                <Download className="h-4 w-4 mr-1" /> Export SRS
              </Button>

              <Button onClick={() => { setEditingReq(null); setIsModalOpen(true); }}>
                <Plus className="h-4 w-4 mr-1" /> Add Requirement
              </Button>
            </div>
          </div>
        )}
      </div>

      {error && (
        <div className="rounded-xl bg-red-50 p-4 text-xs font-medium text-red-600 dark:bg-red-950/40 dark:text-red-400 flex items-center gap-2">
          <AlertCircle className="h-4 w-4" /> {error}
        </div>
      )}

      {/* Verification Compiler Summary Card (Sprint 1.8) */}
      <VerificationSummaryCard summary={verifSummary} />

      {/* Intelligence & Impact Analytics Grid (Sprint 1.6 & Sprint 1.7) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <IntelligenceSummaryCard
          summary={intelSummary}
          isScanning={isScanning}
          onRunScan={handleRunIntelligenceScan}
          onOpenWorkspace={() => setIsIntelWorkspaceOpen(true)}
        />

        <ImpactSummaryCard
          summary={impactSummary}
          onOpenWhatIfModal={() => {
            setSimulatingReq(null);
            setIsImpactSimulatorOpen(true);
          }}
        />
      </div>

      {/* Ingested Documents List */}
      <DocumentListCard
        documents={documents}
        onOpenPreview={(doc) => {
          setPreviewDoc(doc);
          setIsPreviewModalOpen(true);
        }}
        onStartExtraction={(doc) => handleStartExtraction(doc.id)}
        onDeleteDocument={handleDeleteDocument}
      />

      {/* Selected Requirement AI Inspection Card */}
      {selectedReqForAnalysis && selectedReqForAnalysis.analysis_result && (
        <AIAnalysisCard
          analysis={selectedReqForAnalysis.analysis_result}
          score={selectedReqForAnalysis.quality_score || 0}
        />
      )}

      {/* Filters Toolbar */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-4">
        <div className="sm:col-span-1">
          <div className="relative">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search requirements..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full rounded-lg border border-slate-200 bg-white pl-9 pr-3 py-2 text-xs text-slate-900 focus:border-indigo-500 focus:outline-none dark:border-slate-800 dark:bg-slate-900 dark:text-white"
            />
          </div>
        </div>

        <div>
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs text-slate-900 focus:border-indigo-500 focus:outline-none dark:border-slate-800 dark:bg-slate-900 dark:text-white"
          >
            <option value="all">All Types</option>
            <option value="functional">Functional</option>
            <option value="non_functional">Non-Functional</option>
            <option value="user">User Story</option>
            <option value="business">Business</option>
            <option value="system">System</option>
          </select>
        </div>

        <div>
          <select
            value={selectedPriority}
            onChange={(e) => setSelectedPriority(e.target.value)}
            className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs text-slate-900 focus:border-indigo-500 focus:outline-none dark:border-slate-800 dark:bg-slate-900 dark:text-white"
          >
            <option value="all">All Priorities</option>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="critical">Critical</option>
          </select>
        </div>

        <div>
          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs text-slate-900 focus:border-indigo-500 focus:outline-none dark:border-slate-800 dark:bg-slate-900 dark:text-white"
          >
            <option value="all">All Statuses</option>
            <option value="draft">Draft</option>
            <option value="in_review">In Review</option>
            <option value="approved">Approved</option>
            <option value="rejected">Rejected</option>
          </select>
        </div>
      </div>

      {/* Requirements Table */}
      {isLoading ? (
        <div className="flex h-48 items-center justify-center rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
          <p className="text-xs font-medium text-slate-400">Loading requirements workspace...</p>
        </div>
      ) : (
        <RequirementTable
          requirements={requirements}
          onEdit={(req) => { setEditingReq(req); setIsModalOpen(true); }}
          onDelete={(req) => setDeletingReq(req)}
          onAnalyze={handleAnalyze}
          onImprove={handleImprove}
          onOpenRelationships={(req) => { setGraphReq(req); setIsGraphModalOpen(true); }}
          onSimulateImpact={(req) => { setSimulatingReq(req); setIsImpactSimulatorOpen(true); }}
          onOpenVerification={(req) => { setVerifReq(req); setIsVerifPanelOpen(true); }}
          analyzingId={analyzingId}
          improvingId={improvingId}
        />
      )}

      {/* Requirement Verification Compiler Panel (Sprint 1.8) */}
      {id && (
        <RequirementVerificationPanel
          isOpen={isVerifPanelOpen}
          projectId={id}
          requirement={verifReq}
          onClose={() => { setIsVerifPanelOpen(false); setVerifReq(null); }}
          onRefreshSummary={fetchProjectAndRequirements}
        />
      )}

      {/* Ephemeral What-If Change Impact Simulator Modal (Sprint 1.7) */}
      {id && (
        <WhatIfSimulatorModal
          isOpen={isImpactSimulatorOpen}
          projectId={id}
          requirement={simulatingReq}
          requirements={requirements}
          onClose={() => { setIsImpactSimulatorOpen(false); setSimulatingReq(null); }}
          onCommitChange={handleCommitSimulatorEdits}
        />
      )}

      {/* Suggestion Review Workspace Modal (Sprint 1.6) */}
      {id && (
        <SuggestionReviewWorkspace
          isOpen={isIntelWorkspaceOpen}
          projectId={id}
          requirements={requirements}
          onClose={() => setIsIntelWorkspaceOpen(false)}
          onRefreshSummary={fetchProjectAndRequirements}
        />
      )}

      {/* Document Ingestion Modals */}
      <DocumentUploadModal
        isOpen={isUploadModalOpen}
        projectId={id || ''}
        onClose={() => setIsUploadModalOpen(false)}
        onUploadSuccess={handleUploadSuccess}
      />

      <ExtractionPreviewModal
        isOpen={isPreviewModalOpen}
        projectId={id || ''}
        document={previewDoc}
        onClose={() => { setIsPreviewModalOpen(false); setPreviewDoc(null); }}
        onStartExtraction={(docId) => handleStartExtraction(docId)}
      />

      {isReviewWorkspaceOpen && activeExtractDoc && id && (
        <CandidateReviewWorkspace
          projectId={id}
          document={activeExtractDoc}
          initialCandidates={extractedCandidates}
          onClose={() => setIsReviewWorkspaceOpen(false)}
          onAcceptSuccess={() => {
            setIsReviewWorkspaceOpen(false);
            fetchProjectAndRequirements();
          }}
        />
      )}

      {/* Requirement Graph Relationships Modal */}
      <RequirementRelationshipModal
        isOpen={isGraphModalOpen}
        projectId={id || ''}
        requirement={graphReq}
        allRequirements={requirements}
        onClose={() => { setIsGraphModalOpen(false); setGraphReq(null); }}
      />

      {/* Requirement Create/Edit Modal */}
      <RequirementModal
        isOpen={isModalOpen}
        onClose={() => { setIsModalOpen(false); setEditingReq(null); }}
        onSubmit={handleCreateOrUpdate}
        requirement={editingReq}
        isLoading={isSubmitting}
      />

      {/* AI Suggestion Diff Modal */}
      <AISuggestionDiffModal
        isOpen={!!improvingReq}
        onClose={() => { setImprovingReq(null); setAiSuggestion(null); }}
        onAccept={handleAcceptSuggestion}
        originalTitle={improvingReq?.title || ''}
        originalDescription={improvingReq?.description || ''}
        suggestion={aiSuggestion}
        isLoading={isSubmitting}
      />

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={!!deletingReq}
        onClose={() => setDeletingReq(null)}
        title="Delete Requirement Specification"
      >
        <p className="text-xs text-slate-600 dark:text-slate-400">
          Are you sure you want to delete <strong className="text-slate-900 dark:text-white">{deletingReq?.title}</strong>? This action cannot be undone.
        </p>
        <div className="mt-6 flex justify-end gap-3">
          <Button variant="secondary" onClick={() => setDeletingReq(null)} disabled={isSubmitting}>
            Cancel
          </Button>
          <Button variant="danger" onClick={handleDelete} isLoading={isSubmitting}>
            Delete Requirement
          </Button>
        </div>
      </Modal>
    </div>
  );
};
