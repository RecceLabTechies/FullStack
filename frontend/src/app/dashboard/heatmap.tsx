import { Card, CardContent } from "@/components/ui/card";

interface PlaceholderCardProps {
  title: string;
}

function PlaceholderCard({ title }: PlaceholderCardProps) {
  return (
    <Card className="transition-all duration-200 hover:shadow-md">
      <CardContent className="p-6">
        <p className="text-lg font-semibold">{title}</p>
      </CardContent>
    </Card>
  );
}

export default function PlaceholderCards() {
  return (
    <section className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
      <PlaceholderCard title="Placeholder Card 1" />
      <PlaceholderCard title="Placeholder Card 2" />
    </section>
  );
}
