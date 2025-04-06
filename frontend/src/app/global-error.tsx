'use client';

import { useEffect } from 'react';

import { RefreshCcw } from 'lucide-react';

import { ThemeProvider } from '@/components/theme-provider';
import { Button } from '@/components/ui/button';

export default function GlobalError({
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
    <html lang="en" suppressHydrationWarning>
      <body>
        <ThemeProvider
          attribute="class"
          defaultTheme="light"
          enableSystem
          disableTransitionOnChange
        >
          <main className="flex min-h-screen flex-col items-center justify-center bg-muted/40 p-8 text-center">
            <div className="space-y-6">
              <h1 className="text-6xl font-bold">Oops!</h1>
              <h2 className="text-2xl font-semibold">Critical Error</h2>
              <p className="mx-auto max-w-md text-muted-foreground">
                We&apos;ve encountered a critical error that prevents the app from running properly.
              </p>
              <Button onClick={reset} className="inline-flex items-center gap-2">
                <RefreshCcw className="h-4 w-4" />
                Try again
              </Button>
            </div>
          </main>
        </ThemeProvider>
      </body>
    </html>
  );
}
