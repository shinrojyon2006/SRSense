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
