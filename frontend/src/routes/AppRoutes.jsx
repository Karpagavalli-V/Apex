import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import ProtectedRoute from './ProtectedRoute';
import AppLayout from '../components/layout/AppLayout';

// Pages
import LoginPage from '../pages/LoginPage';
import RegisterPage from '../pages/RegisterPage';
import DashboardPage from '../pages/DashboardPage';
import AccountsPage from '../pages/AccountsPage';
import OperationsPage from '../pages/OperationsPage';
import TransactionsPage from '../pages/TransactionsPage';
import FraudMonitoringPage from '../pages/FraudMonitoringPage';
import AIAssistantPage from '../pages/AIAssistantPage';
import HomePage from '../pages/HomePage';

export const AppRoutes = () => {
  return (
    <Routes>
      {/* Public Authentication Routes */}
      <Route path="/" element={<HomePage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      {/* Protected Banking Dashboard Routes */}
      <Route
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/accounts" element={<AccountsPage />} />
        <Route path="/operations" element={<OperationsPage />} />
        <Route path="/transactions" element={<TransactionsPage />} />
        <Route path="/fraud-monitoring" element={<FraudMonitoringPage />} />
        <Route path="/ai-assistant" element={<AIAssistantPage />} />
      </Route>

      {/* Wildcard Fallback */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};

export default AppRoutes;
