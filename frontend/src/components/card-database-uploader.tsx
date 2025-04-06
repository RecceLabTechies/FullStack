'use client';

import { useEffect } from 'react';
import { useForm } from 'react-hook-form';

import * as z from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { Info, LoaderCircle, Upload } from 'lucide-react';
import { toast } from 'sonner';

import { Button } from '@/components/ui/button';
import { Form, FormControl, FormField, FormItem, FormMessage } from '@/components/ui/form';
import { HoverCard, HoverCardContent, HoverCardTrigger } from '@/components/ui/hover-card';
import { Label } from '@/components/ui/label';

import { useCsvUpload } from '@/hooks/use-backend-api';

import { Input } from './ui/input';

const formSchema = z.object({
  csvFile: z
    .custom<FileList>()
    .transform((files) => files?.[0])
    .refine((file): file is File => file !== undefined, {
      message: 'Please select a CSV file.',
    })
    .refine((file) => file.name.endsWith('.csv'), {
      message: 'Only CSV files are accepted.',
    }),
});

type FormSchema = z.infer<typeof formSchema>;

interface DatabaseUploaderCardProps {
  onUploadSuccess?: () => void;
}

export default function DatabaseUploaderCard({ onUploadSuccess }: DatabaseUploaderCardProps) {
  const { uploadCsv, isLoading: isUploading, data, resetData } = useCsvUpload();

  const form = useForm<FormSchema>({
    resolver: zodResolver(formSchema),
  });

  const onSubmit = async (values: FormSchema) => {
    try {
      await uploadCsv(values.csvFile);
    } catch (error) {
      console.error('Error uploading file:', error);
      toast.error(
        `Error uploading file: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
    }
  };

  // Handle successful upload
  useEffect(() => {
    if (data) {
      toast.success(`Uploaded file to cloud! (${data.count} records to ${data.collection})`);
      form.reset();
      resetData();
      onUploadSuccess?.();
    }
  }, [data, form, resetData, onUploadSuccess]);

  return (
    <>
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium">Upload Data</h3>
        <HoverCard>
          <HoverCardTrigger asChild>
            <Info size={16} className="text-muted-foreground cursor-help" />
          </HoverCardTrigger>
          <HoverCardContent className="w-80">
            <div className="space-y-2">
              <h4 className="text-sm font-semibold">CSV Upload Requirements</h4>
              <p className="text-sm text-muted-foreground">
                Uploaded CSV files will create a new collection in MongoDB. The first row should
                contain headers. Supported data types are automatically detected. File size limit is
                10MB. Required columns: date (YYYY-MM-DD), campaign_id, and metric values.
              </p>
            </div>
          </HoverCardContent>
        </HoverCard>
      </div>
      {/* File Upload Section */}
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
          <FormField
            control={form.control}
            name="csvFile"
            render={({ field: { onChange, value, ...field } }) => (
              <FormItem>
                <Label htmlFor="csv-file">CSV File</Label>
                <FormControl>
                  <div className="flex w-full max-w-sm items-center space-x-2">
                    <Input
                      id="csv-file"
                      type="file"
                      accept=".csv"
                      onChange={(e) => {
                        const files = e.target.files;
                        if (files?.length) {
                          onChange(files);
                        }
                      }}
                      disabled={isUploading}
                      {...field}
                    />
                    <Button type="submit" disabled={isUploading} size="icon">
                      {isUploading ? (
                        <LoaderCircle size={24} className="animate-spin" />
                      ) : (
                        <Upload size={24} />
                      )}
                    </Button>
                  </div>
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        </form>
      </Form>
    </>
  );
}
