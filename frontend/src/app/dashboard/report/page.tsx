'use client';

import React, { useEffect, useState } from 'react';

import { Avatar } from '@/components/ui/avatar';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Skeleton } from '@/components/ui/skeleton';

import { useLLMQuery } from '@/hooks/use-llm-api';

// Type for chat history items
type ChatHistoryItem = {
  id: string;
  query: string;
  timestamp: Date;
};

export default function ReportPage() {
  const [query, setQuery] = useState('');
  const [chatHistory, setChatHistory] = useState<ChatHistoryItem[]>([]);
  const { executeQuery, processedResult, loading, error } = useLLMQuery();

  // Load chat history from localStorage on mount
  useEffect(() => {
    const savedHistory = localStorage.getItem('queryHistory');
    if (savedHistory) {
      try {
        const parsedHistory = JSON.parse(savedHistory);
        setChatHistory(parsedHistory.map((item: any) => ({
          ...item,
          timestamp: new Date(item.timestamp)
        })));
      } catch (err) {
        console.error('Failed to parse saved chat history:', err);
      }
    }
  }, []);

  // Save chat history to localStorage when it changes
  useEffect(() => {
    if (chatHistory.length > 0) {
      localStorage.setItem('queryHistory', JSON.stringify(chatHistory));
    }
  }, [chatHistory]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    // Add query to chat history
    const newChatItem = {
      id: Date.now().toString(),
      query: query.trim(),
      timestamp: new Date()
    };
    
    setChatHistory(prev => [newChatItem, ...prev]);

    try {
      await executeQuery(query);
      setQuery(''); // Clear input after submission
    } catch (err) {
      console.error('Failed to execute query:', err);
    }
  };

  const handleHistoryItemClick = (item: ChatHistoryItem) => {
    setQuery(item.query);
  };

  const renderResult = () => {
    if (!processedResult || !processedResult.content) return null;

    if (processedResult.type === 'report') {
      // Report results as an array of content
      const results = processedResult.content as Array<string | React.ReactNode>;

      if (!results.length) {
        return <p className="text-muted-foreground">No results available</p>;
      }

      return (
        <div className="space-y-6">
          {results.map((content, index) => {
            // If it's a React node (image), render directly
            if (React.isValidElement(content)) {
              return (
                <Card key={index}>
                  <CardHeader>
                    <CardTitle>Chart {index + 1}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    {content}
                  </CardContent>
                </Card>
              );
            }
            
            // If it's a string (base64 image or text)
            if (typeof content === 'string') {
              // Check if it's a data URL or base64 image
              if (content.startsWith('data:image')) {
                return (
                  <Card key={index}>
                    <CardHeader>
                      <CardTitle>Chart {index + 1}</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <img src={content} alt={`Chart ${index + 1}`} className="w-full" />
                    </CardContent>
                  </Card>
                );
              }
              
              // Otherwise it's a text description
              return (
                <Card key={index}>
                  <CardHeader>
                    <CardTitle>Analysis {index + 1}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p>{content}</p>
                  </CardContent>
                </Card>
              );
            }
            
            return null;
          })}
        </div>
      );
    } else if (processedResult.type === 'chart') {
      // Single chart result - already formatted as URL
      return (
        <Card>
          <CardContent className="pt-6">
            <img src={processedResult.content as string} alt="Chart result" className="w-full" />
          </CardContent>
        </Card>
      );
    } else if (processedResult.type === 'description') {
      // Single description result
      return (
        <Card>
          <CardContent className="pt-6">
            <p>{processedResult.content as string}</p>
          </CardContent>
        </Card>
      );
    }

    // For unknown types or error results, just display as string
    return (
      <Card>
        <CardContent className="pt-6">
          <p>{String(processedResult.content)}</p>
        </CardContent>
      </Card>
    );
  };

  return (
    <div className="flex flex-col container gap-4 mx-auto pb-4">
      <div className="grid grid-cols-1 md:grid-cols-12 gap-4">
        <div className="md:col-span-4">
          {/* Query input card */}
          <Card>
            <CardHeader>
              <CardTitle>Query</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-4">
                <Input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Enter your query here..."
                  disabled={loading}
                  className="w-full"
                />
                <Button 
                  type="submit" 
                  disabled={loading || !query.trim()}
                  className="w-full"
                >
                  {loading ? 'Processing...' : 'Submit Query'}
                </Button>
              </form>

              {error && (
                <div className="mt-4 p-3 bg-destructive/10 text-destructive rounded">
                  Error: {error.message}
                </div>
              )}
            </CardContent>
          </Card>
          
          {/* Chat history card */}
          <Card className="mt-4">
            <CardHeader>
              <CardTitle>Query History</CardTitle>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[400px] pr-4">
                {chatHistory.length > 0 ? (
                  <div className="space-y-4">
                    {chatHistory.map((item) => (
                      <div 
                        key={item.id} 
                        className="flex items-start space-x-3 p-3 rounded-lg bg-muted/50 hover:bg-muted cursor-pointer transition-colors"
                        onClick={() => handleHistoryItemClick(item)}
                      >
                        <Avatar className="h-8 w-8">
                          <div className="bg-primary text-xs text-primary-foreground flex items-center justify-center h-full rounded-full">
                            {item.timestamp.getHours().toString().padStart(2, '0')}:{item.timestamp.getMinutes().toString().padStart(2, '0')}
                          </div>
                        </Avatar>
                        <div className="space-y-1">
                          <p className="text-sm font-medium leading-none">{item.query}</p>
                          <p className="text-xs text-muted-foreground">
                            {item.timestamp.toLocaleDateString()} {item.timestamp.toLocaleTimeString()}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-muted-foreground text-center py-4">No query history yet</p>
                )}
              </ScrollArea>
            </CardContent>
          </Card>
        </div>

        <div className="md:col-span-8">
          <Card>
            <CardHeader>
              <CardTitle>Results</CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="space-y-4">
                  <Skeleton className="h-4 w-full" />
                  <Skeleton className="h-32 w-full" />
                  <Skeleton className="h-4 w-3/4" />
                </div>
              ) : processedResult ? (
                renderResult()
              ) : (
                <p className="text-muted-foreground">Submit a query to see results</p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
