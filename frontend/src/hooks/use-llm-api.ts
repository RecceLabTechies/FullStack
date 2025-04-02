/**
 * This module provides React hooks for interacting with the Language Learning Model (LLM) API.
 * It handles state management, data fetching, and response type checking for LLM analysis.
 */
import { useState } from 'react';

import {
  type AnalysisResponse,
  analyzeData,
  isChartResponse,
  isDescriptionResponse,
  isErrorResponse,
  isReportResponse,
} from '@/api/llmApi';

/**
 * State interface for LLM analysis hook
 */
interface LlmAnalysisState {
  /** The analysis response data */
  data: AnalysisResponse | null;
  /** Loading state indicator */
  loading: boolean;
  /** Error object if analysis failed */
  error: Error | null;
  /** Whether the response contains chart data */
  isChart: boolean;
  /** Whether the response contains a description */
  isDescription: boolean;
  /** Whether the response contains a report */
  isReport: boolean;
  /** Whether the response contains an error */
  isError: boolean;
}

/**
 * Initial state for the LLM analysis hook
 */
const initialState: LlmAnalysisState = {
  data: null,
  loading: false,
  error: null,
  isChart: false,
  isDescription: false,
  isReport: false,
  isError: false,
};

/**
 * Hook for performing LLM analysis on queries
 *
 * Provides functionality to:
 * - Send natural language queries for analysis
 * - Track loading and error states
 * - Determine response type (chart, description, report, or error)
 *
 * @example
 * ```tsx
 * function AnalysisComponent() {
 *   const { analyze, loading, data, isChart, error } = useLlmAnalysis();
 *
 *   const handleAnalysis = async () => {
 *     await analyze("Show me revenue trends for last month");
 *   };
 *
 *   if (loading) return <Loading />;
 *   if (error) return <Error message={error.message} />;
 *   if (isChart && data) return <Chart data={data.output.chart} />;
 *
 *   return <div>No analysis yet</div>;
 * }
 * ```
 *
 * @returns Object containing analysis state and analyze function
 */
export const useLlmAnalysis = () => {
  const [state, setState] = useState<LlmAnalysisState>(initialState);

  /**
   * Performs LLM analysis on the provided query
   *
   * @param query - Natural language query to analyze
   * @returns Analysis response or null if error occurred
   */
  const analyze = async (query: string): Promise<AnalysisResponse | null> => {
    // Reset state before new analysis
    setState({
      ...initialState,
      loading: true,
    });

    try {
      const data = await analyzeData(query);

      // Update state with response and type indicators
      setState({
        data,
        loading: false,
        error: null,
        isChart: isChartResponse(data),
        isDescription: isDescriptionResponse(data),
        isReport: isReportResponse(data),
        isError: isErrorResponse(data),
      });

      return data;
    } catch (error) {
      // Handle errors and update state
      setState({
        ...initialState,
        error: error instanceof Error ? error : new Error('Unknown error occurred'),
        isError: true,
      });
      return null;
    }
  };

  return {
    ...state,
    analyze,
  };
};
