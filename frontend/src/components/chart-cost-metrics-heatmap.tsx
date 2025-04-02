import { useEffect, useRef } from 'react';

import * as d3 from 'd3';

import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';

import { useCostMetricsHeatmap } from '@/hooks/use-backend-api';

interface HeatmapDataPoint {
  metric: string;
  channel: string;
  value: number;
  intensity: number;
  formattedValue: string;
}

/**
 * A component that displays a heatmap of cost metrics (cost per lead, cost per view, cost per account)
 * across different channels, with color intensity representing relative cost values.
 */
export default function CostMetricsHeatmap() {
  const { data, isLoading, error, fetchCostMetricsHeatmap } = useCostMetricsHeatmap();
  const svgRef = useRef<SVGSVGElement>(null);

  // Format values based on the metric (different precision for different metrics)
  const formatValue = (value: number, metric: string): string => {
    if (metric.includes('Lead') || metric.includes('Account')) {
      // For larger values, show 2 decimal places
      return value.toFixed(2);
    } else {
      // For smaller values (like Cost Per View), show 3 decimal places
      return value.toFixed(3);
    }
  };

  useEffect(() => {
    void fetchCostMetricsHeatmap();
  }, [fetchCostMetricsHeatmap]);

  useEffect(() => {
    if (!data?.channels?.length || !data?.metrics?.length || !svgRef.current) return;

    // Clear any existing elements
    d3.select(svgRef.current).selectAll('*').remove();

    // Set up dimensions
    const margin = { top: 50, right: 25, bottom: 20, left: 150 };
    const svgWidth = Math.max(800, 80 * data.channels.length + margin.left + margin.right);
    const svgHeight = 85 * data.metrics.length + margin.top + margin.bottom;

    // Resize the SVG
    const svg = d3.select(svgRef.current).attr('width', svgWidth).attr('height', svgHeight);

    // Create scales
    const xScale = d3
      .scaleBand()
      .domain(data.channels)
      .range([margin.left, svgWidth - margin.right])
      .padding(0.05);

    const yScale = d3
      .scaleBand()
      .domain(data.metrics)
      .range([margin.top, svgHeight - margin.bottom])
      .padding(0.05);

    // Define color scale for intensity
    const colorScale = d3
      .scaleLinear<string>()
      .domain([0, 1])
      .range(['#f0e6ea', '#d65d7a'])
      .interpolate(d3.interpolateRgb);

    // Prepare data for visualization
    const heatmapData: HeatmapDataPoint[] = [];
    data.data.forEach((metricData) => {
      data.channels.forEach((channel) => {
        const cellData = metricData.values[channel];
        heatmapData.push({
          metric: metricData.metric,
          channel: channel,
          value: cellData?.value ?? 0,
          intensity: cellData?.intensity ?? 0,
          formattedValue: formatValue(cellData?.value ?? 0, metricData.metric),
        });
      });
    });

    // Create the heatmap cells
    svg
      .selectAll('.heatmap-cell')
      .data(heatmapData)
      .enter()
      .append('rect')
      .attr('class', 'heatmap-cell')
      .attr('x', (d) => xScale(d.channel) ?? 0)
      .attr('y', (d) => yScale(d.metric) ?? 0)
      .attr('width', xScale.bandwidth())
      .attr('height', yScale.bandwidth())
      .attr('fill', (d) => colorScale(d.intensity))
      .attr('rx', 2)
      .attr('ry', 2);

    // Add text labels to cells
    svg
      .selectAll('.cell-text')
      .data(heatmapData)
      .enter()
      .append('text')
      .attr('class', 'cell-text')
      .attr('x', (d) => (xScale(d.channel) ?? 0) + xScale.bandwidth() / 2)
      .attr('y', (d) => (yScale(d.metric) ?? 0) + yScale.bandwidth() / 2)
      .attr('text-anchor', 'middle')
      .attr('dominant-baseline', 'middle')
      .attr('font-size', '12px')
      .attr('font-weight', '500')
      .attr('fill', (d) => (d.intensity > 0.6 ? 'white' : 'black'))
      .text((d) => d.formattedValue);

    // Add channel names (column headers)
    svg
      .selectAll('.channel-label')
      .data(data.channels)
      .enter()
      .append('text')
      .attr('class', 'channel-label')
      .attr('x', (d) => (xScale(d) ?? 0) + xScale.bandwidth() / 2)
      .attr('y', margin.top / 2 - 10)
      .attr('text-anchor', 'middle')
      .attr('dominant-baseline', 'middle')
      .attr('font-size', '12px')
      .attr('font-weight', 'bold')
      .each(function (d) {
        const text = d3.select(this);
        const words = d.split(/\s+/);
        text.text('');

        words.forEach((word, i) => {
          const tspan = text
            .append('tspan')
            .text(word)
            .attr('x', (xScale(d) ?? 0) + xScale.bandwidth() / 2)
            .attr('dy', i ? '1.2em' : 0);
        });
      });

    // Add metric names (row labels)
    svg
      .selectAll('.metric-label')
      .data(data.metrics)
      .enter()
      .append('text')
      .attr('class', 'metric-label')
      .attr('x', margin.left / 2)
      .attr('y', (d) => (yScale(d) ?? 0) + yScale.bandwidth() / 2)
      .attr('text-anchor', 'middle')
      .attr('dominant-baseline', 'middle')
      .attr('font-size', '13px')
      .attr('font-weight', 'bold')
      .text((d) => d);

    // Add gridlines
    svg
      .selectAll('.grid-line-h')
      .data(data.metrics)
      .enter()
      .append('line')
      .attr('class', 'grid-line-h')
      .attr('x1', margin.left - 5)
      .attr('y1', (d) => yScale(d) ?? 0)
      .attr('x2', svgWidth - margin.right)
      .attr('y2', (d) => yScale(d) ?? 0)
      .attr('stroke', '#e5e7eb')
      .attr('stroke-width', 1);

    svg
      .append('line')
      .attr('x1', margin.left - 5)
      .attr('y1', svgHeight - margin.bottom)
      .attr('x2', svgWidth - margin.right)
      .attr('y2', svgHeight - margin.bottom)
      .attr('stroke', '#e5e7eb')
      .attr('stroke-width', 1);

    svg
      .selectAll('.grid-line-v')
      .data(data.channels)
      .enter()
      .append('line')
      .attr('class', 'grid-line-v')
      .attr('x1', (d) => xScale(d) ?? 0)
      .attr('y1', margin.top - 5)
      .attr('x2', (d) => xScale(d) ?? 0)
      .attr('y2', svgHeight - margin.bottom)
      .attr('stroke', '#e5e7eb')
      .attr('stroke-width', 1);

    svg
      .append('line')
      .attr('x1', svgWidth - margin.right)
      .attr('y1', margin.top - 5)
      .attr('x2', svgWidth - margin.right)
      .attr('y2', svgHeight - margin.bottom)
      .attr('stroke', '#e5e7eb')
      .attr('stroke-width', 1);
  }, [data]);

  if (isLoading) {
    return (
      <Card>
        <CardContent className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="border-red-200">
        <CardContent className="pt-6 text-red-700">
          <p className="font-medium">Error loading heatmap data</p>
          <p className="text-sm">{error.message}</p>
        </CardContent>
      </Card>
    );
  }

  if (!data?.channels?.length || !data?.metrics?.length) {
    return (
      <Card>
        <CardContent className="pt-6 text-center text-gray-500">
          No data available for cost metrics heatmap
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Cost Metrics by Channel</CardTitle>
        <CardDescription>
          {data.time_range?.from_ &&
            data.time_range?.to &&
            `Data from ${data.time_range.from_} to ${data.time_range.to}`}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <svg ref={svgRef} className="heatmap w-full" />
      </CardContent>
      <CardFooter>
        <small>Color intensity indicates relative cost (darker = higher cost)</small>
      </CardFooter>
    </Card>
  );
}
