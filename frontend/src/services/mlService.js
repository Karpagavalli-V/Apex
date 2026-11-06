import apiClient from '../api/client';

export const mlService = {
  async getModelInfo() {
    const response = await apiClient.get('/ml/model-info');
    return response.data;
  },

  async predictRisk({ account_id, amount, tx_type, features }) {
    const payload = features ? { features } : { account_id, amount: Number(amount), tx_type };
    const response = await apiClient.post('/ml/predict-risk', payload);
    return response.data?.prediction || response.data;
  },

  async getAdminMetrics() {
    const response = await apiClient.get('/ml/metrics');
    return response.data;
  },

  async getFlaggedTransactions(limit = 50) {
    try {
      const response = await apiClient.get(`/ml/transactions/flagged?limit=${limit}`);
      return response.data?.flagged_transactions || response.data?.transactions || [];
    } catch {
      // If customer role gets 403 Forbidden on admin endpoint, fallback to empty or handled list
      return [];
    }
  },
};

export default mlService;
