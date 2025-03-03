"use client"

import { useState } from "react"
import FilterBar from "@/components/filter-bar"
import RevenueChart from "@/components/revenue-chart"
import KpiCards from "@/components/kpi-cards"
import ChannelBarChart from "@/components/channel-bar-chart"
import AgeGroupBarChart from "@/components/age-group-bar-chart"
import AdSpendTable from "@/components/ad-spend-table"
import PredictionTable from "@/components/prediction-table"
import { Card } from "@/components/ui/card"

export default function Page() {
  const [dateRange, setDateRange] = useState<[Date, Date] | undefined>()
  const [selectedChannels, setSelectedChannels] = useState<string[]>([])
  const [selectedAgeGroups, setSelectedAgeGroups] = useState<string[]>([])

  return (
    <div className="container mx-auto py-6 px-4">
      <FilterBar
        dateRange={dateRange}
        setDateRange={setDateRange}
        selectedChannels={selectedChannels}
        setSelectedChannels={setSelectedChannels}
        selectedAgeGroups={selectedAgeGroups}
        setSelectedAgeGroups={setSelectedAgeGroups}
      />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
        <Card className="bg-white p-4 rounded-lg shadow">
          <RevenueChart />
        </Card>
        <div>
          <KpiCards />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
            <Card className="bg-white p-4 rounded-lg shadow">
              <ChannelBarChart />
            </Card>
            <Card className="bg-white p-4 rounded-lg shadow">
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
  )
}

