import { Suspense } from "react";
import StaffList from "./StaffList";
import SearchBar from "./SearchBar";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export default function AdminPage() {
  return (
    <div className="container mx-auto p-4">
      <Card>
        <CardHeader>
          <CardTitle>Staff Management</CardTitle>
          <CardDescription>
            Manage your team&apos;s permissions and access
          </CardDescription>
        </CardHeader>
        <CardContent>
          <SearchBar />
          <Suspense fallback={<div>Loading staff list...</div>}>
            <StaffList />
          </Suspense>
        </CardContent>
      </Card>
    </div>
  );
}
