import { useEffect, useState } from 'react';

import { Info, PlayCircle } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardTitle } from '@/components/ui/card';
import { HoverCard, HoverCardContent, HoverCardTrigger } from '@/components/ui/hover-card';
import { Slider } from '@/components/ui/slider';

import { useProphetPipelineStatus, useProphetPipelineTrigger } from '@/hooks/use-backend-api';

export function CardMLTrigger() {
  const [forecastMonths, setForecastMonths] = useState(4);
  const {
    data: statusData,
    error: statusError,
    isLoading: isStatusLoading,
    checkStatus,
  } = useProphetPipelineStatus();
  const {
    error: triggerError,
    isLoading: isTriggerLoading,
    triggerPipeline,
  } = useProphetPipelineTrigger();

  // Function to handle pipeline trigger
  const handleTriggerPipeline = async () => {
    await triggerPipeline(forecastMonths);
    await checkStatus();
  };

  // Effect for polling status when needed
  useEffect(() => {
    // Check status immediately on mount
    void checkStatus();

    // Set up polling if status is in_progress or started
    if (statusData?.status === 'in_progress' || statusData?.status === 'started') {
      const intervalId = setInterval(() => {
        void checkStatus();
      }, 5000); // Poll every 5 seconds

      // Cleanup interval on unmount or when polling should stop
      return () => clearInterval(intervalId);
    }
  }, [checkStatus, statusData?.status]); // Only depend on the status value

  // Determine status display
  const getStatusDisplay = () => {
    if (isStatusLoading) {
      return <p className="text-muted-foreground">Checking status...</p>;
    }

    if (statusError) {
      return <p className="text-destructive">Error checking status</p>;
    }

    if (!statusData) {
      return <p className="text-muted-foreground">No status available</p>;
    }

    switch (statusData.status) {
      case 'in_progress':
        return <p className="text-blue-500">Prediction in progress...</p>;
      case 'started':
        return <p className="text-blue-500">Starting prediction...</p>;
      case 'success':
        return <p className="text-green-500">Prediction completed</p>;
      case 'error':
        return <p className="text-destructive">Error: {statusData.message}</p>;
      case 'idle':
        return <p className="text-muted-foreground">Ready to start prediction</p>;
      default:
        return <p className="text-muted-foreground">Unknown status</p>;
    }
  };

  return (
    <Card>
      <CardContent className="pt-6 flex flex-col gap-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="rounded-full bg-secondary p-3">
              <PlayCircle className="h-6 w-6" />
            </div>
            <CardTitle>Prophet ML</CardTitle>
          </div>
          <HoverCard>
            <HoverCardTrigger asChild>
              <Info className="h-4 w-4 text-muted-foreground cursor-help" />
            </HoverCardTrigger>
            <HoverCardContent className="w-80">
              <div className="space-y-2">
                <h4 className="text-sm font-semibold">Prophet ML Model</h4>
                <p className="text-sm text-muted-foreground">
                  This triggers Facebook&apos;s Prophet machine learning model to analyze your
                  historical advertising data and generate predictions for future revenue, ad spend,
                  and ROI. The model identifies patterns and trends to help optimize your
                  advertising strategy.
                </p>
              </div>
            </HoverCardContent>
          </HoverCard>
        </div>
        <div className="flex flex-col gap-2">
          <div className="flex items-center justify-between">
            <div className="text-sm text-muted-foreground">
              Forecast duration: {forecastMonths} month{forecastMonths > 1 ? 's' : ''}
            </div>
            <HoverCard>
              <HoverCardTrigger asChild>
                <Info className="h-4 w-4 text-muted-foreground cursor-help" />
              </HoverCardTrigger>
              <HoverCardContent className="w-80">
                <p className="text-sm text-muted-foreground">
                  Select how many months into the future you want the prediction to forecast.
                  Longer ranges may take more time to calculate.
                </p>
              </HoverCardContent>
            </HoverCard>
          </div>
          <Slider
            min={1}
            max={12}
            step={1}
            value={[forecastMonths]}
            onValueChange={(value) => setForecastMonths(value[0] ?? 4)}
          />
          <div className="text-sm text-muted-foreground mt-1">{getStatusDisplay()}</div>
          <Button
            onClick={handleTriggerPipeline}
            disabled={
              isTriggerLoading ||
              isStatusLoading ||
              statusData?.status === 'in_progress' ||
              statusData?.status === 'started'
            }
          >
            <PlayCircle className="mr-2 h-4 w-4" />
            Run Prediction
          </Button>

          {triggerError && (
            <div className="text-sm text-destructive">
              Error triggering pipeline: {triggerError.message}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
