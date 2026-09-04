import React, { useState, useEffect } from 'react';
import { Link, AlertCircle, Loader2 } from 'lucide-react';
import { Modal } from '@/components/ui/Modal';
import { Button } from '@/components/ui/Button';
import { Requirement } from '@/types';
import { CodeFileSummary, CodeSymbol } from '../types/codebase.types';
import { codebaseService } from '../api/codebaseService';

interface RequirementCodeLinkModalProps {
  isOpen: boolean;
  projectId: string;
  requirements: Requirement[];
  files: CodeFileSummary[];
  initialFileId?: string;
  initialSymbolId?: string;
  onClose: () => void;
  onLinkCreated: () => void;
}

export const RequirementCodeLinkModal: React.FC<RequirementCodeLinkModalProps> = ({
  isOpen,
  projectId,
  requirements,
  files,
  initialFileId,
  initialSymbolId,
  onClose,
  onLinkCreated,
}) => {
  const [selectedReqId, setSelectedReqId] = useState<string>(requirements[0]?.id || '');
  const [selectedFileId, setSelectedFileId] = useState<string>(initialFileId || files[0]?.id || '');
  const [selectedSymbolId, setSelectedSymbolId] = useState<string>(initialSymbolId || '');
  const [availableSymbols, setAvailableSymbols] = useState<CodeSymbol[]>([]);
  const [notes, setNotes] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (initialFileId) setSelectedFileId(initialFileId);
    if (initialSymbolId) setSelectedSymbolId(initialSymbolId);
    if (requirements.length > 0 && !selectedReqId) {
      setSelectedReqId(requirements[0].id);
    }
    if (files.length > 0 && !selectedFileId) {
      setSelectedFileId(files[0].id);
    }
  }, [initialFileId, initialSymbolId, requirements, files]);

  // Load symbols when file changes
  useEffect(() => {
    if (selectedFileId && projectId) {
      codebaseService
        .getFileDetail(projectId, selectedFileId)
        .then((detail) => setAvailableSymbols(detail.symbols || []))
        .catch(() => setAvailableSymbols([]));
    }
  }, [selectedFileId, projectId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedReqId || !selectedFileId) {
      setError('Please select both a requirement and a source code file.');
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);
      await codebaseService.createLink(projectId, {
        requirement_id: selectedReqId,
        file_id: selectedFileId,
        symbol_id: selectedSymbolId || undefined,
        link_type: 'explicit_manual',
        notes: notes.trim() || undefined,
      });
      onLinkCreated();
      onClose();
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to link requirement to code.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={isSubmitting ? () => {} : onClose} title="Create Requirement ↔ Code Link">
      <form onSubmit={handleSubmit} className="space-y-4">
        <p className="text-xs text-slate-500 dark:text-slate-400">
          Establish an explicit traceability link connecting an SRS specification to an implementation file or code construct.
        </p>

        {error && (
          <div className="flex items-center gap-2 rounded-lg bg-red-50 p-3 text-xs text-red-600 dark:bg-red-950/40 dark:text-red-400">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Select Requirement */}
        <div className="space-y-1">
          <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
            Target Requirement *
          </label>
          <select
            value={selectedReqId}
            onChange={(e) => setSelectedReqId(e.target.value)}
            className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs text-slate-900 focus:border-indigo-500 focus:outline-none dark:border-slate-800 dark:bg-slate-900 dark:text-white"
            required
          >
            {requirements.map((req) => (
              <option key={req.id} value={req.id}>
                {req.original_req_id ? `[${req.original_req_id}] ` : ''}
                {req.title}
              </option>
            ))}
          </select>
        </div>

        {/* Select File */}
        <div className="space-y-1">
          <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
            Source Code File *
          </label>
          <select
            value={selectedFileId}
            onChange={(e) => {
              setSelectedFileId(e.target.value);
              setSelectedSymbolId('');
            }}
            className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs text-slate-900 focus:border-indigo-500 focus:outline-none dark:border-slate-800 dark:bg-slate-900 dark:text-white"
            required
          >
            {files.map((f) => (
              <option key={f.id} value={f.id}>
                {f.path} ({f.language})
              </option>
            ))}
          </select>
        </div>

        {/* Select Specific Symbol (Optional) */}
        {availableSymbols.length > 0 && (
          <div className="space-y-1">
            <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
              Specific Code Symbol (Optional)
            </label>
            <select
              value={selectedSymbolId}
              onChange={(e) => setSelectedSymbolId(e.target.value)}
              className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs text-slate-900 focus:border-indigo-500 focus:outline-none dark:border-slate-800 dark:bg-slate-900 dark:text-white"
            >
              <option value="">-- Link to entire file --</option>
              {availableSymbols.map((sym) => (
                <option key={sym.id} value={sym.id}>
                  {sym.symbol_name} ({sym.symbol_type})
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Notes */}
        <div className="space-y-1">
          <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
            Traceability Notes / Rationale
          </label>
          <textarea
            rows={2}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="e.g. Implements the checkout payment validation routine..."
            className="w-full rounded-lg border border-slate-200 bg-white p-2.5 text-xs text-slate-900 focus:border-indigo-500 focus:outline-none dark:border-slate-800 dark:bg-slate-900 dark:text-white"
          />
        </div>

        {/* Actions */}
        <div className="flex justify-end gap-2 pt-2">
          <Button variant="secondary" onClick={onClose} disabled={isSubmitting}>
            Cancel
          </Button>
          <Button type="submit" disabled={isSubmitting || !selectedReqId || !selectedFileId}>
            {isSubmitting ? (
              <>
                <Loader2 className="h-4 w-4 mr-1.5 animate-spin" /> Creating Link...
              </>
            ) : (
              <>
                <Link className="h-4 w-4 mr-1.5" /> Establish Link
              </>
            )}
          </Button>
        </div>
      </form>
    </Modal>
  );
};
