import apiClient from './api';

export interface Integration {
  id: number;
  provider: string;
  connected: boolean;
  last_sync: string | null;
  email_count?: number;
  unread_count?: number;
  upcoming_events_count?: number;
}

export interface SyncResponse {
  status: string;
  synced_providers: string[];
  sync_time: string;
}

export interface GmailStats {
  total_emails: number;
  unread_emails: number;
  last_sync: string | null;
  latest_email?: {
    id: number;
    sender: string;
    subject: string;
    snippet: string;
    received_at: string;
  } | null;
}

export interface CalendarStats {
  total_events: number;
  upcoming_events: number;
  events_this_week: number;
  last_sync: string | null;
  next_event?: {
    id: number;
    title: string;
    start_time: string;
    end_time: string;
    location: string | null;
  } | null;
}

export interface DashboardOverview {
  emails_total: number;
  emails_unread: number;
  calendar_events: number;
  next_meeting: {
    id?: number;
    title?: string;
    description?: string;
    start_time?: string;
    end_time?: string;
    location?: string | null;
    meeting_link?: string | null;
    organizer?: string | null;
  } | Record<string, never>;
  gmail_connected: boolean;
  calendar_connected: boolean;
  last_sync: string;
}

export interface IntegrationStatusItem {
  connected: boolean;
  last_sync: string | null;
}

export interface IntegrationStatus {
  gmail: IntegrationStatusItem;
  calendar: IntegrationStatusItem;
  github: IntegrationStatusItem;
  notion: IntegrationStatusItem;
}

export const integrationsService = {
  // Get all active integration provider states
  getIntegrations: async (): Promise<Integration[]> => {
    const response = await apiClient.get<Integration[]>('/integrations');
    return response.data;
  },

  // Authorize connections to integrations
  connectIntegration: async (provider: string): Promise<{ status: string; message: string }> => {
    const response = await apiClient.post(`/integrations/${provider}/connect`);
    return response.data;
  },

  // Trigger data synchronization for selected providers (legacy sync endpoint)
  syncAll: async (providers?: string[]): Promise<SyncResponse> => {
    const response = await apiClient.post<SyncResponse>('/integrations/sync', {
      providers
    });
    return response.data;
  },

  // Gmail-specific stats and sync
  getGmailStats: async (): Promise<GmailStats> => {
    const response = await apiClient.get<GmailStats>('/integrations/gmail/stats');
    return response.data;
  },
  syncGmail: async (): Promise<{ emails_synced: number }> => {
    const response = await apiClient.post<{ emails_synced: number }>('/sync/gmail');
    return response.data;
  },

  // Calendar-specific stats and sync
  getCalendarStats: async (): Promise<CalendarStats> => {
    const response = await apiClient.get<CalendarStats>('/integrations/calendar/stats');
    return response.data;
  },
  syncCalendar: async (): Promise<{ events_synced: number }> => {
    const response = await apiClient.post<{ events_synced: number }>('/sync/calendar');
    return response.data;
  },

  // Get dynamic dashboard overview stats from database
  getDashboardOverview: async (): Promise<DashboardOverview> => {
    const response = await apiClient.get<DashboardOverview>('/dashboard/overview');
    return response.data;
  },

  // Get integration status using database records
  getIntegrationsStatus: async (): Promise<IntegrationStatus> => {
    const response = await apiClient.get<IntegrationStatus>('/integrations/status');
    return response.data;
  }
};
