'use client';

/* eslint-disable @next/next/no-img-element */
import React, { useState } from 'react';

import { useLLMQuery } from '@/hooks/use-llm-api';

export default function ReportPage() {
  const [query, setQuery] = useState('');

  const { executeQuery, processedResult, loading, error } = useLLMQuery();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    try {
      await executeQuery(query);
      setQuery('');
    } catch (err) {
      console.error('Failed to execute query:', err);
    }
  };

  const renderResult = () => {
    if (!processedResult?.content) return null;

    if (processedResult.type === 'report') {
      const results = processedResult.content as Array<string | React.ReactNode>;

      if (!results.length) {
        return <p>No results available</p>;
      }

      return (
        <div>
          {results.map((content, index) => {
            if (React.isValidElement(content)) {
              return (
                <div key={index}>
                  <h3>Chart {index + 1}</h3>
                  <div>{content}</div>
                </div>
              );
            }
            if (typeof content === 'string') {
              if (content.startsWith('data:image')) {
                return (
                  <div key={index}>
                    <h3>Chart {index + 1}</h3>
                    <img src={content} alt={`Chart ${index + 1}`} />
                  </div>
                );
              }
              return (
                <div key={index}>
                  <h3>Analysis {index + 1}</h3>
                  <p>{content}</p>
                </div>
              );
            }
            return null;
          })}
        </div>
      );
    } else if (processedResult.type === 'chart') {
      return <img src={processedResult.content as string} alt="Chart result" />;
    } else if (processedResult.type === 'description') {
      return <p>{processedResult.content as string}</p>;
    }

    // For unknown types or error results, just display as string
    return (
      <p>
        {processedResult.content
          ? typeof processedResult.content === 'object'
            ? JSON.stringify(processedResult.content)
            : String(processedResult.content)
          : ''}
      </p>
    );
  };

  return (
    <div>
      <section>
        {/* Query input card */}
        <h2>Query</h2>
        <form onSubmit={handleSubmit}>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter your query here..."
            disabled={loading}
          />
          <button type="submit" disabled={loading || !query.trim()}>
            {loading ? 'Processing...' : 'Submit Query'}
          </button>
        </form>

        {error && <div>Error: {error.message}</div>}
      </section>
      <section>
        <h2>Results</h2>
        {loading ? (
          <div>Loading...</div>
        ) : processedResult ? (
          renderResult()
        ) : (
          <p>Submit a query to see results</p>
        )}
      </section>
    </div>
  );
}
