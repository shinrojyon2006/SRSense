import React from 'react';
import { Button } from '@/components/ui';

export const CtaSection: React.FC = () => {
  return (
    <section id="cta" className="mx-auto max-w-4xl px-4 sm:px-6">
      <div className="rounded-2xl bg-gradient-to-br from-[#4F46E5] to-indigo-700 p-10 text-center text-white shadow-xl sm:p-14">
        <h2 className="text-3xl font-extrabold sm:text-4xl">
          SRSense AI Feature Architecture Ready
        </h2>
        <p className="mx-auto mt-4 max-w-xl text-indigo-100">
          Sprint 1.1 Project Foundation completed with strict engineering standards, ready for upcoming feature sprint modules.
        </p>
        <div className="mt-8 flex justify-center gap-4">
          <a href="/api/health" target="_blank" rel="noopener noreferrer">
            <Button variant="secondary" size="lg">
              View Health API
            </Button>
          </a>
        </div>
      </div>
    </section>
  );
};
