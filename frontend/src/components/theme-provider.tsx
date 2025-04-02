/**
 * Theme Provider Component Module
 * Provides theme management functionality using next-themes,
 * with support for system theme, light/dark modes, and SSR.
 */

'use client';

import * as React from 'react';

import { ThemeProvider as NextThemesProvider, type ThemeProviderProps } from 'next-themes';

/**
 * Theme Provider Component Module
 * Provides theme management functionality using next-themes,
 * with support for system theme, light/dark modes, and SSR.
 */

/**
 * ThemeProvider Component
 * A wrapper around next-themes provider with additional hydration handling
 *
 * Features:
 * - SSR compatibility with hydration handling
 * - System theme detection
 * - Light/dark theme support
 * - Smooth theme transitions
 * - Class-based theme application
 *
 * Default Configuration:
 * - Uses 'class' attribute for theme application
 * - Default theme set to 'light'
 * - System theme detection enabled
 * - Theme transitions disabled on change to prevent flicker
 *
 * @param {ThemeProviderProps} props - Component props from next-themes
 * @param {React.ReactNode} props.children - Child components to be themed
 * @returns JSX.Element - Theme provider wrapper
 */
export function ThemeProvider({ children, ...props }: ThemeProviderProps) {
  // State to track component hydration
  const [mounted, setMounted] = React.useState(false);

  // Effect to handle hydration
  React.useEffect(() => {
    setMounted(true);
  }, []);

  // Return children without theme context during SSR
  if (!mounted) {
    return <>{children}</>;
  }

  return (
    <NextThemesProvider
      attribute="class"
      defaultTheme="light"
      enableSystem
      disableTransitionOnChange
      {...props}
    >
      {children}
    </NextThemesProvider>
  );
}
