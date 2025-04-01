"use client";

import { useEffect } from "react";
import { DatePickerWithRange } from "@/components/date-range-picker";
import { MultiSelect } from "@/components/ui/multi-select";
import { useCampaignFilterOptions } from "@/hooks/use-backend-api";
import { type CampaignFilters } from "@/types/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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

export default function DashboardPage() {
  const {
    data: filterOptions,
    isLoading,
    error,
    fetchFilterOptions,
  } = useCampaignFilterOptions();

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

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>Error loading filter options</div>;
  }

  if (!filterOptions) {
    return null;
  }

  const onSubmit = (data: FilterFormValues) => {
    const filterPayload: CampaignFilters = {};

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
    console.log("Filter payload:", filterPayload);
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

      {/* Dashboard content will go here */}
    </div>
  );
}
