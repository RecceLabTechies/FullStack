import { useDatabaseOperations } from '@/context/database-operations-context';

import DatabaseEditorCard from './card-database-editor';
import DatabaseUploaderCard from './card-database-uploader';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';

export default function DatabaseUploaderEditorCard() {
  const { triggerRefresh } = useDatabaseOperations();

  return (
    <Card
      className="w-full max-w-md row-span-2"
      aria-labelledby="mongo-manager-title"
      aria-describedby="mongo-manager-desc"
    >
      <CardHeader>
        <CardTitle id="mongo-manager-title">Mongo Manager</CardTitle>
        <CardDescription id="mongo-manager-desc">
          Upload new CSV files or manage existing tables
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <DatabaseUploaderCard onUploadSuccess={triggerRefresh} />
        <div className="relative">
          <div className="absolute inset-0 flex items-center">
            <span className="w-full border-t" />
          </div>
          <div className="relative flex justify-center text-xs uppercase">
            <span className="bg-background px-2 text-muted-foreground">Existing Files</span>
          </div>
        </div>
        <DatabaseEditorCard onEditSuccess={triggerRefresh} />
      </CardContent>
    </Card>
  );
}
