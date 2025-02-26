"use client";

import React, { useEffect, useState } from 'react';
import { fetchDbStructure } from '../../api/dbApi';
import { type AdCampaignData } from '@/types/adCampaignTypes';
import { LineChart, Line, XAxis, CartesianGrid, Tooltip } from 'recharts';

const LeadDateChart = () => {
  const [data, setData] = useState<AdCampaignData[]>([]);

  useEffect(() => {
    const fetchData = async () => {
      const result = await fetchDbStructure();
      const campaignData = result?.test_database?.campaign_data_mock ?? [];
      setData(campaignData);
      console.log('Fetched data:', campaignData); // Log the fetched data
    };
  
    fetchData();
  }, []);

  // Transform data for the line chart
  const transformedData = data.map((row) => ({
    date: row.date,
    leads: row.leads,
  }));

  return (
    <div>
      <h1>Lead Date Chart</h1>
      {data.length > 0 ? (
        <LineChart
          width={500}
          height={300}
          data={transformedData}
          margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <Tooltip />
          <Line type="monotone" dataKey="leads" stroke="#8884d8" />
        </LineChart>
      ) : (
        <p>Loading data...</p>
      )}
    </div>
  );
};

export default LeadDateChart;
