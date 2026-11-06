import apiClient from '../api/client';

export const authService = {
  async register({ username, email, password, full_name }) {
    const response = await apiClient.post('/auth/register', {
      username,
      email,
      password,
      full_name,
    });
    return response.data;
  },

  async login({ identifier, password }) {
    const response = await apiClient.post('/auth/login', {
      identifier,
      password,
    });
    return response.data;
  },

  async getCurrentUser() {
    const response = await apiClient.get('/auth/me');
    return response.data.user;
  },

  async changePassword({ old_password, new_password }) {
    const response = await apiClient.post('/auth/change-password', {
      old_password,
      new_password,
    });
    return response;
  },

  async createAdmin({ username, email, password, full_name }) {
    const response = await apiClient.post('/auth/admin/create-admin', {
      username,
      email,
      password,
      full_name,
    });
    return response.data;
  },
};

export default authService;
