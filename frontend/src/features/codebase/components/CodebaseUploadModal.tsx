import React, { useState, useRef } from 'react';
import { UploadCloud, AlertCircle, FileArchive, Check, Loader2 } from 'lucide-react';
import { Modal } from '@/components/ui/Modal';
import { Button } from '@/components/ui/Button';

interface CodebaseUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUpload: (file: File) => Promise<void>;
}

export const CodebaseUploadModal: React.FC<CodebaseUploadModalProps> = ({
  isOpen,
  onClose,
  onUpload,
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setError(null);
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (!file.name.toLowerCase().endsWith('.zip')) {
        setError('Please select a valid .zip source code archive.');
        return;
      }
      if (file.size > 50 * 1024 * 1024) {
        setError('Archive exceeds the 50 MB maximum size limit.');
        return;
      }
      setSelectedFile(file);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    setError(null);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (!file.name.toLowerCase().endsWith('.zip')) {
        setError('Please drop a valid .zip source code archive.');
        return;
      }
      if (file.size > 50 * 1024 * 1024) {
        setError('Archive exceeds the 50 MB maximum size limit.');
        return;
      }
      setSelectedFile(file);
    }
  };

  const handleSubmit = async () => {
    if (!selectedFile) return;
    try {
      setIsUploading(true);
      setError(null);
      await onUpload(selectedFile);
      setSelectedFile(null);
      onClose();
    } catch (err: any) {
      setError(
        err?.response?.data?.detail ||
          'Failed to upload and index the codebase archive.'
      );
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={isUploading ? () => {} : onClose}
      title="Import Codebase (ZIP Archive)"
    >
      <div className="space-y-4">
        <p className="text-xs text-slate-500 dark:text-slate-400">
          Upload a source code repository archive (.zip). SRSense will safely detect programming languages, extract classes, functions, and endpoints, and build a project-scoped symbol index without executing any code.
        </p>

        {error && (
          <div className="flex items-center gap-2 rounded-lg bg-red-50 p-3 text-xs text-red-600 dark:bg-red-950/40 dark:text-red-400">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Drag & Drop Area */}
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setIsDragOver(true);
          }}
          onDragLeave={() => setIsDragOver(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`flex flex-col items-center justify-center p-8 border-2 border-dashed rounded-xl cursor-pointer transition-colors ${
            isDragOver
              ? 'border-indigo-500 bg-indigo-50/50 dark:bg-indigo-950/20'
              : 'border-slate-300 hover:border-indigo-400 bg-slate-50/50 dark:border-slate-700 dark:bg-slate-900/50'
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".zip"
            className="hidden"
            onChange={handleFileChange}
          />
          {selectedFile ? (
            <div className="flex flex-col items-center text-center space-y-2">
              <div className="p-3 bg-emerald-50 text-emerald-600 rounded-full dark:bg-emerald-950/50 dark:text-emerald-400">
                <Check className="h-6 w-6" />
              </div>
              <div className="text-xs font-semibold text-slate-900 dark:text-white">
                {selectedFile.name}
              </div>
              <div className="text-[11px] text-slate-500 dark:text-slate-400">
                {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
              </div>
              <span className="text-[10px] text-indigo-500 font-medium hover:underline">
                Click or drop to choose a different archive
              </span>
            </div>
          ) : (
            <div className="flex flex-col items-center text-center space-y-2">
              <div className="p-3 bg-indigo-50 text-indigo-600 rounded-full dark:bg-indigo-950/50 dark:text-indigo-400">
                <FileArchive className="h-6 w-6" />
              </div>
              <div className="text-xs font-semibold text-slate-900 dark:text-white">
                Click to browse or drag and drop your .zip file here
              </div>
              <div className="text-[10px] text-slate-400">
                Supported: Python, C, C++, Java, JavaScript, TypeScript, HTML, CSS, SQL (Max 50MB)
              </div>
            </div>
          )}
        </div>

        {/* Security Disclaimers */}
        <div className="text-[11px] text-slate-400 dark:text-slate-500 bg-slate-100/60 dark:bg-slate-950/40 p-2.5 rounded-lg border border-slate-200/60 dark:border-slate-800 space-y-1">
          <div className="font-semibold text-slate-600 dark:text-slate-400">
            Security & Ingestion Policy:
          </div>
          <ul className="list-disc list-inside space-y-0.5">
            <li>Static AST parsing only; zero code execution.</li>
            <li>Automatically filters out .git, node_modules, .venv, and binaries.</li>
            <li>Protected against path traversal and archive zip-slip exploits.</li>
          </ul>
        </div>

        {/* Actions */}
        <div className="flex justify-end gap-2 pt-2">
          <Button variant="secondary" onClick={onClose} disabled={isUploading}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={!selectedFile || isUploading}>
            {isUploading ? (
              <>
                <Loader2 className="h-4 w-4 mr-1.5 animate-spin" /> Indexing Repository...
              </>
            ) : (
              <>
                <UploadCloud className="h-4 w-4 mr-1.5" /> Start Code Indexing
              </>
            )}
          </Button>
        </div>
      </div>
    </Modal>
  );
};
