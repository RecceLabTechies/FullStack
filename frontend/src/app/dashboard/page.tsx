"use client";

import { useEffect } from "react";
import { DatePickerWithRange } from "@/components/date-range-picker";
import { MultiSelect } from "@/components/ui/multi-select";
import { useCampaignFilterOptions } from "@/hooks/use-backend-api";
import { type DateRange } from "react-day-picker";

export default function DashboardPage() {
  const {
    data: filterOptions,
    isLoading,
    error,
    fetchFilterOptions,
  } = useCampaignFilterOptions();

  useEffect(() => {
    void fetchFilterOptions();
  }, [fetchFilterOptions]);

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>Error loading filter options</div>;
  }

  if (!filterOptions) {
    return null;
  }

  const handleDateRangeChange = (range: DateRange | undefined) => {
    // Handle date range change
    console.log("Date range changed:", range);
  };

  const handleAgeGroupsChange = (values: string[]) => {
    // Handle age groups change
    console.log("Age groups changed:", values);
  };

  const handleChannelsChange = (values: string[]) => {
    // Handle channels change
    console.log("Channels changed:", values);
  };

  const handleCountriesChange = (values: string[]) => {
    // Handle countries change
    console.log("Countries changed:", values);
  };

  const handleCampaignIdsChange = (values: string[]) => {
    // Handle campaign IDs change
    console.log("Campaign IDs changed:", values);
  };

  return (
    <div className="container mx-auto p-4">
      <div className="mb-8">
        <h1 className="mb-4 text-2xl font-bold">Campaign Dashboard</h1>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {/* Date Range Filter */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Date Range</label>
            <DatePickerWithRange
              onRangeChange={handleDateRangeChange}
              minDate={new Date(filterOptions.date_range.min_date * 1000)}
              maxDate={new Date(filterOptions.date_range.max_date * 1000)}
            />
          </div>

          {/* Age Groups Filter */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Age Groups</label>
            <MultiSelect
              options={filterOptions.categorical.age_groups.map((group) => ({
                label: group,
                value: group,
              }))}
              onValueChange={handleAgeGroupsChange}
              placeholder="Select age groups"
            />
          </div>

          {/* Channels Filter */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Channels</label>
            <MultiSelect
              options={filterOptions.categorical.channels.map((channel) => ({
                label: channel,
                value: channel,
              }))}
              onValueChange={handleChannelsChange}
              placeholder="Select channels"
            />
          </div>

          {/* Countries Filter */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Countries</label>
            <MultiSelect
              options={filterOptions.categorical.countries.map((country) => ({
                label: country,
                value: country,
              }))}
              onValueChange={handleCountriesChange}
              placeholder="Select countries"
            />
          </div>

          {/* Campaign IDs Filter */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Campaigns</label>
            <MultiSelect
              options={filterOptions.categorical.campaign_ids.map((id) => ({
                label: id,
                value: id,
              }))}
              onValueChange={handleCampaignIdsChange}
              placeholder="Select campaigns"
            />
          </div>
        </div>
      </div>

      {/* Dashboard content will go here */}
    </div>
  );
}
