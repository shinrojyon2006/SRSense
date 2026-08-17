import React, { useState, useRef } from 'react';
import { Upload, X, FileText, AlertCircle, Loader2 } from 'lucide-react';
import { documentService } from '../api/documentService';
import { Document } from '../types/document.types';

interface DocumentUploadModalProps {
  isOpen: boolean;
  projectId: string;
  onClose: () => void;
  onUploadSuccess: (doc: Document) => void;
}

export const DocumentUploadModal: React.FC<DocumentUploadModalProps> = ({
  isOpen,
  projectId,
  onClose,
  onUploadSuccess,
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragOver, setIsDragOver] = useState<boolean>(false);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  const MAX_SIZE = 10 * 1024 * 1024; // 10 MB
  const ALLOWED_EXTENSIONS = ['.pdf', '.docx', '.txt'];

  const validateAndSetFile = (file: File) => {
    setError(null);
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      setError(`Invalid file format '${ext}'. Only PDF, DOCX, and TXT files are allowed.`);
      setSelectedFile(null);
      return;
    }
    if (file.size > MAX_SIZE) {
      setError(`File size (${(file.size / (1024 * 1024)).toFixed(2)} MB) exceeds 10 MB limit.`);
      setSelectedFile(null);
      return;
    }
    setSelectedFile(file);
  };

  const handleFileDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const handleUploadSubmit = async () => {
    if (!selectedFile) return;
    setIsUploading(true);
    setError(null);
    try {
      const doc = await documentService.uploadDocument(projectId, selectedFile);
      onUploadSuccess(doc);
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Failed to upload document. Please try again.';
      setError(msg);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-xl shadow-2xl w-full max-w-lg overflow-hidden animate-in fade-in duration-200">
        {/* Header */}
        <div className="flex justify-between items-center px-6 py-4 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <Upload className="w-5 h-5 text-indigo-400" />
            <h3 className="text-lg font-semibold text-white">Ingest SRS Document</h3>
          </div>
          <button
            onClick={onClose}
            disabled={isUploading}
            className="text-slate-400 hover:text-white transition-colors p-1 rounded-lg hover:bg-slate-800"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          {error && (
            <div className="flex items-start gap-3 p-3 bg-red-950/40 border border-red-800/60 rounded-lg text-red-300 text-sm">
              <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {/* Drag and drop area */}
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setIsDragOver(true);
            }}
            onDragLeave={() => setIsDragOver(false)}
            onDrop={handleFileDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${
              isDragOver
                ? 'border-indigo-500 bg-indigo-950/20 scale-[0.99]'
                : 'border-slate-700 hover:border-slate-500 bg-slate-950/40 hover:bg-slate-900/60'
            }`}
          >
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileSelect}
              accept=".pdf,.docx,.txt"
              className="hidden"
            />
            <div className="w-12 h-12 mx-auto mb-3 rounded-full bg-slate-800 flex items-center justify-center text-slate-400">
              <FileText className="w-6 h-6 text-indigo-400" />
            </div>
            <p className="text-sm font-medium text-slate-200">
              Click to browse or drag & drop SRS file
            </p>
            <p className="text-xs text-slate-400 mt-1">
              Supports <span className="font-semibold text-slate-300">PDF, DOCX, TXT</span> (Max 10 MB)
            </p>
          </div>

          {/* Selected File Details */}
          {selectedFile && (
            <div className="flex items-center justify-between p-3 bg-slate-800/60 border border-slate-700/60 rounded-lg">
              <div className="flex items-center gap-3 overflow-hidden">
                <FileText className="w-5 h-5 text-indigo-400 shrink-0" />
                <div className="truncate">
                  <p className="text-sm font-medium text-slate-200 truncate">
                    {selectedFile.name}
                  </p>
                  <p className="text-xs text-slate-400">
                    {(selectedFile.size / 1024).toFixed(1)} KB
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  setSelectedFile(null);
                }}
                className="text-slate-400 hover:text-red-400 p-1 rounded-md transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-3 px-6 py-4 bg-slate-950/60 border-t border-slate-800">
          <button
            type="button"
            onClick={onClose}
            disabled={isUploading}
            className="px-4 py-2 text-sm font-medium text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleUploadSubmit}
            disabled={!selectedFile || isUploading}
            className="flex items-center gap-2 px-5 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg shadow-md transition-all"
          >
            {isUploading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Uploading...</span>
              </>
            ) : (
              <>
                <Upload className="w-4 h-4" />
                <span>Upload SRS</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
