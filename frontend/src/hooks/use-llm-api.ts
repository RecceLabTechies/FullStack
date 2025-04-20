/**
 * This module provides React hooks for interacting with the Language Learning Model (LLM) API.
 * It handles state management, data fetching, and response type checking for LLM analysis.
 */
import React, { type ReactNode, useCallback, useEffect, useRef, useState } from 'react';

import { base64ChartToDataUrl, checkHealth, checkQueryStatus, sendQuery } from '@/api/llmApi';
import {
  type AsyncQueryResponse,
  type HealthResponse,
  type ProcessedQueryResult,
  type QueryStatusResponse,
} from '@/types/types';

// Default polling interval in milliseconds
const DEFAULT_POLLING_INTERVAL = 2000;
// Maximum polling duration in milliseconds (5 minutes)
const MAX_POLLING_DURATION = 5 * 60 * 1000;

/**
 * Hook for sending queries to the LLM API
 */
export const useLLMQuery = (pollingInterval = DEFAULT_POLLING_INTERVAL) => {
  const [loading, setLoading] = useState(false);
  const [polling, setPolling] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [statusData, setStatusData] = useState<QueryStatusResponse | null>(null);
  const [processedResult, setProcessedResult] = useState<ProcessedQueryResult | null>(null);

  // Ref for keeping track of polling timeout/interval
  const pollingRef = useRef<{
    startTime: number;
    intervalId: NodeJS.Timeout | null;
  }>({ startTime: 0, intervalId: null });

  /**
   * Process the response based on the result type
   */
  const processResponse = (response: QueryStatusResponse): ProcessedQueryResult => {
    if (!response.output) {
      return {
        type: 'unknown',
        content: null,
        originalQuery: response.original_query,
      };
    }

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
          if (typeof item === 'string') {
            // Check if it's already a data URL
            if (item.startsWith('data:image/png;base64,')) {
              console.log(`Report item ${index} is a data URL image`);
              // Create image element for chart
              const imgElement: ReactNode = React.createElement('img', {
                key: index.toString(),
                src: item,
                alt: `Chart ${index + 1}`,
                className: 'mx-auto',
                style: { maxWidth: '100%' },
              });
              return imgElement;
            }
            // Text content
            console.log(
              `Report item ${index} is text: ${item.substring(0, 50)}${item.length > 50 ? '...' : ''}`
            );
            return item;
          } else {
            console.warn(`Report item ${index} is not a string:`, typeof item);
            try {
              // Handle various non-string formats
              if (item === null) {
                return 'null';
              } else if (typeof item === 'object') {
                // Try to stringify the object
                return JSON.stringify(item);
              } else {
                // Binary data for chart - convert from base64
                console.log(`Report item ${index} appears to be binary data, converting to image`);
                const imgElement: ReactNode = React.createElement('img', {
                  key: index.toString(),
                  src: base64ChartToDataUrl(String(item)),
                  alt: `Chart ${index + 1}`,
                  className: 'mx-auto',
                  style: { maxWidth: '100%' },
                });
                return imgElement;
              }
            } catch (err) {
              console.error(`Error processing report item ${index}:`, err);
              return `[Error: Could not process item ${index}]`;
            }
          }
        });
      } else {
        console.warn('Report object does not have results array:', reportObj);
      }
    } else if (type === 'error') {
      // Error result is a string
      if (typeof result === 'string') {
        processed.content = result;
      }
    }

    return processed;
  };

  /**
   * Clear polling interval and reset polling state
   */
  const clearPolling = useCallback(() => {
    if (pollingRef.current.intervalId) {
      clearInterval(pollingRef.current.intervalId);
      pollingRef.current.intervalId = null;
    }
    setPolling(false);
  }, []);

  /**
   * Start polling for query status
   */
  const startPolling = useCallback(
    (id: string) => {
      if (!id) return;

      // Set up polling state
      setPolling(true);
      pollingRef.current.startTime = Date.now();

      // Clear any existing polling
      clearPolling();

      // Start new polling interval
      pollingRef.current.intervalId = setInterval(() => {
        // Use a void IIFE to handle the async operation
        void (async () => {
          try {
            // Check if we've exceeded maximum polling duration
            if (Date.now() - pollingRef.current.startTime > MAX_POLLING_DURATION) {
              clearPolling();
              setError(new Error('Query processing timed out after 5 minutes'));
              setLoading(false);
              return;
            }

            // Check query status
            const status = await checkQueryStatus(id);
            setStatusData(status);

            // If the query is completed or has an error, stop polling
            if (status.status === 'completed' || status.status === 'error') {
              clearPolling();

              // Process the completed result
              if (status.output) {
                const processed = processResponse(status);
                setProcessedResult(processed);
              }

              setLoading(false);
            }
          } catch (err) {
            clearPolling();
            const error = err instanceof Error ? err : new Error('An unknown error occurred');
            setError(error);
            setLoading(false);
          }
        })();
      }, pollingInterval);
    },
    [clearPolling, pollingInterval]
  );

  /**
   * Clean up interval on unmount
   */
  useEffect(() => {
    return () => {
      if (pollingRef.current.intervalId) {
        clearInterval(pollingRef.current.intervalId);
      }
    };
  }, []);

  /**
   * Submit a new query and start polling for results
   */
  const executeQuery = async (query: string): Promise<AsyncQueryResponse> => {
    try {
      // Reset states
      setLoading(true);
      setError(null);
      setProcessedResult(null);
      setStatusData(null);

      // Clear any existing polling
      clearPolling();

      // Submit the query
      const response = await sendQuery(query);
      setJobId(response.job_id);

      // Start polling for status
      startPolling(response.job_id);

      return response;
    } catch (err) {
      clearPolling();
      const error = err instanceof Error ? err : new Error('An unknown error occurred');
      setError(error);
      setLoading(false);
      throw error;
    }
  };

  /**
   * Reset the state
   */
  const reset = useCallback(() => {
    clearPolling();
    setJobId(null);
    setStatusData(null);
    setProcessedResult(null);
    setError(null);
    setLoading(false);
  }, [clearPolling]);

  return {
    executeQuery,
    jobId,
    statusData,
    processedResult,
    loading,
    polling,
    error,
    reset,
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
