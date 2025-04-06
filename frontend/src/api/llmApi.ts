/**
 * This module handles interactions with the LLM (Language Learning Model) API.
 * It provides functions for querying and analyzing data through natural language processing.
 */
import axios from 'axios';

import { type HealthResponse, type QueryRequest, type QueryResponse } from '../types/types';

/**
 * Base URL for all LLM API endpoints
 */
const LLM_API_BASE_URL = process.env.NEXT_PUBLIC_LLM_API_URL || '';

/**
 * Sends a natural language query to the LLM API for processing
 *
 * @param query - The natural language query string
 * @returns Promise with the query processing results
 */
export const sendQuery = async (query: string): Promise<QueryResponse> => {
  try {
    const request: QueryRequest = { query };
    const response = await axios.post<QueryResponse>(`${LLM_API_BASE_URL}/api/query`, request, {
      responseType: 'json',
    });
    return response.data;
  } catch (error) {
    throw error;
  }
};

/**
 * Checks the health status of the LLM API service
 *
 * @returns Promise with the health check response
 */
export const checkHealth = async (): Promise<HealthResponse> => {
  try {
    const response = await axios.get<HealthResponse>(`${LLM_API_BASE_URL}/api/health`);
    return response.data;
  } catch (error) {
    throw error;
  }
};

/**
 * Utility function to convert base64-encoded chart data to a displayable URL
 * @param base64Data Base64-encoded chart data from the API
 * @returns Data URL that can be used as image source
 */
export const base64ChartToDataUrl = (base64Data: string): string => {
  return `data:image/png;base64,${base64Data}`;
};
