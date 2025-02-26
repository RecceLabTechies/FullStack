"use client";

import * as React from "react";

import { AreaChartCard } from "@/app/area-chart";
import { BarChartCard } from "@/app/bar-chart";
import { LineChartCard } from "@/app/line-chart";

export default function Page() {
  const [isLoading, setIsLoading] = React.useState(true);

  React.useEffect(() => {
    const timer = setTimeout(() => {
      setIsLoading(false);
    }, 2000);
    return () => clearTimeout(timer);
  }, []);

  return (
    <div className="grid gap-4 md:grid-cols-2">
      <AreaChartCard isLoading={isLoading} />
      <BarChartCard isLoading={isLoading} />
      <BarChartCard isLoading={isLoading} />
      <LineChartCard isLoading={isLoading} />
    </div>
  );
}


