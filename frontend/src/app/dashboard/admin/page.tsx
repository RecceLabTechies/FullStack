"use client";

import AdminPage from "@/components/admin-page";
import { type UserData } from "@/types/types";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

export default function Page() {
  const router = useRouter();
  const [user, setUser] = useState<UserData | null>(null);

  useEffect(() => {
    const storedUser = localStorage.getItem("user");
    if (!storedUser) {
      router.push("/login");
    } else {
      setUser(JSON.parse(storedUser) as UserData);
    }
  }, [router]);

  if (!user) return <p>Redirecting...</p>;

  return <AdminPage />;
}
