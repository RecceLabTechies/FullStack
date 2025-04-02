'use client';

import { useEffect, useState } from 'react';

import { useRouter } from 'next/navigation';

import { type UserData } from '@/types/types';

import AdminPage from '@/components/admin-page';

export default function Page() {
  const router = useRouter();
  const [user, setUser] = useState<UserData | null>(null);

  useEffect(() => {
    const storedUser = localStorage.getItem('user');
    if (!storedUser) {
      router.push('/login');
    } else {
      setUser(JSON.parse(storedUser) as UserData);
    }
  }, [router]);

  if (!user) return <p>Redirecting...</p>;

  return <AdminPage />;
}
