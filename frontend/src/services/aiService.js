import apiClient from '../api/client';

function normalizeAiResponse(response) {
  if (!response) return {};
  const data = response.data || response;
  return {
    ...data,
    data: data,
    success: response.success ?? true,
    message: response.message ?? '',
  };
}

export const aiService = {
  async getFinancialSummary(month = null) {
    const url = month ? `/ai/financial-summary?month=${month}` : '/ai/financial-summary';
    const response = await apiClient.get(url);
    return normalizeAiResponse(response);
  },

  async getSpendingAnalysis(days = 30) {
    const response = await apiClient.get(`/ai/spending-analysis?days=${days}`);
    return normalizeAiResponse(response);
  },

  async getSavingsSuggestions() {
    const response = await apiClient.get('/ai/savings-suggestions');
    return normalizeAiResponse(response);
  },

  async sendChatMessage({ message, transaction_id = null }) {
    const payload = { message };
    if (transaction_id) {
      payload.transaction_id = transaction_id;
    }
    const response = await apiClient.post('/ai/chat', payload);
    return normalizeAiResponse(response);
  },

  async getProviderInfo() {
    const response = await apiClient.get('/ai/provider-info');
    return normalizeAiResponse(response);
  },
};

export default aiService;
