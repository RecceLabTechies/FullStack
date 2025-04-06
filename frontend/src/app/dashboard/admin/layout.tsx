import { type Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Admin Dashboard',
  description: 'Manage staff members, permissions, and system settings in the admin dashboard.',
  keywords: [
    'admin panel',
    'user management',
    'permissions',
    'system settings',
    'role management',
    'access control',
  ],
  robots: {
    index: false,
    follow: false,
  },
};

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
