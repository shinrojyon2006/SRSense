import React, { useState, useEffect } from 'react';
import { FileText, Sparkles, X, Loader2, AlertCircle, Eye } from 'lucide-react';
import { documentService } from '../api/documentService';
import { Document, DocumentTextResponse } from '../types/document.types';

interface ExtractionPreviewModalProps {
  isOpen: boolean;
  projectId: string;
  document: Document | null;
  onClose: () => void;
  onStartExtraction: (docId: string) => void;
}

export const ExtractionPreviewModal: React.FC<ExtractionPreviewModalProps> = ({
  isOpen,
  projectId,
  document,
  onClose,
  onStartExtraction,
}) => {
  const [extractedData, setExtractedData] = useState<DocumentTextResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && document) {
      fetchTextPreview();
    }
  }, [isOpen, document]);

  const fetchTextPreview = async () => {
    if (!document) return;
    setIsLoading(true);
    setError(null);
    try {
      const data = await documentService.getDocumentText(projectId, document.id);
      setExtractedData(data);
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Failed to load document text preview.';
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen || !document) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-xl shadow-2xl w-full max-w-3xl overflow-hidden flex flex-col max-h-[85vh] animate-in fade-in duration-200">
        {/* Header */}
        <div className="flex justify-between items-center px-6 py-4 border-b border-slate-800 shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-indigo-950/60 border border-indigo-800/60 flex items-center justify-center text-indigo-400">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-white truncate max-w-md">
                {document.filename}
              </h3>
              <p className="text-xs text-slate-400">
                Format: <span className="uppercase text-slate-300">{document.file_type}</span> • Size:{' '}
                {(document.file_size / 1024).toFixed(1)} KB
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body Content */}
        <div className="p-6 overflow-y-auto flex-1 space-y-4">
          {error && (
            <div className="flex items-start gap-3 p-3 bg-red-950/40 border border-red-800/60 rounded-lg text-red-300 text-sm">
              <AlertCircle className="w-5 h-5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {isLoading ? (
            <div className="flex flex-col items-center justify-center py-16 gap-3 text-slate-400">
              <Loader2 className="w-8 h-8 animate-spin text-indigo-400" />
              <p className="text-sm">Reading document content...</p>
            </div>
          ) : extractedData ? (
            <>
              {/* Document Overview Metadata */}
              <div className="grid grid-cols-3 gap-3 p-4 bg-slate-950/60 border border-slate-800 rounded-xl">
                <div>
                  <span className="text-xs text-slate-400">Total Segments</span>
                  <p className="text-lg font-bold text-white">{extractedData.total_segments}</p>
                </div>
                <div>
                  <span className="text-xs text-slate-400">Total Word Count</span>
                  <p className="text-lg font-bold text-white">{extractedData.word_count}</p>
                </div>
                <div>
                  <span className="text-xs text-slate-400">Ingestion Status</span>
                  <p className="text-sm font-semibold capitalize text-emerald-400 mt-1">
                    {document.status}
                  </p>
                </div>
              </div>

              {/* Text Preview Box */}
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <Eye className="w-4 h-4 text-indigo-400" />
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                    Extracted Text Preview
                  </span>
                </div>
                <div className="p-4 bg-slate-950/90 border border-slate-800 rounded-xl max-h-80 overflow-y-auto font-mono text-xs text-slate-300 whitespace-pre-wrap leading-relaxed">
                  {extractedData.raw_text || 'No textual content extracted.'}
                </div>
              </div>
            </>
          ) : null}
        </div>

        {/* Footer */}
        <div className="flex justify-between items-center px-6 py-4 bg-slate-950/60 border-t border-slate-800 shrink-0">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors"
          >
            Close
          </button>
          <button
            type="button"
            onClick={() => onStartExtraction(document.id)}
            disabled={isLoading || !extractedData}
            className="flex items-center gap-2 px-5 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 rounded-lg shadow-md transition-all"
          >
            <Sparkles className="w-4 h-4 text-amber-300 animate-pulse" />
            <span>Extract Requirement Candidates</span>
          </button>
        </div>
      </div>
    </div>
  );
};
