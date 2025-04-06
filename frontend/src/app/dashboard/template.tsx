import { type Metadata } from 'next';

export const metadata: Metadata = {
  title: {
    default: 'Dashboard',
    template: '%s | RecceLabs LLM Dashboard',
  },
  description: 'View and manage your business analytics and data.',
  keywords: [
    'analytics dashboard',
    'business data',
    'performance metrics',
    'data insights',
    'AI analytics',
  ],
  openGraph: {
    title: 'RecceLabs Dashboard',
    description: 'Your centralized business analytics platform',
    type: 'website',
  },
};

export default function DashboardTemplate({ children }: { children: React.ReactNode }) {
  return children;
}
