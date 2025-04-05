/**
 * This module provides a React Context for managing Prophet prediction data across the application.
 * It handles data fetching, loading states, and error management for Prophet predictions.
 */
import { createContext, type ReactNode, useContext, useEffect } from 'react';

import { useDatabaseOperations } from '@/context/database-operations-context';
import { type ProphetPredictionData } from '@/types/types';

import { useProphetPredictions } from '@/hooks/use-backend-api';

/**
 * Context state interface for Prophet predictions
 */
interface ProphetPredictionsContextState {
  /** Array of prediction data or null if not yet loaded */
  data: ProphetPredictionData[] | null;
  /** Loading state indicator */
  isLoading: boolean;
  /** Error object if fetch failed, null otherwise */
  error: Error | null;
  /** Function to manually trigger predictions fetch */
  fetchPredictions: () => Promise<void>;
}

/**
 * Props interface for the Provider component
 */
interface ProphetPredictionsProviderProps {
  /** Child components that will have access to the context */
  children: ReactNode;
}

/**
 * Context instance for Prophet predictions
 * Initially undefined, will be populated by the Provider
 */
const ProphetPredictionsContext = createContext<ProphetPredictionsContextState | undefined>(
  undefined
);

/**
 * Provider component for Prophet predictions context
 * Manages the state and data fetching for Prophet predictions
 *
 * @example
 * ```tsx
 * function App() {
 *   return (
 *     <ProphetPredictionsProvider>
 *       <YourComponents />
 *     </ProphetPredictionsProvider>
 *   );
 * }
 * ```
 */
export function ProphetPredictionsProvider({ children }: ProphetPredictionsProviderProps) {
  // Get prediction data and utilities from the hook
  const { data, isLoading, error, fetchPredictions } = useProphetPredictions();
  const { lastUpdated } = useDatabaseOperations();

  // Fetch predictions when the component mounts or when database is updated
  useEffect(() => {
    void fetchPredictions();
  }, [fetchPredictions, lastUpdated]);

  const contextValue: ProphetPredictionsContextState = {
    data,
    isLoading,
    error,
    fetchPredictions,
  };

  return (
    <ProphetPredictionsContext.Provider value={contextValue}>
      {children}
    </ProphetPredictionsContext.Provider>
  );
}

/**
 * Hook to access Prophet predictions context
 * Must be used within a ProphetPredictionsProvider
 *
 * @example
 * ```tsx
 * function YourComponent() {
 *   const { data, isLoading, error } = useProphetPredictionsContext();
 *
 *   if (isLoading) return <Loading />;
 *   if (error) return <Error message={error.message} />;
 *   if (!data) return null;
 *
 *   return <DisplayPredictions predictions={data} />;
 * }
 * ```
 *
 * @throws {Error} If used outside of ProphetPredictionsProvider
 * @returns {ProphetPredictionsContextState} Context state and utilities
 */
export function useProphetPredictionsContext(): ProphetPredictionsContextState {
  const context = useContext(ProphetPredictionsContext);

  if (context === undefined) {
    throw new Error(
      'useProphetPredictionsContext must be used within a ProphetPredictionsProvider'
    );
  }

  return context;
}
