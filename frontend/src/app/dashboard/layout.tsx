import { type Metadata } from 'next';

import { DashboardLayoutContent } from '@/components/dashboard-layout';

export const metadata: Metadata = {
  title: {
    default: 'Dashboard',
    template: '%s | RecceLabs LLM Dashboard',
  },
  description: 'View and manage your business analytics and data.',
};

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return <DashboardLayoutContent>{children}</DashboardLayoutContent>;
}
