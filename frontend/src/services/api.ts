import axios from 'axios';

// Base API configuration with local proxy redirection or configurable backend URL
const API_URL = import.meta.env.VITE_API_URL || '/api/v1';

const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor to attach the auth token to every request automatically
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('fb_access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Optional interceptor to handle token expiry / redirection
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear token and redirect to login if auth expires
      localStorage.removeItem('fb_access_token');
      localStorage.removeItem('fb_user');
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default apiClient;
