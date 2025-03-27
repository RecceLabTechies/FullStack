"use client";

import { fetchCampaignFilterOptions } from "@/api/backendApi";
import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
} from "@/components/ui/form";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";
import {
  type CampaignFilterOptions,
  type CampaignFilters,
} from "@/types/types";
import { zodResolver } from "@hookform/resolvers/zod";
import { format } from "date-fns";
import { CalendarIcon } from "lucide-react";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import * as z from "zod";

interface FilterBarProps {
  onFilterChange: (filters: Partial<CampaignFilters>) => void;
}

// Define form schema
const FormSchema = z.object({
  channel: z.string().optional().nullable(),
  country: z.string().optional().nullable(),
  ageGroup: z.string().optional().nullable(),
  fromDate: z.date().optional(),
  toDate: z.date().optional(),
});

type FilterFormValues = z.infer<typeof FormSchema>;

export default function FilterBar({ onFilterChange }: FilterBarProps) {
  // State for filter options
  const [filterOptions, setFilterOptions] =
    useState<CampaignFilterOptions | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Initialize form
  const form = useForm<FilterFormValues>({
    resolver: zodResolver(FormSchema),
    defaultValues: {
      channel: null,
      country: null,
      ageGroup: null,
      fromDate: undefined,
      toDate: undefined,
    },
  });

  // Watch for form changes and update filters automatically
  useEffect(() => {
    const subscription = form.watch((values) => {
      const filters: Partial<CampaignFilters> = {};

      if (values.channel) {
        filters.channels = [values.channel];
      }

      if (values.country) {
        filters.countries = [values.country];
      }

      if (values.ageGroup) {
        filters.age_groups = [values.ageGroup];
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

  // Fetch filter options on component mount
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
                name="channel"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Channel</FormLabel>
                    <Select
                      onValueChange={field.onChange}
                      value={field.value ?? undefined}
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="All Channels" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {filterOptions.categorical.channels.map((channel) => (
                          <SelectItem key={channel} value={channel}>
                            {channel}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </FormItem>
                )}
              />

              {/* Country Filter */}
              <FormField
                control={form.control}
                name="country"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Country</FormLabel>
                    <Select
                      onValueChange={field.onChange}
                      value={field.value ?? undefined}
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="All Countries" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {filterOptions.categorical.countries.map((country) => (
                          <SelectItem key={country} value={country}>
                            {country}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </FormItem>
                )}
              />

              {/* Age Group Filter */}
              <FormField
                control={form.control}
                name="ageGroup"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Age Group</FormLabel>
                    <Select
                      onValueChange={field.onChange}
                      value={field.value ?? undefined}
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="All Age Groups" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {filterOptions.categorical.age_groups.map(
                          (ageGroup) => (
                            <SelectItem key={ageGroup} value={ageGroup}>
                              {ageGroup}
                            </SelectItem>
                          ),
                        )}
                      </SelectContent>
                    </Select>
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
