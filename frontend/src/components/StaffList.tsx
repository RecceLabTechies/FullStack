"use client";

import { useState } from "react";
import StaffCard from "./StaffCard";

interface Permissions {
  reportGeneration: boolean;
  chartViewing: boolean;
}

interface StaffMember {
  id: number;
  name: string;
  role: string;
  permissions: Permissions;
}

// Mock data for staff members
const mockStaffMembers: StaffMember[] = [
  {
    id: 1,
    name: "John Doe",
    role: "Developer",
    permissions: { reportGeneration: true, chartViewing: false },
  },
  {
    id: 2,
    name: "Jane Smith",
    role: "Designer",
    permissions: { reportGeneration: false, chartViewing: true },
  },
  {
    id: 3,
    name: "Bob Johnson",
    role: "Manager",
    permissions: { reportGeneration: true, chartViewing: true },
  },
];

export default function StaffList() {
  const [staffMembers, setStaffMembers] =
    useState<StaffMember[]>(mockStaffMembers);

  const updateStaffMember = (id: number, updatedPermissions: Permissions) => {
    setStaffMembers(
      staffMembers.map((staff) =>
        staff.id === id ? { ...staff, permissions: updatedPermissions } : staff,
      ),
    );
  };

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {staffMembers.map((staff) => (
        <StaffCard
          key={staff.id}
          staff={staff}
          updatePermissions={updateStaffMember}
        />
      ))}
    </div>
  );
}
