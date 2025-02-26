"use client";

import { useState } from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import * as z from "zod";
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
import { Textarea } from "@/components/ui/textarea";
import { Separator } from "@/components/ui/separator";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";

const settingsFormSchema = z.object({
  name: z.string().min(2, {
    message: "Name must be at least 2 characters.",
  }),
  email: z.string().email({
    message: "Please enter a valid email address.",
  }),
  bio: z.string().max(160).optional(),
  cardNumber: z.string().regex(/^\d{16}$/, {
    message: "Card number must be 16 digits.",
  }),
  expiryDate: z.string().regex(/^\d{2}\/\d{2}$/, {
    message: "Expiry date must be in MM/YY format.",
  }),
  cvc: z.string().regex(/^\d{3}$/, {
    message: "CVC must be 3 digits.",
  }),
  zip: z.string().regex(/^\d{5}$/, {
    message: "ZIP code must be 5 digits.",
  }),
});

type SettingsFormValues = z.infer<typeof settingsFormSchema>;

const defaultValues: Partial<SettingsFormValues> = {
  name: "",
  email: "",
  bio: "",
  cardNumber: "",
  expiryDate: "",
  cvc: "",
  zip: "",
};

export default function SettingsPage() {
  const [currentPlan, setCurrentPlan] = useState("pro");

  const form = useForm<SettingsFormValues>({
    resolver: zodResolver(settingsFormSchema),
    defaultValues,
  });

  function onSubmit(data: SettingsFormValues) {
    console.log(data);
    // TODO: Implement the actual update logic
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6 p-10 pb-16">
      <div className="space-y-0.5">
        <h2 className="text-2xl font-bold tracking-tight">Settings</h2>
        <p className="text-muted-foreground">
          Manage your account settings, billing information, and view your usage
          limits.
        </p>
      </div>
      <Separator className="my-6" />

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
          {/* General Settings */}
          <div className="space-y-6">
            <h3 className="text-lg font-medium">General</h3>
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Name</FormLabel>
                  <FormControl>
                    <Input placeholder="Your name" {...field} />
                  </FormControl>
                  <FormDescription>
                    This is your public display name.
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
                    You can manage verified email addresses in your email
                    settings.
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="bio"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Bio</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="Tell us a little bit about yourself"
                      className="resize-none"
                      {...field}
                    />
                  </FormControl>
                  <FormDescription>
                    Brief description for your profile. URLs are hyperlinked.
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
          </div>

          <Separator />

          {/* Billing Settings */}
          <div className="space-y-6">
            <h3 className="text-lg font-medium">Billing</h3>
            <Card>
              <CardHeader>
                <CardTitle>Current Plan</CardTitle>
                <CardDescription>
                  You are currently on the{" "}
                  {currentPlan.charAt(0).toUpperCase() + currentPlan.slice(1)}{" "}
                  plan.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span>Plan</span>
                    <span className="font-medium">
                      {currentPlan.charAt(0).toUpperCase() +
                        currentPlan.slice(1)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Price</span>
                    <span className="font-medium">$19.99 / month</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Billing Cycle</span>
                    <span className="font-medium">Monthly</span>
                  </div>
                </div>
              </CardContent>
            </Card>
            <div className="space-y-4">
              <FormField
                control={form.control}
                name="cardNumber"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Card Number</FormLabel>
                    <FormControl>
                      <Input placeholder="1234 5678 9012 3456" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <div className="grid grid-cols-3 gap-4">
                <FormField
                  control={form.control}
                  name="expiryDate"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Expiry Date</FormLabel>
                      <FormControl>
                        <Input placeholder="MM/YY" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="cvc"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>CVC</FormLabel>
                      <FormControl>
                        <Input placeholder="123" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="zip"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>ZIP</FormLabel>
                      <FormControl>
                        <Input placeholder="12345" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
            </div>
          </div>

          <Separator />

          {/* Limits */}
          <div className="space-y-6">
            <h3 className="text-lg font-medium">Limits</h3>
            <div className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>API Requests</CardTitle>
                  <CardDescription>Monthly API request limit</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>15,000 / 20,000 requests</span>
                      <span className="text-muted-foreground">75% used</span>
                    </div>
                    <Progress value={75} />
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle>Storage</CardTitle>
                  <CardDescription>Total storage space used</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>7.5 GB / 10 GB</span>
                      <span className="text-muted-foreground">75% used</span>
                    </div>
                    <Progress value={75} />
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle>Team Members</CardTitle>
                  <CardDescription>
                    Number of team members in your account
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>3 / 5 members</span>
                      <span className="text-muted-foreground">60% used</span>
                    </div>
                    <Progress value={60} />
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>

          <Button type="submit">Save Changes</Button>
        </form>
      </Form>
    </div>
  );
}
