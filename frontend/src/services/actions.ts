import apiClient from './api';

export interface ActionItem {
  id: number;
  title: string;
  description: string | null;
  priority: number;
  due_date: string | null;
  financial_impact: number | null;
  source_type: 'red' | 'amber';
  source_signal: string;
  status: 'pending' | 'done' | 'dismissed';
  created_at: string;
}

export interface ActionSummary {
  total_pending: number;
  total_done: number;
  total_dismissed: number;
  total_financial_at_stake: number;
  next_due_date: string | null;
}

export const actionsService = {
  getActions: async (): Promise<ActionItem[]> => {
    const response = await apiClient.get<ActionItem[]>('/actions');
    return response.data;
  },

  updateActionStatus: async (actionId: number, status: 'done' | 'dismissed'): Promise<ActionItem> => {
    const response = await apiClient.patch<ActionItem>(`/actions/${actionId}`, { status });
    return response.data;
  },

  getActionsSummary: async (): Promise<ActionSummary> => {
    const response = await apiClient.get<ActionSummary>('/actions/summary');
    return response.data;
  },
};
