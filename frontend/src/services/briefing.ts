import apiClient from './api';

export interface BriefingItem {
  id?: number;
  severity?: 'red' | 'amber' | 'green';
  title: string;
  source?: string;
  detail: string;
  financial_impact?: string;
  confidence?: 'high' | 'medium' | 'low';
}

export interface BriefingResponse {
  id: number;
  user_id: number;
  generated_at: string;
  focus: string;
  headline?: string;
  ignored_count?: number;
  about_to_break: BriefingItem[];
  needs_decision: BriefingItem[];
  wins: BriefingItem[];
}

export interface BriefingHistoryItem {
  id: number;
  user_id: number;
  generated_at: string;
  focus: string;
  wins_count: number;
  breaks_count: number;
  decisions_count: number;
}

export interface DeadlineItem {
  id: number;
  project: string;
  date: string;
  priority: 'high' | 'medium' | 'low';
}

export interface InsightsResponse {
  business_risk_score: number;
  open_risks: number;
  upcoming_deadlines: DeadlineItem[];
  activity_summary: {
    gmail: string;
    calendar: string;
    github: string;
    notion: string;
  };
}

export interface SettingsData {
  name: string;
  email: string;
  email_notifications: boolean;
  share_analytics: boolean;
  ai_provider: string;
}

export interface ClientData {
  name: string;
  value_inr: number;
  status: string;
  notes?: string;
}

export interface ProjectData {
  name: string;
  client_name: string;
  value_inr: number;
  deadline?: string;
  completion_percent: number;
  status: string;
}

export interface TeamMemberData {
  name: string;
  role: string;
  email?: string;
}

export interface BusinessContextData {
  business_type: string;
  clients: ClientData[];
  projects: ProjectData[];
  team_members: TeamMemberData[];
}

export const briefingService = {
  // Fetch latest briefing for the dashboard
  getLatestBriefing: async (): Promise<BriefingResponse> => {
    const response = await apiClient.get<BriefingResponse>('/briefing/latest');
    return response.data;
  },

  // Trigger briefing generation manually
  generateBriefing: async (): Promise<{ status: string; message: string; briefing: BriefingResponse }> => {
    const response = await apiClient.post('/briefing/generate');
    return response.data;
  },

  // Get log history of previous briefings
  getBriefingHistory: async (): Promise<BriefingHistoryItem[]> => {
    const response = await apiClient.get<BriefingHistoryItem[]>('/briefing/history');
    return response.data;
  },

  // Get founder dashboard metrics and analytics
  getInsights: async (): Promise<InsightsResponse> => {
    const response = await apiClient.get<InsightsResponse>('/insights');
    return response.data;
  },

  // Retrieve app configurations
  getSettings: async (): Promise<SettingsData> => {
    const response = await apiClient.get<SettingsData>('/settings');
    return response.data;
  },

  // Update profile or notifications
  updateSettings: async (settings: Partial<SettingsData>): Promise<SettingsData> => {
    const response = await apiClient.put<SettingsData>('/settings', settings);
    return response.data;
  },

  // Fetch user's business context details
  getBusinessContext: async (userId: number): Promise<BusinessContextData> => {
    const response = await apiClient.get<BusinessContextData>(`/business-context/${userId}`);
    return response.data;
  },

  // Update user's business context (full replace)
  updateBusinessContext: async (userId: number, data: BusinessContextData): Promise<{ status: string; message: string }> => {
    const response = await apiClient.put<{ status: string; message: string }>(`/business-context/${userId}`, data);
    return response.data;
  }
};
