import { createContext, type ReactNode, useContext, useEffect } from 'react';

import { type ProphetPredictionData } from '@/types/types';

import { useProphetPredictions } from '@/hooks/use-backend-api';

type ProphetPredictionsContextType = {
  data: ProphetPredictionData[] | null;
  isLoading: boolean;
  error: Error | null;
  fetchPredictions: () => Promise<void>;
};

const ProphetPredictionsContext = createContext<ProphetPredictionsContextType | undefined>(
  undefined
);

export function ProphetPredictionsProvider({ children }: { children: ReactNode }) {
  const { data, isLoading, error, fetchPredictions } = useProphetPredictions();

  useEffect(() => {
    void fetchPredictions();
  }, [fetchPredictions]);

  return (
    <ProphetPredictionsContext.Provider
      value={{
        data,
        isLoading,
        error,
        fetchPredictions,
      }}
    >
      {children}
    </ProphetPredictionsContext.Provider>
  );
}

export function useProphetPredictionsContext() {
  const context = useContext(ProphetPredictionsContext);
  if (context === undefined) {
    throw new Error(
      'useProphetPredictionsContext must be used within a ProphetPredictionsProvider'
    );
  }
  return context;
}
