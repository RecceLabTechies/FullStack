'use client';

import { useState } from 'react';

import { type ReportResults, type TruncatedResultType } from '@/types/types';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

import { useLLMQuery } from '@/hooks/use-llm-api';

// Get Minio endpoint from environment variable or use default
const MINIO_ENDPOINT = 'localhost:9000';
const MINIO_BUCKET = 'temp-charts';

export default function ReportPage() {
  const [query, setQuery] = useState('');
  const { executeQuery, data, loading, error } = useLLMQuery();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    try {
      await executeQuery(query);
    } catch (err) {
      console.error('Failed to execute query:', err);
    }
  };

  // Function to convert relative image paths to full URLs
  const getImageUrl = (imagePath: string): string => {
    // If it's already a full URL, return as is
    if (imagePath.startsWith('http://') || imagePath.startsWith('https://')) {
      return imagePath;
    }

    // If it's a path from Minio API
    if (imagePath.startsWith('/api/minio/')) {
      // Extract the filename from the path
      const parts = imagePath.split('/');
      const filename = parts[parts.length - 1];

      // Construct direct Minio URL
      return `http://${MINIO_ENDPOINT}/${MINIO_BUCKET}/${filename}`;
    }

    // If it's just a filename
    if (!imagePath.startsWith('/')) {
      return `http://${MINIO_ENDPOINT}/${MINIO_BUCKET}/${imagePath}`;
    }

    // If it's another path format, return as is
    return imagePath;
  };

  const renderResultItem = (type: TruncatedResultType, content: string, index: number) => {
    switch (type) {
      case 'chart':
        return (
          <div key={index}>
            <h3>Chart {index + 1}</h3>
            <img src={getImageUrl(content)} alt={`Chart ${index + 1}`} />
          </div>
        );
      case 'description':
        return (
          <div key={index}>
            <h3>Description {index + 1}</h3>
            <p>{content}</p>
          </div>
        );
      default:
        return <p key={index}>{content}</p>;
    }
  };

  const renderResult = () => {
    if (!data?.output.result) return null;

    if (data.output.type === 'report') {
      const reportResults = data.output.result as ReportResults;

      if (!reportResults.results.length) {
        return <p>No results available</p>;
      }

      return (
        <div>
          {reportResults.results.map(([type, content], index) =>
            renderResultItem(type, content, index)
          )}
        </div>
      );
    } else if (data.output.type === 'chart') {
      // Single chart result
      return <img src={getImageUrl(data.output.result as string)} alt="Chart result" />;
    } else if (data.output.type === 'description') {
      // Single description result
      return <p>{data.output.result as string}</p>;
    }

    // For unknown types or error results, just display as JSON
    return <p>{JSON.stringify(data.output.result, null, 2)}</p>;
  };

  return (
    <>
      <form onSubmit={handleSubmit}>
        <Input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Enter your query here..."
          disabled={loading}
        />
        <Button type="submit" disabled={loading || !query.trim()}>
          {loading ? 'Processing...' : 'Submit Query'}
        </Button>
      </form>

      {error && <div>Error: {error.message}</div>}

      {loading && <div>Processing your query...</div>}

      {data && (
        <>
          <h2>Results</h2>
          <div>{renderResult()}</div>
        </>
      )}
    </>
  );
}
