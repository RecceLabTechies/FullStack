'use client';

/**
 * Date Range Picker Component Module
 * Provides a popover calendar interface for selecting date ranges
 * with customizable constraints and styling options.
 */
import * as React from 'react';
import { type DateRange } from 'react-day-picker';

import { format } from 'date-fns';
import { CalendarIcon } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Calendar } from '@/components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';

import { cn } from '@/lib/utils';

/**
 * Props interface for the DatePickerWithRange component
 * Extends standard HTML div attributes with custom date range functionality
 *
 * @interface DatePickerWithRangeProps
 * @extends {React.HTMLAttributes<HTMLDivElement>}
 * @property {(range: DateRange | undefined) => void} [onRangeChange] - Callback when date range changes
 * @property {DateRange | undefined} [initialDateRange] - Initial date range to display
 * @property {Date} [minDate] - Minimum selectable date
 * @property {Date} [maxDate] - Maximum selectable date
 */
interface DatePickerWithRangeProps extends React.HTMLAttributes<HTMLDivElement> {
  onRangeChange?: (range: DateRange | undefined) => void;
  initialDateRange?: DateRange | undefined;
  minDate?: Date;
  maxDate?: Date;
}

/**
 * DatePickerWithRange Component
 * A customizable date range picker with popover calendar interface
 *
 * Features:
 * - Two-month calendar view
 * - Date range selection
 * - Min/max date constraints
 * - Formatted date display
 * - Accessible button trigger
 * - Customizable styling
 *
 * Usage:
 * ```tsx
 * <DatePickerWithRange
 *   onRangeChange={(range) => console.log(range)}
 *   initialDateRange={{ from: new Date(), to: new Date() }}
 *   minDate={new Date(2024, 0, 1)}
 *   maxDate={new Date(2024, 11, 31)}
 * />
 * ```
 *
 * @param {DatePickerWithRangeProps} props - Component props
 * @returns JSX.Element - Date range picker component
 */
export function DatePickerWithRange({
  className,
  onRangeChange,
  initialDateRange,
  minDate,
  maxDate,
}: DatePickerWithRangeProps) {
  // State to track the selected date range
  const [date, setDate] = React.useState<DateRange | undefined>(
    initialDateRange ?? {
      from: undefined,
      to: undefined,
    }
  );

  /**
   * Handles date range selection
   * Updates internal state and calls the onRangeChange callback if provided
   * @param {DateRange | undefined} selectedDate - The newly selected date range
   */
  const handleSelect = (selectedDate: DateRange | undefined) => {
    setDate(selectedDate);
    if (onRangeChange) {
      onRangeChange(selectedDate);
    }
  };

  return (
    <div className={cn('grid gap-2', className)}>
      <Popover>
        <PopoverTrigger asChild>
          <Button
            id="date"
            variant={'outline'}
            className={cn(
              'w-full justify-start text-left font-normal',
              !date && 'text-muted-foreground'
            )}
          >
            <CalendarIcon className="mr-2 h-4 w-4" />
            {date?.from ? (
              date.to ? (
                <>
                  {format(date.from, 'LLL dd, y')} - {format(date.to, 'LLL dd, y')}
                </>
              ) : (
                format(date.from, 'LLL dd, y')
              )
            ) : (
              <span>Select Date Range</span>
            )}
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-auto p-0" align="start">
          <Calendar
            initialFocus
            mode="range"
            defaultMonth={date?.from}
            selected={date}
            onSelect={handleSelect}
            numberOfMonths={2}
            fromDate={minDate}
            toDate={maxDate}
          />
        </PopoverContent>
      </Popover>
    </div>
  );
}
