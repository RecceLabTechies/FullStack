"use client";

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
import { Toaster } from "sonner";
import SearchBar from "./admin-search-bar";
import StaffList from "./admin-staff-list";
import { useUsers } from "@/hooks/use-backend-api";
import CreateUserModal from "./admin-create-user-modal";

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
  const [filteredUsers, setFilteredUsers] = useState<UserData[] | null>(null);
  const [currentUser, setCurrentUser] = useState<UserData | null>(null);
  const { data: users, isLoading, error, fetchUsers } = useUsers();

  useEffect(() => {
    // Get current user from localStorage
    const userStr = localStorage.getItem("user");
    if (userStr) {
      const user = JSON.parse(userStr) as UserData;
      setCurrentUser(user);
    }
  }, []);

  useEffect(() => {
    if (currentUser) {
      void fetchUsers();
    }
  }, [currentUser, fetchUsers]);

  useEffect(() => {
    if (!users) return;

    // Filter users based on role hierarchy
    const filtered = Array.isArray(users)
      ? users.filter((user) => {
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
        })
      : [];

    setFilteredUsers(filtered);
  }, [users, currentUser]);

  const handleSearch = (searchTerm: string) => {
    if (!users || !Array.isArray(users)) return;

    if (!searchTerm.trim()) {
      setFilteredUsers(
        users.filter((user) => {
          if (user.email === currentUser?.email) return false;
          const currentUserRole = currentUser?.role.toLowerCase() ?? "";
          const userRole = user.role.toLowerCase();
          if (currentUserRole === "root") return true;
          if (currentUserRole === "admin") return userRole === "user";
          return false;
        }),
      );
      return;
    }

    const filtered = users.filter(
      (user) =>
        (user.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
          user.role.toLowerCase().includes(searchTerm.toLowerCase())) &&
        user.email !== currentUser?.email &&
        (currentUser?.role.toLowerCase() === "root" ||
          (currentUser?.role.toLowerCase() === "admin" &&
            user.role.toLowerCase() === "user")),
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
      <Toaster richColors position="top-right" />
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Staff Management</CardTitle>
              <CardDescription>
                Manage your team&apos;s permissions and access
              </CardDescription>
            </div>
            <CreateUserModal />
          </div>
        </CardHeader>
        <CardContent>
          <SearchBar onSearch={handleSearch} />
          {isLoading ? (
            <SkeletonStaffList />
          ) : error ? (
            <div className="text-destructive" role="alert">
              {error.message}
            </div>
          ) : (
            filteredUsers && <StaffList users={filteredUsers} />
          )}
        </CardContent>
      </Card>
    </section>
  );
}
