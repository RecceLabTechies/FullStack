export interface AdCampaignData {
  _id: { $oid: string }; // MongoDB ObjectId
  ad_spend: string; // Updated to string
  age_group: string;
  avg_cost_per_lead: string; // Updated to string
  campaign_type: string;
  channel: string;
  clicks: string; // Updated to string
  date: string; // Can convert to Date if needed
  leads: string; // Updated to string
  new_accounts: string; // Updated to string
  rev_per_dollar_adspend: string; // Updated to string
  revenue: string; // Updated to string
}
