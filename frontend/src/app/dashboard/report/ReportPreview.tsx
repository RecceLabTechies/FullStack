"use client";

import { useState, useEffect } from "react";

export default function ReportPreview() {
  const [previewContent, setPreviewContent] = useState<string>("");

  useEffect(() => {
    // In a real application, you would listen for changes in the report data
    // and update the preview accordingly. For this example, we'll just set some placeholder content.
    setPreviewContent(`
      # Sample Report Preview

      ## Executive Summary
      This is a placeholder for the executive summary of your report.

      ## Introduction
      Here's where you would introduce the topic and purpose of your report.

      ## Methodology
      Describe the methods used to gather and analyze data for this report.

      ## Findings
      Present the main findings of your research or analysis here.

      ## Conclusion
      Summarize the key points and conclusions drawn from your findings.

      ## Recommendations
      Based on the findings, provide recommendations for future actions or decisions.
    `);
  }, []);

  return (
    <div className="flex-1 overflow-y-auto p-6">
      <h2 className="mb-4 text-2xl font-bold">Report Preview</h2>
      <div className="prose max-w-none">
        {previewContent.split("\n").map((line, index) => {
          if (line.startsWith("# ")) {
            return <h1 key={index}>{line.slice(2)}</h1>;
          } else if (line.startsWith("## ")) {
            return <h2 key={index}>{line.slice(3)}</h2>;
          } else if (line.trim() !== "") {
            return <p key={index}>{line}</p>;
          }
          return null;
        })}
      </div>
    </div>
  );
}
