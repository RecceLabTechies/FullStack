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
  description: 'Advanced AI-powered analytics and marketing intelligence platform for businesses',
  keywords: [
    'analytics',
    'marketing',
    'AI',
    'dashboard',
    'reports',
    'LLM',
    'business intelligence',
    'data visualization',
    'marketing analytics',
    'AI reports',
  ],
  authors: [{ name: 'RecceLabs Team' }],
  creator: 'RecceLabs',
  publisher: 'RecceLabs',
  applicationName: 'RecceLabs LLM Dashboard',
  formatDetection: {
    telephone: false,
  },
  viewport: {
    width: 'device-width',
    initialScale: 1,
    maximumScale: 1,
  },
  robots: {
    index: true,
    follow: true,
  },
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
          <Toaster richColors expand={true} />
        </ThemeProvider>
      </body>
    </html>
  );
}
