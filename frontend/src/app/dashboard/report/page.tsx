'use client';

import React, { useEffect, useState } from 'react';

import { type ProcessedQueryResult } from '@/types/types';

import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Separator } from '@/components/ui/separator';

import { useLLMQuery } from '@/hooks/use-llm-api';

/* eslint-disable @next/next/no-img-element */

export default function ReportPage() {
  const [query, setQuery] = useState('');
  const [resultHistory, setResultHistory] = useState<
    Array<{
      query: string;
      result: ProcessedQueryResult;
    }>
  >([]);

  const { executeQuery, processedResult, loading, error } = useLLMQuery();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    try {
      await executeQuery(query);
      // We'll add the result to history in the useEffect below
      setQuery('');
    } catch (err) {
      console.error('Failed to execute query:', err);
    }
  };

  // Update result history when a new result come s in
  useEffect(() => {
    if (processedResult?.content) {
      setResultHistory((prev) => [
        ...prev,
        {
          query: processedResult.originalQuery || 'Unknown query',
          result: processedResult,
        },
      ]);
    }
  }, [processedResult]);

  const renderSingleResult = (
    result: ProcessedQueryResult,
    queryText: string,
    index: number
  ): React.ReactNode => {
    if (!result?.content) return null;

    return (
      <Card key={index}>
        <CardContent className="pt-6">{renderResultContent(result)}</CardContent>
      </Card>
    );
  };

  const renderResultContent = (result: ProcessedQueryResult) => {
    if (result.type === 'report') {
      const results = result.content as Array<string | React.ReactNode>;

      if (!results.length) {
        return <p>No results available</p>;
      }

      return (
        <div>
          {results.map((content, index) => {
            if (React.isValidElement(content)) {
              return (
                <Card key={index}>
                  <CardContent className="pt-6">{content}</CardContent>
                </Card>
              );
            }
            if (typeof content === 'string') {
              if (content.startsWith('data:image')) {
                return (
                  <Card key={index}>
                    <CardContent className="pt-6">
                      <img src={content} alt={`Chart ${index + 1}`} />
                    </CardContent>
                  </Card>
                );
              }
              return (
                <Card key={index}>
                  <p>{content}</p>
                </Card>
              );
            }
            return null;
          })}
        </div>
      );
    } else if (result.type === 'chart') {
      return <img src={result.content as string} alt="Chart result" />;
    } else if (result.type === 'description') {
      return <p>{result.content as string}</p>;
    }

    // For unknown types or error results, just display as string
    return (
      <p>
        {result.content
          ? typeof result.content === 'object'
            ? JSON.stringify(result.content)
            : String(result.content)
          : ''}
      </p>
    );
  };

  return (
    <div className="container mx-auto flex gap-6 p-4 ">
      <aside className="flex flex-col w-1/3 ">
        <h2 className="text-xl font-bold mb-4">Report Builder</h2>
        <form onSubmit={handleSubmit} className="space-y-2">
          <Input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter your query here..."
            disabled={loading}
            className="w-full"
          />
          <Button type="submit" disabled={loading || !query.trim()} className="w-full">
            {loading ? 'Processing...' : 'Submit Query'}
          </Button>
        </form>

        {error && <div className="text-red-500 mt-2">Error: {error.message}</div>}
      </aside>
      <main className="w-2/3">
        <nav className="flex justify-between ">
          <h2 className="text-xl font-bold mb-4">Report Generator</h2>
          <Button>Export to PDF</Button>
        </nav>

        <Separator className="my-4" />

        <article id="report-container" className="space-y-1">
          <h4 className="text-lg font-bold">Report Title</h4>
          <p>
            <small>Report Author</small>
          </p>

          {resultHistory.length > 0 ? (
            <>
              {resultHistory.map((item, index) =>
                renderSingleResult(item.result, item.query, index)
              )}
            </>
          ) : (
            <Card>
              <CardContent className="pt-6 flex justify-center items-center">
                <p>Submit a query to see results</p>
              </CardContent>
            </Card>
          )}
          {loading && (
            <Card>
              <CardContent className="pt-6 flex justify-center items-center">
                <div className="loader"></div>
              </CardContent>
            </Card>
          )}
        </article>
      </main>
    </div>
  );
}
