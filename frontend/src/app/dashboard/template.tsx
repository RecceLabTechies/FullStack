import { type Metadata } from 'next';

export const metadata: Metadata = {
  title: {
    default: 'Dashboard',
    template: '%s | RecceLabs LLM Dashboard',
  },
  description: 'View and manage your business analytics and data.',
};

export default function DashboardTemplate({ children }: { children: React.ReactNode }) {
  return children;
}
