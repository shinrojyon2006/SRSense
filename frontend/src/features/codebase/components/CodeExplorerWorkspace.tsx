import React, { useState, useEffect } from 'react';
import {
  Search,
  FileCode,
  Layers,
  Code,
  Link,
  Database,
  Globe,
  Plus,
  Trash2,
  X,
} from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { codebaseService } from '../api/codebaseService';
import {
  CodeFileSummary,
  CodeFileDetail,
  CodeSymbol,
  CodeDependency,
  RequirementCodeLink,
} from '../types/codebase.types';

interface CodeExplorerWorkspaceProps {
  isOpen: boolean;
  projectId: string;
  onClose: () => void;
  onOpenLinkModal: (fileId?: string, symbolId?: string) => void;
}

export const CodeExplorerWorkspace: React.FC<CodeExplorerWorkspaceProps> = ({
  isOpen,
  projectId,
  onClose,
  onOpenLinkModal,
}) => {
  const [activeTab, setActiveTab] = useState<'files' | 'symbols' | 'dependencies' | 'links'>('files');

  // Files Tab State
  const [files, setFiles] = useState<CodeFileSummary[]>([]);
  const [selectedFile, setSelectedFile] = useState<CodeFileDetail | null>(null);
  const [fileSearch, setFileSearch] = useState('');
  const [selectedLang, setSelectedLang] = useState('all');
  const [isLoadingFiles, setIsLoadingFiles] = useState(false);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);

  // Symbols Tab State
  const [symbolQuery, setSymbolQuery] = useState('');
  const [symbolTypeFilter, setSymbolTypeFilter] = useState('all');
  const [symbolResults, setSymbolResults] = useState<CodeSymbol[]>([]);
  const [isSearchingSymbols, setIsSearchingSymbols] = useState(false);

  // Dependencies Tab State
  const [dependencies, setDependencies] = useState<CodeDependency[]>([]);
  const [isLoadingDeps, setIsLoadingDeps] = useState(false);

  // Requirement Links State
  const [links, setLinks] = useState<RequirementCodeLink[]>([]);
  const [isLoadingLinks, setIsLoadingLinks] = useState(false);

  // Initial Load
  useEffect(() => {
    if (isOpen && projectId) {
      loadFiles();
      loadLinks();
    }
  }, [isOpen, projectId]);

  const loadFiles = async (search?: string, lang?: string) => {
    try {
      setIsLoadingFiles(true);
      const res = await codebaseService.listFiles(projectId, search, lang);
      setFiles(res);
      if (res.length > 0 && !selectedFile) {
        loadFileDetail(res[0].id);
      }
    } catch (err) {
      console.error('Failed to load code files:', err);
    } finally {
      setIsLoadingFiles(false);
    }
  };

  const loadFileDetail = async (fileId: string) => {
    try {
      setIsLoadingDetail(true);
      const detail = await codebaseService.getFileDetail(projectId, fileId);
      setSelectedFile(detail);
    } catch (err) {
      console.error('Failed to load file detail:', err);
    } finally {
      setIsLoadingDetail(false);
    }
  };

  const handleSearchSymbols = async (q: string, symType?: string) => {
    if (!q.trim()) return;
    try {
      setIsSearchingSymbols(true);
      const res = await codebaseService.searchSymbols(
        projectId,
        q,
        symType !== 'all' ? symType : undefined
      );
      setSymbolResults(res);
    } catch (err) {
      console.error('Failed to search symbols:', err);
    } finally {
      setIsSearchingSymbols(false);
    }
  };

  const loadDependencies = async () => {
    try {
      setIsLoadingDeps(true);
      const res = await codebaseService.getDependencies(projectId);
      setDependencies(res);
    } catch (err) {
      console.error('Failed to load dependencies:', err);
    } finally {
      setIsLoadingDeps(false);
    }
  };

  const loadLinks = async () => {
    try {
      setIsLoadingLinks(true);
      const res = await codebaseService.listLinks(projectId);
      setLinks(res);
    } catch (err) {
      console.error('Failed to load requirement links:', err);
    } finally {
      setIsLoadingLinks(false);
    }
  };

  const handleDeleteLink = async (linkId: string) => {
    try {
      await codebaseService.deleteLink(projectId, linkId);
      await loadLinks();
    } catch (err) {
      console.error('Failed to delete link:', err);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 p-4 sm:p-6 backdrop-blur-xs">
      <div className="flex h-[90vh] w-full max-w-6xl flex-col rounded-2xl border border-slate-200 bg-white shadow-2xl dark:border-slate-800 dark:bg-slate-900 overflow-hidden">
        {/* Workspace Top Header */}
        <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4 dark:border-slate-800">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 dark:text-indigo-400">
              <Code className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-900 dark:text-white">
                Code Intelligence Workspace (Sprint 2.0)
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Multi-Language AST Inspection, Discovered Symbols, and Requirement ↔ Code Linking
              </p>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex items-center gap-1 bg-slate-100 dark:bg-slate-800/80 p-1 rounded-lg">
            <button
              onClick={() => setActiveTab('files')}
              className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
                activeTab === 'files'
                  ? 'bg-white text-indigo-600 shadow-xs dark:bg-slate-700 dark:text-white'
                  : 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white'
              }`}
            >
              Files ({files.length})
            </button>
            <button
              onClick={() => setActiveTab('symbols')}
              className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
                activeTab === 'symbols'
                  ? 'bg-white text-indigo-600 shadow-xs dark:bg-slate-700 dark:text-white'
                  : 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white'
              }`}
            >
              Symbol Search
            </button>
            <button
              onClick={() => {
                setActiveTab('dependencies');
                loadDependencies();
              }}
              className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
                activeTab === 'dependencies'
                  ? 'bg-white text-indigo-600 shadow-xs dark:bg-slate-700 dark:text-white'
                  : 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white'
              }`}
            >
              Dependencies
            </button>
            <button
              onClick={() => {
                setActiveTab('links');
                loadLinks();
              }}
              className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
                activeTab === 'links'
                  ? 'bg-white text-indigo-600 shadow-xs dark:bg-slate-700 dark:text-white'
                  : 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white'
              }`}
            >
              Req ↔ Code Links ({links.length})
            </button>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:bg-slate-100 hover:text-slate-700 dark:hover:bg-slate-800 dark:hover:text-slate-200 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Workspace Body */}
        <div className="flex-1 overflow-hidden">
          {activeTab === 'files' && (
            <div className="grid grid-cols-1 md:grid-cols-12 h-full">
              {/* Left Pane: Files List & Filters */}
              <div className="md:col-span-5 border-r border-slate-200 dark:border-slate-800 flex flex-col h-full bg-slate-50/50 dark:bg-slate-950/20">
                {/* Search & Filter Toolbar */}
                <div className="p-3 border-b border-slate-200 dark:border-slate-800 space-y-2">
                  <div className="relative">
                    <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-slate-400" />
                    <input
                      type="text"
                      placeholder="Filter files..."
                      value={fileSearch}
                      onChange={(e) => {
                        setFileSearch(e.target.value);
                        loadFiles(e.target.value, selectedLang);
                      }}
                      className="w-full rounded-lg border border-slate-200 bg-white pl-8 pr-3 py-1.5 text-xs text-slate-900 focus:border-indigo-500 focus:outline-none dark:border-slate-800 dark:bg-slate-900 dark:text-white"
                    />
                  </div>
                  <div className="flex items-center gap-2">
                    <select
                      value={selectedLang}
                      onChange={(e) => {
                        setSelectedLang(e.target.value);
                        loadFiles(fileSearch, e.target.value);
                      }}
                      className="w-full rounded-lg border border-slate-200 bg-white px-2.5 py-1 text-xs text-slate-900 focus:border-indigo-500 focus:outline-none dark:border-slate-800 dark:bg-slate-900 dark:text-white"
                    >
                      <option value="all">All Languages</option>
                      <option value="Python">Python</option>
                      <option value="TypeScript">TypeScript</option>
                      <option value="JavaScript">JavaScript</option>
                      <option value="Java">Java</option>
                      <option value="C">C</option>
                      <option value="C++">C++</option>
                      <option value="SQL">SQL</option>
                      <option value="HTML">HTML</option>
                      <option value="CSS">CSS</option>
                      <option value="Unknown / Unsupported">Unknown / Unsupported</option>
                    </select>
                  </div>
                </div>

                {/* Files List Scroll */}
                <div className="flex-1 overflow-y-auto p-2 space-y-1">
                  {isLoadingFiles ? (
                    <div className="p-6 text-center text-xs text-slate-400">Loading files...</div>
                  ) : files.length === 0 ? (
                    <div className="p-6 text-center text-xs text-slate-400">No files found.</div>
                  ) : (
                    files.map((file) => (
                      <button
                        key={file.id}
                        onClick={() => loadFileDetail(file.id)}
                        className={`w-full text-left p-2.5 rounded-lg transition-all flex items-center justify-between gap-2 text-xs ${
                          selectedFile?.id === file.id
                            ? 'bg-indigo-50 text-indigo-900 font-semibold dark:bg-indigo-950/60 dark:text-indigo-200 border border-indigo-200/60 dark:border-indigo-800/80'
                            : 'hover:bg-slate-100 dark:hover:bg-slate-800/50 text-slate-700 dark:text-slate-300'
                        }`}
                      >
                        <div className="flex items-center gap-2 truncate">
                          <FileCode className="h-4 w-4 shrink-0 text-slate-400" />
                          <span className="truncate">{file.path}</span>
                        </div>
                        <div className="flex items-center gap-1.5 shrink-0">
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-200/70 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
                            {file.language}
                          </span>
                          <span className="text-[10px] text-slate-400">
                            {file.line_count} L
                          </span>
                        </div>
                      </button>
                    ))
                  )}
                </div>
              </div>

              {/* Right Pane: Selected File AST Detail Inspector */}
              <div className="md:col-span-7 flex flex-col h-full overflow-y-auto p-6 space-y-6">
                {isLoadingDetail ? (
                  <div className="p-12 text-center text-xs text-slate-400">Loading AST details...</div>
                ) : !selectedFile ? (
                  <div className="p-12 text-center text-xs text-slate-400">Select a file to inspect its structure.</div>
                ) : (
                  <div className="space-y-6">
                    {/* File Header */}
                    <div className="flex items-start justify-between gap-4 border-b border-slate-100 pb-4 dark:border-slate-800">
                      <div>
                        <div className="flex items-center gap-2">
                          <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                            {selectedFile.filename}
                          </h3>
                          <Badge variant="neutral">{selectedFile.language}</Badge>
                          <Badge variant={selectedFile.confidence === 'High' ? 'success' : 'warning'}>
                            Confidence: {selectedFile.confidence}
                          </Badge>
                        </div>
                        <p className="text-xs text-slate-400 font-mono mt-1">
                          {selectedFile.path}
                        </p>
                      </div>

                      <Button
                        size="sm"
                        onClick={() => onOpenLinkModal(selectedFile.id)}
                        className="shrink-0"
                      >
                        <Link className="h-3.5 w-3.5 mr-1" /> Link to Requirement
                      </Button>
                    </div>

                    {/* Quick Metrics */}
                    <div className="grid grid-cols-3 gap-3">
                      <div className="rounded-lg bg-slate-50 p-2.5 dark:bg-slate-950/40 border border-slate-100 dark:border-slate-800">
                        <div className="text-[11px] text-slate-400">Line Count</div>
                        <div className="text-sm font-bold text-slate-800 dark:text-slate-200">
                          {selectedFile.line_count} lines
                        </div>
                      </div>
                      <div className="rounded-lg bg-slate-50 p-2.5 dark:bg-slate-950/40 border border-slate-100 dark:border-slate-800">
                        <div className="text-[11px] text-slate-400">Symbols Extracted</div>
                        <div className="text-sm font-bold text-slate-800 dark:text-slate-200">
                          {selectedFile.symbols.length}
                        </div>
                      </div>
                      <div className="rounded-lg bg-slate-50 p-2.5 dark:bg-slate-950/40 border border-slate-100 dark:border-slate-800">
                        <div className="text-[11px] text-slate-400">Endpoints / DB</div>
                        <div className="text-sm font-bold text-slate-800 dark:text-slate-200">
                          {selectedFile.endpoints.length + selectedFile.db_interactions.length}
                        </div>
                      </div>
                    </div>

                    {/* Discovered Endpoints / Routes */}
                    {selectedFile.endpoints.length > 0 && (
                      <div className="space-y-2">
                        <div className="text-xs font-bold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
                          <Globe className="h-3.5 w-3.5 text-indigo-500" /> API Endpoints & Routes ({selectedFile.endpoints.length})
                        </div>
                        <div className="space-y-1.5">
                          {selectedFile.endpoints.map((ep, idx) => (
                            <div
                              key={idx}
                              className="p-2.5 rounded-lg border border-indigo-100 bg-indigo-50/40 dark:border-indigo-900/40 dark:bg-indigo-950/20 text-xs flex items-center justify-between"
                            >
                              <div className="flex items-center gap-2">
                                <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-indigo-600 text-white">
                                  {ep.http_method}
                                </span>
                                <span className="font-mono text-slate-800 dark:text-slate-200">
                                  {ep.path}
                                </span>
                              </div>
                              {ep.line_number && (
                                <span className="text-[10px] text-slate-400 font-mono">
                                  Line {ep.line_number}
                                </span>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Discovered AST Symbols */}
                    <div className="space-y-2">
                      <div className="text-xs font-bold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
                        <Layers className="h-3.5 w-3.5 text-emerald-500" /> Extracted Symbols ({selectedFile.symbols.length})
                      </div>
                      {selectedFile.symbols.length === 0 ? (
                        <div className="p-4 text-xs text-slate-400 bg-slate-50 dark:bg-slate-950/40 rounded-lg border border-slate-100 dark:border-slate-800">
                          No top-level classes or functions extracted.
                        </div>
                      ) : (
                        <div className="space-y-2">
                          {selectedFile.symbols.map((sym) => (
                            <div
                              key={sym.id}
                              className="p-3 rounded-lg border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900 flex items-start justify-between gap-3 text-xs"
                            >
                              <div>
                                <div className="flex items-center gap-2">
                                  <span className="font-bold text-slate-900 dark:text-white">
                                    {sym.symbol_name}
                                  </span>
                                  <Badge variant="neutral">{sym.symbol_type}</Badge>
                                  {sym.parent_symbol_name && (
                                    <span className="text-[10px] text-slate-400">
                                      (in {sym.parent_symbol_name})
                                    </span>
                                  )}
                                </div>
                                {sym.signature && (
                                  <div className="mt-1 font-mono text-[11px] text-slate-600 dark:text-slate-400">
                                    {sym.signature}
                                  </div>
                                )}
                                {sym.docstring && (
                                  <div className="mt-1 text-[11px] text-slate-500 dark:text-slate-400 italic">
                                    "{sym.docstring}"
                                  </div>
                                )}
                              </div>
                              <div className="flex items-center gap-2 shrink-0">
                                {sym.line_start && (
                                  <span className="text-[10px] text-slate-400 font-mono">
                                    L{sym.line_start}
                                    {sym.line_end ? `-${sym.line_end}` : ''}
                                  </span>
                                )}
                                <button
                                  onClick={() => onOpenLinkModal(selectedFile.id, sym.id)}
                                  className="text-[11px] text-indigo-600 hover:text-indigo-700 dark:text-indigo-400 font-semibold"
                                  title="Link symbol to requirement"
                                >
                                  Link
                                </button>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Database Interactions */}
                    {selectedFile.db_interactions.length > 0 && (
                      <div className="space-y-2">
                        <div className="text-xs font-bold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
                          <Database className="h-3.5 w-3.5 text-purple-500" /> Database Interactions ({selectedFile.db_interactions.length})
                        </div>
                        <div className="space-y-1.5">
                          {selectedFile.db_interactions.map((db, idx) => (
                            <div
                              key={idx}
                              className="p-2.5 rounded-lg border border-purple-100 bg-purple-50/40 dark:border-purple-900/40 dark:bg-purple-950/20 text-xs flex items-center justify-between"
                            >
                              <div>
                                <span className="font-bold text-purple-900 dark:text-purple-200">
                                  {db.operation_type}
                                </span>
                                <div className="font-mono text-[11px] text-slate-600 dark:text-slate-400 mt-0.5">
                                  {db.matched_code}
                                </div>
                              </div>
                              {db.line_number && (
                                <span className="text-[10px] text-slate-400 font-mono">
                                  Line {db.line_number}
                                </span>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Imports */}
                    {selectedFile.imports.length > 0 && (
                      <div className="space-y-2">
                        <div className="text-xs font-bold text-slate-700 dark:text-slate-300">
                          Imports ({selectedFile.imports.length})
                        </div>
                        <div className="p-3 bg-slate-50 dark:bg-slate-950/50 rounded-lg border border-slate-100 dark:border-slate-800 text-[11px] font-mono text-slate-600 dark:text-slate-400 space-y-1 max-h-36 overflow-y-auto">
                          {selectedFile.imports.map((imp, idx) => (
                            <div key={idx}>{imp}</div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}

          {activeTab === 'symbols' && (
            <div className="p-6 space-y-4 h-full flex flex-col">
              <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
                <div className="sm:col-span-3 relative">
                  <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                  <input
                    type="text"
                    placeholder="Search classes, functions, endpoints across the entire codebase..."
                    value={symbolQuery}
                    onChange={(e) => {
                      setSymbolQuery(e.target.value);
                      handleSearchSymbols(e.target.value, symbolTypeFilter);
                    }}
                    className="w-full rounded-lg border border-slate-200 bg-white pl-9 pr-3 py-2 text-xs text-slate-900 focus:border-indigo-500 focus:outline-none dark:border-slate-800 dark:bg-slate-900 dark:text-white"
                  />
                </div>
                <div>
                  <select
                    value={symbolTypeFilter}
                    onChange={(e) => {
                      setSymbolTypeFilter(e.target.value);
                      handleSearchSymbols(symbolQuery, e.target.value);
                    }}
                    className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs text-slate-900 focus:border-indigo-500 focus:outline-none dark:border-slate-800 dark:bg-slate-900 dark:text-white"
                  >
                    <option value="all">All Symbol Types</option>
                    <option value="class">Class / Struct</option>
                    <option value="function">Function</option>
                    <option value="method">Method</option>
                    <option value="endpoint">API Endpoint</option>
                    <option value="table">SQL Table</option>
                  </select>
                </div>
              </div>

              <div className="flex-1 overflow-y-auto space-y-2">
                {isSearchingSymbols ? (
                  <div className="p-12 text-center text-xs text-slate-400">Searching symbols...</div>
                ) : symbolResults.length === 0 ? (
                  <div className="p-12 text-center text-xs text-slate-400">
                    {symbolQuery ? 'No matching symbols found.' : 'Type a query to search symbols in the codebase.'}
                  </div>
                ) : (
                  symbolResults.map((sym) => (
                    <div
                      key={sym.id}
                      className="p-3 rounded-lg border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900 flex items-center justify-between text-xs"
                    >
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-slate-900 dark:text-white">
                            {sym.symbol_name}
                          </span>
                          <Badge variant="neutral">{sym.symbol_type}</Badge>
                        </div>
                        {sym.signature && (
                          <div className="text-[11px] font-mono text-slate-500 dark:text-slate-400 mt-0.5">
                            {sym.signature}
                          </div>
                        )}
                      </div>
                      <Button
                        size="sm"
                        variant="secondary"
                        onClick={() => onOpenLinkModal(sym.file_id, sym.id)}
                      >
                        <Link className="h-3 w-3 mr-1" /> Link
                      </Button>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}

          {activeTab === 'dependencies' && (
            <div className="p-6 space-y-4 h-full flex flex-col">
              <div className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                Discovered Import & Module Dependencies ({dependencies.length})
              </div>
              <div className="flex-1 overflow-y-auto space-y-2">
                {isLoadingDeps ? (
                  <div className="p-12 text-center text-xs text-slate-400">Loading dependencies...</div>
                ) : dependencies.length === 0 ? (
                  <div className="p-12 text-center text-xs text-slate-400">No dependencies discovered.</div>
                ) : (
                  dependencies.map((dep) => (
                    <div
                      key={dep.id}
                      className="p-3 rounded-lg border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900 flex items-center justify-between text-xs"
                    >
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-slate-700 dark:text-slate-300">
                          {dep.source_file_path || 'Source File'}
                        </span>
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-indigo-50 text-indigo-600 dark:bg-indigo-950 dark:text-indigo-400 font-semibold">
                          {dep.dependency_type.toUpperCase()}
                        </span>
                        <span className="font-mono font-bold text-slate-900 dark:text-white">
                          {dep.target_module}
                        </span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}

          {activeTab === 'links' && (
            <div className="p-6 space-y-4 h-full flex flex-col">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-xs font-bold text-slate-900 dark:text-white">
                    Requirement ↔ Code Links ({links.length})
                  </h3>
                  <p className="text-[11px] text-slate-500 dark:text-slate-400">
                    Explicit traceability mappings connecting SRS specifications with source files and symbols.
                  </p>
                </div>
                <Button size="sm" onClick={() => onOpenLinkModal()}>
                  <Plus className="h-3.5 w-3.5 mr-1" /> Add New Link
                </Button>
              </div>

              <div className="flex-1 overflow-y-auto space-y-2">
                {isLoadingLinks ? (
                  <div className="p-12 text-center text-xs text-slate-400">Loading links...</div>
                ) : links.length === 0 ? (
                  <div className="p-12 text-center text-xs text-slate-400">
                    No Requirement ↔ Code links created yet. Click "Add New Link" or browse files to create a link.
                  </div>
                ) : (
                  links.map((link) => (
                    <div
                      key={link.id}
                      className="p-3.5 rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900 flex items-center justify-between gap-4 text-xs"
                    >
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-slate-900 dark:text-white">
                            {link.requirement_identifier || 'REQ'}: {link.requirement_title}
                          </span>
                          <Badge variant="success">
                            {link.link_type === 'explicit_manual' ? 'Manual Link' : 'Referenced'}
                          </Badge>
                        </div>
                        <div className="flex items-center gap-2 text-slate-500 dark:text-slate-400 font-mono text-[11px]">
                          <span>File: {link.file_path}</span>
                          {link.symbol_name && (
                            <>
                              <span>•</span>
                              <span>Symbol: {link.symbol_name} ({link.symbol_type})</span>
                            </>
                          )}
                        </div>
                        {link.notes && (
                          <div className="text-[11px] text-slate-600 dark:text-slate-300 italic">
                            Notes: "{link.notes}"
                          </div>
                        )}
                      </div>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => handleDeleteLink(link.id)}
                        className="text-red-500 hover:text-red-600 dark:text-red-400"
                        title="Remove Link"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
