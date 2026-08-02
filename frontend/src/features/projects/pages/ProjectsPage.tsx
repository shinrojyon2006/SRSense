import React, { useEffect, useState } from 'react';
import {
  FolderKanban,
  Plus,
  Search,
  Edit2,
  Trash2,
  FileCheck,
  Calendar,
  AlertTriangle,
} from 'lucide-react';
import { Alert, Badge, Button, Card, Input, Modal } from '@/components/ui';
import { projectService } from '@/services/projectService';
import { Project, ProjectStatus } from '@/types';

export const ProjectsPage: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [search, setSearch] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modal states
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingProject, setEditingProject] = useState<Project | null>(null);
  const [deletingProject, setDeletingProject] = useState<Project | null>(null);

  // Form states
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [status, setStatus] = useState<ProjectStatus>('active');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const fetchProjects = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await projectService.getProjects(search);
      setProjects(data);
    } catch (err: any) {
      setError('Failed to load projects. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    const timer = setTimeout(() => {
      fetchProjects();
    }, 300);
    return () => clearTimeout(timer);
  }, [search]);

  const handleOpenCreateModal = () => {
    setEditingProject(null);
    setTitle('');
    setDescription('');
    setStatus('active');
    setFormError(null);
    setIsModalOpen(true);
  };

  const handleOpenEditModal = (project: Project) => {
    setEditingProject(project);
    setTitle(project.title);
    setDescription(project.description || '');
    setStatus(project.status);
    setFormError(null);
    setIsModalOpen(true);
  };

  const handleFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    if (!title.trim()) {
      setFormError('Project title is required.');
      return;
    }

    try {
      setIsSubmitting(true);
      if (editingProject) {
        await projectService.updateProject(editingProject.id, {
          title: title.trim(),
          description: description.trim(),
          status,
        });
      } else {
        await projectService.createProject({
          title: title.trim(),
          description: description.trim(),
          status,
        });
      }
      setIsModalOpen(false);
      await fetchProjects();
    } catch (err: any) {
      const msg =
        err.response?.data?.detail ||
        'Failed to save project. Please try again.';
      setFormError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteConfirm = async () => {
    if (!deletingProject) return;

    try {
      setIsSubmitting(true);
      await projectService.deleteProject(deletingProject.id);
      setDeletingProject(null);
      await fetchProjects();
    } catch (err: any) {
      setError('Failed to delete project.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const getStatusBadge = (projStatus: ProjectStatus) => {
    switch (projStatus) {
      case 'active':
        return <Badge variant="success">Active</Badge>;
      case 'draft':
        return <Badge variant="warning">Draft</Badge>;
      case 'completed':
        return <Badge variant="primary">Completed</Badge>;
      case 'archived':
        return <Badge variant="neutral">Archived</Badge>;
      default:
        return <Badge variant="neutral">{projStatus}</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight text-slate-900 dark:text-white">
            Software Projects
          </h1>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
            Manage your software requirements specification repositories
          </p>
        </div>

        <Button variant="primary" onClick={handleOpenCreateModal}>
          <Plus className="h-4 w-4" />
          Create Project
        </Button>
      </div>

      {/* Search & Filters */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3.5 top-2.5 h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search projects by title..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-lg border border-slate-200 bg-white pl-10 pr-4 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-[#4F46E5] focus:outline-none focus:ring-2 focus:ring-[#4F46E5]/20 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-100"
          />
        </div>
      </div>

      {error && (
        <Alert variant="error" title="Error">
          {error}
        </Alert>
      )}

      {/* Projects Grid */}
      {isLoading ? (
        <div className="p-12 text-center text-sm text-slate-500">
          Fetching projects from PostgreSQL...
        </div>
      ) : projects.length === 0 ? (
        <Card animate={false} className="p-12 text-center">
          <FolderKanban className="mx-auto h-12 w-12 text-slate-300 dark:text-slate-700" />
          <h3 className="mt-4 text-base font-bold text-slate-900 dark:text-white">
            {search ? 'No matching projects found' : 'No projects created yet'}
          </h3>
          <p className="mt-1 text-sm text-slate-500 max-w-md mx-auto">
            {search
              ? 'Try adjusting your search keywords.'
              : 'Create your first software project to start defining requirements.'}
          </p>
          {!search && (
            <div className="mt-6">
              <Button variant="primary" onClick={handleOpenCreateModal}>
                <Plus className="h-4 w-4" />
                Create First Project
              </Button>
            </div>
          )}
        </Card>
      ) : (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {projects.map((project) => (
            <Card
              key={project.id}
              animate={false}
              className="flex flex-col justify-between space-y-4 hover:border-indigo-200 dark:hover:border-indigo-800 transition-colors"
            >
              <div className="space-y-2">
                <div className="flex items-start justify-between gap-2">
                  <h3 className="text-base font-bold text-slate-900 dark:text-white line-clamp-1">
                    {project.title}
                  </h3>
                  {getStatusBadge(project.status)}
                </div>
                <p className="text-xs text-slate-600 dark:text-slate-400 line-clamp-3 leading-relaxed">
                  {project.description || 'No description provided.'}
                </p>
              </div>

              <div className="space-y-4 pt-2 border-t border-slate-100 dark:border-slate-800">
                <div className="flex items-center justify-between text-xs text-slate-500">
                  <span className="flex items-center gap-1 font-medium">
                    <FileCheck className="h-3.5 w-3.5 text-indigo-500" />
                    {project.requirement_count} Requirements
                  </span>
                  <span className="flex items-center gap-1">
                    <Calendar className="h-3.5 w-3.5" />
                    {new Date(project.created_at).toLocaleDateString()}
                  </span>
                </div>

                <div className="flex items-center justify-end gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleOpenEditModal(project)}
                    className="h-8 px-2.5 text-slate-600 dark:text-slate-300"
                  >
                    <Edit2 className="h-3.5 w-3.5" />
                    Edit
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setDeletingProject(project)}
                    className="h-8 px-2.5 text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-950/40"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                    Delete
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Create / Edit Project Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={editingProject ? 'Edit Software Project' : 'Create New Project'}
      >
        <form onSubmit={handleFormSubmit} className="space-y-4">
          {formError && (
            <Alert variant="error" title="Validation Error">
              {formError}
            </Alert>
          )}

          <div>
            <Input
              label="Project Title"
              type="text"
              placeholder="e.g. E-Commerce Platform SRS"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
            />
          </div>

          <div className="space-y-1.5">
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
              Description
            </label>
            <textarea
              rows={3}
              placeholder="Describe the software scope and requirements objectives..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full rounded-lg border border-slate-200 bg-white p-3 text-sm text-slate-900 placeholder:text-slate-400 focus:border-[#4F46E5] focus:outline-none focus:ring-2 focus:ring-[#4F46E5]/20 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-100"
            />
          </div>

          <div className="space-y-1.5">
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
              Project Status
            </label>
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value as ProjectStatus)}
              className="w-full rounded-lg border border-slate-200 bg-white px-3.5 py-2 text-sm text-slate-900 focus:border-[#4F46E5] focus:outline-none focus:ring-2 focus:ring-[#4F46E5]/20 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-100"
            >
              <option value="active">Active</option>
              <option value="draft">Draft</option>
              <option value="completed">Completed</option>
              <option value="archived">Archived</option>
            </select>
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-slate-100 dark:border-slate-800">
            <Button
              type="button"
              variant="secondary"
              onClick={() => setIsModalOpen(false)}
            >
              Cancel
            </Button>
            <Button type="submit" variant="primary" isLoading={isSubmitting}>
              {editingProject ? 'Save Changes' : 'Create Project'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={!!deletingProject}
        onClose={() => setDeletingProject(null)}
        title="Confirm Delete Project"
      >
        <div className="space-y-4">
          <div className="flex gap-3 text-amber-600 dark:text-amber-400">
            <AlertTriangle className="h-5 w-5 shrink-0" />
            <p className="text-xs leading-relaxed text-slate-700 dark:text-slate-300">
              Are you sure you want to delete{' '}
              <strong className="text-slate-900 dark:text-white">
                "{deletingProject?.title}"
              </strong>
              ? This action will remove the project and its requirements from PostgreSQL.
            </p>
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-slate-100 dark:border-slate-800">
            <Button
              variant="secondary"
              onClick={() => setDeletingProject(null)}
            >
              Cancel
            </Button>
            <Button
              variant="danger"
              onClick={handleDeleteConfirm}
              isLoading={isSubmitting}
            >
              Delete Project
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
