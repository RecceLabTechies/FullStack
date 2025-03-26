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
import DatePicker from "@/components/ui/DatePicker";

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

  const [dateMode, setDateMode] = useState<"single" | "range">("single");
  const [singleDate, setSingleDate] = useState<{ year: string; month: string }>({ year: "", month: "" });
  const [fromDate, setFromDate] = useState<string>("");
  const [toDate, setToDate] = useState<string>("");

// In FilterBar.tsx
  const [appliedFromDate, setAppliedFromDate] = useState<string>("");
  const [appliedToDate, setAppliedToDate] = useState<string>("");
  const [appliedSingleDate, setAppliedSingleDate] = useState<{ year: string; month: string }>({ year: "", month: "" });

  const [datePopoverOpen, setDatePopoverOpen] = useState(false);

  const handleDateApply = () => {
    setAppliedFromDate(fromDate);
    setAppliedToDate(toDate);
    setAppliedSingleDate({ ...singleDate });
  };


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
      const from = dateMode === "range" ? appliedFromDate : buildFromSingle(appliedSingleDate);
      const to = dateMode === "range" ? appliedToDate : buildToSingle(appliedSingleDate);
  
      const data = await fetchFilteredData({
        channels: selectedChannels,
        ageGroups: selectedAgeGroups,
        countries: selectedCountries,
        from,
        to,
      });
  
      console.log("Filtered data:", data);
      setFilteredData(data);
    };
  
    fetchData();
  }, [selectedChannels, selectedAgeGroups, selectedCountries, appliedFromDate, appliedToDate, appliedSingleDate]);
  
  
  const buildFromSingle = (date: { year: string; month: string }) => {
    if (!date.year) return "";
    return date.month ? `${date.month}/1/${date.year}` : `1/1/${date.year}`;
  };

  const buildToSingle = (date: { year: string; month: string }) => {
    if (!date.year) return "";
    return date.month ? `${date.month}/31/${date.year}` : `12/31/${date.year}`;
  };

  const formatLabel = (str: string) =>
    str
      .split(" ")
      .map((w) => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
      .join(" ");
      
  const hasActiveFilters =
    selectedChannels.length > 0 ||
    selectedAgeGroups.length > 0 ||
    selectedCountries.length > 0 ||
    (dateMode === "range" && fromDate && toDate) ||
    (dateMode === "single" && singleDate.year);

  const clearFilters = () => {
    setDateRange(undefined); // if you're using this somewhere else
    setSelectedChannels([]);
    setSelectedAgeGroups([]);
    setSelectedCountries([]);
    setFromDate("");
    setToDate("");
    setSingleDate({ year: "", month: "" });
    setAppliedFromDate("");
    setAppliedToDate("");
    setAppliedSingleDate({ year: "", month: "" }); // ✅ resets the *applied* date filter
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
        <Popover open={datePopoverOpen} onOpenChange={setDatePopoverOpen}>
          <PopoverTrigger asChild>
            <Button
              variant="outline"
              className="w-full justify-between bg-white transition-colors hover:bg-gray-50"
            >
              Date
              <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-auto p-0">
            <DatePicker
              dateMode={dateMode}
              setDateMode={setDateMode}
              singleDate={singleDate}
              setSingleDate={setSingleDate}
              fromDate={fromDate}
              toDate={toDate}
              setFromDate={setFromDate}
              setToDate={setToDate}
              onApply={() => {
                handleDateApply();
                setDatePopoverOpen(false); // ✅ collapse after apply
              }}
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
