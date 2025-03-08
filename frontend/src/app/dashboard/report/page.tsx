"use client";

import { analyzeData } from "@/api/llmApi";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Loader2 } from "lucide-react";
import { useState } from "react";

interface Message {
  id: string;
  content: string;
  sender: "user" | "assistant";
  timestamp: Date;
}

interface ReportSection {
  title: string;
  content: string;
  data?: Record<string, any>;
}

interface Report {
  title: string;
  sections: ReportSection[];
}

export default function ReportGenerationPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      content:
        "Hello! I'm your report building assistant. What kind of report would you like to create?",
      sender: "assistant",
      timestamp: new Date(),
    },
  ]);
  const [inputMessage, setInputMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [report, setReport] = useState<Report>({
    title: "Report",
    sections: [],
  });

  const generateReportContent = async (userMessage: string) => {
    const response = await analyzeData(userMessage);

    if (!response.success || !response.result) {
      throw new Error(response.error || "Failed to generate report content");
    }

    const newSection: ReportSection = {
      title: `Analysis ${report.sections.length + 1}`,
      content: response.result.output,
      data: response.result.data_preview,
    };

    setReport((prev) => ({
      ...prev,
      sections: [...prev.sections, newSection],
    }));

    return response;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMessage.trim() || isLoading) return;

    setIsLoading(true);

    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputMessage,
      sender: "user",
      timestamp: new Date(),
    };

    try {
      // Generate report content based on user message
      const response = await generateReportContent(inputMessage);

      // Add assistant response
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        content:
          response.result?.output ||
          "I've updated the report based on your input. What else would you like to add?",
        sender: "assistant",
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, userMessage, assistantMessage]);
    } catch (error) {
      // Add error message
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content:
          error instanceof Error
            ? `Error: ${error.message}`
            : "Sorry, I encountered an error while generating the report. Please try again.",
        sender: "assistant",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, userMessage, errorMessage]);
    } finally {
      setIsLoading(false);
      setInputMessage("");
    }
  };

  return (
    <div className="flex h-full gap-3 overflow-clip p-4">
      <section className="flex h-full w-1/3 min-w-[26rem] max-w-[52rem] flex-col justify-between rounded-lg border bg-card p-4 shadow-sm">
        <div className="mb-4">
          <h2 className="text-xl font-semibold">Chat Assistant</h2>
          <p className="text-sm text-muted-foreground">
            Ask questions or request analysis to build your report
          </p>
        </div>

        {/* Chat History */}
        <ScrollArea className="flex-1 px-2">
          <div className="space-y-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${
                  message.sender === "user" ? "justify-end" : "justify-start"
                }`}
              >
                <div
                  className={`max-w-[80%] rounded-lg px-4 py-2 ${
                    message.sender === "user"
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted"
                  }`}
                >
                  <p className="text-sm">{message.content}</p>
                  <span className="mt-1 block text-xs opacity-70">
                    {message.timestamp.toLocaleTimeString()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>

        {/* Input Form */}
        <form onSubmit={handleSubmit} className="mt-4 flex space-x-2">
          <Input
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            placeholder="Ask a question or request analysis..."
            disabled={isLoading}
            className="flex-1"
          />
          <Button type="submit" disabled={isLoading}>
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Processing
              </>
            ) : (
              "Send"
            )}
          </Button>
        </form>
      </section>

      <section className="flex-1 rounded-lg border bg-card p-4 shadow-sm">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold">{report.title}</h2>
          <Button variant="outline">Export Report</Button>
        </div>

        <Separator className="mb-4 mt-2" />

        <ScrollArea className="h-[calc(100vh-12rem)]">
          <article className="prose prose-sm dark:prose-invert max-w-none">
            {report.sections.length === 0 ? (
              <div className="flex h-40 items-center justify-center text-muted-foreground">
                <p>
                  Your report content will appear here as you chat with the
                  assistant.
                </p>
              </div>
            ) : (
              report.sections.map((section, index) => (
                <div key={index} className="mb-6">
                  <p>{section.content}</p>
                </div>
              ))
            )}
          </article>
        </ScrollArea>
      </section>
    </div>
  );
}
