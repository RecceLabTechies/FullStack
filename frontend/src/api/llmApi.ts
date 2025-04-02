/**
 * This module handles interactions with the LLM (Language Learning Model) API.
 * It provides functions for querying and analyzing data through natural language processing.
 */
import axios from 'axios';

/**
 * Report result structure returned by the LLM
 */
interface ReportResult {
  description?: string;
  chart?: string | Record<string, unknown>;
  [key: string]: string | Record<string, unknown> | undefined;
}

/**
 * Complete report structure containing array of results
 */
interface Report {
  results: ReportResult[];
}

/**
 * Output structure from the backend LLM API
 */
export interface BackendOutput {
  error?: string;
  chart?: string;
  description?: string;
  report?: {
    report: Report;
  };
}

/**
 * Complete response structure from the LLM API
 */
export interface AnalysisResponse {
  output: BackendOutput;
  original_query: string;
}

/**
 * Base URL for all LLM API endpoints
 */
const LLM_API_BASE_URL = 'http://localhost:5152';

/**
 * Type Guards
 */

/**
 * Checks if the response contains chart data
 * @param response Analysis response from the LLM
 * @returns True if response contains chart data
 */
export function isChartResponse(response: AnalysisResponse): boolean {
  return response.output && 'chart' in response.output && !!response.output.chart;
}

/**
 * Checks if the response contains a description
 * @param response Analysis response from the LLM
 * @returns True if response contains a description
 */
export function isDescriptionResponse(response: AnalysisResponse): boolean {
  return response.output && 'description' in response.output && !!response.output.description;
}

/**
 * Checks if the response contains a report
 * @param response Analysis response from the LLM
 * @returns True if response contains a report
 */
export function isReportResponse(response: AnalysisResponse): boolean {
  return response.output && 'report' in response.output && !!response.output.report;
}

/**
 * Checks if the response contains an error
 * @param response Analysis response from the LLM
 * @returns True if response contains an error
 */
export function isErrorResponse(response: AnalysisResponse): boolean {
  return response.output && 'error' in response.output && !!response.output.error;
}

/**
 * LLM API Functions
 */

/**
 * Analyzes data using natural language query
 * @param query Natural language query string
 * @returns Analysis results including charts, descriptions, or reports
 * @throws Error if connection to analysis service fails
 */
export const analyzeData = async (query: string): Promise<AnalysisResponse> => {
  try {
    const response = await axios.post<AnalysisResponse>(`${LLM_API_BASE_URL}/api/query`, {
      query,
    });
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error) && error.response?.data) {
      return error.response.data as AnalysisResponse;
    }
    throw new Error('Failed to connect to analysis service');
  }
};
