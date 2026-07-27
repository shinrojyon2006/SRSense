import React from 'react';
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import { MainLayout } from '@/layouts/MainLayout';
import { LandingPage } from '@/features/landing';
import { Button } from '@/components/ui';
import { Home } from 'lucide-react';

const NotFoundPage: React.FC = () => (
  <div className="flex min-h-[70vh] flex-col items-center justify-center px-4 text-center">
    <h1 className="text-8xl font-black tracking-tighter text-[#4F46E5] dark:text-indigo-400">
      404
    </h1>
    <h2 className="mt-4 text-2xl font-bold text-slate-900 dark:text-white">
      Page Not Found
    </h2>
    <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
      The requested page does not exist or has been moved.
    </p>
    <div className="mt-6">
      <Link to="/">
        <Button variant="primary">
          <Home className="h-4 w-4" />
          Back to Home
        </Button>
      </Link>
    </div>
  </div>
);

export const AppRouter: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<MainLayout />}>
          <Route path="/" element={<LandingPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
};
