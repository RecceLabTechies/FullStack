import { type Metadata } from 'next';

export const metadata: Metadata = {
  title: 'MongoDB Manager',
  description: 'Manage and view your MongoDB database structure, collections, and upload CSV data.',
};

export default function MongoManagerLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
