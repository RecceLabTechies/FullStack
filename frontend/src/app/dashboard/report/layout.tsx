import { type Metadata } from 'next';

export const metadata: Metadata = {
  title: 'AI Report Generator',
  description:
    'Generate, customize, and export AI-powered reports with interactive charts and data visualizations.',
};

export default function ReportLayout({ children }: { children: React.ReactNode }) {
  return <article>{children}</article>;
}
