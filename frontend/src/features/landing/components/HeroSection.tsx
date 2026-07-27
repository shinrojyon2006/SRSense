import React from 'react';
import { motion } from 'framer-motion';
import { Sparkles, ArrowRight, Activity } from 'lucide-react';
import { Button } from '@/components/ui';
import { useHealth } from '@/hooks/useHealth';

const fadeUp = {
  hidden: { opacity: 0, y: 20 },
  visible: (i: number = 0) => ({
    opacity: 1,
    y: 0,
    transition: { duration: 0.5, delay: i * 0.1, ease: 'easeOut' },
  }),
};

export const HeroSection: React.FC = () => {
  const { data: healthStatus, isLoading } = useHealth();

  return (
    <section className="relative overflow-hidden pt-20 pb-16">
      <div className="pointer-events-none absolute inset-0 -z-10 flex items-center justify-center">
        <div className="h-[500px] w-[650px] rounded-full bg-indigo-500/10 blur-3xl dark:bg-indigo-500/15" />
      </div>

      <div className="mx-auto max-w-5xl px-4 text-center sm:px-6">
        <motion.div initial="hidden" animate="visible" className="space-y-6">
          <motion.div variants={fadeUp} custom={0} className="flex justify-center">
            <span className="inline-flex items-center gap-2 rounded-full border border-indigo-200 bg-indigo-50 px-3.5 py-1 text-xs font-semibold text-indigo-700 dark:border-indigo-800 dark:bg-indigo-950/50 dark:text-indigo-300">
              <Sparkles className="h-3.5 w-3.5" />
              Sprint 1.1 Feature Architecture Live
            </span>
          </motion.div>

          <motion.h1
            variants={fadeUp}
            custom={1}
            className="text-4xl font-extrabold tracking-tight text-slate-900 sm:text-6xl dark:text-white"
          >
            The Next-Generation{' '}
            <span className="text-[#4F46E5] dark:text-indigo-400">
              Requirements Engineering
            </span>{' '}
            Platform
          </motion.h1>

          <motion.p
            variants={fadeUp}
            custom={2}
            className="mx-auto max-w-2xl text-lg text-slate-600 dark:text-slate-400"
          >
            SRSense AI transforms how software development teams upload, analyze,
            refine, and manage requirement specifications with production-ready
            architecture.
          </motion.p>

          <motion.div
            variants={fadeUp}
            custom={3}
            className="flex flex-col items-center justify-center gap-4 sm:flex-row"
          >
            <a href="#architecture">
              <Button variant="primary" size="lg">
                Explore Architecture
                <ArrowRight className="h-4 w-4" />
              </Button>
            </a>

            <div className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-4 py-2.5 text-xs font-medium text-slate-700 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300">
              <Activity className="h-4 w-4 text-emerald-500 animate-pulse" />
              Backend API:{' '}
              <span className="font-semibold capitalize text-emerald-600 dark:text-emerald-400">
                {isLoading
                  ? 'Connecting...'
                  : healthStatus
                  ? `${healthStatus.status} (v${healthStatus.version})`
                  : 'Offline'}
              </span>
            </div>
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
};
