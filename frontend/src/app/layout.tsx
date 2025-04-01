import { type Metadata } from 'next';

import { GeistSans } from 'geist/font/sans';
import { Toaster } from 'sonner';

import { ThemeProvider } from '@/components/theme-provider';

import '@/styles/globals.css';

export const metadata: Metadata = {
  title: {
    default: 'RecceLabs LLM Dashboard',
    template: '%s | RecceLabs LLM Dashboard',
  },
  description: 'Powerful analytics and AI-driven reports for your marketing needs',
  keywords: [
    'analytics',
    'marketing',
    'AI',
    'dashboard',
    'reports',
    'LLM',
    'business intelligence',
  ],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={GeistSans.className}>
        <ThemeProvider
          attribute="class"
          defaultTheme="light"
          enableSystem
          disableTransitionOnChange
        >
          <div className="relative min-h-screen bg-background antialiased">{children}</div>
          <Toaster />
        </ThemeProvider>
      </body>
    </html>
  );
}
