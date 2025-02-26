"use client";

import { useState, useEffect } from "react";
import StaffCard from "./StaffCard";
import { User } from "@/api/dbApi";

interface Permissions {
  reportGeneration: boolean;
  chartViewing: boolean;
  userManagement: boolean;
}

interface StaffMember {
  id: number;
  name: string;
  role: string;
  permissions: Permissions;
}

interface StaffListProps {
  users: User[];
}

export default function StaffList({ users }: StaffListProps) {
  const [staffMembers, setStaffMembers] = useState<StaffMember[]>([]);

  useEffect(() => {
    setStaffMembers(
      users.map((user, index) => ({
        id: index,
        name: user.username,
        role: user.role,
        permissions: {
          reportGeneration: user.report_generation_access,
          chartViewing: user.chart_access,
          userManagement: user.user_management_access,
        },
      })),
    );
  }, [users]);

  const updateStaffMember = (id: number, updatedPermissions: Permissions) => {
    setStaffMembers((prevStaffMembers) =>
      prevStaffMembers.map((staff) =>
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
