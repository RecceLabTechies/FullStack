"use client";

import {
  fetchCampaignFilterOptions,
  fetchMonthlyPerformanceData,
} from "@/api/backendApi";
import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
} from "@/components/ui/form";
import { MultiSelect } from "@/components/ui/multi-select";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { cn } from "@/lib/utils";
import {
  type CampaignFilterOptions,
  type CampaignFilters,
  type MonthlyPerformanceData,
} from "@/types/types";
import { zodResolver } from "@hookform/resolvers/zod";
import { format } from "date-fns";
import { CalendarIcon } from "lucide-react";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import * as z from "zod";

// Define form schema
const FormSchema = z.object({
  channels: z.array(z.string()).optional().default([]),
  countries: z.array(z.string()).optional().default([]),
  ageGroups: z.array(z.string()).optional().default([]),
  fromDate: z.date().optional(),
  toDate: z.date().optional(),
});

type FilterFormValues = z.infer<typeof FormSchema>;

// FilterBar Component
function FilterBar({
  onFilterChange,
}: {
  onFilterChange: (filters: Partial<CampaignFilters>) => void;
}) {
  const [filterOptions, setFilterOptions] =
    useState<CampaignFilterOptions | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const form = useForm<FilterFormValues>({
    resolver: zodResolver(FormSchema),
    defaultValues: {
      channels: [],
      countries: [],
      ageGroups: [],
      fromDate: undefined,
      toDate: undefined,
    },
  });

  useEffect(() => {
    const subscription = form.watch((values) => {
      const filters: Partial<CampaignFilters> = {};

      if (values.channels && values.channels.length > 0) {
        filters.channels = values.channels.filter(
          (channel): channel is string => channel !== undefined,
        );
      }

      if (values.countries && values.countries.length > 0) {
        filters.countries = values.countries.filter(
          (country): country is string => country !== undefined,
        );
      }

      if (values.ageGroups && values.ageGroups.length > 0) {
        filters.age_groups = values.ageGroups.filter(
          (ageGroup): ageGroup is string => ageGroup !== undefined,
        );
      }

      if (values.fromDate) {
        filters.from_date = format(values.fromDate, "yyyy-MM-dd");
      }

      if (values.toDate) {
        filters.to_date = format(values.toDate, "yyyy-MM-dd");
      }

      onFilterChange(filters);
    });

    return () => subscription.unsubscribe();
  }, [form, onFilterChange]);

  useEffect(() => {
    const loadFilterOptions = async () => {
      setLoading(true);
      try {
        const options = await fetchCampaignFilterOptions();
        if (options) {
          setFilterOptions(options);
          setError(null);
          console.log("Filter options loaded:", options);
        } else {
          setError("Failed to load filter options");
        }
      } catch (err) {
        setError("An error occurred while fetching filter options");
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    void loadFilterOptions();
  }, []);

  if (loading) {
    return <div className="p-4">Loading filter options...</div>;
  }

  if (error) {
    return <div className="p-4 text-destructive">{error}</div>;
  }

  if (!filterOptions?.categorical) {
    return <div className="text-warning p-4">No filter options available</div>;
  }

  return (
    <Card className="mb-4">
      <CardHeader>
        <CardTitle>Filter Dashboard Data</CardTitle>
      </CardHeader>
      <Form {...form}>
        <form>
          <CardContent>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-5">
              {/* Channel Filter */}
              <FormField
                control={form.control}
                name="channels"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Channel</FormLabel>
                    <MultiSelect
                      options={
                        filterOptions?.categorical.channels.map((channel) => ({
                          label: channel,
                          value: channel,
                        })) ?? []
                      }
                      onValueChange={field.onChange}
                      defaultValue={field.value}
                      placeholder="All Channels"
                      maxCount={3}
                    />
                  </FormItem>
                )}
              />

              {/* Country Filter */}
              <FormField
                control={form.control}
                name="countries"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Country</FormLabel>
                    <MultiSelect
                      options={
                        filterOptions?.categorical.countries.map((country) => ({
                          label: country,
                          value: country,
                        })) ?? []
                      }
                      onValueChange={field.onChange}
                      defaultValue={field.value}
                      placeholder="All Countries"
                      maxCount={3}
                    />
                  </FormItem>
                )}
              />

              {/* Age Group Filter */}
              <FormField
                control={form.control}
                name="ageGroups"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Age Group</FormLabel>
                    <MultiSelect
                      options={
                        filterOptions?.categorical.age_groups.map(
                          (ageGroup) => ({
                            label: ageGroup,
                            value: ageGroup,
                          }),
                        ) ?? []
                      }
                      onValueChange={field.onChange}
                      defaultValue={field.value}
                      placeholder="All Age Groups"
                      maxCount={3}
                    />
                  </FormItem>
                )}
              />

              {/* From Date Filter */}
              <FormField
                control={form.control}
                name="fromDate"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>From Date</FormLabel>
                    <Popover>
                      <PopoverTrigger asChild>
                        <FormControl>
                          <Button
                            variant="outline"
                            className={cn(
                              "w-full justify-start text-left font-normal",
                              !field.value && "text-muted-foreground",
                            )}
                          >
                            <CalendarIcon className="mr-2 h-4 w-4" />
                            {field.value
                              ? format(field.value, "PPP")
                              : "Select date"}
                          </Button>
                        </FormControl>
                      </PopoverTrigger>
                      <PopoverContent className="w-auto p-0">
                        <Calendar
                          mode="single"
                          selected={field.value}
                          onSelect={field.onChange}
                          initialFocus
                          fromDate={
                            filterOptions.date_range
                              ? new Date(filterOptions.date_range.min_date)
                              : undefined
                          }
                          toDate={
                            filterOptions.date_range
                              ? new Date(filterOptions.date_range.max_date)
                              : undefined
                          }
                        />
                      </PopoverContent>
                    </Popover>
                  </FormItem>
                )}
              />

              {/* To Date Filter */}
              <FormField
                control={form.control}
                name="toDate"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>To Date</FormLabel>
                    <Popover>
                      <PopoverTrigger asChild>
                        <FormControl>
                          <Button
                            variant="outline"
                            className={cn(
                              "w-full justify-start text-left font-normal",
                              !field.value && "text-muted-foreground",
                            )}
                          >
                            <CalendarIcon className="mr-2 h-4 w-4" />
                            {field.value
                              ? format(field.value, "PPP")
                              : "Select date"}
                          </Button>
                        </FormControl>
                      </PopoverTrigger>
                      <PopoverContent className="w-auto p-0">
                        <Calendar
                          mode="single"
                          selected={field.value}
                          onSelect={field.onChange}
                          initialFocus
                          fromDate={
                            form.getValues().fromDate ??
                            (filterOptions.date_range
                              ? new Date(filterOptions.date_range.min_date)
                              : undefined)
                          }
                          toDate={
                            filterOptions.date_range
                              ? new Date(filterOptions.date_range.max_date)
                              : undefined
                          }
                          disabled={(date) => {
                            const fromDate = form.getValues().fromDate;
                            return fromDate ? date < fromDate : false;
                          }}
                        />
                      </PopoverContent>
                    </Popover>
                  </FormItem>
                )}
              />
            </div>
          </CardContent>
        </form>
      </Form>
    </Card>
  );
}

