import axios from 'axios';

export const API_BASE_URL = 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000,  // 120s for slow AI responses
});

export const marketApi = {
  getHeatmap: async () => {
    const response = await api.get('/market/heatmap');
    return response.data;
  },
  getLeaders: async () => {
    const response = await api.get('/market/leaders');
    return response.data;
  },
  getSentiment: async () => {
    const response = await api.get('/market/sentiment');
    return response.data;
  },
  getMarketSentiment: async () => {
    const { data } = await api.get('/market/sentiment-radar');
    return data;
  },
  
  getMacroEvents: async () => {
    const response = await api.get('/market/macro');
    return response.data;
  },
};

export const anomalyApi = {
  scan: async (filter: string = 'all') => {
    const response = await api.get('/anomaly/scan', { params: { filter } });
    return response.data;
  },
};

export const reviewApi = {
  getDaily: async () => {
    const response = await api.get('/review/daily');
    return response.data;
  },
};

export const watchlistApi = {
  list: async () => {
    const response = await api.get('/watchlist');
    return response.data;
  },
  search: async (query: string) => {
    const response = await api.get('/watchlist/search', { params: { q: query } });
    return response.data;
  },
  add: async (code: string, name?: string, tags?: string[]) => {
    const response = await api.post('/watchlist', { code, name, tags });
    return response.data;
  },
  remove: async (code: string) => {
    const response = await api.delete(`/watchlist/${code}`);
    return response.data;
  },
  updateTags: async (code: string, tags: string[]) => {
    const response = await api.put(`/watchlist/${code}/tags`, { tags });
    return response.data;
  },
  getQuotes: async () => {
    const response = await api.get('/watchlist/quotes');
    return response.data;
  },
};

export const logicApi = {
  search: async (query: string) => {
    const response = await api.get('/logic/search', { params: { q: query } });
    return response.data;
  },
  analyze: async (query: string) => {
    const response = await api.get('/logic/analyze', { params: { q: query } });
    return response.data;
  },
};

export const aiApi = {
  diagnose: async (ticker: string) => {
    const response = await api.post('/ai/diagnose', { ticker });
    return response.data;
  },
};

export const agentApi = {
  getSignals: async (limit: number = 20) => {
    const response = await api.get('/agent/signals', { params: { limit } });
    return response.data;
  },
};
