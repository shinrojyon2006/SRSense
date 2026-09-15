import React, { useState, useEffect } from 'react';
import {
  ShieldAlert,
  AlertTriangle,
  Info,
  Play,
  RotateCw,
  Activity,
  CheckCircle,
  FileCode,
} from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { codeQualityService } from '../api/codeQualityService';
import {
  CodeReviewReport,
  CodeReviewFinding,
  CodeReviewFindingsQueryParams,
  CodeHealthStatus,
} from '../types/codeQuality.types';
import { CodeFindingsTable } from './CodeFindingsTable';
import { CodeImprovementModal } from './CodeImprovementModal';

interface CodeQualityDashboardProps {
  projectId: string;
}

export const CodeQualityDashboard: React.FC<CodeQualityDashboardProps> = ({
  projectId,
}) => {
  const [report, setReport] = useState<CodeReviewReport | null>(null);
  const [findings, setFindings] = useState<CodeReviewFinding[]>([]);
  const [totalFindings, setTotalFindings] = useState<number>(0);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [pageSize] = useState<number>(20);

  const [isLoadingReport, setIsLoadingReport] = useState<boolean>(true);
  const [isScanning, setIsScanning] = useState<boolean>(false);
  const [isLoadingFindings, setIsLoadingFindings] = useState<boolean>(false);
  const [activeFilters, setActiveFilters] = useState<CodeReviewFindingsQueryParams>({});
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Code Improvement Modal state
  const [isImprovementModalOpen, setIsImprovementModalOpen] = useState<boolean>(false);
  const [targetFindingId, setTargetFindingId] = useState<string | undefined>();

  // Load initial report
  useEffect(() => {
    if (projectId) {
      loadLatestReport();
    }
  }, [projectId]);

  const loadLatestReport = async () => {
    try {
      setIsLoadingReport(true);
      setErrorMsg(null);
      const res = await codeQualityService.getLatestReview(projectId);
      setReport(res);
      if (res) {
        loadFindings(1, activeFilters);
      }
    } catch (err: any) {
      console.error('Failed to load code review report:', err);
      setErrorMsg('Failed to load code quality report.');
    } finally {
      setIsLoadingReport(false);
    }
  };

  const loadFindings = async (
    page: number,
    params?: CodeReviewFindingsQueryParams
  ) => {
    try {
      setIsLoadingFindings(true);
      const res = await codeQualityService.getFindings(projectId, {
        ...params,
        page,
        page_size: pageSize,
      });
      setFindings(res.findings);
      setTotalFindings(res.total_findings);
      setCurrentPage(res.page);
    } catch (err: any) {
      console.error('Failed to load findings:', err);
    } finally {
      setIsLoadingFindings(false);
    }
  };

  const handleTriggerScan = async () => {
    try {
      setIsScanning(true);
      setErrorMsg(null);
      const newReport = await codeQualityService.triggerReview(projectId);
      setReport(newReport);
      setCurrentPage(1);
      loadFindings(1, activeFilters);
    } catch (err: any) {
      console.error('Failed to trigger code review scan:', err);
      setErrorMsg(
        err.response?.data?.detail || 'Failed to trigger code quality scan. Ensure codebase is imported.'
      );
    } finally {
      setIsScanning(false);
    }
  };

  const handleFilterChange = (filters: CodeReviewFindingsQueryParams) => {
    setActiveFilters(filters);
    setCurrentPage(1);
    loadFindings(1, filters);
  };

  const getHealthBadge = (status: CodeHealthStatus) => {
    switch (status) {
      case 'healthy':
        return (
          <Badge variant="success" size="md">
            <CheckCircle className="h-3.5 w-3.5" /> HEALTHY
          </Badge>
        );
      case 'needs_attention':
        return (
          <Badge variant="warning" size="md">
            <AlertTriangle className="h-3.5 w-3.5" /> NEEDS ATTENTION
          </Badge>
        );
      case 'at_risk':
        return (
          <Badge variant="error" size="md">
            <ShieldAlert className="h-3.5 w-3.5" /> AT RISK
          </Badge>
        );
      default:
        return <Badge variant="neutral">{status}</Badge>;
    }
  };

  const getScoreColorClass = (score: number) => {
    if (score >= 85) return 'text-emerald-600 dark:text-emerald-400';
    if (score >= 60) return 'text-amber-600 dark:text-amber-400';
    return 'text-red-600 dark:text-red-400';
  };

  if (isLoadingReport) {
    return (
      <div className="p-12 text-center text-xs text-slate-400">
        Loading Code Quality Intelligence dashboard...
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      {/* Dashboard Top Header & Actions */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-200 pb-5 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2.5">
            <h2 className="text-lg font-bold text-slate-900 dark:text-white">
              Code Quality & Review Intelligence (Sprint 2.1)
            </h2>
            {report && getHealthBadge(report.health_status)}
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Static multi-language vulnerability detection, quality scoring, and grounded AI remediation analysis
          </p>
        </div>

        <Button
          onClick={handleTriggerScan}
          disabled={isScanning}
          className="shrink-0 font-semibold"
        >
          {isScanning ? (
            <>
              <RotateCw className="h-4 w-4 mr-2 animate-spin" /> Scanning Codebase...
            </>
          ) : report ? (
            <>
              <RotateCw className="h-4 w-4 mr-2" /> Re-scan Codebase
            </>
          ) : (
            <>
              <Play className="h-4 w-4 mr-2" /> Trigger Review Scan
            </>
          )}
        </Button>
      </div>

      {errorMsg && (
        <div className="p-4 rounded-xl border border-red-200 bg-red-50 text-red-700 text-xs dark:border-red-900/60 dark:bg-red-950/40 dark:text-red-300">
          {errorMsg}
        </div>
      )}

      {!report ? (
        <div className="p-12 text-center rounded-2xl border border-dashed border-slate-300 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-950/20 space-y-3">
          <Activity className="h-10 w-10 text-indigo-500 mx-auto" />
          <h3 className="text-sm font-bold text-slate-900 dark:text-white">
            No Code Review Report Generated Yet
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 max-w-md mx-auto">
            Click "Trigger Review Scan" above to analyze the project's source code for security flaws, performance bottlenecks, and requirement compliance gaps.
          </p>
          <Button size="sm" onClick={handleTriggerScan} disabled={isScanning}>
            {isScanning ? 'Scanning...' : 'Start Code Review Scan'}
          </Button>
        </div>
      ) : (
        <>
          {/* Metrics Summary Overview Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
            {/* Score Card */}
            <div className="p-4 rounded-2xl border border-slate-200 bg-white shadow-xs dark:border-slate-800 dark:bg-slate-900 flex flex-col justify-between">
              <div className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                Overall Quality Score
              </div>
              <div className="my-2 flex items-baseline gap-1">
                <span className={`text-4xl font-extrabold ${getScoreColorClass(report.overall_score)}`}>
                  {report.overall_score}
                </span>
                <span className="text-sm font-semibold text-slate-400">/ 100</span>
              </div>
              <div className="text-[11px] text-slate-500 dark:text-slate-400">
                Base 100 deterministic score
              </div>
            </div>

            {/* Critical Count */}
            <div className="p-4 rounded-2xl border border-red-200 bg-red-50/40 shadow-xs dark:border-red-950/50 dark:bg-red-950/20 flex flex-col justify-between">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-red-700 dark:text-red-400 uppercase tracking-wider">
                  Critical Issues
                </span>
                <ShieldAlert className="h-4 w-4 text-red-600 dark:text-red-400" />
              </div>
              <div className="my-2 text-3xl font-extrabold text-red-700 dark:text-red-300">
                {report.critical_count}
              </div>
              <div className="text-[11px] text-red-600/80 dark:text-red-400/80">
                -15 pts each
              </div>
            </div>

            {/* Warning Count */}
            <div className="p-4 rounded-2xl border border-amber-200 bg-amber-50/40 shadow-xs dark:border-amber-950/50 dark:bg-amber-950/20 flex flex-col justify-between">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-amber-700 dark:text-amber-400 uppercase tracking-wider">
                  Warning Issues
                </span>
                <AlertTriangle className="h-4 w-4 text-amber-600 dark:text-amber-400" />
              </div>
              <div className="my-2 text-3xl font-extrabold text-amber-700 dark:text-amber-300">
                {report.warning_count}
              </div>
              <div className="text-[11px] text-amber-600/80 dark:text-amber-400/80">
                -5 pts each
              </div>
            </div>

            {/* Info Count */}
            <div className="p-4 rounded-2xl border border-indigo-200 bg-indigo-50/40 shadow-xs dark:border-indigo-950/50 dark:bg-indigo-950/20 flex flex-col justify-between">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-indigo-700 dark:text-indigo-400 uppercase tracking-wider">
                  Info Suggestions
                </span>
                <Info className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
              </div>
              <div className="my-2 text-3xl font-extrabold text-indigo-700 dark:text-indigo-300">
                {report.info_count}
              </div>
              <div className="text-[11px] text-indigo-600/80 dark:text-indigo-400/80">
                -1 pt each
              </div>
            </div>

            {/* Files Analyzed */}
            <div className="p-4 rounded-2xl border border-slate-200 bg-white shadow-xs dark:border-slate-800 dark:bg-slate-900 flex flex-col justify-between">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                  Files Scanned
                </span>
                <FileCode className="h-4 w-4 text-slate-400" />
              </div>
              <div className="my-2 text-3xl font-extrabold text-slate-900 dark:text-white">
                {report.total_files_analyzed}
              </div>
              <div className="text-[11px] text-slate-500 dark:text-slate-400">
                {report.total_issues_count} total findings
              </div>
            </div>
          </div>

          {/* Report Summary Card */}
          <div className="p-4 rounded-xl border border-slate-200 bg-slate-50/80 dark:border-slate-800 dark:bg-slate-900/50 text-xs text-slate-700 dark:text-slate-300 font-medium leading-relaxed">
            {report.summary}
          </div>

          {/* Category Distribution Breakdown */}
          <div className="p-5 rounded-2xl border border-slate-200 bg-white shadow-xs dark:border-slate-800 dark:bg-slate-900 space-y-3">
            <h3 className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider">
              Category Distribution Breakdown
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-5 gap-3">
              {Object.entries(report.category_counts).map(([cat, count]) => (
                <div
                  key={cat}
                  className="p-3 rounded-xl border border-slate-100 bg-slate-50/50 dark:border-slate-800 dark:bg-slate-950/30"
                >
                  <div className="flex items-center justify-between text-xs mb-1">
                    <span className="font-semibold capitalize text-slate-700 dark:text-slate-300">
                      {cat}
                    </span>
                    <span className="font-bold text-slate-900 dark:text-white">{count}</span>
                  </div>
                  <div className="w-full bg-slate-200 dark:bg-slate-800 h-1.5 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${
                        cat === 'security'
                          ? 'bg-red-500'
                          : cat === 'performance'
                          ? 'bg-amber-500'
                          : cat === 'maintainability'
                          ? 'bg-indigo-500'
                          : cat === 'compliance'
                          ? 'bg-purple-500'
                          : 'bg-emerald-500'
                      }`}
                      style={{
                        width: `${Math.min(100, (count / (report.total_issues_count || 1)) * 100)}%`,
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Findings Table */}
          <div className="space-y-3">
            <h3 className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider">
              Detailed Code Quality Findings ({totalFindings})
            </h3>
            <CodeFindingsTable
              findings={findings}
              totalFindings={totalFindings}
              currentPage={currentPage}
              pageSize={pageSize}
              isLoading={isLoadingFindings}
              onPageChange={(page) => {
                setCurrentPage(page);
                loadFindings(page, activeFilters);
              }}
              onFilterChange={handleFilterChange}
              onOpenImprovementModal={(fId) => {
                setTargetFindingId(fId);
                setIsImprovementModalOpen(true);
              }}
            />
          </div>

          <CodeImprovementModal
            isOpen={isImprovementModalOpen}
            projectId={projectId}
            findingId={targetFindingId}
            onClose={() => setIsImprovementModalOpen(false)}
            onAppliedSuccess={() => {
              loadLatestReport();
            }}
          />
        </>
      )}
    </div>
  );
};
