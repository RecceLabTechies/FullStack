'use client';

import { useEffect } from 'react';

import { Banknote } from 'lucide-react';

import { Card, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';

import { useLatestMonthROI } from '@/hooks/use-backend-api';

export function MetricsROICard() {
  const { data, isLoading, error, fetchLatestMonthROI } = useLatestMonthROI();

  useEffect(() => {
    void fetchLatestMonthROI();
  }, [fetchLatestMonthROI]);

  const formatROI = (value: number) => {
    return `${value.toFixed(1)}%`;
  };

  const getMonthName = (month: number) => {
    return new Intl.DateTimeFormat('en-US', { month: 'long' }).format(new Date(2024, month - 1));
  };

  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex items-center gap-4">
          <div className="rounded-full bg-secondary p-3">
            <Banknote className="h-6 w-6" />
          </div>
        </div>
        <div className="mt-4">
          {isLoading ? (
            <Skeleton className="h-8 w-32" />
          ) : error ? (
            <div className="text-sm text-destructive">Failed to load ROI data</div>
          ) : (
            <>
              <h2 className="text-3xl font-bold">{formatROI(data?.roi ?? 0)}</h2>
              <p className="text-sm text-muted-foreground mt-1">
                ROI {data ? `${getMonthName(data.month)} ${data.year}` : ''}
              </p>
            </>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
