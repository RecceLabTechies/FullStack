import * as React from "react";
import { AreaChartCard } from "@/app/dashboard/area-chart";
import { BarChartCard } from "@/app/dashboard/bar-chart";
import { LineChartCard } from "@/app/dashboard/line-chart";
import LeadDateChart from "./lead-date-chart";

export default function Page() {
  
  const isLoading = false;
  return (
    <div className="grid gap-4 md:grid-cols-2">
      <AreaChartCard isLoading={isLoading} />
      <BarChartCard isLoading={isLoading} />
      <BarChartCard isLoading={isLoading} />
      <LineChartCard isLoading={isLoading} />
      <LeadDateChart />
    </div>
  );

}


