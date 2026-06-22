import React, { createContext, useContext, useState, useEffect } from 'react';
import apiClient from '../services/api';

export interface UserProfile {
  id?: number;
  email: string;
  name: string;
  avatar_url: string;
}

interface AuthContextType {
  user: UserProfile | null;
  token: string | null;
  isAuthenticated: boolean;
  loading: boolean;
  login: (token: string, user: UserProfile) => void;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(() => {
    const savedUser = localStorage.getItem('fb_user');
    try {
      return savedUser ? JSON.parse(savedUser) : null;
    } catch {
      return null;
    }
  });
  const [token, setToken] = useState<string | null>(() => {
    return localStorage.getItem('fb_access_token');
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const verifySession = async () => {
      const storedToken = localStorage.getItem('fb_access_token');
      if (storedToken) {
        try {
          // Fetch current user from /auth/me to verify token validity
          const response = await apiClient.get<UserProfile>('/auth/me');
          setUser(response.data);
          localStorage.setItem('fb_user', JSON.stringify(response.data));
        } catch (error) {
          console.error('Session verification failed, logging out...', error);
          // Token is invalid/expired
          localStorage.removeItem('fb_access_token');
          localStorage.removeItem('fb_user');
          setToken(null);
          setUser(null);
        }
      }
      setLoading(false);
    };

    verifySession();
  }, []);

  const login = (newToken: string, newUser: UserProfile) => {
    localStorage.setItem('fb_access_token', newToken);
    localStorage.setItem('fb_user', JSON.stringify(newUser));
    setToken(newToken);
    setUser(newUser);
  };

  const logout = async () => {
    try {
      await apiClient.post('/auth/logout');
    } catch (error) {
      console.error('Logout error on backend:', error);
    } finally {
      localStorage.removeItem('fb_access_token');
      localStorage.removeItem('fb_user');
      setToken(null);
      setUser(null);
      window.location.href = '/login';
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!user,
        loading,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
