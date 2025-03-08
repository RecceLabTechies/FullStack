"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { useState } from "react";

interface Message {
  id: string;
  content: string;
  sender: "user" | "assistant";
  timestamp: Date;
}

interface PaperSize {
  name: string;
  widthClass: string;
}

const DEFAULT_SIZE: PaperSize = {
  name: "A4",
  widthClass: "w-[51rem]",
};

const paperSizes: Record<string, PaperSize> = {
  letter: {
    name: "Letter",
    widthClass: "w-[52rem]",
  },
  a4: {
    name: "A4",
    widthClass: "w-[51rem]",
  },
};

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
  const [selectedSize, setSelectedSize] = useState<string>("a4");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMessage.trim()) return;

    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputMessage,
      sender: "user",
      timestamp: new Date(),
    };

    // Add assistant response
    const assistantMessage: Message = {
      id: (Date.now() + 1).toString(),
      content:
        "I'll help you create that report. Could you provide more details about what you'd like to include?",
      sender: "assistant",
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage, assistantMessage]);
    setInputMessage("");
  };
  return (
    <div className="flex h-full gap-3 overflow-clip">
      <section className="flex h-full w-1/3 min-w-[26rem] max-w-[52rem] flex-col justify-between">
        {/* Chat History */}
        <ScrollArea className="h-[calc(100%_-_4rem)]">
          <div className="flex-1 space-y-2 overflow-y-auto">
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
                  <p>{message.content}</p>
                  <span className="text-xs opacity-70">
                    {message.timestamp.toLocaleTimeString()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>
        {/* Input Form */}
        <form onSubmit={handleSubmit} className="flex space-x-2 pb-4">
          <Input
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            placeholder="Type your message here..."
          />
          <Button type="submit">Send</Button>
        </form>
      </section>
      <section>
        <h2 className="text-2xl font-bold">Report Preview</h2>
        <Separator className="mb-4 mt-2" />
        <ScrollArea className="h-[calc(100%_-_4rem)]">
          <article className="flex-1 space-y-2 overflow-y-auto">
            <p>
              Lorem ipsum dolor sit amet, consectetur adipiscing elit. Aenean ut
              est ullamcorper, euismod nisl a, viverra purus. Phasellus ac
              congue lacus, eu hendrerit arcu. Maecenas consectetur eu odio non
              mattis. Nunc scelerisque tristique purus. Mauris interdum justo
              vitae lacus imperdiet, ac aliquam dui auctor. Aliquam viverra
              scelerisque ante. Mauris vel risus justo. Praesent ullamcorper
              libero in odio ornare, id rutrum sem scelerisque. In sodales, arcu
              sit amet euismod tempor, sem risus laoreet enim, pellentesque
              venenatis ipsum nisi fringilla turpis. Ut rutrum mi tincidunt orci
              sollicitudin mollis. Curabitur non placerat sem. Nullam sit amet
              varius augue. Duis id rhoncus dolor, sit amet fermentum ante.
              Pellentesque lobortis dapibus eleifend. Nulla facilisis commodo
              nisl, vitae dictum justo auctor at.
            </p>
            <p>
              Lorem ipsum dolor sit amet, consectetur adipiscing elit. Aenean ut
              est ullamcorper, euismod nisl a, viverra purus. Phasellus ac
              congue lacus, eu hendrerit arcu. Maecenas consectetur eu odio non
              mattis. Nunc scelerisque tristique purus. Mauris interdum justo
              vitae lacus imperdiet, ac aliquam dui auctor. Aliquam viverra
              scelerisque ante. Mauris vel risus justo. Praesent ullamcorper
              libero in odio ornare, id rutrum sem scelerisque. In sodales, arcu
              sit amet euismod tempor, sem risus laoreet enim, pellentesque
              venenatis ipsum nisi fringilla turpis. Ut rutrum mi tincidunt orci
              sollicitudin mollis. Curabitur non placerat sem. Nullam sit amet
              varius augue. Duis id rhoncus dolor, sit amet fermentum ante.
              Pellentesque lobortis dapibus eleifend. Nulla facilisis commodo
              nisl, vitae dictum justo auctor at.
            </p>
            <p>
              Lorem ipsum dolor sit amet, consectetur adipiscing elit. Aenean ut
              est ullamcorper, euismod nisl a, viverra purus. Phasellus ac
              congue lacus, eu hendrerit arcu. Maecenas consectetur eu odio non
              mattis. Nunc scelerisque tristique purus. Mauris interdum justo
              vitae lacus imperdiet, ac aliquam dui auctor. Aliquam viverra
              scelerisque ante. Mauris vel risus justo. Praesent ullamcorper
              libero in odio ornare, id rutrum sem scelerisque. In sodales, arcu
              sit amet euismod tempor, sem risus laoreet enim, pellentesque
              venenatis ipsum nisi fringilla turpis. Ut rutrum mi tincidunt orci
              sollicitudin mollis. Curabitur non placerat sem. Nullam sit amet
              varius augue. Duis id rhoncus dolor, sit amet fermentum ante.
              Pellentesque lobortis dapibus eleifend. Nulla facilisis commodo
              nisl, vitae dictum justo auctor at.
            </p>
            <p>
              Lorem ipsum dolor sit amet, consectetur adipiscing elit. Aenean ut
              est ullamcorper, euismod nisl a, viverra purus. Phasellus ac
              congue lacus, eu hendrerit arcu. Maecenas consectetur eu odio non
              mattis. Nunc scelerisque tristique purus. Mauris interdum justo
              vitae lacus imperdiet, ac aliquam dui auctor. Aliquam viverra
              scelerisque ante. Mauris vel risus justo. Praesent ullamcorper
              libero in odio ornare, id rutrum sem scelerisque. In sodales, arcu
              sit amet euismod tempor, sem risus laoreet enim, pellentesque
              venenatis ipsum nisi fringilla turpis. Ut rutrum mi tincidunt orci
              sollicitudin mollis. Curabitur non placerat sem. Nullam sit amet
              varius augue. Duis id rhoncus dolor, sit amet fermentum ante.
              Pellentesque lobortis dapibus eleifend. Nulla facilisis commodo
              nisl, vitae dictum justo auctor at.
            </p>
          </article>
        </ScrollArea>
      </section>
    </div>
  );
}
