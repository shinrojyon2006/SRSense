import React from 'react';
import { FileText, Sparkles, Trash2, Eye } from 'lucide-react';
import { Document } from '../types/document.types';

interface DocumentListCardProps {
  documents: Document[];
  onOpenPreview: (doc: Document) => void;
  onStartExtraction: (doc: Document) => void;
  onDeleteDocument: (docId: string) => void;
}

export const DocumentListCard: React.FC<DocumentListCardProps> = ({
  documents,
  onOpenPreview,
  onStartExtraction,
  onDeleteDocument,
}) => {
  if (documents.length === 0) {
    return null;
  }

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 mb-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
          <FileText className="w-4 h-4 text-indigo-400" />
          <span>Ingested SRS Documents ({documents.length})</span>
        </h3>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {documents.map((doc) => (
          <div
            key={doc.id}
            className="p-4 bg-slate-950/80 border border-slate-800 hover:border-slate-700 rounded-xl flex items-center justify-between gap-4 transition-all"
          >
            <div className="flex items-center gap-3 overflow-hidden">
              <div className="w-10 h-10 rounded-lg bg-indigo-950/60 border border-indigo-800/60 flex items-center justify-center text-indigo-400 shrink-0">
                <FileText className="w-5 h-5" />
              </div>
              <div className="truncate">
                <h4 className="text-sm font-semibold text-white truncate">{doc.filename}</h4>
                <div className="flex items-center gap-3 text-xs text-slate-400 mt-1">
                  <span className="uppercase font-mono text-indigo-300">{doc.file_type}</span>
                  <span>•</span>
                  <span>{(doc.file_size / 1024).toFixed(1)} KB</span>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-2 shrink-0">
              <button
                onClick={() => onOpenPreview(doc)}
                title="Preview extracted text"
                className="p-2 text-slate-400 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors"
              >
                <Eye className="w-4 h-4" />
              </button>
              <button
                onClick={() => onStartExtraction(doc)}
                title="Extract requirement candidates"
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 rounded-lg shadow-sm transition-all"
              >
                <Sparkles className="w-3.5 h-3.5 text-amber-300" />
                <span>Extract</span>
              </button>
              <button
                onClick={() => onDeleteDocument(doc.id)}
                title="Delete document"
                className="p-2 text-slate-400 hover:text-red-400 bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
