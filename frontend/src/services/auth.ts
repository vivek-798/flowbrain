import apiClient from './api';

export interface UserProfile {
  id?: number;
  email: string;
  name: string;
  avatar_url: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: UserProfile;
}

export const authService = {
  // Triggers the Google Sign In flow redirect
  loginWithGoogle: () => {
    window.location.href = '/api/v1/auth/google/login';
  },

  // Processes Google callback authorization parameters
  handleCallback: async (code: string): Promise<AuthResponse> => {
    const response = await apiClient.get<AuthResponse>(`/auth/google/callback`, {
      params: { code },
    });
    
    // Store credentials in localStorage for session handling
    if (response.data.access_token) {
      localStorage.setItem('fb_access_token', response.data.access_token);
      localStorage.setItem('fb_user', JSON.stringify(response.data.user));
    }
    
    return response.data;
  },

  // Removes session tokens and logs out user
  logout: async (): Promise<void> => {
    try {
      await apiClient.post('/auth/logout');
    } catch (error) {
      console.error('Logout error on backend:', error);
    } finally {
      localStorage.removeItem('fb_access_token');
      localStorage.removeItem('fb_user');
      window.location.href = '/login';
    }
  },

  // Local state check to see if user session exists
  isAuthenticated: (): boolean => {
    return !!localStorage.getItem('fb_access_token');
  },

  // Retrieve details of authenticated founder
  getCurrentUser: (): UserProfile | null => {
    const userStr = localStorage.getItem('fb_user');
    return userStr ? JSON.parse(userStr) : null;
  }
};
