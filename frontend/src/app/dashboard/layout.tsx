'use client';

import { useEffect, useState } from 'react';

import { useRouter } from 'next/navigation';

import { DashboardLayoutContent } from '@/components/dashboard-layout';

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);
  const router = useRouter();

  useEffect(() => {
    // Client-side authentication check
    const checkAuth = () => {
      // Check if auth token exists in cookies
      const hasAuthCookie = document.cookie
        .split('; ')
        .some((row) => row.startsWith('auth-token='));

      // Check if user data exists in localStorage
      const userData = localStorage.getItem('user');

      if (!hasAuthCookie || !userData) {
        router.push('/');
        return;
      }

      setIsAuthenticated(true);
    };

    checkAuth();
  }, [router]);

  // Show loading state while checking authentication
  if (isAuthenticated === null) {
    return (
      <div
        className="flex h-screen w-full items-center justify-center"
        role="status"
        aria-live="polite"
      >
        <div className="text-center">
          <div
            className="h-8 w-8 animate-spin rounded-full border-b-2 border-primary"
            aria-hidden="true"
          ></div>
          <p className="mt-2">Loading...</p>
        </div>
      </div>
    );
  }

  // Show content once authenticated
  return isAuthenticated ? <DashboardLayoutContent>{children}</DashboardLayoutContent> : null;
}
