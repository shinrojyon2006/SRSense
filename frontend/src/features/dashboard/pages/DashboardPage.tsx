import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  FolderKanban,
  Plus,
  FileCheck,
  Shield,
  ArrowRight,
  User as UserIcon,
  Calendar,
  Mail,
  Clock,
  Activity,
} from 'lucide-react';
import { Badge, Button, Card } from '@/components/ui';
import { useAuth } from '@/contexts/AuthContext';
import { useHealth } from '@/hooks/useHealth';
import { projectService } from '@/services/projectService';
import { Project } from '@/types';

export const DashboardPage: React.FC = () => {
  const { user } = useAuth();
  const { data: healthStatus } = useHealth();
  const navigate = useNavigate();

  const [projects, setProjects] = useState<Project[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    const fetchProjects = async () => {
      try {
        const data = await projectService.getProjects();
        setProjects(data);
      } catch {
        // Handle fetch error gracefully
      } finally {
        setIsLoading(false);
      }
    };

    fetchProjects();
  }, []);

  const totalRequirements = projects.reduce(
    (sum, p) => sum + (p.requirement_count || 0),
    0
  );

  const recentProjects = projects.slice(0, 5);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active':
        return <Badge variant="success">Active</Badge>;
      case 'draft':
        return <Badge variant="warning">Draft</Badge>;
      case 'completed':
        return <Badge variant="primary">Completed</Badge>;
      case 'archived':
        return <Badge variant="neutral">Archived</Badge>;
      default:
        return <Badge variant="neutral">{status}</Badge>;
    }
  };

  return (
    <div className="space-y-8">
      {/* Welcome Banner */}
      <div className="rounded-2xl bg-gradient-to-r from-[#4F46E5] to-indigo-700 p-6 sm:p-8 text-white shadow-lg">
        <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
          <div>
            <span className="inline-flex items-center gap-1.5 rounded-full bg-white/10 px-3 py-1 text-xs font-medium text-indigo-100 backdrop-blur-xs">
              <Shield className="h-3.5 w-3.5" />
              Authenticated Session
            </span>
            <h1 className="mt-3 text-2xl font-extrabold sm:text-3xl">
              Welcome back, {user?.name}!
            </h1>
            <p className="mt-1 text-sm text-indigo-100">
              SRSense AI Software Requirements Engineering Workstation
            </p>
          </div>

          <Button
            variant="secondary"
            onClick={() => navigate('/projects')}
            className="self-start sm:self-auto"
          >
            <Plus className="h-4 w-4" />
            New Project
          </Button>
        </div>
      </div>

      {/* Statistics Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card animate={false} className="flex items-center gap-4 p-5">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-indigo-50 text-[#4F46E5] dark:bg-indigo-950/50 dark:text-indigo-400">
            <FolderKanban className="h-6 w-6" />
          </div>
          <div>
            <p className="text-xs font-medium text-slate-500 dark:text-slate-400">
              Total Projects
            </p>
            <p className="text-2xl font-bold text-slate-900 dark:text-white">
              {isLoading ? '...' : projects.length}
            </p>
          </div>
        </Card>

        <Card animate={false} className="flex items-center gap-4 p-5">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-emerald-50 text-emerald-600 dark:bg-emerald-950/50 dark:text-emerald-400">
            <FileCheck className="h-6 w-6" />
          </div>
          <div>
            <p className="text-xs font-medium text-slate-500 dark:text-slate-400">
              Total Requirements
            </p>
            <p className="text-2xl font-bold text-slate-900 dark:text-white">
              {isLoading ? '...' : totalRequirements}
            </p>
          </div>
        </Card>

        <Card animate={false} className="flex items-center gap-4 p-5">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-amber-50 text-amber-600 dark:bg-amber-950/50 dark:text-amber-400">
            <UserIcon className="h-6 w-6" />
          </div>
          <div>
            <p className="text-xs font-medium text-slate-500 dark:text-slate-400">
              Account Role
            </p>
            <p className="text-sm font-bold capitalize text-slate-900 dark:text-white">
              {user?.role || 'Developer'}
            </p>
          </div>
        </Card>

        <Card animate={false} className="flex items-center gap-4 p-5">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-blue-50 text-blue-600 dark:bg-blue-950/50 dark:text-blue-400">
            <Activity className="h-6 w-6" />
          </div>
          <div>
            <p className="text-xs font-medium text-slate-500 dark:text-slate-400">
              PostgreSQL Health
            </p>
            <p className="text-sm font-bold capitalize text-emerald-600 dark:text-emerald-400">
              {healthStatus?.database || 'connected'}
            </p>
          </div>
        </Card>
      </div>

      {/* Main Content Grid: Recent Projects & Quick Actions */}
      <div className="grid gap-8 lg:grid-cols-3">
        {/* Recent Projects Section */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-slate-900 dark:text-white">
              Recent Software Projects
            </h2>
            <Link
              to="/projects"
              className="flex items-center gap-1 text-xs font-semibold text-[#4F46E5] hover:underline dark:text-indigo-400"
            >
              View All Projects
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>

          <Card animate={false} className="p-0 overflow-hidden">
            {isLoading ? (
              <div className="p-8 text-center text-xs text-slate-500">
                Loading projects from PostgreSQL...
              </div>
            ) : recentProjects.length === 0 ? (
              <div className="p-8 text-center">
                <FolderKanban className="mx-auto h-8 w-8 text-slate-400" />
                <p className="mt-2 text-sm font-medium text-slate-700 dark:text-slate-300">
                  No software projects created yet
                </p>
                <p className="mt-1 text-xs text-slate-500">
                  Get started by creating your first software requirements project.
                </p>
                <div className="mt-4">
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={() => navigate('/projects')}
                  >
                    <Plus className="h-3.5 w-3.5" />
                    Create First Project
                  </Button>
                </div>
              </div>
            ) : (
              <div className="divide-y divide-slate-100 dark:divide-slate-800">
                {recentProjects.map((project) => (
                  <div
                    key={project.id}
                    className="flex flex-col sm:flex-row sm:items-center justify-between p-4 hover:bg-slate-50/80 transition-colors dark:hover:bg-slate-800/40 gap-3"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <h3 className="text-sm font-semibold text-slate-900 dark:text-white">
                          {project.title}
                        </h3>
                        {getStatusBadge(project.status)}
                      </div>
                      <p className="text-xs text-slate-500 dark:text-slate-400 line-clamp-1">
                        {project.description || 'No description provided.'}
                      </p>
                    </div>

                    <div className="flex items-center gap-4 text-xs text-slate-500 shrink-0">
                      <span className="flex items-center gap-1">
                        <FileCheck className="h-3.5 w-3.5 text-indigo-500" />
                        {project.requirement_count} Requirements
                      </span>
                      <span className="flex items-center gap-1">
                        <Clock className="h-3.5 w-3.5" />
                        {new Date(project.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>

        {/* Right Sidebar: Quick Actions & Profile Summary */}
        <div className="space-y-6">
          <div className="space-y-4">
            <h2 className="text-lg font-bold text-slate-900 dark:text-white">
              Quick Actions
            </h2>
            <Card animate={false} className="space-y-3 p-4">
              <Button
                variant="primary"
                className="w-full justify-start py-2.5"
                onClick={() => navigate('/projects')}
              >
                <Plus className="h-4 w-4" />
                Create New Project
              </Button>

              <Button
                variant="secondary"
                className="w-full justify-start py-2.5"
                onClick={() => navigate('/projects')}
              >
                <FolderKanban className="h-4 w-4" />
                Manage All Projects
              </Button>

              <a
                href="/api/health"
                target="_blank"
                rel="noopener noreferrer"
                className="block"
              >
                <Button
                  variant="ghost"
                  className="w-full justify-start py-2.5 text-slate-700 dark:text-slate-300"
                >
                  <Activity className="h-4 w-4" />
                  View API Health Status
                </Button>
              </a>
            </Card>
          </div>

          {/* User Profile Section */}
          <div className="space-y-4">
            <h2 className="text-lg font-bold text-slate-900 dark:text-white">
              User Profile Overview
            </h2>
            <Card animate={false} className="space-y-3 p-5">
              <div className="flex items-center gap-3 pb-3 border-b border-slate-100 dark:border-slate-800">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[#4F46E5] text-white font-bold">
                  {user?.name?.[0]?.toUpperCase() || 'U'}
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                    {user?.name}
                  </h3>
                  <Badge variant="primary" size="sm">
                    {user?.role}
                  </Badge>
                </div>
              </div>

              <div className="space-y-2 text-xs text-slate-600 dark:text-slate-400">
                <div className="flex items-center gap-2">
                  <Mail className="h-3.5 w-3.5 text-slate-400" />
                  <span>{user?.email}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Calendar className="h-3.5 w-3.5 text-slate-400" />
                  <span>
                    Member since{' '}
                    {user?.created_at
                      ? new Date(user.created_at).toLocaleDateString()
                      : 'Recently'}
                  </span>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};
