"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";

interface ReportData {
  prompt: string;
  sections: string[];
  generatorName: string;
  dateRange: string;
  audienceType: string;
  format: string;
}

export default function ReportBuilder() {
  const [reportData, setReportData] = useState<ReportData>({
    prompt: "",
    sections: [],
    generatorName: "",
    dateRange: "",
    audienceType: "",
    format: "",
  });

  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>,
  ) => {
    setReportData({ ...reportData, [e.target.name]: e.target.value });
  };

  const handleSectionChange = (value: string[]) => {
    setReportData({ ...reportData, sections: value });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // Here you would typically send the data to a backend service
    console.log("Report Data:", reportData);
  };

  return (
    <div className="h-full w-80 overflow-y-auto border-r border-border bg-background p-4">
      <h2 className="mb-4 text-2xl font-bold">Report Builder</h2>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="prompt">Report Description</Label>
          <Textarea
            id="prompt"
            name="prompt"
            placeholder="Describe the purpose of your report..."
            value={reportData.prompt}
            onChange={handleInputChange}
            className="min-h-[100px]"
          />
        </div>

        <div className="space-y-2">
          <Label>Report Sections</Label>
          <div className="space-y-2">
            {[
              "Executive Summary",
              "Introduction",
              "Methodology",
              "Findings",
              "Conclusion",
              "Recommendations",
            ].map((section) => (
              <div key={section} className="flex items-center space-x-2">
                <Checkbox
                  id={section}
                  checked={reportData.sections.includes(section)}
                  onCheckedChange={(checked) => {
                    if (checked) {
                      handleSectionChange([...reportData.sections, section]);
                    } else {
                      handleSectionChange(
                        reportData.sections.filter((s) => s !== section),
                      );
                    }
                  }}
                />
                <Label htmlFor={section}>{section}</Label>
              </div>
            ))}
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="generatorName">Your Name</Label>
          <Input
            id="generatorName"
            name="generatorName"
            placeholder="Enter your name"
            value={reportData.generatorName}
            onChange={handleInputChange}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="dateRange">Date Range</Label>
          <Input
            id="dateRange"
            name="dateRange"
            placeholder="e.g., Jan 2023 - Jun 2023"
            value={reportData.dateRange}
            onChange={handleInputChange}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="audienceType">Audience Type</Label>
          <Select
            onValueChange={(value) =>
              setReportData({ ...reportData, audienceType: value })
            }
          >
            <SelectTrigger>
              <SelectValue placeholder="Select audience type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="internal">Internal</SelectItem>
              <SelectItem value="client">Client</SelectItem>
              <SelectItem value="public">Public</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label htmlFor="format">Format Preference</Label>
          <Select
            onValueChange={(value) =>
              setReportData({ ...reportData, format: value })
            }
          >
            <SelectTrigger>
              <SelectValue placeholder="Select format" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="pdf">PDF</SelectItem>
              <SelectItem value="docx">DOCX</SelectItem>
              <SelectItem value="pptx">PPTX</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <Button type="submit" className="w-full">
          Generate Report
        </Button>
      </form>
    </div>
  );
}
