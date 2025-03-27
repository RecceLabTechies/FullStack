export interface CampaignData {
  date: string; // Format: YYYY-MM-DD, stored as datetime in backend
  campaign_id: string;
  channel: string;
  age_group: string;
  ad_spend: number;
  views: number;
  leads: number;
  new_accounts: number;
  country: string;
  revenue: number;
}

export interface UserData {
  username: string;
  email: string;
  role: string;
  company: string;
  password: string;
  chart_access: boolean;
  report_generation_access: boolean;
  user_management_access: boolean;
}
