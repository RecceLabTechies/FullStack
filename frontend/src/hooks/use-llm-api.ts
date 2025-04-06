/**
 * This module provides React hooks for interacting with the Language Learning Model (LLM) API.
 * It handles state management, data fetching, and response type checking for LLM analysis.
 */
import React, { type ReactNode, useState } from 'react';

import { base64ChartToDataUrl, checkHealth, sendQuery } from '@/api/llmApi';
import { type HealthResponse, type ProcessedQueryResult, type QueryResponse } from '@/types/types';

/**
 * Hook for sending queries to the LLM API
 */
export const useLLMQuery = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [data, setData] = useState<QueryResponse | null>(null);
  const [processedResult, setProcessedResult] = useState<ProcessedQueryResult | null>(null);

  /**
   * Process the response based on the result type
   */
  const processResponse = (response: QueryResponse): ProcessedQueryResult => {
    const { output, original_query } = response;
    const { type, result } = output;

    // Default processed result
    const processed: ProcessedQueryResult = {
      type,
      content: null,
      originalQuery: original_query,
    };

    // Process based on type
    if (type === 'chart') {
      // Chart result is now a base64 string
      if (typeof result === 'string') {
        processed.content = base64ChartToDataUrl(result);
      }
    } else if (type === 'description') {
      // Description result is a string
      if (typeof result === 'string') {
        processed.content = result;
      }
    } else if (type === 'report' && typeof result === 'object' && result !== null) {
      // Report result is an object with an array of results
      const reportObj = result as { results: string[] };
      if ('results' in reportObj) {
        // Process each report item
        processed.content = reportObj.results.map((item, index) => {
          if (!item.startsWith('data:image')) {
            // Text content
            return item;
          } else {
            // Already a data URL or base64 encoded chart
            const imgElement: ReactNode = React.createElement('img', {
              key: index.toString(),
              src: item,
              alt: `Chart ${index + 1}`,
            });
            return imgElement;
          }
        });
      }
    } else if (type === 'error') {
      // Error result is a string
      if (typeof result === 'string') {
        processed.content = result;
      }
    }

    return processed;
  };

  const executeQuery = async (query: string) => {
    try {
      setLoading(true);
      setError(null);
      const response = await sendQuery(query);
      setData(response);

      // Process the response
      const processed = processResponse(response);
      setProcessedResult(processed);

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
    processedResult,
    loading,
    error,
    reset: () => {
      setData(null);
      setProcessedResult(null);
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
