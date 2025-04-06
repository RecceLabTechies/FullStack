import { type Metadata } from 'next';

export const metadata: Metadata = {
  title: 'AI Report Generator',
  description:
    'Generate, customize, and export AI-powered reports with interactive charts and data visualizations.',
  keywords: [
    'report generator',
    'AI reports',
    'data visualization',
    'marketing analytics',
    'custom reports',
    'interactive charts',
  ],
  openGraph: {
    title: 'AI Report Generator | RecceLabs',
    description: 'Create customized marketing reports powered by advanced AI',
    type: 'website',
  },
};

export default function ReportLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
