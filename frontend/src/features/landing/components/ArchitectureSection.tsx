import React from 'react';
import { Server, Database, Code2, CheckCircle2 } from 'lucide-react';

const archModules = [
  {
    name: 'FastAPI Backend Engine',
    type: 'Feature Modules',
    icon: Server,
    desc: 'Modular app/modules/ setup with CORS, logging, and health routes',
  },
  {
    name: 'PostgreSQL 18 Database',
    icon: Database,
    type: 'Data Persistence',
    desc: 'Asyncpg connection pooling with Alembic migration pipeline',
  },
  {
    name: 'React + TypeScript + Tailwind v4',
    icon: Code2,
    type: 'Frontend Feature Engine',
    desc: 'Vite build engine, Framer Motion, Axios client, Lucide icons',
  },
];

export const ArchitectureSection: React.FC = () => {
  return (
    <section id="architecture" className="mx-auto max-w-6xl px-4 sm:px-6">
      <div className="rounded-2xl border border-slate-200 bg-white p-8 dark:border-slate-800 dark:bg-slate-900 sm:p-12">
        <div className="mb-10 text-center">
          <span className="text-xs font-bold uppercase tracking-wider text-[#4F46E5] dark:text-indigo-400">
            System Architecture
          </span>
          <h2 className="mt-2 text-2xl font-bold text-slate-900 sm:text-3xl dark:text-white">
            Sprint 1.1 Feature Architecture Overview
          </h2>
        </div>

        <div className="grid gap-6 md:grid-cols-3">
          {archModules.map((m) => (
            <div
              key={m.name}
              className="rounded-xl border border-slate-100 bg-slate-50 p-6 dark:border-slate-800/80 dark:bg-slate-950"
            >
              <div className="mb-3 flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#4F46E5] text-white">
                  <m.icon className="h-4 w-4" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                    {m.name}
                  </h3>
                  <p className="text-[11px] font-medium text-slate-500">
                    {m.type}
                  </p>
                </div>
              </div>
              <p className="text-xs leading-relaxed text-slate-600 dark:text-slate-400">
                {m.desc}
              </p>
            </div>
          ))}
        </div>

        <div className="mt-8 flex flex-wrap items-center justify-center gap-6 text-xs font-medium text-slate-500 border-t border-slate-100 pt-6 dark:border-slate-800 dark:text-slate-400">
          <span className="flex items-center gap-1.5">
            <CheckCircle2 className="h-4 w-4 text-emerald-500" />
            FastAPI Async Modules
          </span>
          <span className="flex items-center gap-1.5">
            <CheckCircle2 className="h-4 w-4 text-emerald-500" />
            React TypeScript Strict
          </span>
          <span className="flex items-center gap-1.5">
            <CheckCircle2 className="h-4 w-4 text-emerald-500" />
            Multi-Stage Docker Builds
          </span>
          <span className="flex items-center gap-1.5">
            <CheckCircle2 className="h-4 w-4 text-emerald-500" />
            ESLint & Prettier & Husky
          </span>
        </div>
      </div>
    </section>
  );
};
