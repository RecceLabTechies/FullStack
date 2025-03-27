"use client";

import { patchUser } from "@/api/backendApi";
import { type UserData } from "@/types/types";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import StaffCard from "./StaffCard";

interface StaffListProps {
  users: UserData[];
}

export default function StaffList({ users }: StaffListProps) {
  const [staffMembers, setStaffMembers] = useState<UserData[]>([]);

  useEffect(() => {
    setStaffMembers(users);
  }, [users]);

  const updateStaffMember = async (
    username: string,
    permissions: {
      reportGeneration: boolean;
      chartViewing: boolean;
      userManagement: boolean;
    },
  ) => {
    const staffMember = staffMembers.find(
      (staff) => staff.username === username,
    );
    if (!staffMember) return;

    toast.loading("Updating permissions...");

    try {
      const patchData = {
        report_generation_access: permissions.reportGeneration,
        chart_access: permissions.chartViewing,
        user_management_access: permissions.userManagement,
      };

      const result = await patchUser(staffMember.username, patchData);

      if (result) {
        setStaffMembers((prevStaffMembers) =>
          prevStaffMembers.map((staff) =>
            staff.username === username
              ? {
                  ...staff,
                  report_generation_access: permissions.reportGeneration,
                  chart_access: permissions.chartViewing,
                  user_management_access: permissions.userManagement,
                }
              : staff,
          ),
        );
        toast.success("Permissions updated successfully");
      } else {
        throw new Error("Failed to update permissions");
      }
    } catch (error) {
      console.error("Error updating permissions:", error);
      toast.error("Failed to update permissions");

      // Revert local state on error
      setStaffMembers((prevStaffMembers) =>
        prevStaffMembers.map((staff) =>
          staff.username === username ? staffMember : staff,
        ),
      );
    }
  };

  return (
    <section
      className="grid gap-4 md:grid-cols-2 lg:grid-cols-3"
      aria-label="Staff members list"
    >
      {staffMembers.map((staff) => (
        <StaffCard
          key={staff.username}
          staff={{
            username: staff.username,
            name: staff.username,
            role: staff.role,
            permissions: {
              reportGeneration: staff.report_generation_access,
              chartViewing: staff.chart_access,
              userManagement: staff.user_management_access,
            },
          }}
          updatePermissions={(_, permissions) =>
            updateStaffMember(staff.username, permissions)
          }
        />
      ))}
    </section>
  );
}
