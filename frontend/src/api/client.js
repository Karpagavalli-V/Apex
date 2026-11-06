import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000,
});

// Request Interceptor: Attach JWT Bearer Token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('apex_bank_token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response Interceptor: Handle Token Expiration and Normalize Errors
apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const originalRequest = error.config;

    // Handle 401 Unauthorized (expired or invalid token)
    if (error.response?.status === 401 && !originalRequest._isRetry) {
      // Do not redirect if already on login/register endpoints
      const isAuthEndpoint = originalRequest.url?.includes('/auth/login') || originalRequest.url?.includes('/auth/register');
      if (!isAuthEndpoint) {
        localStorage.removeItem('apex_bank_token');
        localStorage.removeItem('apex_bank_user');
        window.dispatchEvent(new Event('auth:session_expired'));
      }
    }

    // Extract standardized API error message
    const apiError = error.response?.data?.error;
    const message = apiError?.message || error.message || 'An unexpected error occurred. Please try again.';
    const errorCode = apiError?.code || 'UNKNOWN_ERROR';
    const status = error.response?.status || 500;

    return Promise.reject({
      message,
      code: errorCode,
      status,
      details: apiError?.details || [],
      raw: error,
    });
  }
);

export default apiClient;
