import { useEffect } from 'react';

import dynamic from 'next/dynamic';

import { useDatabaseOperations } from '@/context/database-operations-context';
import { type ApexOptions } from 'apexcharts';
import { Info } from 'lucide-react';

import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { HoverCard, HoverCardContent, HoverCardTrigger } from '@/components/ui/hover-card';

import { useCostMetricsHeatmap } from '@/hooks/use-backend-api';

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
  const { lastUpdated } = useDatabaseOperations();

  useEffect(() => {
    void fetchCostMetricsHeatmap();
  }, [fetchCostMetricsHeatmap, lastUpdated]);

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Cost Metrics by Channel</CardTitle>
          <CardDescription>Loading...</CardDescription>
        </CardHeader>
        <CardContent className="flex justify-center items-center h-48">
          <div className="animate-spin rounded-full h-8 w-8" />
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
        <CardContent className="flex justify-center items-center h-[350px] text-muted-foreground">
          {error ? error.message : 'No data available for cost metrics analysis'}
        </CardContent>
      </Card>
    );
  }

  // Transform data for ApexCharts format
  const series: SeriesData[] = data.data.map((row) => ({
    name: row.metric,
    data: data.channels.map((channel) => {
      const cellData = row.values[channel];
      return {
        x: channel,
        y: cellData?.intensity ?? 0,
        value: cellData?.value ?? 0, // Store actual value for tooltip
      };
    }),
  }));

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
          ranges: [
            {
              from: 0,
              to: 0.3,
              color: '#90EE90',
              name: 'low',
            },
            {
              from: 0.3,
              to: 0.7,
              color: '#FFB74D',
              name: 'medium',
            },
            {
              from: 0.7,
              to: 1,
              color: '#FF5252',
              name: 'high',
            },
          ],
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
          <CardTitle>Cost Metrics by Channel</CardTitle>
          <CardDescription>
            {data.time_range?.from_ &&
              data.time_range?.to &&
              `Data from ${data.time_range.from_} to ${data.time_range.to}`}
          </CardDescription>
        </CardHeader>
        <HoverCard>
          <HoverCardTrigger asChild>
            <Info className="h-4 w-4 text-muted-foreground cursor-help" />
          </HoverCardTrigger>
          <HoverCardContent className="w-80">
            <div className="space-y-2">
              <h4 className="text-sm font-semibold">Cost Metrics Analysis</h4>
              <p className="text-sm text-muted-foreground">
                This heatmap visualizes various cost metrics across different advertising channels.
                Darker colors indicate higher costs, helping you identify which channels are more
                expensive for specific metrics. Use this to optimize your budget allocation and
                identify cost-efficient channels.
              </p>
            </div>
          </HoverCardContent>
        </HoverCard>
      </div>
      <CardContent>
        <div className="w-full">
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
