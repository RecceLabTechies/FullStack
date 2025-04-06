'use client';

import Link from 'next/link';

import { ArrowLeft } from 'lucide-react';

import { Button } from '@/components/ui/button';

export default function NotFound() {
  return (
    <main
      className="flex min-h-screen flex-col items-center justify-center bg-muted/40 p-8 text-center"
      aria-labelledby="not-found-heading"
    >
      <div className="space-y-6">
        <h1 className="text-6xl font-bold" id="not-found-heading">
          404
        </h1>
        <h2 className="text-2xl font-semibold">Page Not Found</h2>
        <p className="mx-auto max-w-md text-muted-foreground">
          The page you&apos;re looking for doesn&apos;t exist or has been moved.
        </p>
        <Button asChild>
          <Link
            href="/"
            className="inline-flex items-center gap-2"
            aria-label="Navigate back to home page"
          >
            <ArrowLeft className="h-4 w-4" aria-hidden="true" />
            Back to Home
          </Link>
        </Button>
      </div>
    </main>
  );
}
