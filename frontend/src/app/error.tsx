'use client';

import { useEffect } from 'react';

import { RefreshCcw } from 'lucide-react';

import { Button } from '@/components/ui/button';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log the error to an error reporting service
    console.error(error);
  }, [error]);

  return (
    <main
      className="flex min-h-screen flex-col items-center justify-center bg-muted/40 p-8 text-center"
      role="alert"
      aria-labelledby="error-heading"
    >
      <div className="space-y-6">
        <h1 className="text-6xl font-bold" id="error-heading">
          500
        </h1>
        <h2 className="text-2xl font-semibold">Something went wrong</h2>
        <p className="mx-auto max-w-md text-muted-foreground">
          We&apos;ve encountered an unexpected error.
        </p>
        <Button onClick={reset} className="inline-flex items-center gap-2" aria-label="Try again">
          <RefreshCcw className="h-4 w-4" aria-hidden="true" />
          Try again
        </Button>
      </div>
    </main>
  );
}
