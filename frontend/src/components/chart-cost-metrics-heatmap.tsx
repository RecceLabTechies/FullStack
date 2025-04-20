import { useEffect, useState } from 'react';
import { type DateRange } from 'react-day-picker';

import dynamic from 'next/dynamic';

import { useDatabaseOperations } from '@/context/database-operations-context';
import { type ApexOptions } from 'apexcharts';
import { Info } from 'lucide-react';

import { DatePickerWithRange } from '@/components/date-range-picker';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { HoverCard, HoverCardContent, HoverCardTrigger } from '@/components/ui/hover-card';

import { useCampaignDateRange, useCostMetricsHeatmap } from '@/hooks/use-backend-api';

// Dynamically import ReactApexChart with SSR disabled
const ReactApexChart = dynamic(() => import('react-apexcharts'), { ssr: false });

interface DataPoint {
  x: string;
  y: number;
  value: number;
}

interface SeriesData {
  name: string;
  data: DataPoint[];
}

interface TooltipContext {
  seriesIndex: number;
  dataPointIndex: number;
  w: {
    config: {
      series: SeriesData[];
    };
  };
}

export function CostMetricsHeatmap() {
  const { data, isLoading, error, fetchCostMetricsHeatmap } = useCostMetricsHeatmap();
  const {
    data: dateRangeData,
    isLoading: isDateRangeLoading,
    fetchDateRange,
  } = useCampaignDateRange();
  const { lastUpdated } = useDatabaseOperations();
  const [dateRange, setDateRange] = useState<DateRange | undefined>(undefined);
  const [normalizedData, setNormalizedData] = useState<SeriesData[]>([]);
  const [colorRanges, setColorRanges] = useState<
    { from: number; to: number; color: string; name: string }[]
  >([]);
  const [minDataValue, setMinDataValue] = useState<number | null>(null);
  const [maxDataValue, setMaxDataValue] = useState<number | null>(null);

  // Fetch available date range on mount
  useEffect(() => {
    void fetchDateRange();
  }, [fetchDateRange, lastUpdated]);

  // Fetch data with date range filter
  useEffect(() => {
    const minDate = dateRange?.from ? Math.floor(dateRange.from.getTime() / 1000) : undefined;
    const maxDate = dateRange?.to ? Math.floor(dateRange.to.getTime() / 1000) : undefined;
    void fetchCostMetricsHeatmap(minDate, maxDate);
  }, [fetchCostMetricsHeatmap, dateRange, lastUpdated]);

  // Process and normalize data
  useEffect(() => {
    if (!data?.data) return;

    // Find min and max values across all metrics and channels
    let minValue = Infinity;
    let maxValue = -Infinity;

    // First pass to find min/max
    data.data.forEach((row) => {
      Object.values(row.values).forEach((cellData) => {
        if (cellData?.value !== undefined) {
          minValue = Math.min(minValue, cellData.value);
          maxValue = Math.max(maxValue, cellData.value);
        }
      });
    });

    // Store min/max values for display
    setMinDataValue(minValue !== Infinity ? minValue : null);
    setMaxDataValue(maxValue !== -Infinity ? maxValue : null);

    // Create normalized data with recalculated intensity
    const normalized = data.data.map((row) => ({
      name: row.metric,
      data: data.channels.map((channel) => {
        const cellData = row.values[channel];
        const value = cellData?.value ?? 0;
        // Normalize intensity based on min/max instead of using the pre-calculated intensity
        const normalizedIntensity =
          maxValue === minValue
            ? 0.5 // If all values are the same, use middle intensity
            : (value - minValue) / (maxValue - minValue);

        return {
          x: channel,
          y: normalizedIntensity, // Use normalized intensity for the heatmap coloring
          value: value, // Keep original value for display
        };
      }),
    }));

    setNormalizedData(normalized);

    // Create dynamic color ranges based on the data distribution
    const ranges = [
      { from: 0, to: 0.1, color: '#1a9850', name: '0–10%' },
      { from: 0.1, to: 0.2, color: '#66bd63', name: '10–20%' },
      { from: 0.2, to: 0.3, color: '#a6d96a', name: '20–30%' },
      { from: 0.3, to: 0.4, color: '#d9ef8b', name: '30–40%' },
      { from: 0.4, to: 0.5, color: '#fee08b', name: '40–50%' },
      { from: 0.5, to: 0.6, color: '#fdae61', name: '50–60%' },
      { from: 0.6, to: 0.7, color: '#ef6548', name: '60–70%' },
      { from: 0.7, to: 0.8, color: '#d7301f', name: '70–80%' },
      { from: 0.8, to: 0.9, color: '#b30000', name: '80–90%' },
      { from: 0.9, to: 1.0, color: '#7f0000', name: '90–100%' },
    ];

    setColorRanges(ranges);
  }, [data]);

  // Convert Unix timestamps to Date objects for the date picker
  const minDate = dateRangeData?.min_date ? new Date(dateRangeData.min_date * 1000) : undefined;
  const maxDate = dateRangeData?.max_date ? new Date(dateRangeData.max_date * 1000) : undefined;

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Cost Metrics by Channel</CardTitle>
          <CardDescription>Loading...</CardDescription>
        </CardHeader>
        <CardContent className="flex justify-center items-center h-48">
          <div
            className="animate-spin rounded-full h-8 w-8"
            role="status"
            aria-label="Loading cost metrics data"
          />
        </CardContent>
      </Card>
    );
  }

  if (!data?.channels?.length || !data?.metrics?.length) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Cost Metrics by Channel</CardTitle>
          <CardDescription>{error ? 'Error loading data' : 'No data available'}</CardDescription>
        </CardHeader>
        <CardContent
          className="flex justify-center items-center h-[350px] text-muted-foreground"
          role={error ? 'alert' : undefined}
        >
          {error ? error.message : 'No data available for cost metrics analysis'}
        </CardContent>
      </Card>
    );
  }

  // Use normalizedData instead of directly transforming the data
  const series = normalizedData;

  const options: ApexOptions = {
    chart: {
      type: 'heatmap' as const,
      toolbar: {
        show: false,
      },
    },
    dataLabels: {
      enabled: true,
      style: {
        colors: ['#333'],
      },
      formatter: function (val: number, ctx: TooltipContext) {
        const series = ctx.w.config.series[ctx.seriesIndex];
        const point = series?.data[ctx.dataPointIndex];
        return point?.value.toFixed(2) ?? '0.00';
      },
    },
    colors: ['#008FFB'],
    xaxis: {
      type: 'category',
      labels: {
        rotate: -45,
        style: {
          fontSize: '12px',
        },
      },
    },
    plotOptions: {
      heatmap: {
        shadeIntensity: 0.5,
        colorScale: {
          ranges: colorRanges,
        },
      },
    },
    tooltip: {
      custom: function (ctx: TooltipContext) {
        const series = ctx.w.config.series[ctx.seriesIndex];
        const point = series?.data[ctx.dataPointIndex];
        if (!series || !point) return '';

        return `
            <div class="p-2">
              <h3 class="font-bold">${series.name} - ${point.x}</h3>
              <p>Value: $ ${point.value.toFixed(3)}</p>
              <p>Intensity: ${(point.y * 100).toFixed(1)}%</p>
            </div>
        `;
      },
    },
    grid: {
      borderColor: 'hsl(var(--border))',
      padding: {
        right: 20,
        left: 20,
      },
    },
  };

  return (
    <Card>
      <div className="flex items-center justify-between pr-6">
        <CardHeader>
          <CardTitle id="cost-metrics-title">Cost Metrics by Channel</CardTitle>
          <DatePickerWithRange
            onRangeChange={setDateRange}
            initialDateRange={dateRange}
            minDate={minDate}
            maxDate={maxDate}
            className="w-[300px]"
          />
        </CardHeader>
        <HoverCard>
          <HoverCardTrigger asChild>
            <Info
              className="h-4 w-4 text-muted-foreground cursor-help"
              aria-label="About cost metrics analysis"
            />
          </HoverCardTrigger>
          <HoverCardContent className="w-[320px]">
            <div className="space-y-2">
              <h4 className="text-sm font-semibold">Cost Metrics Analysis</h4>
              <p className="text-sm text-muted-foreground">
                This heatmap visualizes various cost metrics across different advertising channels.
                Darker colors indicate higher costs, helping you identify which channels are more
                expensive for specific metrics.
              </p>
              <p className="text-sm text-muted-foreground">
                <strong>Value calculation:</strong> Each cell shows the actual metric value in
                dollars. Color intensity is normalized on a scale from 0-100% where:
                <br />• 0% = lowest value in dataset{' '}
                {minDataValue !== null ? `($${minDataValue.toFixed(3)})` : ''}
                <br />• 100% = highest value in dataset{' '}
                {maxDataValue !== null ? `($${maxDataValue.toFixed(3)})` : ''}
              </p>
              <p className="text-sm text-muted-foreground">
                <strong>Normalization formula:</strong> For each value (v), intensity is calculated
                as:
                <br />
                <code>(v - min) / (max - min) × 100%</code>
              </p>
              <p className="text-sm text-muted-foreground">
                Cells with similar intensities have comparable relative costs within the current
                dataset. Use this to optimize your budget allocation and identify cost-efficient
                channels.
              </p>
            </div>
          </HoverCardContent>
        </HoverCard>
      </div>

      <CardContent>
        <div className="w-full" aria-labelledby="cost-metrics-title">
          <ReactApexChart options={options} series={series} type="heatmap" height={350} />
        </div>
      </CardContent>
      <CardFooter>
        <small className="text-muted-foreground">
          Color intensity indicates relative cost (darker = higher cost)
        </small>
      </CardFooter>
    </Card>
  );
}
