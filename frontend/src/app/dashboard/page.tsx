"use client";

import AdSpendTable from "@/app/dashboard/ad-spend-table";
import AgeGroupBarChart from "@/app/dashboard/age-group-bar-chart";
import ChannelBarChart from "@/app/dashboard/channel-bar-chart";
import KpiCards from "@/app/dashboard/kpi-cards";
import PredictionTable from "@/app/dashboard/prediction-table";
import RevenueChart from "@/app/dashboard/revenue-chart";
import FilterBar from "@/components/filter-bar";
import { Card } from "@/components/ui/card";
import { useState } from "react";

export default function Page() {
  const [dateRange, setDateRange] = useState<[Date, Date] | undefined>();
  const [selectedChannels, setSelectedChannels] = useState<string[]>([]);
  const [selectedAgeGroups, setSelectedAgeGroups] = useState<string[]>([]);

  return (
    <div className="container mx-auto p-4">
      <FilterBar
        dateRange={dateRange}
        setDateRange={setDateRange}
        selectedChannels={selectedChannels}
        setSelectedChannels={setSelectedChannels}
        selectedAgeGroups={selectedAgeGroups}
        setSelectedAgeGroups={setSelectedAgeGroups}
      />

      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card className="rounded-lg bg-white p-4 shadow">
          <RevenueChart />
        </Card>
        <div>
          <KpiCards />
          <div className="mt-6 grid grid-cols-1 gap-6 md:grid-cols-2">
            <Card className="rounded-lg bg-white p-4 shadow">
              <ChannelBarChart />
            </Card>
            <Card className="rounded-lg bg-white p-4 shadow">
              <AgeGroupBarChart />
            </Card>
          </div>
        </div>
      </div>

      <div className="mt-6 space-y-6">
        <AdSpendTable />
        <PredictionTable />
      </div>
    </div>
  );
}
