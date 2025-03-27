"use client";

import { fetchUsers } from "@/api/backendApi";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import type { UserData } from "@/types/types";
import { useEffect, useState } from "react";
import SearchBar from "./SearchBar";
import StaffList from "./StaffList";

function SkeletonStaffList() {
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {Array.from({ length: 6 }).map((_, index) => (
        <Card key={index}>
          <CardHeader>
            <Skeleton className="h-6 w-32" />
            <Skeleton className="h-4 w-24" />
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="flex items-center justify-between">
                  <Skeleton className="h-4 w-24" />
                  <Skeleton className="h-6 w-10" />
                </div>
              ))}
            </div>
          </CardContent>
          <div className="p-6 pt-0">
            <Skeleton className="h-10 w-28" />
          </div>
        </Card>
      ))}
    </div>
  );
}

export default function AdminPage() {
  const [users, setUsers] = useState<UserData[] | null>(null);
  const [filteredUsers, setFilteredUsers] = useState<UserData[] | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [currentUser, setCurrentUser] = useState<UserData | null>(null);

  useEffect(() => {
    // Get current user from localStorage
    const userStr = localStorage.getItem("user");
    if (userStr) {
      const user = JSON.parse(userStr) as UserData;
      setCurrentUser(user);
    }
  }, []);

  useEffect(() => {
    const getUsers = async () => {
      try {
        const fetchedUsers = await fetchUsers();
        if (!fetchedUsers) {
          setError("No users found.");
          return;
        }

        // Filter users based on role hierarchy
        const filteredUsers = fetchedUsers.filter((user) => {
          // Don't show current user
          if (user.email === currentUser?.email) return false;

          // Role hierarchy: root > admin > user
          const currentUserRole = currentUser?.role.toLowerCase() ?? "";
          const userRole = user.role.toLowerCase();

          // If current user is root, they can see all users
          if (currentUserRole === "root") return true;

          // If current user is admin, they can only see users with role 'user'
          if (currentUserRole === "admin") {
            return userRole === "user";
          }

          // If current user is not admin or root, they shouldn't see any users
          return false;
        });

        setUsers(filteredUsers);
        setFilteredUsers(filteredUsers);
      } catch (error) {
        setError("Failed to load users.");
        console.error(error);
      } finally {
        setLoading(false);
      }
    };

    if (currentUser) {
      void getUsers();
    }
  }, [currentUser]);

  const handleSearch = (searchTerm: string) => {
    if (!users) return;

    if (!searchTerm.trim()) {
      setFilteredUsers(users);
      return;
    }

    const filtered = users.filter(
      (user) =>
        user.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
        user.role.toLowerCase().includes(searchTerm.toLowerCase()),
    );
    setFilteredUsers(filtered);
  };

  // Don't render the page if user is not admin or root
  if (
    !currentUser ||
    (currentUser.role.toLowerCase() !== "admin" &&
      currentUser.role.toLowerCase() !== "root")
  ) {
    return (
      <section className="container mx-auto p-4">
        <Card>
          <CardHeader>
            <CardTitle>Access Denied</CardTitle>
            <CardDescription>
              You don&apos;t have permission to access this page.
            </CardDescription>
          </CardHeader>
        </Card>
      </section>
    );
  }

  return (
    <section className="container mx-auto p-4">
      <Card>
        <CardHeader>
          <CardTitle>Staff Management</CardTitle>
          <CardDescription>
            Manage your team&apos;s permissions and access
          </CardDescription>
        </CardHeader>
        <CardContent>
          <SearchBar onSearch={handleSearch} />
          {loading ? (
            <SkeletonStaffList />
          ) : error ? (
            <div className="text-destructive" role="alert">
              {error}
            </div>
          ) : (
            filteredUsers && <StaffList users={filteredUsers} />
          )}
        </CardContent>
      </Card>
    </section>
  );
}
