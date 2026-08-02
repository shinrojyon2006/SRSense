import React, { useState } from 'react';
import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom';
import {
  Sparkles,
  LayoutDashboard,
  FolderKanban,
  LogOut,
  User as UserIcon,
  Menu,
  X,
  ChevronRight,
} from 'lucide-react';
import { Badge, Button, ThemeToggle } from '@/components/ui';
import { useAuth } from '@/contexts/AuthContext';

export const DashboardLayout: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const navItems = [
    {
      label: 'Dashboard',
      to: '/dashboard',
      icon: LayoutDashboard,
    },
    {
      label: 'Projects',
      to: '/projects',
      icon: FolderKanban,
    },
  ];

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100">
      {/* Top Header */}
      <header className="sticky top-0 z-30 h-16 border-b border-slate-200 bg-white/90 backdrop-blur-md dark:border-slate-800 dark:bg-slate-900/90">
        <div className="flex h-full items-center justify-between px-4 sm:px-6">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 md:hidden dark:text-slate-400 dark:hover:bg-slate-800"
              aria-label="Toggle Navigation"
            >
              {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>

            <Link to="/dashboard" className="flex items-center gap-2.5">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#4F46E5] text-white">
                <Sparkles className="h-4 w-4" />
              </div>
              <span className="text-base font-bold tracking-tight text-slate-900 dark:text-white">
                SRSense AI
              </span>
            </Link>
          </div>

          <div className="flex items-center gap-3">
            <ThemeToggle />

            {user && (
              <div className="hidden items-center gap-3 sm:flex">
                <div className="flex items-center gap-2.5 rounded-lg border border-slate-200 bg-slate-50 px-3 py-1.5 dark:border-slate-800 dark:bg-slate-800/60">
                  <div className="flex h-7 w-7 items-center justify-center rounded-full bg-indigo-100 text-indigo-700 dark:bg-indigo-900/50 dark:text-indigo-300">
                    <UserIcon className="h-3.5 w-3.5" />
                  </div>
                  <div className="text-left">
                    <p className="text-xs font-semibold text-slate-900 dark:text-white">
                      {user.name}
                    </p>
                    <Badge variant="primary" size="sm" className="mt-0.5 text-[9px]">
                      {user.role}
                    </Badge>
                  </div>
                </div>

                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleLogout}
                  className="text-slate-500 hover:text-red-600 dark:text-slate-400 dark:hover:text-red-400"
                >
                  <LogOut className="h-4 w-4" />
                  Logout
                </Button>
              </div>
            )}
          </div>
        </div>
      </header>

      <div className="flex">
        {/* Sidebar Navigation */}
        <aside
          className={`fixed inset-y-0 left-0 z-20 w-64 transform border-r border-slate-200 bg-white transition-transform duration-200 ease-in-out md:static md:translate-x-0 dark:border-slate-800 dark:bg-slate-900 ${
            mobileMenuOpen ? 'translate-x-0 pt-16' : '-translate-x-full md:translate-x-0'
          }`}
        >
          <div className="flex h-full flex-col justify-between p-4">
            <nav className="space-y-1">
              <p className="px-3 pb-2 text-[10px] font-bold uppercase tracking-wider text-slate-400">
                Main Menu
              </p>
              {navItems.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  onClick={() => setMobileMenuOpen(false)}
                  className={({ isActive }) =>
                    `flex items-center justify-between rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                      isActive
                        ? 'bg-indigo-50 text-[#4F46E5] dark:bg-indigo-950/60 dark:text-indigo-300'
                        : 'text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800/60'
                    }`
                  }
                >
                  <div className="flex items-center gap-3">
                    <item.icon className="h-4 w-4 shrink-0" />
                    <span>{item.label}</span>
                  </div>
                  <ChevronRight className="h-3.5 w-3.5 opacity-50" />
                </NavLink>
              ))}
            </nav>

            <div className="border-t border-slate-100 pt-4 dark:border-slate-800 sm:hidden">
              {user && (
                <div className="mb-3 space-y-1 px-3">
                  <p className="text-xs font-bold text-slate-900 dark:text-white">
                    {user.name}
                  </p>
                  <p className="text-[11px] text-slate-500">{user.email}</p>
                </div>
              )}
              <Button
                variant="ghost"
                size="sm"
                onClick={handleLogout}
                className="w-full justify-start text-red-600 dark:text-red-400"
              >
                <LogOut className="h-4 w-4" />
                Logout
              </Button>
            </div>
          </div>
        </aside>

        {/* Main Content Area */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8">
          <div className="mx-auto max-w-6xl">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
};
