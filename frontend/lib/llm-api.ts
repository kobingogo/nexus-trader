import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  timeout: 30000,
});

// --- Types ---

export interface Provider {
  id: string;
  name: string;
  type: string;
  auth_type: string;
  api_key_masked: string;
  base_url: string;
  models: string[];
  enabled: boolean;
  user_email?: string;
  user_avatar?: string;
}

export interface ActiveModel {
  provider_id: string;
  model_name: string;
}

export interface ProviderPreset {
  name: string;
  auth_type: string;
  base_url: string;
  default_models: string[];
}

// --- API ---

export const llmApi = {
  /** 获取所有已配置的提供商 */
  listProviders: async (): Promise<{ providers: Provider[] }> => {
    const response = await api.get('/llm/providers');
    return response.data;
  },

  /** 添加新提供商 */
  addProvider: async (data: {
    name: string;
    type: string;
    api_key: string;
    base_url?: string;
    models?: string[];
  }): Promise<{ provider: Provider; active_model: ActiveModel | null }> => {
    const response = await api.post('/llm/providers', data);
    return response.data;
  },

  /** 更新提供商配置 */
  updateProvider: async (
    id: string,
    data: {
      name?: string;
      api_key?: string;
      base_url?: string;
      models?: string[];
      enabled?: boolean;
    }
  ): Promise<{ provider: Provider }> => {
    const response = await api.put(`/llm/providers/${id}`, data);
    return response.data;
  },

  /** 删除提供商 */
  removeProvider: async (
    id: string
  ): Promise<{ success: boolean; active_model: ActiveModel | null }> => {
    const response = await api.delete(`/llm/providers/${id}`);
    return response.data;
  },

  /** 测试提供商连接 */
  testConnection: async (
    id: string
  ): Promise<{ success: boolean; message: string }> => {
    const response = await api.post(`/llm/providers/${id}/test`);
    return response.data;
  },

  /** 获取当前激活的模型 */
  getActiveModel: async (): Promise<{
    active_model: ActiveModel | null;
    provider: Provider | null;
  }> => {
    const response = await api.get('/llm/active');
    return response.data;
  },

  /** 切换激活模型 */
  setActiveModel: async (
    provider_id: string,
    model_name: string
  ): Promise<{ active_model: ActiveModel; provider: Provider }> => {
    const response = await api.put('/llm/active', { provider_id, model_name });
    return response.data;
  },

  /** 获取提供商预设 */
  getPresets: async (): Promise<{ presets: Record<string, ProviderPreset> }> => {
    const response = await api.get('/llm/presets');
    return response.data;
  },

  // ---- Google OAuth2 ----

  /** 获取 Google OAuth 授权 URL */
  getGoogleAuthUrl: async (): Promise<{ auth_url: string }> => {
    const response = await api.get('/llm/google/auth-url');
    return response.data;
  },

  /** 断开 Google 连接 */
  googleLogout: async (): Promise<{ success: boolean; message: string }> => {
    const response = await api.post('/llm/google/logout');
    return response.data;
  },
};
