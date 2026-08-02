/**
 * Global TypeScript Interface & Type Definitions.
 */

export interface HealthResponse {
  status: string;
  version: string;
  database: string;
}

export type ThemeMode = 'light' | 'dark';

export interface BaseComponentProps {
  className?: string;
  children?: React.ReactNode;
}

// ── Auth & User Types ────────────────────────────────────────

export type UserRole = 'admin' | 'developer' | 'analyst';

export interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  created_at: string;
  updated_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  name: string;
  email: string;
  password: string;
  password_confirmation: string;
  role?: UserRole;
}

// ── Project Types ─────────────────────────────────────────────

export type ProjectStatus = 'draft' | 'active' | 'completed' | 'archived';

export interface Project {
  id: string;
  title: string;
  description: string;
  status: ProjectStatus;
  requirement_count: number;
  owner_id: string;
  created_at: string;
  updated_at: string;
}

export interface ProjectCreateInput {
  title: string;
  description?: string;
  status?: ProjectStatus;
}

export interface ProjectUpdateInput {
  title?: string;
  description?: string;
  status?: ProjectStatus;
  requirement_count?: number;
}
