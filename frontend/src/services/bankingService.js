import apiClient from '../api/client';
import { generateIdempotencyKey } from '../utils/idempotency';

export const bankingService = {
  async getMyAccounts() {
    const response = await apiClient.get('/accounts');
    return response.data.accounts || [];
  },

  async getAllAccounts(page = 1, limit = 20) {
    const response = await apiClient.get(`/accounts/all?page=${page}&limit=${limit}`);
    return response.data;
  },

  async getAccount(accountId) {
    const response = await apiClient.get(`/accounts/${accountId}`);
    return response.data.account;
  },

  async getAccountBalance(accountId) {
    const response = await apiClient.get(`/accounts/${accountId}/balance`);
    return response.data;
  },

  async createAccount({ account_type = 'SAVINGS', initial_deposit = 0 }) {
    const idempotencyKey = generateIdempotencyKey();
    const response = await apiClient.post(
      '/accounts',
      { account_type, initial_deposit },
      { headers: { 'Idempotency-Key': idempotencyKey } }
    );
    return response.data.account;
  },

  async deposit(accountId, { amount, description }) {
    const idempotencyKey = generateIdempotencyKey();
    const response = await apiClient.post(
      `/accounts/${accountId}/deposit`,
      { amount: Number(amount), description },
      { headers: { 'Idempotency-Key': idempotencyKey } }
    );
    return response.data;
  },

  async withdraw(accountId, { amount, description }) {
    const idempotencyKey = generateIdempotencyKey();
    const response = await apiClient.post(
      `/accounts/${accountId}/withdraw`,
      { amount: Number(amount), description },
      { headers: { 'Idempotency-Key': idempotencyKey } }
    );
    return response.data;
  },

  async transfer(accountId, { destination_account_number, target_account, amount, description }) {
    const idempotencyKey = generateIdempotencyKey();
    const target = target_account || destination_account_number;
    const response = await apiClient.post(
      `/accounts/${accountId}/transfer`,
      {
        target_account: target,
        target_account_number: target,
        destination_account_number: target,
        amount: Number(amount),
        description,
      },
      { headers: { 'Idempotency-Key': idempotencyKey } }
    );
    return response.data;
  },

  async getAccountTransactions(accountId, { page = 1, limit = 10, type = null } = {}) {
    let url = `/accounts/${accountId}/transactions?page=${page}&limit=${limit}`;
    if (type) {
      url += `&type=${type}`;
    }
    const response = await apiClient.get(url);
    return response.data;
  },
};

export default bankingService;
