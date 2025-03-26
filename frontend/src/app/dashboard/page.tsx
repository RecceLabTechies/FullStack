"use client";

import AdSpendTable from "@/app/dashboard/ad-spend-table";
import AgeGroupBarChart from "@/app/dashboard/age-group-bar-chart";
import ChannelBarChart from "@/app/dashboard/channel-bar-chart";
import FilterBar from "@/app/dashboard/filter-bar";
import KpiCards from "@/app/dashboard/kpi-cards";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useState } from "react";
import { type DateRange } from "react-day-picker";
import RevenueChart from "./revenue-chart";
import HeatmapChart from "@/app/dashboard/cost-heatmap";
import StackedBarChart from "./stacked-bar-chart";

export default function Page() {
  const [dateRange, setDateRange] = useState<DateRange | undefined>();
  const [selectedChannels, setSelectedChannels] = useState<string[]>([]);
  const [selectedAgeGroups, setSelectedAgeGroups] = useState<string[]>([]);

  return (
    <main className="container mx-auto p-4">
      <FilterBar
        dateRange={dateRange}
        setDateRange={setDateRange}
        selectedChannels={selectedChannels}
        setSelectedChannels={setSelectedChannels}
        selectedAgeGroups={selectedAgeGroups}
        setSelectedAgeGroups={setSelectedAgeGroups}
      />

      <section className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Revenue & Ad Spend across Months</CardTitle>
          </CardHeader>
          <CardContent className="h-[32rem]">
            <RevenueChart />
          </CardContent>
        </Card>
        <section>
          <KpiCards />
          <section className="mt-6 grid grid-cols-1 gap-6 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Channels: Revenue per Dollar spend</CardTitle>
              </CardHeader>
              <CardContent className="h-96">
                <ChannelBarChart />
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Age Group: Revenue per Dollar spend</CardTitle>
              </CardHeader>
              <CardContent className="h-96">
                <AgeGroupBarChart />
              </CardContent>
            </Card>
          </section>
        </section>
      </section>
      <section className="mt-6 space-y-6">
        <AdSpendTable />
      </section>

      {/* New */}
      <section className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
        <HeatmapChart />
        <StackedBarChart />
      </section>
    </main>
  );
}
