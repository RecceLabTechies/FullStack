"use client";

import { useEffect } from "react";
import { DatePickerWithRange } from "@/components/date-range-picker";
import { MultiSelect } from "@/components/ui/multi-select";
import {
  useCampaignFilterOptions,
  useCampaigns,
  useMonthlyAggregatedData,
} from "@/hooks/use-backend-api";
import { type CampaignFilters } from "@/types/types";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

const filterSchema = z.object({
  dateRange: z
    .object({
      from: z.date().optional(),
      to: z.date().optional(),
    })
    .optional(),
  ageGroups: z.array(z.string()).optional(),
  channels: z.array(z.string()).optional(),
  countries: z.array(z.string()).optional(),
  campaignIds: z.array(z.string()).optional(),
});

type FilterFormValues = z.infer<typeof filterSchema>;

interface ChartData {
  month: string;
  revenue: number;
  ad_spend: number;
}

export default function DashboardPage() {
  const {
    data: filterOptions,
    isLoading: isLoadingOptions,
    error: filterOptionsError,
    fetchFilterOptions,
  } = useCampaignFilterOptions();

  const {
    data: campaignData,
    isLoading: isLoadingCampaigns,
    error: campaignError,
    fetchCampaigns,
  } = useCampaigns();

  const {
    data: monthlyData,
    error: monthlyDataError,
    isLoading: isLoadingMonthlyData,
    fetchMonthlyData,
  } = useMonthlyAggregatedData();

  const form = useForm<FilterFormValues>({
    resolver: zodResolver(filterSchema),
    defaultValues: {
      dateRange: undefined,
      ageGroups: [],
      channels: [],
      countries: [],
      campaignIds: [],
    },
  });

  useEffect(() => {
    void fetchFilterOptions();
  }, [fetchFilterOptions]);

  // Effect to fetch monthly data when campaign data changes
  useEffect(() => {
    if (!campaignData || !filterOptions) return;

    const fetchData = async () => {
      try {
        // Fetch monthly aggregated data with the same filters used to get the campaign data
        const filterPayload = form.getValues();
        const filters: CampaignFilters = {};

        // Set numeric ranges
        filters.min_revenue = filterOptions.numeric_ranges.revenue.min;
        filters.max_revenue = filterOptions.numeric_ranges.revenue.max;
        filters.min_ad_spend = filterOptions.numeric_ranges.ad_spend.min;
        filters.max_ad_spend = filterOptions.numeric_ranges.ad_spend.max;
        filters.min_views = filterOptions.numeric_ranges.views.min;
        filters.min_leads = filterOptions.numeric_ranges.leads.min;

        // Set filter values from form
        if (filterPayload.channels?.length) {
          filters.channels = filterPayload.channels;
        }
        if (filterPayload.countries?.length) {
          filters.countries = filterPayload.countries;
        }
        if (filterPayload.ageGroups?.length) {
          filters.age_groups = filterPayload.ageGroups;
        }
        if (filterPayload.campaignIds?.length) {
          filters.campaign_ids = filterPayload.campaignIds;
        }
        if (filterPayload.dateRange?.from) {
          filters.from_date = Math.floor(
            filterPayload.dateRange.from.getTime() / 1000,
          );
        }
        if (filterPayload.dateRange?.to) {
          filters.to_date = Math.floor(
            filterPayload.dateRange.to.getTime() / 1000,
          );
        }

        await fetchMonthlyData(filters);
      } catch (error) {
        console.error("Error fetching monthly data:", error);
      }
    };

    void fetchData();
  }, [campaignData, fetchMonthlyData, form, filterOptions]);

  // Transform the data for the chart
  const chartData: ChartData[] = [];

  if (
    monthlyData &&
    !(monthlyData instanceof Error) &&
    monthlyData.items &&
    Array.isArray(monthlyData.items)
  ) {
    // Sort the items by date
    const sortedItems = [...monthlyData.items].sort((a, b) => a.date - b.date);

    // Transform the items to chart data format
    sortedItems.forEach((item) => {
      chartData.push({
        month: new Date(item.date * 1000).toLocaleString("default", {
          month: "short",
        }),
        revenue: item.revenue,
        ad_spend: item.ad_spend,
      });
    });
  }

  if (isLoadingOptions) {
    return <div>Loading...</div>;
  }

  if (filterOptionsError) {
    return <div>Error loading filter options</div>;
  }

  if (!filterOptions) {
    return null;
  }

  const onSubmit = (data: FilterFormValues) => {
    const filterPayload: CampaignFilters = {
      min_revenue: filterOptions.numeric_ranges.revenue.min,
      max_revenue: filterOptions.numeric_ranges.revenue.max,
      min_ad_spend: filterOptions.numeric_ranges.ad_spend.min,
      max_ad_spend: filterOptions.numeric_ranges.ad_spend.max,
      min_views: filterOptions.numeric_ranges.views.min,
      min_leads: filterOptions.numeric_ranges.leads.min,
    };

    // Only add fields that have been filled out
    if (data.channels?.length) {
      filterPayload.channels = data.channels;
    }
    if (data.countries?.length) {
      filterPayload.countries = data.countries;
    }
    if (data.ageGroups?.length) {
      filterPayload.age_groups = data.ageGroups;
    }
    if (data.campaignIds?.length) {
      filterPayload.campaign_ids = data.campaignIds;
    }
    if (data.dateRange?.from) {
      filterPayload.from_date = Math.floor(
        data.dateRange.from.getTime() / 1000,
      );
    }
    if (data.dateRange?.to) {
      filterPayload.to_date = Math.floor(data.dateRange.to.getTime() / 1000);
    }

    // Fetch campaigns with the filter payload
    void fetchCampaigns(filterPayload);
  };

  return (
    <div className="container mx-auto p-4">
      <div className="mb-8">
        <h1 className="mb-4 text-2xl font-bold">Campaign Dashboard</h1>

        <Card>
          <CardHeader>
            <CardTitle>Filter Campaigns</CardTitle>
          </CardHeader>
          <CardContent>
            <Form {...form}>
              <form
                onSubmit={form.handleSubmit(onSubmit)}
                className="grid grid-cols-5 gap-2"
              >
                {/* Date Range Filter */}
                <FormField
                  control={form.control}
                  name="dateRange"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Date Range</FormLabel>
                      <FormControl>
                        <DatePickerWithRange
                          onRangeChange={field.onChange}
                          minDate={
                            new Date(filterOptions.date_range.min_date * 1000)
                          }
                          maxDate={
                            new Date(filterOptions.date_range.max_date * 1000)
                          }
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                {/* Age Groups Filter */}
                <FormField
                  control={form.control}
                  name="ageGroups"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Age Groups</FormLabel>
                      <FormControl>
                        <MultiSelect
                          options={filterOptions.categorical.age_groups.map(
                            (group) => ({
                              label: group,
                              value: group,
                            }),
                          )}
                          onValueChange={field.onChange}
                          placeholder="Select age groups"
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                {/* Channels Filter */}
                <FormField
                  control={form.control}
                  name="channels"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Channels</FormLabel>
                      <FormControl>
                        <MultiSelect
                          options={filterOptions.categorical.channels.map(
                            (channel) => ({
                              label: channel,
                              value: channel,
                            }),
                          )}
                          onValueChange={field.onChange}
                          placeholder="Select channels"
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                {/* Countries Filter */}
                <FormField
                  control={form.control}
                  name="countries"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Countries</FormLabel>
                      <FormControl>
                        <MultiSelect
                          options={filterOptions.categorical.countries.map(
                            (country) => ({
                              label: country,
                              value: country,
                            }),
                          )}
                          onValueChange={field.onChange}
                          placeholder="Select countries"
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                {/* Campaign IDs Filter */}
                <FormField
                  control={form.control}
                  name="campaignIds"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Campaigns</FormLabel>
                      <FormControl>
                        <MultiSelect
                          options={filterOptions.categorical.campaign_ids.map(
                            (id) => ({
                              label: id,
                              value: id,
                            }),
                          )}
                          onValueChange={field.onChange}
                          placeholder="Select campaigns"
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <Button type="submit">Apply Filters</Button>
              </form>
            </Form>
          </CardContent>
        </Card>
      </div>

      {isLoadingCampaigns && <div>Loading campaign data...</div>}
      {campaignError && <div>Error loading campaign data</div>}

      {/* Revenue & Ad Spend Chart */}
      <Card className="w-full">
        <CardHeader>
          <CardTitle>Revenue & Ad Spend Overview</CardTitle>
          <CardDescription>
            Monthly comparison of revenue generated versus advertising
            expenditure
          </CardDescription>
        </CardHeader>
        <CardContent>
          {monthlyDataError ? (
            <div className="flex h-[400px] w-full items-center justify-center text-muted-foreground">
              {monthlyDataError.message}
            </div>
          ) : isLoadingMonthlyData ? (
            <div className="flex h-[400px] w-full items-center justify-center text-muted-foreground">
              Loading...
            </div>
          ) : chartData.length === 0 ? (
            <div className="flex h-[400px] w-full items-center justify-center text-muted-foreground">
              No data available for the selected filters
            </div>
          ) : (
            <div className="h-[400px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart
                  data={chartData}
                  margin={{
                    top: 5,
                    right: 30,
                    left: 20,
                    bottom: 5,
                  }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="revenue"
                    stroke="#8884d8"
                    activeDot={{ r: 8 }}
                    name="Revenue"
                  />
                  <Line
                    type="monotone"
                    dataKey="ad_spend"
                    stroke="#82ca9d"
                    name="Ad Spend"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