// Main Dashboard Component
export default function Dashboard() {
  const [chartData, setChartData] = useState<MonthlyPerformanceData | null>(
    null,
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeFilters, setActiveFilters] = useState<Partial<CampaignFilters>>(
    {},
  );

  // Fetch chart data on initial load and when filters change
  useEffect(() => {
    const fetchChartData = async () => {
      setLoading(true);
      try {
        const data = await fetchMonthlyPerformanceData(activeFilters);
        if (data) {
          setChartData(data);
          setError(null);
        } else {
          setError("Failed to load chart data");
        }
      } catch (err) {
        setError("An error occurred while fetching chart data");
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    void fetchChartData();
  }, [activeFilters]);

  // Handle filter changes from FilterBar
  const handleFilterChange = (filters: Partial<CampaignFilters>) => {
    setActiveFilters(filters);
  };

  // Transform chart data to format required by Recharts
  const transformDataForChart = () => {
    if (!chartData) return [];

    return chartData.months.map((month, index) => ({
      month,
      revenue: chartData.revenue[index],
      adSpend: chartData.ad_spend[index],
      roi: chartData.roi[index],
    }));
  };

  return (
    <div className="container mx-auto py-6">
      {/* Filter Bar */}
      <FilterBar onFilterChange={handleFilterChange} />

      <div className="flex w-full flex-row gap-4">
        {/* Performance Chart */}
        <Card className="w-full">
          <CardHeader>
            <CardTitle>Monthly Performance</CardTitle>
            <CardDescription>
              View revenue, ad spend, and ROI trends over time
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex h-96 items-center justify-center">
                <p>Loading chart data...</p>
              </div>
            ) : error ? (
              <div className="flex h-96 items-center justify-center">
                <p className="text-destructive">{error}</p>
              </div>
            ) : !chartData || chartData.months.length === 0 ? (
              <div className="flex h-96 items-center justify-center">
                <p>No data available for the selected filters</p>
              </div>
            ) : (
              <div className="h-96 w-full">
                <ResponsiveContainer
                  width="100%"
                  height="100%"
                  className="w-full"
                >
                  <LineChart
                    data={transformDataForChart()}
                    margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis yAxisId="left" />
                    <YAxis yAxisId="right" orientation="right" />
                    <Tooltip />
                    <Legend />
                    <Line
                      yAxisId="left"
                      type="monotone"
                      dataKey="revenue"
                      name="Revenue"
                      stroke="#8884d8"
                      activeDot={{ r: 8 }}
                    />
                    <Line
                      yAxisId="left"
                      type="monotone"
                      dataKey="adSpend"
                      name="Ad Spend"
                      stroke="#82ca9d"
                    />
                    <Line
                      yAxisId="right"
                      type="monotone"
                      dataKey="roi"
                      name="ROI"
                      stroke="#ff7300"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}
          </CardContent>
        </Card>
        {/* Summary Cards */}
        {chartData && (
          <div className="grid grid-cols-1 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>
                  {" "}
                  $
                  {chartData.revenue
                    .reduce((sum, val) => sum + val, 0)
                    .toFixed(2)}
                </CardTitle>
                <CardDescription>
                  Total Revenue for selected period
                </CardDescription>
              </CardHeader>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>
                  {" "}
                  $
                  {chartData.ad_spend
                    .reduce((sum, val) => sum + val, 0)
                    .toFixed(2)}
                </CardTitle>
                <CardDescription>
                  Total Ad Spend for selected period
                </CardDescription>
              </CardHeader>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>
                  {(
                    chartData.roi.reduce((sum, val) => sum + val, 0) /
                    (chartData.roi.length || 1)
                  ).toFixed(2)}
                  x
                </CardTitle>
                <CardDescription>Average return on investment</CardDescription>
              </CardHeader>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}
