'use client';

import { useEffect } from 'react';

import { useDatabaseOperations } from '@/context/database-operations-context';
import { Banknote, Info } from 'lucide-react';

import { Card, CardContent } from '@/components/ui/card';
import { HoverCard, HoverCardContent, HoverCardTrigger } from '@/components/ui/hover-card';
import { Skeleton } from '@/components/ui/skeleton';

import { useLatestMonthROI } from '@/hooks/use-backend-api';

export function MetricsROICard() {
  const { data, isLoading, error, fetchLatestMonthROI } = useLatestMonthROI();
  const { lastUpdated } = useDatabaseOperations();

  useEffect(() => {
    void fetchLatestMonthROI();
  }, [fetchLatestMonthROI, lastUpdated]);

  const formatROI = (value: number) => {
    return `${value.toFixed(1)}%`;
  };

  const getMonthName = (month: number) => {
    return new Intl.DateTimeFormat('en-US', { month: 'long' }).format(new Date(2024, month - 1));
  };

  return (
    <Card aria-labelledby="roi-title">
      <CardContent className="pt-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="rounded-full bg-secondary p-3">
              <Banknote className="h-6 w-6" aria-hidden="true" />
            </div>
          </div>
          <HoverCard>
            <HoverCardTrigger asChild>
              <Info
                className="h-4 w-4 text-muted-foreground cursor-help"
                aria-label="ROI information"
              />
            </HoverCardTrigger>
            <HoverCardContent className="w-80">
              <div className="space-y-2">
                <h4 className="text-sm font-semibold">Return on Investment (ROI)</h4>
                <p className="text-sm text-muted-foreground">
                  ROI measures the profitability of your advertising spend. It is calculated as:
                  ((Revenue - Ad Spend) / Ad Spend) × 100. A positive ROI indicates that your
                  advertising revenue exceeds your costs.
                </p>
              </div>
            </HoverCardContent>
          </HoverCard>
        </div>
        <div className="mt-4">
          {isLoading ? (
            <Skeleton className="h-8 w-32" aria-label="Loading ROI data" />
          ) : error ? (
            <div className="text-sm text-destructive" role="alert">
              Failed to load ROI data
            </div>
          ) : (
            <>
              <h2 id="roi-title" className="text-3xl font-bold">
                {formatROI(data?.roi ?? 0)}
              </h2>
              <p className="text-sm text-muted-foreground mt-1">
                ROI {data?.month && data?.year ? `${getMonthName(data.month)} ${data.year}` : ''}
              </p>
            </>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
