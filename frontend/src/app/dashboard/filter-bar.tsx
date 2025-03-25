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
import { CalendarIcon, Check, ChevronsUpDown, X } from "lucide-react";
import { type DateRange } from "react-day-picker";
import { Card } from "../../components/ui/card";
import { useEffect, useState } from "react";
import { fetchDataSynthFilters } from "@/api/dbApi";
import { fetchFilteredData } from "@/api/dbApi";

interface FilterOption {
  label: string;
  value: string;
}




interface FilterPopoverProps {
  options: FilterOption[];
  selected: string[];
  onSelectionChange: (selection: string[]) => void;
  placeholder: string;
  searchPlaceholder: string;
  emptyMessage: string;
}

function FilterPopover({
  options,
  selected,
  onSelectionChange,
  placeholder,
  searchPlaceholder,
  emptyMessage,
}: FilterPopoverProps) {
  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          className="w-full justify-between bg-white transition-colors hover:bg-gray-50"
        >
          {selected.length > 0 ? `${selected.length} selected` : placeholder}
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-full p-0">
        <Command>
          <CommandInput placeholder={searchPlaceholder} />
          <CommandList>
            <CommandEmpty>{emptyMessage}</CommandEmpty>
            <CommandGroup>
              {options.map((option) => (
                <CommandItem
                  key={option.value}
                  value={option.value}
                  onSelect={() => {
                    onSelectionChange(
                      selected.includes(option.value)
                        ? selected.filter((s) => s !== option.value)
                        : [...selected, option.value],
                    );
                  }}
                >
                  <Check
                    className={cn(
                      "mr-2 h-4 w-4 transition-opacity",
                      selected.includes(option.value)
                        ? "opacity-100"
                        : "opacity-0",
                    )}
                  />
                  {option.label}
                </CommandItem>
              ))}
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}

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
  
  const [channels, setChannels] = useState<FilterOption[]>([]);
  const [loadingChannels, setLoadingChannels] = useState(true);

  const [ageGroups, setAgeGroups] = useState<FilterOption[]>([]);
  const [loadingAgeGroups, setLoadingAgeGroups] = useState(true);

  const [countries, setCountries] = useState<FilterOption[]>([]);
  const [selectedCountries, setSelectedCountries] = useState<string[]>([]);
  const [loadingCountries, setLoadingCountries] = useState(true);

  const [filteredData, setFilteredData] = useState<any[]>([]);

  useEffect(() => {
    const loadFilters = async () => {
      const filters = await fetchDataSynthFilters();
  
      if (filters?.channels) {
        const options = filters.channels.map((ch) => ({
          label: formatLabel(ch),
          value: ch.toLowerCase().replace(/\s+/g, "-"),
        }));
        setChannels(options);
      }
  
      if (filters?.age_groups) {
        const ageOptions = filters.age_groups.map((age) => ({
          label: age,
          value: age,
        }));
        setAgeGroups(ageOptions);
      }

      if (filters?.countries) {
        const countryOptions = filters.countries.map((country) => ({
          label: formatLabel(country),
          value: country.toLowerCase().replace(/\s+/g, "-"),
        }));
        setCountries(countryOptions);
      }
      setLoadingCountries(false);    
      setLoadingChannels(false);
      setLoadingAgeGroups(false);
    };
  
    loadFilters();
  }, []);
   
  useEffect(() => {
    const fetchData = async () => {
  
      const data = await fetchFilteredData({
        channels: selectedChannels,
        ageGroups: selectedAgeGroups,
        countries: selectedCountries,
      });
      
      console.log("🎯 Filtered data:", data);
      setFilteredData(data); // or setState for charts/cards etc.
    };
  
    fetchData();
  }, [selectedChannels, selectedAgeGroups, selectedCountries]);
  
  

  const formatLabel = (str: string) =>
    str
      .split(" ")
      .map((w) => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
      .join(" ");
      
  const hasActiveFilters =
    dateRange ?? selectedChannels.length > 0 ?? selectedAgeGroups.length > 0;

  const clearFilters = () => {
    setDateRange(undefined);
    setSelectedChannels([]);
    setSelectedAgeGroups([]);
  };

  return (
    <Card className="flex flex-col items-center gap-4 p-4 md:flex-row">
      <header className="flex items-center gap-2">
        <h2 className="text-lg font-bold">Filter By</h2>
        {hasActiveFilters && (
          <Button
            variant="ghost"
            size="sm"
            onClick={clearFilters}
            className="h-8 px-2 text-muted-foreground hover:text-foreground"
          >
            <X className="mr-1 h-4 w-4" />
            Clear
          </Button>
        )}
      </header>
      <section className="flex-1">
        <Popover>
          <PopoverTrigger asChild>
            <Button
              variant="outline"
              className="w-full justify-start bg-white text-left font-normal transition-colors hover:bg-gray-50"
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
              defaultMonth={new Date()}
              selected={dateRange}
              onSelect={setDateRange}
              numberOfMonths={2}
            />
          </PopoverContent>
        </Popover>
      </section>

      <section className="flex-1">
        {loadingChannels ? (
          <p className="text-muted-foreground text-sm">Loading channels...</p>
        ) : (
          <FilterPopover
            options={channels}
            selected={selectedChannels}
            onSelectionChange={setSelectedChannels}
            placeholder="Channels"
            searchPlaceholder="Search channels..."
            emptyMessage="No channel found."
          />
        )}
      </section>

      <section className="flex-1">
        {loadingAgeGroups ? (
          <p className="text-muted-foreground text-sm">Loading age groups...</p>
        ) : (
          <FilterPopover
            options={ageGroups}
            selected={selectedAgeGroups}
            onSelectionChange={setSelectedAgeGroups}
            placeholder="Age Group"
            searchPlaceholder="Search age groups..."
            emptyMessage="No age group found."
          />
        )}
      </section>
      <section className="flex-1">
        {loadingCountries ? (
          <p className="text-muted-foreground text-sm">Loading countries...</p>
        ) : (
          <FilterPopover
            options={countries}
            selected={selectedCountries}
            onSelectionChange={setSelectedCountries}
            placeholder="Country"
            searchPlaceholder="Search countries..."
            emptyMessage="No country found."
          />
        )}
      </section>
    </Card>
  );
}
