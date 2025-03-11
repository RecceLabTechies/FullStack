"use client";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
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
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { Textarea } from "@/components/ui/textarea";
import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2 } from "lucide-react";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { toast, Toaster } from "sonner";
import * as z from "zod";

const settingsFormSchema = z.object({
  name: z.string().min(2, {
    message: "Name must be at least 2 characters.",
  }),
  email: z.string().email({
    message: "Please enter a valid email address.",
  }),
  bio: z.string().max(160).optional(),
  cardNumber: z
    .string()
    .regex(/^[\d\s]{16,19}$/, {
      message: "Please enter a valid card number.",
    })
    .transform((val) => val.replace(/\s/g, "")),
  expiryDate: z.string().regex(/^\d{2}\/\d{2}$/, {
    message: "Expiry date must be in MM/YY format.",
  }),
  cvc: z.string().regex(/^\d{3,4}$/, {
    message: "CVC must be 3 or 4 digits.",
  }),
  zip: z.string().regex(/^\d{5}(-\d{4})?$/, {
    message: "Enter a valid ZIP code (12345 or 12345-6789).",
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
  const [currentPlan] = useState("pro");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showUnsavedChanges, setShowUnsavedChanges] = useState(false);
  const [initialValues, setInitialValues] = useState(defaultValues);

  const form = useForm<SettingsFormValues>({
    resolver: zodResolver(settingsFormSchema),
    defaultValues: initialValues,
  });

  // Detect unsaved changes
  useEffect(() => {
    const subscription = form.watch((value) => {
      const hasChanges =
        JSON.stringify(value) !== JSON.stringify(initialValues);
      setShowUnsavedChanges(hasChanges);
    });
    return () => subscription.unsubscribe();
  }, [form.watch, initialValues]);

  // Format credit card number with spaces
  const formatCreditCard = (value: string) => {
    const v = value.replace(/\s+/g, "").replace(/[^0-9]/gi, "");
    const matches = v.match(/\d{4,16}/g);
    const match = matches?.[0] ?? "";
    const parts = [];
    for (let i = 0, len = match.length; i < len; i += 4) {
      parts.push(match.substring(i, i + 4));
    }
    if (parts.length) {
      return parts.join(" ");
    }
    return value;
  };

  // Format expiry date
  const formatExpiryDate = (value: string) => {
    const v = value.replace(/\s+/g, "").replace(/[^0-9]/gi, "");
    if (v.length >= 2) {
      return `${v.slice(0, 2)}/${v.slice(2, 4)}`;
    }
    return v;
  };

  async function onSubmit(data: SettingsFormValues) {
    try {
      setIsSubmitting(true);
      // Simulate API call
      await new Promise((resolve) => setTimeout(resolve, 1000));

      // TODO: Implement actual API call here
      console.log(data);

      setInitialValues(data);
      setShowUnsavedChanges(false);
      toast.success("Settings updated successfully");
    } catch (error) {
      console.error("Failed to update settings:", error);
      toast.error(
        error instanceof Error
          ? error.message
          : "Failed to update settings. Please try again.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  const resetForm = () => {
    form.reset(initialValues);
    setShowUnsavedChanges(false);
  };

  return (
    <>
      <div className="container mx-auto max-w-2xl space-y-6 p-4 pb-16">
        <div className="flex items-center justify-between">
          <div className="space-y-0.5">
            <h2 className="text-2xl font-bold tracking-tight">Settings</h2>
            <p className="text-muted-foreground">
              Manage your account settings and preferences.
            </p>
          </div>
          {showUnsavedChanges && (
            <p className="text-sm text-yellow-600">You have unsaved changes</p>
          )}
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

            <div className="flex items-center gap-4">
              <Button
                type="submit"
                disabled={isSubmitting || !showUnsavedChanges}
              >
                {isSubmitting && (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                )}
                {isSubmitting ? "Saving..." : "Save Changes"}
              </Button>
              {showUnsavedChanges && (
                <Button type="button" variant="outline" onClick={resetForm}>
                  Reset
                </Button>
              )}
            </div>
          </form>
        </Form>
      </div>

      <Dialog open={showUnsavedChanges} onOpenChange={setShowUnsavedChanges}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Unsaved Changes</DialogTitle>
            <DialogDescription>
              You have unsaved changes. Are you sure you want to leave?
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowUnsavedChanges(false)}
            >
              Stay
            </Button>
            <Button variant="destructive" onClick={resetForm}>
              Discard Changes
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Toaster />
    </>
  );
}
