"use client";

import { analyzeData } from "@/api/llmApi";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import {
  DragDropContext,
  Draggable,
  Droppable,
  type DropResult,
} from "@hello-pangea/dnd";
import {
  Check,
  Download,
  Edit2,
  GripVertical,
  Loader2,
  Trash2,
  X,
} from "lucide-react";
import { useCallback, useState } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { toast } from "sonner";

interface Message {
  id: string;
  content: string;
  sender: "user" | "assistant";
  timestamp: Date;
}

interface ReportSection {
  title: string;
  content: string | JSX.Element;
  type: "text" | "chart";
  rawContent?: string;
}

interface Report {
  title: string;
  sections: ReportSection[];
}

interface ChartData {
  data: Record<string, unknown>[];
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

    interface HtmlElement {
      tag: string;
      content: string;
    }

    const elements = JSON.parse(cleanedString) as HtmlElement[];

    return elements.map((el: HtmlElement, index: number) => {
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

const REPORT_TEMPLATES = [
  {
    title: "Chart Generation",
    suggestions: ["Generate a chart for spendings over time"],
  },
  {
    title: "Description Generation",
    suggestions: ["Generate a description on spendings"],
  },
  // {
  //   title: "Report Generation",
  //   suggestions: ["Generate a report"],
  // },
];

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
    title: "New Report",
    sections: [],
  });
  const [isEditingTitle, setIsEditingTitle] = useState(false);
  const [editedTitle, setEditedTitle] = useState(report.title);
  const [editingSectionIndex, setEditingSectionIndex] = useState<number | null>(
    null,
  );
  const [editedSectionContent, setEditedSectionContent] = useState("");

  const handleDragEnd = useCallback(
    (result: DropResult) => {
      if (!result.destination) return;

      const items = Array.from(report.sections);
      const [reorderedItem] = items.splice(result.source.index, 1) as [
        ReportSection,
      ];
      items.splice(result.destination.index, 0, reorderedItem);
      setReport((prev) => ({ ...prev, sections: items }));
    },
    [report.sections],
  );

  const exportReport = async (format: "pdf" | "docx" | "html") => {
    try {
      // Placeholder for actual export logic
      toast.success(`Report exported as ${format.toUpperCase()}`, {
        description: `Your report has been successfully exported in ${format.toUpperCase()} format.`,
        action: {
          label: "Download",
          onClick: () => console.log(`Downloading ${format} report...`),
        },
      });
    } catch (error) {
      toast.error("Failed to export report", {
        description:
          error instanceof Error ? error.message : "An unknown error occurred",
      });
    }
  };

  const handleTitleEdit = () => {
    if (isEditingTitle) {
      setReport((prev) => ({ ...prev, title: editedTitle }));
    }
    setIsEditingTitle(!isEditingTitle);
  };

