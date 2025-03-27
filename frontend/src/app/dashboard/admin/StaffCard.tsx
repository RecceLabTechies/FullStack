"use client";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
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
import { useEffect, useState } from "react";

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
  updatePermissions: (username: string, permissions: StaffPermissions) => void;
}

function ClientSideContent({
  permissions,
  handlePermissionChange,
}: {
  permissions: StaffPermissions;
  handlePermissionChange: (permission: keyof StaffPermissions) => void;
}) {
  return (
    <TooltipProvider>
      <div className="flex items-center justify-between">
        <Tooltip>
          <TooltipTrigger>Report Generation</TooltipTrigger>
          <TooltipContent>
            <p>Allow user to generate reports</p>
          </TooltipContent>
        </Tooltip>
        <Switch
          checked={permissions.reportGeneration}
          onCheckedChange={() => handlePermissionChange("reportGeneration")}
        />
      </div>
      <div className="flex items-center justify-between">
        <Tooltip>
          <TooltipTrigger>Chart Viewing</TooltipTrigger>
          <TooltipContent>
            <p>Allow user to view charts</p>
          </TooltipContent>
        </Tooltip>
        <Switch
          checked={permissions.chartViewing}
          onCheckedChange={() => handlePermissionChange("chartViewing")}
        />
      </div>
      <div className="flex items-center justify-between">
        <Tooltip>
          <TooltipTrigger>User Management</TooltipTrigger>
          <TooltipContent>
            <p>Allow user to manage other users</p>
          </TooltipContent>
        </Tooltip>
        <Switch
          checked={permissions.userManagement}
          onCheckedChange={() => handlePermissionChange("userManagement")}
        />
      </div>
    </TooltipProvider>
  );
}

export default function StaffCard({
  staff,
  updatePermissions,
}: StaffCardProps) {
  const [mounted, setMounted] = useState(false);
  const [permissions, setPermissions] = useState<StaffPermissions>(
    staff.permissions,
  );
  const [isDirty, setIsDirty] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (mounted) {
      setPermissions(staff.permissions);
    }
  }, [staff.permissions, mounted]);

  const handlePermissionChange = (permission: keyof StaffPermissions) => {
    setPermissions((prev) => {
      const newPermissions = { ...prev, [permission]: !prev[permission] };
      setIsDirty(true);
      return newPermissions;
    });
  };

  const handleSave = () => {
    updatePermissions(staff.username, permissions);
    setIsDirty(false);
  };

  return (
    <article>
      <Card>
        <CardHeader>
          <CardTitle>{staff.name}</CardTitle>
          <CardDescription>{staff.role}</CardDescription>
        </CardHeader>
        <CardContent>
          <section className="space-y-4">
            {mounted ? (
              <ClientSideContent
                permissions={permissions}
                handlePermissionChange={handlePermissionChange}
              />
            ) : (
              <div>Loading permissions...</div>
            )}
          </section>
        </CardContent>
        <CardFooter>
          <Button onClick={handleSave} disabled={!isDirty}>
            Save Changes
          </Button>
        </CardFooter>
      </Card>
    </article>
  );
}
