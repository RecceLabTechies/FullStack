"use client";

import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { cn } from "@/lib/utils";
import { format } from "date-fns";
import { CalendarIcon, Check, ChevronsUpDown } from "lucide-react";
import { DateRange } from "react-day-picker";
import { Card } from "./ui/card";

const channels = [
  { label: "Instagram", value: "instagram" },
  { label: "Email", value: "email" },
  { label: "Google Banner Ads", value: "google" },
  { label: "Influencer", value: "influencer" },
  { label: "Facebook", value: "facebook" },
  { label: "LinkedIn", value: "linkedin" },
  { label: "Newspaper", value: "newspaper" },
  { label: "Radio", value: "radio" },
];

const ageGroups = [
  { label: "18-24", value: "18-24" },
  { label: "25-34", value: "25-34" },
  { label: "35-54", value: "35-54" },
  { label: "45-54", value: "45-54" },
];

interface FilterBarProps {
  dateRange: DateRange | undefined;
  setDateRange: (date: DateRange | undefined) => void;
  selectedChannels: string[];
  setSelectedChannels: (channels: string[]) => void;
  selectedAgeGroups: string[];
  setSelectedAgeGroups: (ageGroups: string[]) => void;
}

export default function FilterBar({
  dateRange,
  setDateRange,
  selectedChannels,
  setSelectedChannels,
  selectedAgeGroups,
  setSelectedAgeGroups,
}: FilterBarProps) {
  return (
    <Card className="flex flex-col items-center gap-4 p-4 md:flex-row">
      <h2 className="text-lg font-bold">Filter By</h2>
      <div className="flex-1">
        <Popover>
          <PopoverTrigger asChild>
            <Button
              variant="outline"
              className="w-full justify-start bg-white text-left font-normal"
            >
              <CalendarIcon className="mr-2 h-4 w-4" />
              {dateRange?.from && dateRange?.to ? (
                <>
                  {format(dateRange.from, "LLL dd, y")} -{" "}
                  {format(dateRange.to, "LLL dd, y")}
                </>
              ) : (
                <span>Date Range</span>
              )}
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-auto p-0" align="start">
            <Calendar
              initialFocus
              mode="range"
              defaultMonth={new Date(2024, 0)}
              selected={dateRange}
              onSelect={setDateRange}
              numberOfMonths={2}
            />
          </PopoverContent>
        </Popover>
      </div>

      <div className="flex-1">
        <Popover>
          <PopoverTrigger asChild>
            <Button
              variant="outline"
              role="combobox"
              className="w-full justify-between bg-white"
            >
              {selectedChannels.length > 0
                ? `${selectedChannels.length} channels selected`
                : "Channels"}
              <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-full p-0">
            <Command>
              <CommandInput placeholder="Search channels..." />
              <CommandList>
                <CommandEmpty>No channel found.</CommandEmpty>
                <CommandGroup>
                  {channels.map((channel) => (
                    <CommandItem
                      key={channel.value}
                      value={channel.value}
                      onSelect={() => {
                        setSelectedChannels(
                          selectedChannels.includes(channel.value)
                            ? selectedChannels.filter(
                                (c) => c !== channel.value,
                              )
                            : [...selectedChannels, channel.value],
                        );
                      }}
                    >
                      <Check
                        className={cn(
                          "mr-2 h-4 w-4",
                          selectedChannels.includes(channel.value)
                            ? "opacity-100"
                            : "opacity-0",
                        )}
                      />
                      {channel.label}
                    </CommandItem>
                  ))}
                </CommandGroup>
              </CommandList>
            </Command>
          </PopoverContent>
        </Popover>
      </div>

      <div className="flex-1">
        <Popover>
          <PopoverTrigger asChild>
            <Button
              variant="outline"
              role="combobox"
              className="w-full justify-between bg-white"
            >
              {selectedAgeGroups.length > 0
                ? `${selectedAgeGroups.length} age groups selected`
                : "Age Group"}
              <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-full p-0">
            <Command>
              <CommandInput placeholder="Search age groups..." />
              <CommandList>
                <CommandEmpty>No age group found.</CommandEmpty>
                <CommandGroup>
                  {ageGroups.map((ageGroup) => (
                    <CommandItem
                      key={ageGroup.value}
                      value={ageGroup.value}
                      onSelect={() => {
                        setSelectedAgeGroups(
                          selectedAgeGroups.includes(ageGroup.value)
                            ? selectedAgeGroups.filter(
                                (a) => a !== ageGroup.value,
                              )
                            : [...selectedAgeGroups, ageGroup.value],
                        );
                      }}
                    >
                      <Check
                        className={cn(
                          "mr-2 h-4 w-4",
                          selectedAgeGroups.includes(ageGroup.value)
                            ? "opacity-100"
                            : "opacity-0",
                        )}
                      />
                      {ageGroup.label}
                    </CommandItem>
                  ))}
                </CommandGroup>
              </CommandList>
            </Command>
          </PopoverContent>
        </Popover>
      </div>
    </Card>
  );
}