  const generateReportContent = async (userMessage: string) => {
    const response = await analyzeData(userMessage);

    if (response.error) {
      throw new Error(response.error);
    }

    let newSection: ReportSection;

    if (
      response.query_type === "chart" &&
      typeof response.output === "object" &&
      response.output !== null
    ) {
      // Validate that response.output has the required ChartData properties
      const output = response.output;

      // Check if output has all required properties of ChartData
      if (
        Array.isArray(output.data) &&
        typeof output.type === "string" &&
        typeof output.xAxis === "object" &&
        output.xAxis !== null &&
        typeof output.yAxis === "object" &&
        output.yAxis !== null
      ) {
        // Create type-safe references to xAxis and yAxis
        const xAxis = output.xAxis as Record<string, unknown>;
        const yAxis = output.yAxis as Record<string, unknown>;

        // Verify all required properties exist with correct types
        if (
          typeof xAxis.dataKey === "string" &&
          typeof xAxis.label === "string" &&
          typeof xAxis.type === "string" &&
          typeof yAxis.dataKey === "string" &&
          typeof yAxis.label === "string" &&
          typeof yAxis.type === "string"
        ) {
          const chartData: ChartData = {
            data: output.data as Record<string, unknown>[],
            type: output.type,
            xAxis: {
              dataKey: xAxis.dataKey,
              label: xAxis.label,
              type: xAxis.type,
            },
            yAxis: {
              dataKey: yAxis.dataKey,
              label: yAxis.label,
              type: yAxis.type,
            },
          };

          newSection = {
            title: `Chart Analysis`,
            content: (
              <div className="mt-4 h-[400px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart
                    data={chartData.data}
                    margin={{ top: 20, right: 40, left: 55, bottom: 150 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey={chartData.xAxis.dataKey}
                      label={{
                        value: chartData.xAxis.label,
                        position: "bottom",
                        offset: 120,
                      }}
                      angle={90}
                      dy={68}
                      fontSize={12}
                    />
                    <YAxis
                      dataKey={chartData.yAxis.dataKey}
                      label={{
                        value: chartData.yAxis.label,
                        angle: -90,
                        position: "left",
                        offset: 30,
                      }}
                      fontSize={12}
                    />
                    <Tooltip />
                    <Line
                      type="monotone"
                      dataKey={chartData.yAxis.dataKey}
                      strokeWidth={2}
                      dot={{ r: 4 }}
                      activeDot={{ r: 6 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            ),
            type: "chart",
          };
        } else {
          throw new Error("Invalid chart data format");
        }
      } else {
        throw new Error("Invalid chart data format");
      }
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
        rawContent: response.output,
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

    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputMessage,
      sender: "user",
      timestamp: new Date(),
    };

    try {
      await generateReportContent(inputMessage);

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        content:
          "I've updated the report based on your input. What else would you like to analyze?",
        sender: "assistant",
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, userMessage, assistantMessage]);
    } catch (error) {
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

  const handleDeleteSection = (indexToDelete: number) => {
    setReport((prev) => ({
      ...prev,
      sections: prev.sections.filter((_, index) => index !== indexToDelete),
    }));
    toast.success("Section deleted");
  };

  const handleSectionEdit = (index: number) => {
    const section = report.sections[index];
    if (section && section.type === "text") {
      setEditingSectionIndex(index);
      setEditedSectionContent(section.rawContent ?? "");
    }
  };

  const handleSectionEditSave = (index: number) => {
    if (editingSectionIndex === null) return;

    const section = report.sections[index];
    if (!section) return;

    setReport((prev) => ({
      ...prev,
      sections: prev.sections.map((s, i) => {
        if (i === index) {
          return {
            ...s,
            content: (
              <div className="prose prose-sm dark:prose-invert">
                {parseHTMLElements(editedSectionContent)}
              </div>
            ),
            rawContent: editedSectionContent,
          };
        }
        return s;
      }),
    }));

    // Reset editing state
    setEditingSectionIndex(null);
    setEditedSectionContent("");

    toast.success("Section updated successfully");
  };

  const handleSectionEditCancel = () => {
    setEditingSectionIndex(null);
    setEditedSectionContent("");
  };

  return (
    <main className="container mx-auto flex h-full gap-3 overflow-clip p-4">
      <aside className="flex h-full w-1/3 min-w-[26rem] max-w-[52rem] flex-col justify-between rounded-lg border bg-card p-4 shadow-sm">
        <header className="mb-4">
          <h1 className="text-xl font-semibold">Chat Assistant</h1>
          <p className="text-sm text-muted-foreground">
            Ask questions or request analysis to build your report
          </p>

          {/* Template Suggestions */}
          <section className="mt-4">
            <h2 className="mb-2 text-sm font-medium">Suggested Templates</h2>
            <div className="space-y-2">
              {REPORT_TEMPLATES.map((template) => (
                <article key={template.title} className="rounded-md border p-2">
                  <h3 className="text-sm font-medium">{template.title}</h3>
                  <div className="mt-1 space-y-1">
                    {template.suggestions.map((suggestion) => (
                      <button
                        key={suggestion}
                        onClick={() => setInputMessage(suggestion)}
                        className="w-full text-left text-xs text-muted-foreground hover:text-foreground"
                      >
                        {suggestion}
                      </button>
                    ))}
                  </div>
                </article>
              ))}
            </div>
          </section>
        </header>

        {/* Chat History */}
        <ScrollArea className="flex-1 px-2">
          <section className="space-y-4">
            {messages.map((message) => (
              <article
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
              </article>
            ))}
          </section>
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
      </aside>

      <section className="flex-1 rounded-lg border bg-card p-4 shadow-sm">
        <header className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {isEditingTitle ? (
              <div className="flex items-center gap-2">
                <Input
                  value={editedTitle}
                  onChange={(e) => setEditedTitle(e.target.value)}
                  className="h-8 w-[200px]"
                />
                <Button
                  size="icon"
                  variant="ghost"
                  onClick={handleTitleEdit}
                  className="h-8 w-8"
                >
                  <Check className="h-4 w-4" />
                </Button>
                <Button
                  size="icon"
                  variant="ghost"
                  onClick={() => {
                    setIsEditingTitle(false);
                    setEditedTitle(report.title);
                  }}
                  className="h-8 w-8"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            ) : (
              <>
                <h2 className="text-2xl font-bold">{report.title}</h2>
                <Button
                  size="icon"
                  variant="ghost"
                  onClick={handleTitleEdit}
                  className="h-8 w-8"
                >
                  <Edit2 className="h-4 w-4" />
                </Button>
              </>
            )}
          </div>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline">
                <Download className="mr-2 h-4 w-4" />
                Export Report
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => exportReport("pdf")}>
                Export as PDF
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => exportReport("docx")}>
                Export as DOCX
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => exportReport("html")}>
                Export as HTML
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </header>

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
              <DragDropContext onDragEnd={handleDragEnd}>
                <Droppable droppableId="report-sections">
                  {(provided) => (
                    <section
                      {...provided.droppableProps}
                      ref={provided.innerRef}
                      className="space-y-6"
                    >
                      {report.sections.map((section, index) => (
                        <Draggable
                          key={index.toString()}
                          draggableId={index.toString()}
                          index={index}
                        >
                          {(provided) => (
                            <article
                              ref={provided.innerRef}
                              {...provided.draggableProps}
                              className="group relative rounded-lg border bg-background p-4"
                            >
                              <div className="absolute right-2 top-2 flex gap-2 opacity-0 transition-opacity group-hover:opacity-100">
                                <div
                                  {...provided.dragHandleProps}
                                  className="cursor-grab"
                                >
                                  <div className="flex h-6 w-6 items-center justify-center rounded-sm bg-accent">
                                    <GripVertical className="h-4 w-4 text-muted-foreground" />
                                  </div>
                                </div>
                                {section.type === "text" && (
                                  <Button
                                    variant="ghost"
                                    size="icon"
                                    onClick={() => handleSectionEdit(index)}
                                    className="h-6 w-6"
                                  >
                                    <Edit2 className="h-4 w-4" />
                                  </Button>
                                )}
                                <Button
                                  variant="destructive"
                                  size="icon"
                                  onClick={() => handleDeleteSection(index)}
                                  className="h-6 w-6"
                                >
                                  <Trash2 className="h-4 w-4" />
                                </Button>
                              </div>
                              {editingSectionIndex === index ? (
                                <div className="flex flex-col gap-4">
                                  <textarea
                                    value={editedSectionContent}
                                    onChange={(e) =>
                                      setEditedSectionContent(e.target.value)
                                    }
                                    className="min-h-[200px] w-full rounded-md border bg-background px-3 py-2 text-sm"
                                    placeholder="Edit section content..."
                                  />
                                  <div className="flex justify-end gap-2">
                                    <Button
                                      variant="outline"
                                      onClick={handleSectionEditCancel}
                                    >
                                      Cancel
                                    </Button>
                                    <Button
                                      onClick={() =>
                                        handleSectionEditSave(index)
                                      }
                                    >
                                      Save Changes
                                    </Button>
                                  </div>
                                </div>
                              ) : (
                                section.content
                              )}
                            </article>
                          )}
                        </Draggable>
                      ))}
                      {provided.placeholder}
                    </section>
                  )}
                </Droppable>
              </DragDropContext>
            )}
          </article>
        </ScrollArea>
      </section>
    </main>
  );
}
