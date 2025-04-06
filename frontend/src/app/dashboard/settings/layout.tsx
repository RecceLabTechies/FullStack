import { type Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Settings',
  description: 'Manage your account settings, billing, and usage limits.',
  keywords: [
    'account settings',
    'user preferences',
    'billing management',
    'subscription',
    'profile settings',
    'API keys',
  ],
  robots: {
    index: false,
  },
};

export default function SettingsLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
