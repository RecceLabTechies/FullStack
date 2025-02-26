import type { Metadata } from "next";
import ReportBuilder from "@/app/dashboard/report/ReportBuilder";
import ReportPreview from "@/app/dashboard/report/ReportPreview";

export const metadata: Metadata = {
  title: "Report Generation",
  description: "Generate reports for your business",
};

export default function ReportGenerationPage() {
  return (
    <div className="flex h-screen bg-background">
      <ReportBuilder />
      <ReportPreview />
    </div>
  );
}
