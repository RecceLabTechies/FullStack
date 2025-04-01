'use client';

import { Bar, BarChart, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

// Define TypeScript type for data structure
type CategoryDataPoint = {
  category: string;
  [channel: string]: string | number;
};

// Define color mapping for each channel
const CHANNEL_COLORS: Record<string, string> = {
  Influencer: '#8884d8',
  'Sponsored search ads': '#82ca9d',
  'TikTok ads': '#ffc658',
  'Instagram Ads': '#d84d4d',
  Email: '#4d79d8',
  LinkedIn: '#a832a8',
  'Radio ads': '#32a852',
  'TV ads': '#a89d32',
  'Google banner ads': '#d8a832',
};

// Transform data to be grouped by percentage categories instead of channels
const transformedData: CategoryDataPoint[] = [
  {
    category: 'Spending',
    Influencer: 10,
    'Sponsored search ads': 20,
    'TikTok ads': 20,
    'Instagram Ads': 4,
    Email: 2,
    LinkedIn: 4,
    'Radio ads': 3,
    'TV ads': 3,
    'Google banner ads': 34,
  },
  {
    category: 'Views',
    Influencer: 10,
    'Sponsored search ads': 15,
    'TikTok ads': 11,
    'Instagram Ads': 10,
    Email: 4,
    LinkedIn: 15,
    'Radio ads': 10,
    'TV ads': 15,
    'Google banner ads': 10,
  },
  {
    category: 'Leads',
    Influencer: 11,
    'Sponsored search ads': 11,
    'TikTok ads': 25,
    'Instagram Ads': 10,
    Email: 13,
    LinkedIn: 6,
    'Radio ads': 10,
    'TV ads': 4,
    'Google banner ads': 10,
  },
  {
    category: 'New Accounts',
    Influencer: 5,
    'Sponsored search ads': 10,
    'TikTok ads': 20,
    'Instagram Ads': 30,
    Email: 18,
    LinkedIn: 5,
    'Radio ads': 5,
    'TV ads': 5,
    'Google banner ads': 2,
  },
  {
    category: 'Revenue',
    Influencer: 15,
    'Sponsored search ads': 25,
    'TikTok ads': 10,
    'Instagram Ads': 10,
    Email: 5,
    LinkedIn: 10,
    'Radio ads': 10,
    'TV ads': 10,
    'Google banner ads': 5,
  },
];

export default function StackedBarChart() {
  // Get channels from the first data point safely
  const channels =
    transformedData.length > 0
      ? Object.keys(transformedData[0] ?? {}).filter((key) => key !== 'category')
      : [];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Percentage Contribution by Category</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={400}>
          <BarChart data={transformedData} margin={{ top: 20, right: 30, left: 20, bottom: 10 }}>
            <XAxis dataKey="category" />
            <YAxis tickFormatter={(tick) => `${tick}%`} />
            <Tooltip />
            <Legend />

            {/* Dynamically generate Bars for each channel */}
            {channels.filter(Boolean).map((channel) => (
              <Bar
                key={channel}
                dataKey={channel}
                stackId="a"
                fill={CHANNEL_COLORS[channel] ?? '#777777'}
                name={channel}
              />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
