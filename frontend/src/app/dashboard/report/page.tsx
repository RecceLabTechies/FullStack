'use client';

import React, { useEffect, useState } from 'react';

import { type ProcessedQueryResult, type QueryResultType } from '@/types/types';
import { DragDropContext, Draggable, Droppable, type DropResult } from '@hello-pangea/dnd';
import { Bot, Clock, Loader2, Pencil, Save, Send, Trash2, User } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Separator } from '@/components/ui/separator';

import { useLLMQuery } from '@/hooks/use-llm-api';

/* eslint-disable @next/next/no-img-element */

export default function ReportPage() {
  const [query, setQuery] = useState('');
  const [reportTitle, setReportTitle] = useState('Report Title');
  const [reportAuthor, setReportAuthor] = useState('Report Author');
  const [editingTitle, setEditingTitle] = useState(false);
  const [editingAuthor, setEditingAuthor] = useState(false);
  const [resultHistory, setResultHistory] = useState<
    Array<{
      query: string;
      result: ProcessedQueryResult;
      timestamp: string;
      id: string;
    }>
  >([]);
  const [reportItems, setReportItems] = useState<
    Array<{
      id: string;
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

  // Update result history when a new result comes in
  useEffect(() => {
    if (processedResult?.content) {
      const newItemId =
        new Date().getTime().toString() + '-' + Math.random().toString(36).substring(2, 9);

      setResultHistory((prev) => [
        ...prev,
        {
          query: processedResult.originalQuery || 'Unknown query',
          result: processedResult,
          timestamp: new Date().toLocaleTimeString(),
          id: newItemId,
        },
      ]);

      // Add new item(s) to the report items list for drag and drop
      if (processedResult.type === 'report') {
        // Flatten report content items into individual draggable items
        const reportContentItems = processedResult.content as Array<string | React.ReactNode>;

        if (reportContentItems && reportContentItems.length > 0) {
          const newItems = reportContentItems.map((content) => {
            const contentId =
              new Date().getTime().toString() + '-' + Math.random().toString(36).substring(2, 9);
            let type: QueryResultType = 'description';

            // Determine the type of content
            if (typeof content === 'string' && content.startsWith('data:image')) {
              type = 'chart';
            }

            return {
              id: contentId,
              result: {
                type: type,
                content: content,
                originalQuery: processedResult.originalQuery,
              } as ProcessedQueryResult,
            };
          });

          setReportItems((prev) => [...prev, ...newItems]);
        }
      } else {
        // For non-report types, add as a single item
        setReportItems((prev) => [
          ...prev,
          {
            id: newItemId,
            result: processedResult,
          },
        ]);
      }
    }
  }, [processedResult]);

  // Function to clear chat history
  const clearHistory = () => {
    setResultHistory([]);
    setReportItems([]);
  };

  const handleDragEnd = (result: DropResult) => {
    if (!result.destination) return;

    const items = Array.from(reportItems);
    const [reorderedItem] = items.splice(result.source.index, 1);
    if (!reorderedItem) return; // Guard against undefined

    items.splice(result.destination.index, 0, reorderedItem);

    setReportItems(items);
  };

  const renderSingleResult = (
    result: ProcessedQueryResult,
    id: string,
    index: number
  ): React.ReactNode => {
    if (!result?.content) return null;

    return (
      <Draggable key={id} draggableId={id} index={index}>
        {(provided) => (
          <div
            ref={provided.innerRef}
            {...provided.draggableProps}
            {...provided.dragHandleProps}
            className="mb-4"
          >
            <Card>
              <CardContent className="pt-6">
                {result.type === 'chart' && typeof result.content === 'string' && (
                  <img src={result.content} alt="Chart result" className="mx-auto" />
                )}

                {result.type === 'description' && (
                  <p>
                    {typeof result.content === 'string'
                      ? result.content
                      : React.isValidElement(result.content)
                        ? 'React element' // Fallback display
                        : JSON.stringify(result.content)}
                  </p>
                )}

                {result.type !== 'chart' &&
                  result.type !== 'description' &&
                  renderResultContent(result)}
              </CardContent>
            </Card>
          </div>
        )}
      </Draggable>
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
            const contentId = `${new Date().getTime()}-${index}-${Math.random().toString(36).substring(2, 9)}`;

            if (React.isValidElement(content)) {
              return (
                <Card key={contentId}>
                  <CardContent className="pt-6">{content}</CardContent>
                </Card>
              );
            }
            if (typeof content === 'string') {
              if (content.startsWith('data:image')) {
                return (
                  <Card key={contentId}>
                    <CardContent className="pt-6">
                      <img src={content} alt={`Chart ${index + 1}`} />
                    </CardContent>
                  </Card>
                );
              }
              return (
                <Card key={contentId}>
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

  // Function to get a summary of the result content
  const getResultSummary = (result: ProcessedQueryResult): string => {
    if (!result?.content) return 'No content';

    if (result.type === 'chart') {
      return 'Chart visualization';
    } else if (result.type === 'report') {
      return 'Detailed report';
    } else if (result.type === 'description') {
      const content = result.content as string;
      return content.length > 80 ? content.substring(0, 80) + '...' : content;
    }

    return result.type || 'Result';
  };

  return (
    <div className="container mx-auto flex gap-6 p-4">
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
        <div className="flex items-center justify-between my-2">
          <h3 className="text-sm font-semibold">Conversation History</h3>
          {resultHistory.length > 0 && (
            <Button
              variant="ghost"
              size="sm"
              className="h-8 px-2 text-muted-foreground"
              onClick={clearHistory}
              aria-label="Clear history"
            >
              <Trash2 size={16} className="mr-1" />
              <span className="text-xs">Clear</span>
            </Button>
          )}
        </div>

        <article className="flex flex-col gap-3 h-full overflow-y-auto px-1 py-2">
          {resultHistory.length === 0 ? (
            <div className="flex items-center justify-center h-full text-muted-foreground">
              <p className="text-sm">No conversation history yet</p>
            </div>
          ) : (
            resultHistory.map((item) => (
              <div className="flex flex-col w-full gap-3" key={item.id}>
                {/* User query message */}
                <div className="flex gap-2 items-start ml-auto">
                  <div className="flex-1">
                    <div className="bg-primary/10 w-fit rounded-lg p-3 rounded-tr-none ml-auto">
                      <p className="text-sm">{item.query}</p>
                    </div>
                    <div className="flex items-center mt-1 mr-1 justify-end">
                      <Clock size={12} className="text-muted-foreground mr-1" />
                      <p className="text-xs text-muted-foreground">{item.timestamp}</p>
                    </div>
                  </div>
                  <div className="bg-primary text-primary-foreground rounded-full p-1.5 mt-0.5">
                    <User size={14} />
                  </div>
                </div>

                {/* AI response message */}
                <div className="flex gap-2 items-start">
                  <div className="bg-secondary text-secondary-foreground rounded-full p-1.5 mt-0.5">
                    <Bot size={14} />
                  </div>
                  <div className="flex-1">
                    <div className="bg-secondary w-fit  text-secondary-foreground rounded-lg p-3 rounded-tl-none">
                      <div className="flex  items-center mb-1">
                        <Badge>{item.result.type}</Badge>
                      </div>
                      <p className="text-sm">{getResultSummary(item.result)}</p>
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}

          {loading && (
            <div className="flex gap-2 items-start">
              <div className="bg-secondary text-secondary-foreground rounded-full p-1.5 mt-0.5">
                <Bot size={14} />
              </div>
              <div className="flex-1">
                <div className="bg-secondary text-secondary-foreground rounded-lg p-3 rounded-tl-none">
                  <div className="flex items-center justify-center">
                    <Loader2 className="w-5 h-5 animate-spin text-muted-foreground" />
                  </div>
                </div>
              </div>
            </div>
          )}
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
            aria-label="Query input"
          />
          <Button
            type="submit"
            size="icon"
            disabled={loading || !query.trim()}
            aria-label="Send query"
          >
            {loading ? <Loader2 className="animate-spin" size={16} /> : <Send size={16} />}
          </Button>
        </form>

        {error && <div className="text-red-500 mt-2">Error: {error.message}</div>}
      </aside>
      <main className="w-2/3">
        <nav className="flex justify-between h-9">
          <h2 className="text-xl font-bold mb-4">Report Generator</h2>
          <Button>Export to PDF</Button>
        </nav>

        <Separator className="my-4" />

        <article
          id="report-container"
          className="space-y-4 h-[calc(100vh-10.3rem)] overflow-scroll"
        >
          <div className="flex items-center gap-2">
            {editingTitle ? (
              <div className="flex items-center gap-2">
                <Input
                  type="text"
                  value={reportTitle}
                  onChange={(e) => setReportTitle(e.target.value)}
                  className="text-lg font-bold"
                  autoFocus
                />
                <Button size="icon" variant="ghost" onClick={() => setEditingTitle(false)}>
                  <Save size={16} />
                </Button>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <h4 className="text-lg font-bold">{reportTitle}</h4>
                <Button size="icon" variant="ghost" onClick={() => setEditingTitle(true)}>
                  <Pencil size={16} />
                </Button>
              </div>
            )}
          </div>

          <div className="flex items-center gap-2 mb-2">
            {editingAuthor ? (
              <div className="flex items-center gap-2">
                <Input
                  type="text"
                  value={reportAuthor}
                  onChange={(e) => setReportAuthor(e.target.value)}
                  className="text-sm"
                  autoFocus
                />
                <Button size="icon" variant="ghost" onClick={() => setEditingAuthor(false)}>
                  <Save size={16} />
                </Button>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <p>
                  <small>{reportAuthor}</small>
                </p>
                <Button size="icon" variant="ghost" onClick={() => setEditingAuthor(true)}>
                  <Pencil size={16} />
                </Button>
              </div>
            )}
          </div>

          <DragDropContext onDragEnd={handleDragEnd}>
            <Droppable droppableId="report-items">
              {(provided) => (
                <div {...provided.droppableProps} ref={provided.innerRef} className="space-y-4">
                  {reportItems.length > 0 ? (
                    reportItems.map((item, index) =>
                      renderSingleResult(item.result, item.id, index)
                    )
                  ) : (
                    <Card>
                      <CardContent className="pt-6 flex justify-center items-center">
                        <p>Submit a query to see results</p>
                      </CardContent>
                    </Card>
                  )}
                  {provided.placeholder}
                </div>
              )}
            </Droppable>
          </DragDropContext>

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
