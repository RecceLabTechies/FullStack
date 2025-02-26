import type { Metadata } from "next";
import AdminPage from "@/app/dashboard/admin/AdminPage";

export const metadata: Metadata = {
  title: "Staff Management | Admin Dashboard",
  description: "Manage your staff members and their permissions",
};

export default function Page() {
  return <AdminPage />;
}
