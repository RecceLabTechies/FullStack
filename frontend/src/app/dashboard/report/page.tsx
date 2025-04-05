'use client';

import React, { useEffect, useState } from 'react';

import { type ProcessedQueryResult } from '@/types/types';
import { Loader2, Send } from 'lucide-react';

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
    <div className="container  mx-auto flex gap-6 p-4 ">
      <aside className="flex flex-col w-1/3 shadow-lg bg-white rounded-md p-4 h-[calc(100vh-6rem)]">
        <h2 className="text-xl font-bold">Report Builder</h2>

        <Separator className="my-2" />

        {/* TEMPLATE PROMPTS */}

        <div className="space-y-4">
          {/* Report Queries Section */}
          <div className="space-y-1">
            <h3 className="text-xs font-semibold">Report Queries</h3>
            <Button
              variant="link"
              size="free"
              className="justify-start text-wrap text-start text-muted-foreground"
              onClick={() => setQuery('Generate sales performance report for Q2 2024')}
            >
              <small>Generate sales performance report for Q2 2024</small>
            </Button>
            <Button
              variant="link"
              size="free"
              className="justify-start text-wrap text-start text-muted-foreground"
              onClick={() => setQuery('Create marketing campaign analysis report')}
            >
              <small>Create marketing campaign analysis report</small>
            </Button>
          </div>

          {/* Description Queries Section */}
          <div className="space-y-1">
            <h3 className="text-xs font-semibold">Description Queries</h3>
            <Button
              variant="link"
              size="free"
              className="justify-start text-wrap text-start text-muted-foreground"
              onClick={() => setQuery('Describe key trends in customer acquisition')}
            >
              <small>Describe key trends in customer acquisition</small>
            </Button>
            <Button
              variant="link"
              size="free"
              className="justify-start text-wrap text-start text-muted-foreground"
              onClick={() => setQuery('Explain monthly revenue fluctuations')}
            >
              <small>Explain monthly revenue fluctuations</small>
            </Button>
          </div>
          {/* Chart Queries Section */}

          <div className="space-y-1">
            <h3 className="text-xs font-semibold">Chart Queries</h3>
            <Button
              variant="link"
              size="free"
              className="justify-start text-wrap text-start text-muted-foreground"
              onClick={() => setQuery('Show monthly revenue growth as line chart')}
            >
              <small>Show monthly revenue growth as line chart</small>
            </Button>
            <Button
              variant="link"
              size="free"
              className="justify-start text-wrap text-start text-muted-foreground"
              onClick={() => setQuery('Visualize regional sales distribution as pie chart')}
            >
              <small>Visualize regional sales distribution as pie chart</small>
            </Button>
          </div>
        </div>

        {/* CHAT AREA */}

        <Separator className="my-2" />

        <article className="flex flex-col gap-2  h-full  overflow-scroll">
          {resultHistory.map((item, index) => (
            <div className="flex flex-col w-full gap-2" key={`chat-${index}`}>
              <div className="text-left mr-[25%] bg-accent text-accent-foreground rounded-md p-2 ">
                {item.query}
              </div>
              <div className="text-right ml-[25%] bg-primary text-primary-foreground rounded-md p-2">
                {item.result.type}
              </div>
            </div>
          ))}
        </article>

        {/* INPUT AREA */}
        <form onSubmit={handleSubmit} className="flex items-center gap-2 mt-4">
          <Input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter your query here..."
            disabled={loading}
            className="w-full"
          />
          <Button type="submit" size="icon" disabled={loading || !query.trim()}>
            {loading ? <Loader2 className="animate-spin" size={16} /> : <Send size={16} />}
          </Button>
        </form>

        {error && <div className="text-red-500 mt-2">Error: {error.message}</div>}
      </aside>
      <main className="w-2/3 ">
        <nav className="flex justify-between h-9">
          <h2 className="text-xl font-bold mb-4">Report Generator</h2>
          <Button>Export to PDF</Button>
        </nav>

        <Separator className="my-4" />

        <article
          id="report-container"
          className="space-y-1 h-[calc(100vh-10.3rem)] overflow-scroll"
        >
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
