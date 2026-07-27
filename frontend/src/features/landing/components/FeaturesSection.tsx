import React from 'react';
import { Layers, Cpu, ShieldCheck, Zap } from 'lucide-react';
import { Card } from '@/components/ui';

const features = [
  {
    icon: Layers,
    title: 'Clean Feature Architecture',
    description:
      'Engineered following SOLID principles and feature-based directory encapsulation for both frontend and backend.',
  },
  {
    icon: Cpu,
    title: 'Async High Performance',
    description:
      'Powered by Python 3.12, FastAPI, and async SQLAlchemy 2.0 with PostgreSQL connection pooling.',
  },
  {
    icon: ShieldCheck,
    title: 'Enterprise Quality Standards',
    description:
      'TypeScript strict mode, ESLint, Prettier, Husky pre-commit hooks, and multi-stage Docker builds.',
  },
  {
    icon: Zap,
    title: 'Tailwind CSS v4 Design System',
    description:
      'Modern accessible user interface with framer-motion micro-animations and seamless dark mode support.',
  },
];

export const FeaturesSection: React.FC = () => {
  return (
    <section id="features" className="mx-auto max-w-6xl px-4 sm:px-6">
      <div className="mb-12 text-center">
        <h2 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
          Built on Uncompromising Software Engineering Standards
        </h2>
        <p className="mt-3 text-slate-600 dark:text-slate-400">
          Sprint 1.1 establishes a modular, feature-based foundation ready for enterprise scaling.
        </p>
      </div>

      <div className="grid gap-6 sm:grid-cols-2">
        {features.map((feature) => (
          <Card key={feature.title} className="group">
            <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-50 text-[#4F46E5] dark:bg-indigo-950/50 dark:text-indigo-400">
              <feature.icon className="h-5 w-5" />
            </div>
            <h3 className="mb-2 text-base font-semibold text-slate-900 dark:text-white">
              {feature.title}
            </h3>
            <p className="text-sm leading-relaxed text-slate-600 dark:text-slate-400">
              {feature.description}
            </p>
          </Card>
        ))}
      </div>
    </section>
  );
};
