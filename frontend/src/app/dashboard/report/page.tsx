"use client";

import { analyzeData } from "@/api/llmApi";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Loader2 } from "lucide-react";
import { useState } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

interface Message {
  id: string;
  content: string;
  sender: "user" | "assistant";
}

interface ReportSection {
  title: string;
  content: string | JSX.Element;
  type: "text" | "chart";
}

interface Report {
  title: string;
  sections: ReportSection[];
}

interface ChartData {
  data: Record<any, any>[];
  type: string;
  xAxis: {
    dataKey: string;
    label: string;
    type: string;
  };
  yAxis: {
    dataKey: string;
    label: string;
    type: string;
  };
}

// Helper function to parse HTML elements from the description response
const parseHTMLElements = (elementsString: string): JSX.Element[] => {
  try {
    // Clean up the string to get valid JSON
    const cleanedString = elementsString
      .replace(/^elements=\[/, "[") // Remove the "elements=" prefix
      .replace(
        /HTMLElement\(tag='([^']+)', content='([^']+)'\)/g,
        '{"tag":"$1","content":"$2"}',
      );

    const elements = JSON.parse(cleanedString);

    return elements.map((el: any, index: number) => {
      switch (el.tag) {
        case "h2":
          return (
            <h2 key={index} className="mb-3 mt-6 text-2xl font-bold">
              {el.content}
            </h2>
          );
        case "h3":
          return (
            <h3 key={index} className="mb-2 mt-4 text-xl font-semibold">
              {el.content}
            </h3>
          );
        case "p":
          return (
            <p key={index} className="mb-4 text-muted-foreground">
              {el.content}
            </p>
          );
        default:
          return <div key={index}>{el.content}</div>;
      }
    });
  } catch (error) {
    console.error(
      "Failed to parse HTML elements:",
      error,
      "\nInput string:",
      elementsString,
    );
    return [<p key="error">Error parsing content</p>];
  }
};

export default function ReportGenerationPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      content:
        "Hello! I'm your report building assistant. What kind of report would you like to create?",
      sender: "assistant",
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

    if (response.error) {
      throw new Error(response.error);
    }

    let newSection: ReportSection;

    if (
      response.query_type === "chart" &&
      typeof response.output === "object"
    ) {
      const chartData = response.output as ChartData;
      newSection = {
        title: `Chart Analysis`,
        content: (
          <div className="mt-4 h-[400px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData.data}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey={chartData.xAxis.dataKey}
                  label={chartData.xAxis.label}
                />
                <YAxis
                  dataKey={chartData.yAxis.dataKey}
                  label={chartData.yAxis.label}
                />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey={chartData.yAxis.dataKey}
                  stroke="#8884d8"
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        ),
        type: "chart",
      };
    } else if (typeof response.output === "string") {
      // Handle description/report type
      newSection = {
        title: `Analysis`,
        content: (
          <div className="prose prose-sm dark:prose-invert">
            {parseHTMLElements(response.output)}
          </div>
        ),
        type: "text",
      };
    } else {
      throw new Error("Unexpected response format");
    }

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
    };

    try {
      // Generate report content based on user message
      const response = await generateReportContent(inputMessage);

      // Add assistant response
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        content:
          "I've updated the report based on your input. What else would you like to analyze?",
        sender: "assistant",
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
          <article className="max-w-none">
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
                  {section.content}
                </div>
              ))
            )}
          </article>
        </ScrollArea>
      </section>
    </div>
  );
}
