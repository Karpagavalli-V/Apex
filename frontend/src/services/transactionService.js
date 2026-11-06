import apiClient from '../api/client';

export const transactionService = {
  async getMyTransactions({ page = 1, limit = 15, type = null } = {}) {
    let url = `/transactions/my-history?page=${page}&limit=${limit}`;
    if (type && type !== 'ALL') {
      url += `&type=${type}`;
    }
    const response = await apiClient.get(url);
    return response.data;
  },

  async getTransactionDetails(transactionId) {
    const response = await apiClient.get(`/transactions/${transactionId}`);
    return response.data.transaction;
  },
};

export default transactionService;
