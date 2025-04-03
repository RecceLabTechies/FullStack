/**
 * This module provides React hooks for interacting with the Language Learning Model (LLM) API.
 * It handles state management, data fetching, and response type checking for LLM analysis.
 */
import { useState } from 'react';

import { checkHealth, sendQuery } from '@/api/llmApi';
import { type HealthResponse, type QueryResponse } from '@/types/types';

/**
 * Hook for sending queries to the LLM API
 */
export const useLLMQuery = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [data, setData] = useState<QueryResponse | null>(null);

  const executeQuery = async (query: string) => {
    try {
      setLoading(true);
      setError(null);
      const response = await sendQuery(query);
      setData(response);
      return response;
    } catch (err) {
      const error = err instanceof Error ? err : new Error('An unknown error occurred');
      setError(error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  return {
    executeQuery,
    data,
    loading,
    error,
    reset: () => {
      setData(null);
      setError(null);
    },
  };
};

/**
 * Hook for checking LLM API health status
 */
export const useLLMHealth = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [data, setData] = useState<HealthResponse | null>(null);

  const checkApiHealth = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await checkHealth();
      setData(response);
      return response;
    } catch (err) {
      const error = err instanceof Error ? err : new Error('An unknown error occurred');
      setError(error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  return {
    checkApiHealth,
    data,
    loading,
    error,
    reset: () => {
      setData(null);
      setError(null);
    },
  };
};
