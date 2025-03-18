"use client";

import { type User } from "@/api/dbApi";
import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { Switch } from "@/components/ui/switch";
import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import * as z from "zod";

const settingsFormSchema = z.object({
  username: z.string().min(2, {
    message: "Username must be at least 2 characters.",
  }),
  email: z.string().email({
    message: "Please enter a valid email address.",
  }),
  company: z.string().min(1, {
    message: "Company name is required.",
  }),
  role: z.string(),
  chart_access: z.boolean(),
  report_generation_access: z.boolean(),
  user_management_access: z.boolean(),
});

type SettingsFormValues = z.infer<typeof settingsFormSchema>;

const defaultValues: Partial<SettingsFormValues> = {
  username: "",
  email: "",
  company: "",
  role: "",
  chart_access: false,
  report_generation_access: false,
  user_management_access: false,
};

export default function SettingsPage() {
  const [currentPlan] = useState("pro");

  const form = useForm<SettingsFormValues>({
    resolver: zodResolver(settingsFormSchema),
    defaultValues,
  });

  useEffect(() => {
    const userStr = localStorage.getItem("user");
    if (userStr) {
      const user = JSON.parse(userStr) as User;
      form.reset({
        username: user.username,
        email: user.email,
        company: user.company,
        role: user.role,
        chart_access: user.chart_access,
        report_generation_access: user.report_generation_access,
        user_management_access: user.user_management_access,
      });
    }
  }, [form]);

  function onSubmit(data: SettingsFormValues) {
    // Update localStorage with new user data
    const userStr = localStorage.getItem("user");
    if (userStr) {
      const user = JSON.parse(userStr) as User;
      const updatedUser = {
        ...user,
        ...data,
      };
      localStorage.setItem("user", JSON.stringify(updatedUser));
      // TODO: Implement API call to update user data on the server
    }
  }

  return (
    <main className="container mx-auto max-w-2xl space-y-6 p-4 pb-16">
      <header className="space-y-0.5">
        <h1 className="text-2xl font-bold tracking-tight">Settings</h1>
        <p className="text-muted-foreground">
          Manage your account settings and permissions.
        </p>
      </header>
      <Separator className="my-6" />

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
          {/* General Settings */}
          <section className="space-y-6">
            <h2 className="text-lg font-medium">General</h2>
            <FormField
              control={form.control}
              name="username"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Username</FormLabel>
                  <FormControl>
                    <Input placeholder="Your username" {...field} />
                  </FormControl>
                  <FormDescription>
                    This is your display username.
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="email"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Email</FormLabel>
                  <FormControl>
                    <Input placeholder="Your email" {...field} />
                  </FormControl>
                  <FormDescription>
                    Your registered email address.
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="company"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Company</FormLabel>
                  <FormControl>
                    <Input placeholder="Your company" {...field} />
                  </FormControl>
                  <FormDescription>The company you represent.</FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="role"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Role</FormLabel>
                  <FormControl>
                    <Input placeholder="Your role" {...field} disabled />
                  </FormControl>
                  <FormDescription>
                    Your current role in the system.
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
          </section>

          <Separator />

          {/* Access Permissions */}
          <section className="space-y-6">
            <h2 className="text-lg font-medium">Access Permissions</h2>
            <div className="space-y-4">
              <FormField
                control={form.control}
                name="chart_access"
                render={({ field }) => (
                  <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                    <div className="space-y-0.5">
                      <FormLabel className="text-base">Chart Access</FormLabel>
                      <FormDescription>
                        Access to view and analyze charts
                      </FormDescription>
                    </div>
                    <FormControl>
                      <Switch
                        checked={field.value}
                        onCheckedChange={field.onChange}
                      />
                    </FormControl>
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="report_generation_access"
                render={({ field }) => (
                  <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                    <div className="space-y-0.5">
                      <FormLabel className="text-base">
                        Report Generation
                      </FormLabel>
                      <FormDescription>
                        Access to generate reports
                      </FormDescription>
                    </div>
                    <FormControl>
                      <Switch
                        checked={field.value}
                        onCheckedChange={field.onChange}
                      />
                    </FormControl>
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="user_management_access"
                render={({ field }) => (
                  <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                    <div className="space-y-0.5">
                      <FormLabel className="text-base">
                        User Management
                      </FormLabel>
                      <FormDescription>Access to manage users</FormDescription>
                    </div>
                    <FormControl>
                      <Switch
                        checked={field.value}
                        onCheckedChange={field.onChange}
                      />
                    </FormControl>
                  </FormItem>
                )}
              />
            </div>
          </section>

          <Button type="submit">Save Changes</Button>
        </form>
      </Form>
    </main>
  );
}
