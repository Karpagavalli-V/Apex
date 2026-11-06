import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import authService from '../services/authService';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    try {
      const savedUser = localStorage.getItem('apex_bank_user');
      return savedUser ? JSON.parse(savedUser) : null;
    } catch {
      return null;
    }
  });

  const [token, setToken] = useState(() => localStorage.getItem('apex_bank_token'));
  const [loading, setLoading] = useState(true);

  const logout = useCallback(() => {
    localStorage.removeItem('apex_bank_token');
    localStorage.removeItem('apex_bank_user');
    setToken(null);
    setUser(null);
  }, []);

  // Synchronize and verify authentication state on startup
  useEffect(() => {
    const verifyAuth = async () => {
      const storedToken = localStorage.getItem('apex_bank_token');
      if (storedToken) {
        try {
          const freshUser = await authService.getCurrentUser();
          setUser(freshUser);
          localStorage.setItem('apex_bank_user', JSON.stringify(freshUser));
        } catch (err) {
          console.warn('Session verification failed, clearing auth:', err);
          logout();
        }
      }
      setLoading(false);
    };

    verifyAuth();

    // Listen for session expired events from axios interceptor
    const handleSessionExpired = () => {
      logout();
    };

    window.addEventListener('auth:session_expired', handleSessionExpired);
    return () => {
      window.removeEventListener('auth:session_expired', handleSessionExpired);
    };
  }, [logout]);

  const login = useCallback(async (identifier, password) => {
    const data = await authService.login({ identifier, password });
    const { access_token, user: loggedUser } = data;

    localStorage.setItem('apex_bank_token', access_token);
    localStorage.setItem('apex_bank_user', JSON.stringify(loggedUser));

    setToken(access_token);
    setUser(loggedUser);
    return loggedUser;
  }, []);

  const register = useCallback(async (formData) => {
    const data = await authService.register(formData);
    const { access_token, user: newUser } = data;

    localStorage.setItem('apex_bank_token', access_token);
    localStorage.setItem('apex_bank_user', JSON.stringify(newUser));

    setToken(access_token);
    setUser(newUser);
    return newUser;
  }, []);

  const value = {
    user,
    token,
    loading,
    isAuthenticated: !!token && !!user,
    isAdmin: user?.role === 'admin',
    login,
    register,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;
