// A10 FIX: useTheme now reads from ThemeContext (single source of truth).
// Previously it used local useState which caused independent state per component instance.
export { useTheme } from '@/contexts/ThemeContext';
