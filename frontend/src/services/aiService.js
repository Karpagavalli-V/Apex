import apiClient from '../api/client';

export const aiService = {
  async getFinancialSummary(month = null) {
    const url = month ? `/ai/financial-summary?month=${month}` : '/ai/financial-summary';
    const response = await apiClient.get(url);
    return response.data;
  },

  async getSpendingAnalysis(days = 30) {
    const response = await apiClient.get(`/ai/spending-analysis?days=${days}`);
    return response.data;
  },

  async getSavingsSuggestions() {
    const response = await apiClient.get('/ai/savings-suggestions');
    return response.data;
  },

  async sendChatMessage({ message, transaction_id = null }) {
    const payload = { message };
    if (transaction_id) {
      payload.transaction_id = transaction_id;
    }
    const response = await apiClient.post('/ai/chat', payload);
    return response.data;
  },

  async getProviderInfo() {
    const response = await apiClient.get('/ai/provider-info');
    return response.data;
  },
};

export default aiService;
