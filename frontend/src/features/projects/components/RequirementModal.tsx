import React, { useState, useEffect } from 'react';
import { Modal } from '@/components/ui/Modal';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import {
  Requirement,
  RequirementCreateInput,
  RequirementPriority,
  RequirementStatus,
  RequirementType,
} from '@/types';

interface RequirementModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: RequirementCreateInput) => Promise<void>;
  requirement?: Requirement | null;
  isLoading?: boolean;
}

export const RequirementModal: React.FC<RequirementModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  requirement,
  isLoading = false,
}) => {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [type, setType] = useState<RequirementType>('functional');
  const [priority, setPriority] = useState<RequirementPriority>('medium');
  const [status, setStatus] = useState<RequirementStatus>('draft');
  const [error, setError] = useState('');

  useEffect(() => {
    if (requirement) {
      setTitle(requirement.title);
      setDescription(requirement.description);
      setType(requirement.type);
      setPriority(requirement.priority);
      setStatus(requirement.status);
    } else {
      setTitle('');
      setDescription('');
      setType('functional');
      setPriority('medium');
      setStatus('draft');
    }
    setError('');
  }, [requirement, isOpen]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) {
      setError('Requirement title is required');
      return;
    }
    if (!description.trim() || description.length < 5) {
      setError('Requirement description must be at least 5 characters');
      return;
    }

    try {
      setError('');
      await onSubmit({
        title: title.trim(),
        description: description.trim(),
        type,
        priority,
        status,
      });
      onClose();
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to save requirement');
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={requirement ? 'Edit Requirement Specification' : 'Add New Requirement Specification'}
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="rounded-lg bg-red-50 p-3 text-xs font-medium text-red-600 dark:bg-red-950/40 dark:text-red-400">
            {error}
          </div>
        )}

        <Input
          label="Requirement Title *"
          placeholder="e.g., User OAuth2 Authentication"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          required
        />

        <div className="space-y-1">
          <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
            Requirement Description *
          </label>
          <textarea
            rows={4}
            className="w-full rounded-lg border border-slate-200 bg-white p-3 text-xs text-slate-900 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 dark:border-slate-800 dark:bg-slate-950 dark:text-white"
            placeholder="Specify clear, measurable acceptance criteria (e.g., The system shall allow users to log in...)"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            required
          />
        </div>

        <div className="grid grid-cols-3 gap-3">
          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
              Type
            </label>
            <select
              value={type}
              onChange={(e) => setType(e.target.value as RequirementType)}
              className="w-full rounded-lg border border-slate-200 bg-white px-2.5 py-2 text-xs text-slate-900 focus:border-indigo-500 focus:outline-none dark:border-slate-800 dark:bg-slate-950 dark:text-white"
            >
              <option value="functional">Functional</option>
              <option value="non_functional">Non-Functional</option>
              <option value="user">User Story</option>
              <option value="business">Business</option>
              <option value="system">System</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
              Priority
            </label>
            <select
              value={priority}
              onChange={(e) => setPriority(e.target.value as RequirementPriority)}
              className="w-full rounded-lg border border-slate-200 bg-white px-2.5 py-2 text-xs text-slate-900 focus:border-indigo-500 focus:outline-none dark:border-slate-800 dark:bg-slate-950 dark:text-white"
            >
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="critical">Critical</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
              Status
            </label>
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value as RequirementStatus)}
              className="w-full rounded-lg border border-slate-200 bg-white px-2.5 py-2 text-xs text-slate-900 focus:border-indigo-500 focus:outline-none dark:border-slate-800 dark:bg-slate-950 dark:text-white"
            >
              <option value="draft">Draft</option>
              <option value="in_review">In Review</option>
              <option value="approved">Approved</option>
              <option value="rejected">Rejected</option>
            </select>
          </div>
        </div>

        <div className="flex justify-end gap-3 pt-4 border-t border-slate-100 dark:border-slate-800">
          <Button type="button" variant="secondary" onClick={onClose} disabled={isLoading}>
            Cancel
          </Button>
          <Button type="submit" isLoading={isLoading}>
            {requirement ? 'Update Requirement' : 'Create Requirement'}
          </Button>
        </div>
      </form>
    </Modal>
  );
};
