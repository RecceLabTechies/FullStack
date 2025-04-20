'use client';

import { useEffect } from 'react';
import { useForm } from 'react-hook-form';

import * as z from 'zod';
import { useDatabaseOperations } from '@/context/database-operations-context';
import { type CampaignFilters } from '@/types/types';
import { zodResolver } from '@hookform/resolvers/zod';
import { Info } from 'lucide-react';
import moment from 'moment';
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import { DatePickerWithRange } from '@/components/date-range-picker';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { HoverCard, HoverCardContent, HoverCardTrigger } from '@/components/ui/hover-card';
import { MultiSelect } from '@/components/ui/multi-select';

import { useCampaignFilterOptions, useMonthlyAggregatedData } from '@/hooks/use-backend-api';

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

export function RevenueAdSpendChart() {
  const {
    data: filterOptions,
    isLoading: isLoadingOptions,
    error: filterOptionsError,
    fetchFilterOptions,
  } = useCampaignFilterOptions();

  const {
    data: monthlyData,
    error: monthlyDataError,
    isLoading: isLoadingMonthlyData,
    fetchMonthlyData,
  } = useMonthlyAggregatedData();

  const { lastUpdated } = useDatabaseOperations();

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
  }, [fetchFilterOptions, lastUpdated]);

  // Add effect to fetch monthly data on mount and when database is updated
  useEffect(() => {
    if (filterOptions) {
      const defaultFilters: CampaignFilters = {
        min_revenue: filterOptions.numeric_ranges.revenue.min,
        max_revenue: filterOptions.numeric_ranges.revenue.max,
        min_ad_spend: filterOptions.numeric_ranges.ad_spend.min,
        max_ad_spend: filterOptions.numeric_ranges.ad_spend.max,
        min_views: filterOptions.numeric_ranges.views.min,
        min_leads: filterOptions.numeric_ranges.leads.min,
      };
      void fetchMonthlyData(defaultFilters);
    }
  }, [filterOptions, fetchMonthlyData, lastUpdated]);

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
        month: moment.unix(item.date).format('MMM'),
        revenue: item.revenue,
        ad_spend: item.ad_spend,
      });
    });
  }

  if (isLoadingOptions) {
    return (
      <div role="status" aria-live="polite">
        Loading...
      </div>
    );
  }

  if (filterOptionsError) {
    return <div role="alert">Error loading filter options</div>;
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
      filterPayload.from_date = moment(data.dateRange.from).unix();
    }
    if (data.dateRange?.to) {
      filterPayload.to_date = moment(data.dateRange.to).unix();
    }

    // Fetch monthly data with the filter payload
    void fetchMonthlyData(filterPayload);
  };

  return (
    <div className="flex gap-4">
      <Card className="w-full">
        <div className="flex items-center justify-between pr-6">
          <CardHeader>
            <CardTitle id="revenue-adspend-chart-title">Revenue & Ad Spend Filter Chart</CardTitle>
            <CardDescription>
              Monthly comparison of revenue generated versus advertising expenditure
            </CardDescription>
          </CardHeader>
          <HoverCard>
            <HoverCardTrigger asChild>
              <Info
                className="h-4 w-4 text-muted-foreground cursor-help"
                aria-label="About revenue and ad spend analysis"
              />
            </HoverCardTrigger>
            <HoverCardContent className="w-80">
              <div className="space-y-2">
                <h4 className="text-sm font-semibold">Revenue & Ad Spend Analysis</h4>
                <p className="text-sm text-muted-foreground">
                  This chart visualizes the relationship between your revenue and advertising costs
                  over time. Compare monthly trends to identify periods of high ROI and optimize
                  your ad strategy. Use the filters to analyze specific campaigns, channels,
                  regions, or time periods.
                </p>
              </div>
            </HoverCardContent>
          </HoverCard>
        </div>

        <CardContent>
          {monthlyDataError ? (
            <div
              className="flex h-[400px] w-full items-center justify-center text-muted-foreground"
              role="alert"
            >
              {monthlyDataError.message}
            </div>
          ) : isLoadingMonthlyData ? (
            <div
              className="flex h-[400px] w-full items-center justify-center text-muted-foreground"
              role="status"
              aria-live="polite"
            >
              Loading...
            </div>
          ) : chartData.length === 0 ? (
            <div
              className="flex h-[400px] w-full items-center justify-center text-muted-foreground"
              aria-label="No data available"
            >
              No data available for the selected filters
            </div>
          ) : (
            <div className="h-[400px] w-full">
              <ResponsiveContainer
                width="100%"
                height="100%"
                aria-labelledby="revenue-adspend-chart-title"
              >
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
                  <Tooltip
                    formatter={(value: number | string) =>
                      typeof value === 'number' ? value.toFixed(3) : value
                    }
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="revenue"
                    stroke="hsl(var(--chart-1))"
                    activeDot={{ r: 8 }}
                    name="Revenue"
                    strokeWidth={3}
                  />
                  <Line
                    type="monotone"
                    dataKey="ad_spend"
                    stroke="hsl(var(--chart-2))"
                    name="Ad Spend"
                    strokeWidth={3}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </CardContent>
      </Card>

      <Card className="w-1/4">
        <CardHeader>
          <CardTitle id="filter-controls-title">Filters</CardTitle>
          <CardDescription>
            Filter Revenue & Ad Spend Chart by date range, age groups, channels, countries, and
            campaign IDs
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Form {...form}>
            <form
              onSubmit={form.handleSubmit(onSubmit)}
              className="grid gap-2"
              aria-labelledby="filter-controls-title"
            >
              {/* Date Range Filter */}
              <FormField
                control={form.control}
                name="dateRange"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel htmlFor="date-range">Date Range</FormLabel>
                    <FormControl>
                      <DatePickerWithRange
                        onRangeChange={field.onChange}
                        minDate={moment.unix(filterOptions.date_range.min_date).toDate()}
                        maxDate={moment.unix(filterOptions.date_range.max_date).toDate()}
                        id="date-range"
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
                    <FormLabel htmlFor="age-groups">Age Groups</FormLabel>
                    <FormControl>
                      <MultiSelect
                        options={filterOptions.categorical.age_groups.map((group) => ({
                          label: group,
                          value: group,
                        }))}
                        onValueChange={field.onChange}
                        placeholder="Select age groups"
                        id="age-groups"
                        aria-label="Select age groups"
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
                    <FormLabel htmlFor="channels">Channels</FormLabel>
                    <FormControl>
                      <MultiSelect
                        options={filterOptions.categorical.channels.map((channel) => ({
                          label: channel,
                          value: channel,
                        }))}
                        onValueChange={field.onChange}
                        placeholder="Select channels"
                        id="channels"
                        aria-label="Select channels"
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
                    <FormLabel htmlFor="countries">Countries</FormLabel>
                    <FormControl>
                      <MultiSelect
                        options={filterOptions.categorical.countries.map((country) => ({
                          label: country,
                          value: country,
                        }))}
                        onValueChange={field.onChange}
                        placeholder="Select countries"
                        id="countries"
                        aria-label="Select countries"
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
                    <FormLabel htmlFor="campaigns">Campaigns</FormLabel>
                    <FormControl>
                      <MultiSelect
                        options={filterOptions.categorical.campaign_ids.map((id) => ({
                          label: id,
                          value: id,
                        }))}
                        onValueChange={field.onChange}
                        placeholder="Select campaigns"
                        id="campaigns"
                        aria-label="Select campaigns"
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <Button type="submit" aria-label="Apply filters to chart">
                Apply Filters
              </Button>
            </form>
          </Form>
        </CardContent>
      </Card>
    </div>
  );
}
