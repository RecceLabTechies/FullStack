"use client";

import AdSpendTable from "@/components/ad-spend-table";
import AgeGroupBarChart from "@/components/age-group-bar-chart";
import ChannelBarChart from "@/components/channel-bar-chart";
import FilterBar from "@/components/filter-bar";
import KpiCards from "@/components/kpi-cards";
import PredictionTable from "@/components/prediction-table";
import RevenueChart from "@/components/revenue-chart";
import { Card } from "@/components/ui/card";
import { useState } from "react";

export default function Page() {
  const [dateRange, setDateRange] = useState<[Date, Date] | undefined>();
  const [selectedChannels, setSelectedChannels] = useState<string[]>([]);
  const [selectedAgeGroups, setSelectedAgeGroups] = useState<string[]>([]);

  return (
    <div className="container mx-auto px-4 py-6">
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
