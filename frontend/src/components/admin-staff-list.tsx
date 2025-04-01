"use client";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { type UserData } from "@/types/types";
import { useEffect, useState } from "react";

interface StaffListProps {
  users: UserData[];
}

export default function StaffList({ users }: StaffListProps) {
  return (
    <section
      className="grid gap-4 md:grid-cols-2 lg:grid-cols-3"
      aria-label="Staff members list"
    >
      {users.map((staff) => (
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
        />
      ))}
    </section>
  );
}

interface StaffMember {
  username: string;
  name: string;
  role: string;
  permissions: {
    userManagement: boolean;
    reportGeneration: boolean;
    chartViewing: boolean;
  };
}

type StaffPermissions = StaffMember["permissions"];

interface StaffCardProps {
  staff: StaffMember;
}

function PermissionControls({
  permissions,
}: {
  permissions: StaffPermissions;
}) {
  const permissionItems = [
    {
      name: "Report Generation",
      description: "Allow user to generate reports",
      value: permissions.reportGeneration,
    },
    {
      name: "Chart Viewing",
      description: "Allow user to view charts",
      value: permissions.chartViewing,
    },
    {
      name: "User Management",
      description: "Allow user to manage other users",
      value: permissions.userManagement,
    },
  ];

  return (
    <TooltipProvider>
      <div className="space-y-3">
        {permissionItems.map((item) => (
          <div key={item.name} className="flex items-center justify-between">
            <Tooltip>
              <TooltipTrigger>{item.name}</TooltipTrigger>
              <TooltipContent>
                <p>{item.description}</p>
              </TooltipContent>
            </Tooltip>
            <Switch checked={item.value} disabled={true} />
          </div>
        ))}
      </div>
    </TooltipProvider>
  );
}

function StaffCard({ staff }: StaffCardProps) {
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  return (
    <article>
      <Card>
        <CardHeader>
          <CardTitle>{staff.name}</CardTitle>
          <CardDescription>{staff.role}</CardDescription>
        </CardHeader>
        <CardContent>
          <section className="space-y-4">
            {isMounted ? (
              <PermissionControls permissions={staff.permissions} />
            ) : (
              <div>Loading permissions...</div>
            )}
          </section>
        </CardContent>
      </Card>
    </article>
  );
}
