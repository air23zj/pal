import { api } from './api';

export const deals = {
  async getRecommendations() {
    const response = await api.get('/deals/recommendations');
    return response.data;
  },

  async summarizeDeal(description) {
    const response = await api.post('/deals/summarize', { description });
    return response.data;
  }
}; 